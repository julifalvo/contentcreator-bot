"""CLI: genera contenido de TikTok (texto + gráficos) para el perfil de negocios/IA.

Por defecto usa un banco local de casos reales (modo "gratis"): no llama a
ninguna API y no consume créditos. Si querés contenido dinámico (rubro,
demo, textos distintos cada vez, decididos por un modelo) sin gastar
créditos, usá --modo ollama (requiere tener Ollama corriendo en tu PC). Si
preferís la mejor calidad y no te importa el costo (centavos por pieza),
usá --modo ia (Claude).

Uso:
    python generate.py --pillar automatizacion
    python generate.py --pillar random --count 3
    python generate.py --pillar automatizacion --modo ollama
    python generate.py --pillar automatizacion --modo ia
    python generate.py --list-pillars
"""

import argparse
import json
import random
import sys
from datetime import datetime
from pathlib import Path

# La consola de Windows suele usar cp1252, que no soporta emojis/flechas.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from config import CTAS, FONT_SETS, HASHTAGS_BASE, NARRATIVE_TEMPLATES, PALETTES, PILLARS, STYLES
from image_gen import (
    render_cover, render_cta, render_demo, render_photo_slide, render_slide, render_solution_mockup,
    set_fonts, set_palette, set_photo_bg_chance, set_style,
)
from offline_client import generate_content_offline
from solution_mockups import pick_mockups, pick_mockups_ai

OUTPUT_DIR = Path(__file__).parent / "output"


def slugify(text: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in text.lower()).strip("-")[:40]


def build_piece(pillar_key: str, modo: str) -> Path:
    pillar = PILLARS[pillar_key]
    set_palette(random.choice(PALETTES))
    set_fonts(random.choice(FONT_SETS))
    set_style(random.choice(STYLES))

    if modo == "ia":
        from ai_client import generate_content

        print(f"→ Generando con IA (consume créditos) para: {pillar['label']} ...")
        content = generate_content(pillar["label"], pillar["angle"])
    elif modo == "ollama":
        from ollama_client import generate_content

        print(f"→ Generando con modelo local (Ollama, sin costo) para: {pillar['label']} ...")
        content = generate_content(pillar["label"], pillar["angle"])
    else:
        print(f"→ Generando en modo gratis (sin API) para: {pillar['label']} ...")
        content = generate_content_offline(pillar_key)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = slugify(content["portada_text"])
    folder = OUTPUT_DIR / f"{timestamp}_{pillar_key}_{slug}"
    folder.mkdir(parents=True, exist_ok=True)

    # --- Texto ---
    hashtags = content["hashtags"] or HASHTAGS_BASE
    hashtag_line = " ".join(f"#{h.lstrip('#')}" for h in hashtags)
    cta = random.choice(CTAS)

    demo = content["demo"]
    if modo == "ollama":
        print("  Generando mockups con el modelo local...")
        mockups = pick_mockups_ai(content["negocio_ejemplo"], count=2)
    else:
        mockups = pick_mockups(content["negocio_ejemplo"], count=2)
    mockup_labels = {"web": "mockup de sitio web", "bot": "mockup de flujo automatizado", "agente": "mockup de agente de recomendaciones"}
    slides = content["slides"]
    template = random.choice(NARRATIVE_TEMPLATES)
    total_slides_in_template = sum(1 for t in template if t.startswith("slide:"))

    # --- Gráficos + guion, recorriendo la plantilla narrativa elegida ---
    img_index = 0
    slide_position = 0
    script_lines: list[str] = []

    def next_path(suffix: str) -> Path:
        nonlocal img_index
        img_index += 1
        return folder / f"{img_index:02d}_{suffix}.png"

    for token in template:
        if token == "portada":
            render_cover(content["portada_text"], pillar["label"], pillar["emoji"], next_path("portada"))
            script_lines.append(f'Slide {img_index} (portada): "{content["portada_text"]}"')

        elif token.startswith("slide:"):
            slide = slides[int(token.split(":")[1])]
            render_slide(
                slide["title"], slide["text"], slide_position, total_slides_in_template,
                pillar["emoji"], next_path("slide"),
            )
            script_lines.append(f'Slide {img_index}: "{slide["title"]}" — {slide["text"]}')
            slide_position += 1

        elif token == "demo":
            render_demo(
                demo["canal"], demo["mensaje_cliente"], demo["respuesta_bot"], demo["tiempo_respuesta"],
                next_path("demo"),
            )
            script_lines.append(
                f'Slide {img_index} (demo, chat {demo["canal"]}):\n'
                f'  Cliente: "{demo["mensaje_cliente"]}"\n'
                f'  Agente: "{demo["respuesta_bot"]}"\n'
                f'  ({demo["tiempo_respuesta"]})'
            )

        elif token.startswith("mockup:"):
            mockup = mockups[int(token.split(":")[1])]
            render_solution_mockup(mockup, next_path(f"solucion_{mockup['kind']}"))
            script_lines.append(
                f'Slide {img_index} (solución, {mockup_labels[mockup["kind"]]}):\n  {mockup["caption"]}'
            )

        elif token == "foto":
            render_photo_slide(next_path("foto"))
            script_lines.append(f"Slide {img_index} (foto de ambiente, sin texto)")

        elif token == "cta":
            render_cta(content["cta_slide_text"], cta, next_path("cta"))
            script_lines.append(f'Slide {img_index} (CTA): "{content["cta_slide_text"]}"')

    script_body = "\n\n".join(script_lines)
    script_txt = f"""PILAR: {pillar['label']}
NEGOCIO DE EJEMPLO: {content['negocio_ejemplo']}

Este es un carrusel de imágenes con música de fondo, sin voz en off.
Cada línea de abajo corresponde a una imagen ya generada en esta carpeta, en orden.

{script_body}

CAPTION PARA TIKTOK:
  {content['caption']}

  {cta}

HASHTAGS:
  {hashtag_line}
"""
    content_with_mockup = {**content, "soluciones_visuales": mockups, "narrative_template": template}
    (folder / "contenido.txt").write_text(script_txt, encoding="utf-8")
    (folder / "contenido.json").write_text(
        json.dumps(content_with_mockup, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"  ✓ Listo: {folder}")
    return folder


def main() -> None:
    parser = argparse.ArgumentParser(description="Generador de contenido TikTok (automatización/IA)")
    parser.add_argument(
        "--pillar", default="random",
        choices=list(PILLARS.keys()) + ["random"],
        help="Pilar de contenido a usar (default: random)",
    )
    parser.add_argument("--count", type=int, default=1, help="Cantidad de piezas a generar")
    parser.add_argument(
        "--modo", default="gratis", choices=["gratis", "ollama", "ia"],
        help=(
            "'gratis' usa un banco local de casos, sin costo (default). "
            "'ollama' genera contenido dinámico con un modelo local (gratis, requiere Ollama corriendo). "
            "'ia' genera con Claude, consume créditos."
        ),
    )
    parser.add_argument(
        "--fondos", default="auto", choices=["auto", "siempre", "nunca"],
        help=(
            "Fondo con foto real (gratis, vía Pollinations.ai) en los mockups de bot/agente. "
            "'auto' sortea 50/50 (default), 'siempre' fuerza foto en los dos, 'nunca' usa solo degradé."
        ),
    )
    parser.add_argument("--list-pillars", action="store_true", help="Lista los pilares disponibles y sale")
    args = parser.parse_args()

    if args.list_pillars:
        for key, p in PILLARS.items():
            print(f"  {key:24s} {p['emoji']}  {p['label']}")
        return

    set_photo_bg_chance({"auto": 0.5, "siempre": 1.0, "nunca": 0.0}[args.fondos])
    OUTPUT_DIR.mkdir(exist_ok=True)

    for _ in range(args.count):
        pillar_key = random.choice(list(PILLARS.keys())) if args.pillar == "random" else args.pillar
        try:
            build_piece(pillar_key, args.modo)
        except RuntimeError as e:
            print(f"\n✗ {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
