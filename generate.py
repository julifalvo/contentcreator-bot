"""CLI: genera un carrusel de TikTok (imágenes + caption) para el perfil de negocios/IA.

Pipeline:
    ángulo (angulos_pool.json) + contexto estratégico (audiencia.py: la
    intención de la pieza y la tensión de la audiencia contra la que se
    escribe) -> ai_providers.py le pide el texto a Groq o
    Gemini (el que esté disponible, alternando entre los dos) -> si alguna
    slide es tipo 'foto', image_gen.py le pide esa imagen al generador de
    imágenes (Cloudflare Workers AI, con Pollinations de respaldo)
    -> design.py arma el HTML editorial de cada slide -> Chrome headless lo
    rinde a PNG 1080x1920 (9:16, el tamaño que TikTok recomienda).

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
import demo_build
import design
import image_gen
import mockups
import reel_build
import render
import video_narrado
from ai_providers import (
    generate_carousel, generate_chisme, generate_demo, generate_humor, generate_ig_caption,
    generate_impacto, generate_reel, generate_sabias_que, generate_video_script,
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


def build_demo_piece(pillar_key: str, angulo: str | None = None) -> Path:
    """Arma un DEMO animado (ver demo_build.py / demo_designs.py): un video de
    demostraciones gráficas rápidas de la solución funcionando —un agente
    contestando, una agenda llenándose, la facturación subiendo— en vez de
    slides estáticas o b-roll de stock.

    Usa los mismos pilares de caso que el video narrado y el reel (ver
    PILARES_VIDEO): el guion es el caso de un cliente en tercera persona, y
    las escenas son lo que se ve de ese caso funcionando."""
    if pillar_key not in PILARES_VIDEO:
        raise ValueError(f"El pilar '{pillar_key}' no soporta el formato demo (solo: {PILARES_VIDEO})")

    pillar = PILLARS[pillar_key]
    angulo = angulo or angulos.elegir_angulo(pillar_key)
    rubro = random.choice(RUBROS)
    ctx = audiencia.contexto_de_pieza(pillar_key)

    print(f"→ [demo] {pillar['label']} — {angulo}")
    print(f"  Rubro: {rubro} · intención: {INTENCIONES[ctx['intencion']]['label']}")
    data = generate_demo(pillar["label"], angulo, rubro, ctx["bloque"])
    print(f"  Caso: {data['negocio']} · ancla: {data['ancla']}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = OUTPUT_DIR / f"{timestamp}_{pillar_key}_demo_{slugify(data['negocio'])}"
    folder.mkdir(parents=True, exist_ok=True)

    escenas = data["escenas"]
    print(f"  Escenas: {', '.join(e['tipo'] for e in escenas)}")
    demo_build.build_demo(folder, data)

    hashtag_line = " ".join(f"#{h.lstrip('#')}" for h in data["hashtags"])
    guion = "\n\n".join(
        f"Escena {i} ({e['tipo']}): {e.get('titular','')}"
        + (f"\n  {e['bajada']}" if e.get("bajada") else "")
        for i, e in enumerate(escenas, 1)
    )
    (folder / "contenido.txt").write_text(
        f"""PILAR: {pillar['label']}
INTENCIÓN: {INTENCIONES[ctx['intencion']]['label']}
ÁNGULO: {angulo}
NEGOCIO: {data['negocio']}
DETALLE ANCLA: {data['ancla']}

HISTORIA (lo que el demo muestra de punta a punta):
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
        json.dumps({**data, "formato": "demo", "pilar": pillar_key, "angulo": angulo,
                    "intencion": ctx["intencion"], "tension": ctx["tension"]},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"  ✓ Listo: {folder}")
    return folder


def build_tip_reel_piece(angulo: str | None = None) -> Path:
    """Arma un Reel 'aesthetic' (formato 'reel_tips', ver reel_build.build_tip_reel):
    mismo contenido educativo de 'sabías que...?' (generate_sabias_que, sin
    caso de cliente ni solución puntual) que el carrusel de ese pilar, pero
    en vez del papel editorial cada slide sale como una tarjeta flotante
    arriba de un único clip de b-roll "aesthetic" (laptop, café, escritorio)
    que se repite en todo el video — el look de fondo+popup que pidió este
    formato. Fijo al pilar 'sabias_que': es el único cuyo contenido (un dato o
    consejo suelto, sin caso) calza con una tarjeta individual."""
    pillar_key = "sabias_que"
    pillar = PILLARS[pillar_key]
    angulo = angulo or angulos.elegir_angulo(pillar_key)
    ctx = audiencia.contexto_de_pieza(pillar_key)

    print(f"→ [reel tips] {pillar['label']} — {angulo}")
    print(f"  Intención: {INTENCIONES[ctx['intencion']]['label']}")
    data = generate_sabias_que(pillar["label"], angulo, False, ctx["bloque"])

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = OUTPUT_DIR / f"{timestamp}_{pillar_key}_reeltips_{slugify(data['tema'])}"
    folder.mkdir(parents=True, exist_ok=True)

    print(f"  Armando reel ({len(data['slides'])} tarjetas sobre un fondo aesthetic fijo)...")
    reel_build.build_tip_reel(folder, data)

    hashtag_line = " ".join(f"#{h.lstrip('#')}" for h in data["hashtags"])
    guion = "\n\n".join(
        f"Slide {i} ({s['tipo']}): " + " | ".join(f"{k}: {v}" for k, v in s.items() if k != "tipo")
        for i, s in enumerate(data["slides"], 1)
    )
    (folder / "contenido.txt").write_text(
        f"""PILAR: {pillar['label']}
INTENCIÓN: {INTENCIONES[ctx['intencion']]['label']}
ÁNGULO: {angulo}
TEMA: {data['tema']}

{guion}

CAPTION PARA TIKTOK:
  {data['caption']}

HASHTAGS:
  {hashtag_line}
""",
        encoding="utf-8",
    )
    (folder / "contenido.json").write_text(
        json.dumps({**data, "formato": "reel_tips", "pilar": pillar_key, "angulo": angulo,
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


def build_reel_piece(pillar_key: str, angulo: str | None = None) -> Path:
    """Arma un Reel de texto en pantalla (b-roll real de Pexels + texto
    superpuesto por beat, SIN voz generada por IA — ver reel_rules.py/
    reel_build.py) en vez de un carrusel o un video narrado. Mismos pilares
    de caso que el video narrado (ver PILARES_VIDEO)."""
    if pillar_key not in PILARES_VIDEO:
        raise ValueError(f"El pilar '{pillar_key}' no soporta el formato reel (solo: {PILARES_VIDEO})")

    pillar = PILLARS[pillar_key]
    angulo = angulo or angulos.elegir_angulo(pillar_key)
    rubro = random.choice(RUBROS)

    ctx = audiencia.contexto_de_pieza(pillar_key)

    print(f"→ [reel] {pillar['label']} — {angulo}")
    print(f"  Rubro: {rubro} · intención: {INTENCIONES[ctx['intencion']]['label']}")
    data = generate_reel(pillar["label"], angulo, rubro, ctx["bloque"])
    print(f"  Caso: {data['negocio']} · ancla: {data['ancla']} · objetivo: {data['objetivo_comercial']}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = OUTPUT_DIR / f"{timestamp}_{pillar_key}_reel_{slugify(data['negocio'])}"
    folder.mkdir(parents=True, exist_ok=True)

    beats = [data["hook"], *data["desarrollo"], data["cta"]]
    print(f"  Armando reel ({len(beats)} beats: b-roll + texto en pantalla, sin voz)...")
    reel_build.build_reel(folder, data)

    hashtag_line = " ".join(f"#{h.lstrip('#')}" for h in data["hashtags"])
    guion = "\n\n".join(
        [f"HOOK: {data['hook']['texto_pantalla']}\n  (visual: {data['hook']['visual']})"]
        + [
            f"Desarrollo {i}: {b['texto_pantalla']}\n  (visual: {b['visual']})"
            for i, b in enumerate(data["desarrollo"], 1)
        ]
        + [f"CTA: {data['cta']['texto_pantalla']}\n  (visual: {data['cta']['visual']})"]
    )
    (folder / "contenido.txt").write_text(
        f"""PILAR: {pillar['label']}
INTENCIÓN: {INTENCIONES[ctx['intencion']]['label']}
ÁNGULO: {angulo}
OBJETIVO COMERCIAL: {data['objetivo_comercial']}
NEGOCIO: {data['negocio']}
DETALLE ANCLA: {data['ancla']}

HISTORIA (lo que el reel cuenta de punta a punta):
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
        json.dumps({**data, "formato": "reel", "pilar": pillar_key, "angulo": angulo,
                    "intencion": ctx["intencion"], "tension": ctx["tension"]},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"  ✓ Listo: {folder}")
    return folder


def asegurar_caption_ig(folder: Path) -> dict:
    """Genera el caption nativo de Instagram (content_rules.SYSTEM_PROMPT_IG_CAPTION)
    a partir del contenido YA generado para TikTok, y lo cachea en
    contenido.json para no volver a pedirlo si /publicar reintenta la misma
    pieza. Devuelve {"caption_ig": ..., "hashtags_ig": [...]}."""
    content_path = folder / "contenido.json"
    data = json.loads(content_path.read_text(encoding="utf-8"))
    if "caption_ig" in data:
        return {"caption_ig": data["caption_ig"], "hashtags_ig": data["hashtags_ig"]}

    partes = [
        f"PILAR: {PILLARS.get(data.get('pilar'), {}).get('label', data.get('pilar', ''))}",
        f"ÁNGULO: {data.get('angulo', '')}",
    ]
    if "historia" in data:
        partes.append(f"NEGOCIO: {data.get('negocio', '')}\nANCLA: {data.get('ancla', '')}\nHISTORIA: {data['historia']}")
    elif "tema" in data:
        partes.append(f"TEMA: {data['tema']}")
    partes.append(f"CAPTION ORIGINAL (TikTok): {data.get('caption', '')}")
    partes.append(f"HASHTAGS ORIGINALES: {', '.join(data.get('hashtags', []))}")

    ig = generate_ig_caption("\n\n".join(partes))
    data["caption_ig"] = ig["caption_ig"]
    data["hashtags_ig"] = ig["hashtags_ig"]
    content_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return ig


def main() -> None:
    parser = argparse.ArgumentParser(description="Generador de carruseles TikTok (automatización/IA)")
    parser.add_argument("--pillar", default="random", choices=list(PILLARS) + ["random"],
                        help="Pilar de contenido (default: random)")
    parser.add_argument("--count", type=int, default=1, help="Cantidad de piezas a generar")
    parser.add_argument("--foto", action="store_true",
                        help="Permite que el modelo elija una slide de foto real (IA). Off por default.")
    parser.add_argument("--tip-reel", action="store_true",
                        help="Genera un Reel 'aesthetic' (fondo laptop+café fijo + tarjetas de 'sabías que...?') "
                             "en vez de un carrusel. Ignora --pillar/--foto: siempre usa el pilar sabias_que.")
    parser.add_argument("--demo", action="store_true",
                        help="Genera un DEMO animado (escenas gráficas rápidas de la solución funcionando) "
                             "en vez de un carrusel. Usa --pillar (solo pilares de caso).")
    parser.add_argument("--list-pillars", action="store_true", help="Lista los pilares y sale")
    args = parser.parse_args()

    if args.list_pillars:
        for key, p in PILLARS.items():
            print(f"  {key:24s} {p['label']}")
        return

    OUTPUT_DIR.mkdir(exist_ok=True)
    for _ in range(args.count):
        try:
            if args.tip_reel:
                build_tip_reel_piece()
                continue
            if args.demo:
                pillar_key = random.choice(PILARES_VIDEO) if args.pillar == "random" else args.pillar
                build_demo_piece(pillar_key)
                continue
            pillar_key = random.choice(list(PILLARS)) if args.pillar == "random" else args.pillar
            build_piece(pillar_key, con_foto=args.foto)
        except RuntimeError as e:
            print(f"\n✗ {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
