"""CLI: genera un carrusel de TikTok (imágenes + caption) para el perfil de negocios/IA.

Pipeline:
    ángulo (angulos_pool.json) + contexto estratégico (audiencia.py: la
    intención de la pieza y la tensión de la audiencia contra la que se
    escribe) -> ai_providers.py le pide el texto a Groq o
    Gemini (el que esté disponible, alternando entre los dos) -> si alguna
    slide es tipo 'foto', image_gen.py le pide esa imagen al generador de
    imágenes (Cloudflare Workers AI, con Pollinations de respaldo)
    -> design.py arma el HTML editorial de cada slide -> Chrome headless lo
    rinde a PNG 1080x1920.

Todo gratis: Groq/Gemini tienen free tier sin tarjeta, las imágenes salen del
free tier de Cloudflare Workers AI (o de Pollinations, que ni API key pide), y
el render es local.

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

import angulos
import audiencia
import design
import image_gen
import mockups
import render
import video_narrado
from ai_providers import (
    generate_carousel, generate_chisme, generate_humor, generate_impacto,
    generate_sabias_que, generate_video_script,
)
from config import INTENCIONES, PILLARS, RUBROS

OUTPUT_DIR = Path(__file__).parent / "output"

# Pilares cuyo formato NO es el caso de cliente en tercera persona (llevan
# "tema" en vez de "negocio"/"ancla"/"historia" en el JSON que devuelve la IA).
_FORMATOS_SIN_CASO = {"humor", "sabias_que", "chisme", "impacto"}

# El formato 'video narrado' (voz de ElevenLabs + b-roll de Pexels, ver
# video_rules.py) todavía es solo para el caso serio de cliente en tercera
# persona: no soporta humor ni el formato educativo 'sabías que'.
PILARES_VIDEO = [k for k, p in PILLARS.items() if p.get("formato") not in _FORMATOS_SIN_CASO]


def slugify(text: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in text.lower()).strip("-")[:40]


def build_piece(pillar_key: str, angulo: str | None = None, con_foto: bool = False) -> Path:
    pillar = PILLARS[pillar_key]
    angulo = angulo or angulos.elegir_angulo(pillar_key)
    palette = design.pick_palette()
    formato = pillar.get("formato", "caso")
    sin_caso = formato in _FORMATOS_SIN_CASO
    # Para qué está hecha esta pieza (educativo/emocional/conexión/venta) y
    # contra qué problema, miedo y objeción concretos de la audiencia se
    # escribe. Se sortea por pieza, así el mismo ángulo no rinde siempre la
    # misma pieza. Ver audiencia.py.
    ctx = audiencia.contexto_de_pieza(pillar_key)

    print(f"→ {pillar['label']} — {angulo}")
    print(f"  Intención: {INTENCIONES[ctx['intencion']]['label']} · contra: {ctx['tension']['objecion']}")
    if formato == "humor":
        data = generate_humor(pillar["label"], angulo, con_foto, ctx["bloque"])
    elif formato == "sabias_que":
        data = generate_sabias_que(pillar["label"], angulo, con_foto, ctx["bloque"])
    elif formato == "chisme":
        data = generate_chisme(pillar["label"], angulo, ctx["bloque"])
    elif formato == "impacto":
        data = generate_impacto(pillar["label"], angulo, ctx["bloque"])
    else:
        rubro = random.choice(RUBROS)
        print(f"  Rubro: {rubro}")
        data = generate_carousel(pillar["label"], angulo, rubro, con_foto, ctx["bloque"])
        print(f"  Caso: {data['negocio']} · ancla: {data['ancla']}")

    slides = data["slides"]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = OUTPUT_DIR / f"{timestamp}_{pillar_key}_{slugify(slides[0]['titular'])}"
    folder.mkdir(parents=True, exist_ok=True)

    for slide in slides:
        if slide.get("tipo") == "foto":
            print(f"  Generando imagen: {slide['prompt_imagen'][:70]}...")
            slide["_img_data_uri"] = image_gen.fetch_image_data_uri(slide["prompt_imagen"])
        elif slide.get("tipo") == "item":
            print(f"  Generando ícono pixel art: {slide['icono_prompt'][:70]}...")
            icon_prompt = (
                f"pixel art icon of {slide['icono_prompt']}, 8-bit retro video game style, "
                "vibrant colors, centered single object, flat plain background, no text, "
                "no watermark, no logo"
            )
            slide["_img_data_uri"] = image_gen.fetch_image_data_uri(icon_prompt, width=700, height=700)
        elif "fondo_prompt" in slide:
            print(f"  Generando fondo llamativo: {slide['fondo_prompt'][:70]}...")
            # A diferencia de 'prompt_imagen' (foto de acompañamiento) e
            # 'icono_prompt' (ícono chico), esta imagen va a página completa
            # detrás de texto grande (ver design.py _page_fondo): necesita
            # ser dramática/vistosa por diseño para que el texto se recorte
            # fuerte, no una foto realista neutra.
            fondo_prompt = (
                f"{slide['fondo_prompt']}, dramatic cinematic lighting, bold vibrant colors, "
                "high contrast, striking eye-catching composition, professional photography, "
                "no text, no watermark, no logo"
            )
            slide["_img_data_uri"] = image_gen.fetch_image_data_uri(fondo_prompt)

    # Las variantes visuales de los mockups (telefono, navegador, diagrama):
    # una por tipo, sorteadas juntas para toda la pieza igual que la paleta.
    skins = mockups.pick_skins()
    print(f"  Renderizando {len(slides)} slides ({palette['name']} · {skins['chat']})...")
    for i, slide in enumerate(slides, 1):
        html = design.build_slide_html(slide, palette, i, len(slides), kicker=pillar["label"],
                                       skin=skins.get(slide["tipo"]))
        render.html_to_png(html, folder / f"{i:02d}_{slide['tipo']}.png")

    hashtag_line = " ".join(f"#{h.lstrip('#')}" for h in data["hashtags"])
    # '_img_data_uri' no es contenido de la IA de texto (lo agrega el paso de
    # arriba con la imagen ya descargada): afuera del guion y del JSON, o cada
    # pieza con foto dejaría un contenido.json de varios MB en base64.
    guion = "\n\n".join(
        f"Slide {i} ({s['tipo']}): "
        + " | ".join(f"{k}: {v}" for k, v in s.items() if k not in ("tipo", "_img_data_uri"))
        for i, s in enumerate(slides, 1)
    )
    intencion_label = INTENCIONES[ctx["intencion"]]["label"]
    if sin_caso:
        cabecera = f"""PILAR: {pillar['label']}
INTENCIÓN: {intencion_label}
ÁNGULO: {angulo}
TEMA: {data['tema']}"""
    else:
        cabecera = f"""PILAR: {pillar['label']}
INTENCIÓN: {intencion_label}
ÁNGULO: {angulo}
NEGOCIO: {data['negocio']}
DETALLE ANCLA: {data['ancla']}

HISTORIA (lo que el carrusel cuenta de punta a punta):
  {data['historia']}"""

    (folder / "contenido.txt").write_text(
        f"""{cabecera}

{guion}

CAPTION PARA TIKTOK:
  {data['caption']}

HASHTAGS:
  {hashtag_line}
""",
        encoding="utf-8",
    )
    data_sin_imagenes = {
        **data,
        "slides": [{k: v for k, v in s.items() if k != "_img_data_uri"} for s in slides],
    }
    (folder / "contenido.json").write_text(
        json.dumps({**data_sin_imagenes, "formato": "carrusel", "paleta": palette["name"],
                    "pilar": pillar_key, "angulo": angulo, "skins": skins,
                    "intencion": ctx["intencion"], "tension": ctx["tension"]},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"  ✓ Listo: {folder}")
    return folder


def build_video_piece(pillar_key: str, angulo: str | None = None) -> Path:
    """Arma un video narrado (voz de ElevenLabs + b-roll de Pexels) en vez de
    un carrusel de imágenes. Solo para los pilares de caso (no humor, ver
    PILARES_VIDEO)."""
    if pillar_key not in PILARES_VIDEO:
        raise ValueError(f"El pilar '{pillar_key}' no soporta el formato video (solo: {PILARES_VIDEO})")

    pillar = PILLARS[pillar_key]
    angulo = angulo or angulos.elegir_angulo(pillar_key)
    rubro = random.choice(RUBROS)

    ctx = audiencia.contexto_de_pieza(pillar_key)

    print(f"→ [video] {pillar['label']} — {angulo}")
    print(f"  Rubro: {rubro} · intención: {INTENCIONES[ctx['intencion']]['label']}")
    data = generate_video_script(pillar["label"], angulo, rubro, ctx["bloque"])
    print(f"  Caso: {data['negocio']} · ancla: {data['ancla']}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = OUTPUT_DIR / f"{timestamp}_{pillar_key}_video_{slugify(data['negocio'])}"
    folder.mkdir(parents=True, exist_ok=True)

    print(f"  Armando video ({len(data['escenas'])} escenas: locución + b-roll)...")
    video_narrado.build_video(folder, data)

    hashtag_line = " ".join(f"#{h.lstrip('#')}" for h in data["hashtags"])
    guion = "\n\n".join(
        f"Escena {i}: {e['narracion']}"
        + f"\n  (b-roll: {e['b_roll']})"
        for i, e in enumerate(data["escenas"], 1)
    )
    (folder / "contenido.txt").write_text(
        f"""PILAR: {pillar['label']}
INTENCIÓN: {INTENCIONES[ctx['intencion']]['label']}
ÁNGULO: {angulo}
NEGOCIO: {data['negocio']}
DETALLE ANCLA: {data['ancla']}

HISTORIA (lo que el video cuenta de punta a punta):
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
        json.dumps({**data, "formato": "video", "pilar": pillar_key, "angulo": angulo,
                    "intencion": ctx["intencion"], "tension": ctx["tension"]},
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
    parser.add_argument("--foto", action="store_true",
                        help="Permite que el modelo elija una slide de foto real (IA). Off por default.")
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
            build_piece(pillar_key, con_foto=args.foto)
        except RuntimeError as e:
            print(f"\n✗ {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
