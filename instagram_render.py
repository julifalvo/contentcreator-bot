"""Adapta las piezas ya renderizadas (1080x1920, 9:16) a los formatos que
necesita Instagram, sin tocar el sistema de diseño (design.py/render.py):

- Reels y Stories aceptan 9:16 nativo, así que reusan el mismo PNG/MP4 tal
  cual generado para TikTok.
- El feed (carrusel de fotos) es el único que exige otra proporción: la
  Graph API solo acepta imágenes entre 4:5 y 1.91:1, y 9:16 (0.56) queda
  afuera de ese rango. En vez de rehacer a mano el layout editorial a otra
  altura -retocar cada tamaño de fuente y margen ya afinado en design.py-,
  se hace *pillarbox* del PNG ya generado: se escala completo manteniendo
  la proporción y se centra sobre un lienzo 1080x1350 del color de papel de
  la misma paleta de la pieza, como una foto puesta sobre una mesa del
  mismo color. Es una decisión de diseño (bordes del color de la paleta que
  ya trae la pieza), no un recorte que pierda contenido.
"""

from pathlib import Path

from PIL import Image

from design import PALETTES

# Recomendado por Instagram para carrusel de feed (4:5, el más alto que
# admite sin recortar en el grid).
FEED_W, FEED_H = 1080, 1350

_PALETTE_BG = {p["name"]: p["bg"] for p in PALETTES}
_BG_DEFAULT = PALETTES[0]["bg"]


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def _slides(folder: Path) -> list[Path]:
    slides = sorted(folder.glob("[0-9][0-9]_*.png"))
    if not slides:
        raise RuntimeError(f"No hay slides PNG en {folder}")
    return slides


def build_feed_images(folder: Path, palette_name: str, out_dir_name: str = "ig_feed") -> list[Path]:
    """Pillarboxea cada slide de `folder` a 1080x1350 para el carrusel de
    feed de Instagram. Devuelve las rutas nuevas, en el mismo orden que las
    slides originales. Idempotente: si ya se generaron para esta pieza, las
    reusa en vez de volver a procesarlas."""
    bg_rgb = _hex_to_rgb(_PALETTE_BG.get(palette_name, _BG_DEFAULT))

    out_dir = folder / out_dir_name
    slides = _slides(folder)
    existentes = sorted(out_dir.glob("*.png")) if out_dir.exists() else []
    if len(existentes) == len(slides):
        return existentes

    out_dir.mkdir(exist_ok=True)
    salidas = []
    for src in slides:
        img = Image.open(src).convert("RGB")
        escala = min(FEED_W / img.width, FEED_H / img.height)
        nuevo_w, nuevo_h = round(img.width * escala), round(img.height * escala)
        img_reducida = img.resize((nuevo_w, nuevo_h), Image.LANCZOS)

        lienzo = Image.new("RGB", (FEED_W, FEED_H), bg_rgb)
        lienzo.paste(img_reducida, ((FEED_W - nuevo_w) // 2, (FEED_H - nuevo_h) // 2))

        out_path = out_dir / src.name
        lienzo.save(out_path, "PNG", optimize=True, compress_level=9)
        salidas.append(out_path)

    return salidas


def story_image(folder: Path) -> Path:
    """La portada (primera slide) ya es 1080x1920: Instagram Stories acepta
    9:16 nativo, no hace falta procesarla. Las Stories no admiten carrusel,
    así que se manda solo esta, como teaser del posteo completo."""
    return _slides(folder)[0]
