"""CLI: genera un carrusel de TikTok (imágenes + caption) para el perfil de negocios/IA.

Pipeline:
    ángulo (config.PILLARS) -> Groq escribe la historia y la parte en slides
    -> design.py arma el HTML editorial de cada slide -> Chrome headless lo
    rinde a PNG 1080x1920.

Todo gratis: Groq tiene free tier sin tarjeta y el render es local.

Uso:
    python generate.py --pillar automatizacion
    python generate.py --pillar random --count 3
    python generate.py --list-pillars
"""

import argparse
import json
import random
import sys
from datetime import datetime
from pathlib import Path

# La consola de Windows suele usar cp1252, que no soporta emojis/acentos raros.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

import design
import render
from config import PILLARS
from groq_client import generate_carousel

OUTPUT_DIR = Path(__file__).parent / "output"


def slugify(text: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in text.lower()).strip("-")[:40]


def build_piece(pillar_key: str) -> Path:
    pillar = PILLARS[pillar_key]
    angulo = random.choice(pillar["angle"])
    palette = design.pick_palette()

    print(f"→ {pillar['label']} — {angulo}")
    data = generate_carousel(pillar["label"], angulo)
    print(f"  Caso: {data['negocio']} · ancla: {data['ancla']}")

    slides = data["slides"]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = OUTPUT_DIR / f"{timestamp}_{pillar_key}_{slugify(slides[0]['titular'])}"
    folder.mkdir(parents=True, exist_ok=True)

    print(f"  Renderizando {len(slides)} slides ({palette['name']})...")
    for i, slide in enumerate(slides, 1):
        html = design.build_slide_html(slide, palette, i, len(slides), kicker=pillar["label"])
        render.html_to_png(html, folder / f"{i:02d}_{slide['tipo']}.png")

    hashtag_line = " ".join(f"#{h.lstrip('#')}" for h in data["hashtags"])
    guion = "\n\n".join(
        f"Slide {i} ({s['tipo']}): "
        + " | ".join(f"{k}: {v}" for k, v in s.items() if k != "tipo")
        for i, s in enumerate(slides, 1)
    )
    (folder / "contenido.txt").write_text(
        f"""PILAR: {pillar['label']}
ÁNGULO: {angulo}
NEGOCIO: {data['negocio']}
DETALLE ANCLA: {data['ancla']}

HISTORIA (lo que el carrusel cuenta de punta a punta):
  {data['historia']}

{guion}

CAPTION PARA TIKTOK:
  {data['caption']}

HASHTAGS:
  {hashtag_line}
""",
        encoding="utf-8",
    )
    (folder / "contenido.json").write_text(
        json.dumps({**data, "paleta": palette["name"], "pilar": pillar_key, "angulo": angulo},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"  ✓ Listo: {folder}")
    return folder


def main() -> None:
    parser = argparse.ArgumentParser(description="Generador de carruseles TikTok (automatización/IA)")
    parser.add_argument("--pillar", default="random", choices=list(PILLARS) + ["random"],
                        help="Pilar de contenido (default: random)")
    parser.add_argument("--count", type=int, default=1, help="Cantidad de piezas a generar")
    parser.add_argument("--list-pillars", action="store_true", help="Lista los pilares y sale")
    args = parser.parse_args()

    if args.list_pillars:
        for key, p in PILLARS.items():
            print(f"  {key:24s} {p['label']}")
        return

    OUTPUT_DIR.mkdir(exist_ok=True)
    for _ in range(args.count):
        pillar_key = random.choice(list(PILLARS)) if args.pillar == "random" else args.pillar
        try:
            build_piece(pillar_key)
        except RuntimeError as e:
            print(f"\n✗ {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
