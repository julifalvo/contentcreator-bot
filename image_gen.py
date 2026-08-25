"""Generación de piezas gráficas (slides verticales 1080x1920) con Pillow."""

import random
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import pollinations_client
from config import BRAND, CANVAS_SIZE, FONTS, HANDLE, STYLE

# Probabilidad de usar una foto de fondo (gratis, vía Pollinations.ai) en vez
# del degradé de siempre en los mockups. Si el pedido falla (sin internet,
# rate limit, etc.) siempre cae de nuevo al degradé, nunca rompe la pieza.
PHOTO_BG_CHANCE = 0.5


def set_photo_bg_chance(chance: float) -> None:
    """Ajusta la probabilidad de fondo con foto (0.0 = nunca, 1.0 = siempre)."""
    global PHOTO_BG_CHANCE
    PHOTO_BG_CHANCE = chance


def set_palette(palette: dict) -> None:
    """Cambia la paleta activa (in-place, así todas las funciones de este módulo
    que ya referencian BRAND[...] la ven actualizada sin tener que pasarla
    como parámetro por todos lados)."""
    BRAND.clear()
    BRAND.update(palette)


def set_fonts(font_set: dict) -> None:
    """Cambia la combinación tipográfica activa (in-place, mismo mecanismo que set_palette)."""
    FONTS.clear()
    FONTS.update(font_set)


def set_style(style: dict) -> None:
    """Cambia el estilo de forma/layout activo (badge, esquinas, acento, progreso)."""
    STYLE.clear()
    STYLE.update(style)


def _lighten(color: tuple, amount: int) -> tuple:
    return tuple(min(255, c + amount) for c in color)

# Las fuentes del sistema usadas acá no traen glifos de emoji a color, así que
# cualquier emoji en el texto se dibujaría como un cuadro vacío ("tofu").
# Los emojis se reservan para la caption de texto plano (fuera de las imágenes).
_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F1E6-\U0001F1FF"
    "\U0000FE0F"
    "]+",
    flags=re.UNICODE,
)


def _clean(text: str) -> str:
    return _EMOJI_RE.sub("", text).strip()


def _font(kind: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONTS[kind], size)


def _lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def _gradient_background(top: tuple, bottom: tuple) -> Image.Image:
    w, h = CANVAS_SIZE
    img = Image.new("RGB", CANVAS_SIZE, top)
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / (h - 1)
        color = (
            _lerp(top[0], bottom[0], t),
            _lerp(top[1], bottom[1], t),
            _lerp(top[2], bottom[2], t),
        )
        draw.line([(0, y), (w, y)], fill=color)
    return img


def _mockup_background(kind: str) -> tuple[Image.Image, bool]:
    """Fondo para un mockup: a veces una foto real gratis (Pollinations.ai,
    sin texto, con un velo oscuro encima para que el contenido dibujado arriba
    siga siendo legible); si no hay suerte con la foto (falla, sin red, etc.)
    o no tocó por sorteo, el degradé de siempre. Devuelve (imagen, es_foto)."""
    w, h = CANVAS_SIZE
    if random.random() < PHOTO_BG_CHANCE:
        photo = pollinations_client.fetch_background(kind, w, h)
        if photo is not None:
            if photo.size != (w, h):
                photo = photo.resize((w, h))
            veil = Image.new("RGBA", (w, h), BRAND["bg_top"] + (150,))
            return Image.alpha_composite(photo.convert("RGBA"), veil).convert("RGB"), True
    return _gradient_background(BRAND["bg_top"], BRAND["bg_bottom"]), False


def render_photo_slide(out_path: Path) -> None:
    """Slide 100% foto, sin ningún texto ni título encima — solo el handle
    chiquito de siempre en el pie. Gratis, vía Pollinations.ai. Si la foto no
    está disponible (sin red, timeout, etc.) cae al degradé de marca de
    siempre, para no dejar un espacio vacío en el carrusel."""
    w, h = CANVAS_SIZE
    photo = pollinations_client.fetch_background("ambiente", w, h)
    if photo is not None:
        if photo.size != (w, h):
            photo = photo.resize((w, h))
        img = photo
    else:
        img = _gradient_background(BRAND["bg_top"], BRAND["bg_bottom"])

    # Franja oscura sutil abajo, para que el handle se lea sin importar qué
    # tan clara sea la foto que tocó.
    strip_h = 160
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    for i in range(strip_h):
        alpha = int(150 * (i / strip_h))
        odraw.line([(0, h - strip_h + i), (w, h - strip_h + i)], fill=(0, 0, 0, alpha))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    draw = ImageDraw.Draw(img)
    _draw_footer(draw)
    img.save(out_path, "PNG")


def _apply_bg_pattern(img: Image.Image) -> Image.Image:
    """Superpone una textura sutil sobre el fondo (grilla/puntos/diagonales/manchas),
    según STYLE['bg_pattern']. Usa alpha bajo para no restarle contraste al texto."""
    pattern = STYLE.get("bg_pattern", "plain")
    if pattern == "plain":
        return img

    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)

    if pattern == "dots":
        dot_rgba = BRAND["accent"] + (26,)
        for gy in range(50, h, 80):
            for gx in range(50, w, 80):
                odraw.ellipse([gx - 3, gy - 3, gx + 3, gy + 3], fill=dot_rgba)
    elif pattern == "grid":
        line_rgba = BRAND["accent"] + (16,)
        for gx in range(0, w, 100):
            odraw.line([(gx, 0), (gx, h)], fill=line_rgba, width=2)
        for gy in range(0, h, 100):
            odraw.line([(0, gy), (w, gy)], fill=line_rgba, width=2)
    elif pattern == "diagonal":
        line_rgba = BRAND["accent"] + (18,)
        for x in range(-h, w, 90):
            odraw.line([(x, 0), (x + h, h)], fill=line_rgba, width=3)
    elif pattern == "blobs":
        blob_rgba = BRAND["accent"] + (28,)
        for cx, cy, r in [(w * 0.85, h * 0.1, 300), (w * 0.05, h * 0.92, 260)]:
            odraw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=blob_rgba)

    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if bbox[2] - bbox[0] <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _fit_font(
    draw: ImageDraw.ImageDraw, text: str, kind: str, size: int, max_width: int, min_size: int = 48
) -> ImageFont.FreeTypeFont:
    """Devuelve la fuente en el tamaño pedido, achicándola si alguna palabra
    suelta no entra en `max_width` (el wrap no puede cortar palabras, así que
    sin esto una palabra larga se desborda del bloque)."""
    size_actual = size
    while size_actual > min_size:
        font = _font(kind, size_actual)
        longest = max(
            (draw.textbbox((0, 0), word, font=font)[2] - draw.textbbox((0, 0), word, font=font)[0])
            for word in text.split()
        )
        if longest <= max_width:
            return font
        size_actual -= 4
    return _font(kind, min_size)


def _draw_multiline_left(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    x: int,
    top_y: int,
    max_width: int,
    fill,
    line_spacing: float = 1.15,
) -> int:
    """Dibuja texto alineado a la izquierda desde `top_y` hacia abajo.
    Devuelve la altura total ocupada."""
    lines = _wrap_text(draw, text, font, max_width)
    line_height = int((font.getbbox("Ay")[3] - font.getbbox("Ay")[1]) * line_spacing)
    for i, line in enumerate(lines):
        draw.text((x, top_y + i * line_height), line, font=font, fill=fill)
    return line_height * len(lines)


def _draw_multiline_centered(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    center_x: int,
    center_y: int,
    max_width: int,
    fill,
    line_spacing: float = 1.15,
    align: str = "center",
) -> int:
    """Dibuja texto centrado en varias líneas. Devuelve la altura total ocupada."""
    lines = _wrap_text(draw, text, font, max_width)
    line_height = font.getbbox("Ay")[3] - font.getbbox("Ay")[1]
    line_height = int(line_height * line_spacing)
    total_height = line_height * len(lines)
    start_y = center_y - total_height // 2
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        x = center_x - line_w // 2
        y = start_y + i * line_height
        draw.text((x, y), line, font=font, fill=fill)
    return total_height


def _text_block_height(
    draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int, line_spacing: float = 1.15
) -> int:
    """Altura total que ocuparía _draw_multiline_centered, sin dibujar nada (para maquetar antes)."""
    lines = _wrap_text(draw, text, font, max_width)
    line_height = font.getbbox("Ay")[3] - font.getbbox("Ay")[1]
    return int(line_height * line_spacing) * len(lines)


def _draw_badge(draw: ImageDraw.ImageDraw, text: str, x: int, y: int) -> None:
    font = _font("bold", 34)
    bbox = draw.textbbox((0, 0), text, font=font)
    pad_x, pad_y = 34, 18
    w = (bbox[2] - bbox[0]) + pad_x * 2
    h = (bbox[3] - bbox[1]) + pad_y * 2
    radius = h // 2 if STYLE["badge_style"] == "pill" else min(STYLE["corner_radius"], h // 2)
    draw.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=BRAND["badge_bg"])
    draw.text((x + pad_x, y + pad_y - bbox[1]), text, font=font, fill=(15, 15, 25))


def _draw_footer(draw: ImageDraw.ImageDraw) -> None:
    font = _font("regular", 30)
    w, h = CANVAS_SIZE
    bbox = draw.textbbox((0, 0), HANDLE, font=font)
    text_w = bbox[2] - bbox[0]
    draw.text(((w - text_w) // 2, h - 90), HANDLE, font=font, fill=BRAND["text_dim"])


def _draw_dots(draw: ImageDraw.ImageDraw, total: int, active_index: int) -> None:
    w, h = CANVAS_SIZE
    y = h - 150

    if STYLE["progress_style"] == "bars":
        bar_w, bar_h, gap = 44, 8, 16
        total_w = total * bar_w + (total - 1) * gap
        start_x = w // 2 - total_w // 2
        for i in range(total):
            x0 = start_x + i * (bar_w + gap)
            color = BRAND["accent"] if i == active_index else (80, 84, 100)
            draw.rounded_rectangle([x0, y - bar_h // 2, x0 + bar_w, y + bar_h // 2], radius=bar_h // 2, fill=color)
        return

    dot_r = 8
    gap = 26
    start_x = w // 2 - (total * gap) // 2
    for i in range(total):
        x = start_x + i * gap
        color = BRAND["accent"] if i == active_index else (80, 84, 100)
        r = dot_r + 2 if i == active_index else dot_r
        draw.ellipse([x - r, y - r, x + r, y + r], fill=color)


def _draw_bubble(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    top_y: int,
    align: str,
    max_bubble_width: int,
    fill,
    text_fill,
    side_margin: int = 60,
    pad_x: int = 38,
    pad_y: int = 30,
    line_spacing: float = 1.3,
    radius: int = 40,
) -> int:
    """Dibuja una burbuja de chat (estilo mensajería) y devuelve su borde inferior."""
    w = CANVAS_SIZE[0]
    lines = _wrap_text(draw, text, font, max_bubble_width - pad_x * 2)
    line_height = int((font.getbbox("Ay")[3] - font.getbbox("Ay")[1]) * line_spacing)
    content_height = line_height * len(lines)
    max_line_w = max(
        draw.textbbox((0, 0), line, font=font)[2] - draw.textbbox((0, 0), line, font=font)[0]
        for line in lines
    )
    bubble_w = min(max_bubble_width, max_line_w + pad_x * 2)
    bubble_h = content_height + pad_y * 2

    if align == "left":
        x0 = side_margin
        x1 = x0 + bubble_w
    else:
        x1 = w - side_margin
        x0 = x1 - bubble_w

    draw.rounded_rectangle([x0, top_y, x1, top_y + bubble_h], radius=radius, fill=fill)
    for i, line in enumerate(lines):
        draw.text((x0 + pad_x, top_y + pad_y + i * line_height), line, font=font, fill=text_fill)
    return top_y + bubble_h


def render_demo(canal: str, mensaje_cliente: str, respuesta_bot: str, tiempo_respuesta: str, out_path: Path) -> None:
    """Slide de demo: simula un chat real cliente -> agente de IA. A veces el
    fondo es una foto real (gratis, vía Pollinations.ai) con un velo CLARO
    encima —no oscuro como en los otros mockups— para que siga leyéndose el
    texto oscuro sobre fondo claro de esta slide en particular."""
    w, h = CANVAS_SIZE
    photo = pollinations_client.fetch_background("bot", w, h) if random.random() < PHOTO_BG_CHANCE else None
    if photo is not None:
        if photo.size != (w, h):
            photo = photo.resize((w, h))
        veil = Image.new("RGBA", (w, h), (240, 242, 247, 210))
        img = Image.alpha_composite(photo.convert("RGBA"), veil).convert("RGB")
    else:
        img = _gradient_background((240, 242, 247), (221, 225, 235))
    draw = ImageDraw.Draw(img)

    # Header estilo app de chat
    header_h = 170
    draw.rectangle([0, 0, w, header_h], fill=(18, 20, 32))
    header_font = _font("bold", 42)
    label = f"{_clean(canal).upper()} - AGENTE DE IA"
    bbox = draw.textbbox((0, 0), label, font=header_font)
    label_w = bbox[2] - bbox[0]
    draw.ellipse([w // 2 - label_w // 2 - 46, header_h // 2 - 12, w // 2 - label_w // 2 - 22, header_h // 2 + 12], fill=(60, 220, 130))
    draw.text((w // 2 - label_w // 2, header_h // 2 - (bbox[3] - bbox[1]) // 2 - bbox[1]), label, font=header_font, fill=(255, 255, 255))

    tag_font = _font("bold", 28)
    body_font = _font("regular", 40)

    draw.text((60, header_h + 60), "CLIENTE", font=tag_font, fill=(140, 144, 158))
    bubble_bottom = _draw_bubble(
        draw, _clean(mensaje_cliente), body_font, top_y=header_h + 105, align="left",
        max_bubble_width=800, fill=(255, 255, 255), text_fill=(25, 25, 35),
    )

    tag_bbox = draw.textbbox((0, 0), "AGENTE DE IA", font=tag_font)
    draw.text((w - 60 - (tag_bbox[2] - tag_bbox[0]), bubble_bottom + 55), "AGENTE DE IA", font=tag_font, fill=(60, 65, 85))
    bot_bottom = _draw_bubble(
        draw, _clean(respuesta_bot), body_font, top_y=bubble_bottom + 95, align="right",
        max_bubble_width=820, fill=BRAND["accent"], text_fill=(10, 15, 25),
    )

    time_font = _font("regular", 32)
    time_text = _clean(tiempo_respuesta)
    tbbox = draw.textbbox((0, 0), time_text, font=time_font)
    draw.text((w - 60 - (tbbox[2] - tbbox[0]), bot_bottom + 22), time_text, font=time_font, fill=(120, 124, 140))

    caption_font = _font("black", 58)
    caption_y = min(bot_bottom + 280, h - 420)
    _draw_multiline_centered(
        draw, "ASI RESPONDE UN AGENTE DE IA", caption_font, w // 2, caption_y, max_width=w - 180,
        fill=(22, 24, 36), line_spacing=1.1,
    )

    footer_font = _font("regular", 30)
    fbbox = draw.textbbox((0, 0), HANDLE, font=footer_font)
    draw.text(((w - (fbbox[2] - fbbox[0])) // 2, h - 90), HANDLE, font=footer_font, fill=(110, 114, 130))

    img.save(out_path, "PNG")


def _draw_accent(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    """Dibuja el acento decorativo sobre el título de la portada; la forma varía según STYLE."""
    color = BRAND["accent"]
    shape = STYLE["accent_shape"]

    if shape == "triangle":
        draw.polygon([(x, y + 34), (x + 60, y + 34), (x + 30, y - 6)], fill=color)
    elif shape == "frame":
        length, width = 46, 8
        draw.line([(x, y), (x, y + length)], fill=color, width=width)
        draw.line([(x, y), (x + length, y)], fill=color, width=width)
    elif shape == "dots-cluster":
        for i, (dx, r) in enumerate([(0, 12), (36, 9), (66, 6)]):
            draw.ellipse([x + dx - r, y + 6 - r, x + dx + r, y + 6 + r], fill=color)
    else:  # "bar"
        draw.rectangle([x, y, x + 140, y + 10], fill=color)


COVER_LAYOUTS = ("centrado", "izquierda", "bloque")


def render_cover(
    portada_text: str, pillar_label: str, pillar_emoji: str, out_path: Path,
    layout: str = "centrado",
) -> None:
    """Portada del carrusel. `layout` cambia la composición del gancho."""
    img = _apply_bg_pattern(_gradient_background(BRAND["bg_top"], BRAND["bg_bottom"]))
    draw = ImageDraw.Draw(img)
    w, h = CANVAS_SIZE
    margin = 90
    hook = _clean(portada_text).upper()

    if layout == "izquierda":
        _draw_badge(draw, f"• {pillar_label.upper()}", margin, 90)
        max_w = w - margin * 2
        font = _fit_font(draw, hook, "black", 108, max_w)
        title_h = _text_block_height(draw, hook, font, max_w, 1.06)
        # Anclado abajo, dejando aire arriba (estilo portada editorial)
        title_top = h - 420 - title_h
        _draw_accent(draw, margin, title_top - 70)
        _draw_multiline_left(
            draw, hook, font, margin, title_top, max_w,
            fill=BRAND["text"], line_spacing=1.06,
        )
        sub_font = _font("bold", 40)
        _draw_multiline_left(
            draw, "TOCA PARA VER COMO", sub_font, margin, h - 300, max_w,
            fill=BRAND["accent"],
        )
        arrow_x, arrow_y = margin + 8, h - 232
        draw.polygon(
            [(arrow_x - 16, arrow_y), (arrow_x + 16, arrow_y), (arrow_x, arrow_y + 22)],
            fill=BRAND["accent"],
        )

    elif layout == "bloque":
        _draw_badge(draw, f"• {pillar_label.upper()}", margin, 90)
        pad_block = 56
        max_w = w - margin * 2 - pad_block * 2
        font = _fit_font(draw, hook, "black", 100, max_w)
        title_h = _text_block_height(draw, hook, font, max_w, 1.08)
        block_top = (h - (title_h + pad_block * 2)) // 2 - 60
        # Panel sólido detrás del título, con texto en color de fondo (alto contraste)
        draw.rounded_rectangle(
            [margin, block_top, w - margin, block_top + title_h + pad_block * 2],
            radius=STYLE["corner_radius"], fill=BRAND["accent"],
        )
        _draw_multiline_left(
            draw, hook, font, margin + pad_block, block_top + pad_block, max_w,
            fill=BRAND["bg_top"], line_spacing=1.08,
        )
        sub_font = _font("bold", 40)
        _draw_multiline_centered(
            draw, "TOCA PARA VER COMO", sub_font, w // 2, h - 260, max_width=w - 200,
            fill=BRAND["accent"],
        )
        arrow_y = h - 218
        draw.polygon(
            [(w // 2 - 16, arrow_y), (w // 2 + 16, arrow_y), (w // 2, arrow_y + 22)],
            fill=BRAND["accent"],
        )

    else:  # "centrado" — la composición original
        _draw_badge(draw, f"• {pillar_label.upper()}", 60, 90)
        _draw_accent(draw, 60, h // 2 - 260)
        font = _font("black", 104)
        _draw_multiline_centered(
            draw, hook, font, w // 2, h // 2, max_width=w - 160,
            fill=BRAND["text"], line_spacing=1.08,
        )
        sub_font = _font("bold", 40)
        _draw_multiline_centered(
            draw, "TOCA PARA VER COMO", sub_font, w // 2, h - 260, max_width=w - 200,
            fill=BRAND["accent"],
        )
        # Flechita dibujada a mano (no como glifo de texto): algunas de las fuentes
        # decorativas de FONT_SETS no traen el carácter ↓.
        arrow_y = h - 218
        draw.polygon(
            [(w // 2 - 16, arrow_y), (w // 2 + 16, arrow_y), (w // 2, arrow_y + 22)],
            fill=BRAND["accent"],
        )

    _draw_footer(draw)
    img.save(out_path, "PNG")


SLIDE_LAYOUTS = ("centrado", "izquierda", "numero", "barra", "abajo")


def render_slide(
    title: str, text: str, index: int, total: int, pillar_emoji: str, out_path: Path,
    layout: str = "centrado",
) -> None:
    """Dibuja un slide de contenido. `layout` cambia la composición (dónde y
    cómo se ubican título y texto) para que el carrusel no sea siempre la
    misma imagen con distinto texto."""
    img = _apply_bg_pattern(_gradient_background(BRAND["bg_top"], BRAND["bg_bottom"]))
    draw = ImageDraw.Draw(img)
    w, h = CANVAS_SIZE
    margin = 90
    max_w = w - margin * 2

    if layout == "izquierda":
        _draw_badge(draw, f"• {index + 1}/{total}", margin, 90)
        title_font = _fit_font(draw, _clean(title).upper(), "black", 88, max_w)
        body_font = _font("regular", 52)
        title_h = _text_block_height(draw, _clean(title).upper(), title_font, max_w, 1.05)
        body_h = _text_block_height(draw, _clean(text), body_font, max_w - 40, 1.3)
        block_top = (h - (title_h + 60 + body_h)) // 2
        _draw_multiline_left(
            draw, _clean(title).upper(), title_font, margin, block_top, max_w,
            fill=BRAND["accent"], line_spacing=1.05,
        )
        _draw_multiline_left(
            draw, _clean(text), body_font, margin, block_top + title_h + 60, max_w - 40,
            fill=BRAND["text"], line_spacing=1.3,
        )

    elif layout == "numero":
        num_font = _font("black", 300)
        num_text = str(index + 1)
        nbbox = draw.textbbox((0, 0), num_text, font=num_font)
        draw.text((margin - 10, 150), num_text, font=num_font, fill=BRAND["accent"])
        num_bottom = 150 + (nbbox[3] - nbbox[1]) + 90

        title_font = _fit_font(draw, _clean(title).upper(), "black", 80, max_w)
        body_font = _font("regular", 50)
        title_h = _draw_multiline_left(
            draw, _clean(title).upper(), title_font, margin, num_bottom, max_w,
            fill=BRAND["text"], line_spacing=1.05,
        )
        _draw_multiline_left(
            draw, _clean(text), body_font, margin, num_bottom + title_h + 50, max_w - 40,
            fill=BRAND["text_dim"], line_spacing=1.3,
        )

    elif layout == "barra":
        _draw_badge(draw, f"• {index + 1}/{total}", margin, 90)
        bar_x = margin
        text_x = margin + 46
        text_w = w - text_x - margin
        title_font = _fit_font(draw, _clean(title).upper(), "black", 86, text_w)
        body_font = _font("regular", 52)
        title_h = _text_block_height(draw, _clean(title).upper(), title_font, text_w, 1.05)
        body_h = _text_block_height(draw, _clean(text), body_font, text_w - 40, 1.3)
        block_top = (h - (title_h + 55 + body_h)) // 2
        # Barra vertical de acento a la izquierda de todo el bloque
        draw.rounded_rectangle(
            [bar_x, block_top, bar_x + 14, block_top + title_h + 55 + body_h],
            radius=7, fill=BRAND["accent"],
        )
        _draw_multiline_left(
            draw, _clean(title).upper(), title_font, text_x, block_top, text_w,
            fill=BRAND["text"], line_spacing=1.05,
        )
        _draw_multiline_left(
            draw, _clean(text), body_font, text_x, block_top + title_h + 55, text_w - 40,
            fill=BRAND["text_dim"], line_spacing=1.3,
        )

    elif layout == "abajo":
        _draw_badge(draw, f"• {index + 1}/{total}", margin, 90)
        title_font = _fit_font(draw, _clean(title).upper(), "black", 92, max_w)
        body_font = _font("regular", 52)
        title_h = _text_block_height(draw, _clean(title).upper(), title_font, max_w, 1.05)
        body_h = _text_block_height(draw, _clean(text), body_font, max_w - 40, 1.3)
        block_bottom = h - 300
        block_top = block_bottom - (title_h + 55 + body_h)
        _draw_multiline_left(
            draw, _clean(title).upper(), title_font, margin, block_top, max_w,
            fill=BRAND["accent"], line_spacing=1.05,
        )
        _draw_multiline_left(
            draw, _clean(text), body_font, margin, block_top + title_h + 55, max_w - 40,
            fill=BRAND["text"], line_spacing=1.3,
        )

    else:  # "centrado" — la composición original
        _draw_badge(draw, f"• {index + 1}/{total}", 60, 90)
        title_font = _font("black", 84)
        title_h = _draw_multiline_centered(
            draw, _clean(title).upper(), title_font, w // 2, h // 2 - 120, max_width=w - 160,
            fill=BRAND["accent"], line_spacing=1.05,
        )
        body_font = _font("regular", 52)
        body_y = h // 2 - 120 + title_h // 2 + 110
        _draw_multiline_centered(
            draw, _clean(text), body_font, w // 2, body_y, max_width=w - 220,
            fill=BRAND["text"], line_spacing=1.3,
        )

    _draw_dots(draw, total, index)
    _draw_footer(draw)
    img.save(out_path, "PNG")


def render_web_mockup(
    url: str, headline: str, subheadline: str, cta: str, features: list[str], caption: str, out_path: Path
) -> None:
    """Slide de solución: mockup dibujado a mano de una landing page (sin templates de terceros)."""
    w, h = CANVAS_SIZE
    img = _gradient_background((235, 237, 245), (215, 218, 232))
    draw = ImageDraw.Draw(img)

    browser_top, browser_left, browser_right = 70, 60, w - 60
    chrome_h = 90

    # Alturas de cada bloque calculadas antes de dibujar, para que el "screenshot"
    # ocupe todo el alto disponible sin dejar espacio muerto abajo.
    content_top = browser_top + chrome_h + 90
    headline_font = _font("black", 66)
    headline_h = _text_block_height(draw, _clean(headline), headline_font, browser_right - browser_left - 120, 1.08)
    headline_y = content_top + headline_h // 2

    sub_font = _font("regular", 36)
    sub_y = headline_y + headline_h // 2 + 75

    btn_font = _font("bold", 38)
    btn_text = _clean(cta)
    bbox = draw.textbbox((0, 0), btn_text, font=btn_font)
    btn_w, btn_h = (bbox[2] - bbox[0]) + 100, 100
    btn_x0, btn_y0 = w // 2 - btn_w // 2, sub_y + 110

    card_font = _font("bold", 30)
    card_y0, card_h, gap = btn_y0 + btn_h + 110, 210, 24
    card_w = (browser_right - browser_left - 80 - gap * 2) // 3

    browser_bottom = card_y0 + card_h + 70

    draw.rounded_rectangle([browser_left, browser_top, browser_right, browser_bottom], radius=28, fill=(255, 255, 255))
    draw.rectangle([browser_left, browser_top + 28, browser_right, browser_top + chrome_h], fill=(28, 30, 42))
    draw.rounded_rectangle([browser_left, browser_top, browser_right, browser_top + chrome_h], radius=28, fill=(28, 30, 42))

    for i, color in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        cx = browser_left + 40 + i * 34
        cy = browser_top + chrome_h // 2
        draw.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=color)

    url_font = _font("regular", 26)
    pill_x0, pill_x1 = browser_left + 170, browser_right - 170
    pill_y0, pill_y1 = browser_top + 22, browser_top + chrome_h - 22
    draw.rounded_rectangle([pill_x0, pill_y0, pill_x1, pill_y1], radius=(pill_y1 - pill_y0) // 2, fill=(50, 53, 70))
    draw.text((pill_x0 + 24, (pill_y0 + pill_y1) // 2 - 15), _clean(url), font=url_font, fill=(190, 194, 210))

    _draw_multiline_centered(
        draw, _clean(headline), headline_font, w // 2, headline_y, max_width=browser_right - browser_left - 120,
        fill=(18, 20, 32), line_spacing=1.08,
    )
    _draw_multiline_centered(
        draw, _clean(subheadline), sub_font, w // 2, sub_y, max_width=browser_right - browser_left - 160,
        fill=(90, 94, 115),
    )

    draw.rounded_rectangle([btn_x0, btn_y0, btn_x0 + btn_w, btn_y0 + btn_h], radius=btn_h // 2, fill=BRAND["accent"])
    draw.text(
        (btn_x0 + 50, btn_y0 + btn_h // 2 - (bbox[3] - bbox[1]) // 2 - bbox[1]),
        btn_text, font=btn_font, fill=(10, 15, 25),
    )

    for i, feat in enumerate(features[:3]):
        cx0 = browser_left + 40 + i * (card_w + gap)
        draw.rounded_rectangle([cx0, card_y0, cx0 + card_w, card_y0 + card_h], radius=STYLE["corner_radius"], fill=(244, 245, 250))
        dot_cy = card_y0 + 55
        draw.ellipse([cx0 + card_w // 2 - 18, dot_cy - 18, cx0 + card_w // 2 + 18, dot_cy + 18], fill=BRAND["accent"])
        _draw_multiline_centered(
            draw, _clean(feat), card_font, cx0 + card_w // 2, card_y0 + 135, max_width=card_w - 24,
            fill=(40, 42, 58), line_spacing=1.15,
        )

    caption_font = _font("black", 54)
    caption_y = browser_bottom + (h - 90 - browser_bottom) // 2 - 20
    _draw_multiline_centered(
        draw, _clean(caption).upper(), caption_font, w // 2, caption_y, max_width=w - 160,
        fill=(22, 24, 36), line_spacing=1.2,
    )

    footer_font = _font("regular", 30)
    fbbox = draw.textbbox((0, 0), HANDLE, font=footer_font)
    draw.text(((w - (fbbox[2] - fbbox[0])) // 2, h - 90), HANDLE, font=footer_font, fill=(110, 114, 130))

    img.save(out_path, "PNG")


def render_bot_mockup(steps: list[str], caption: str, out_path: Path) -> None:
    """Slide de solución: mockup dibujado a mano de un flujo de automatización (canvas de nodos)."""
    w, h = CANVAS_SIZE
    canvas_bg = BRAND["bg_top"]
    img, used_photo = _mockup_background("bot")
    draw = ImageDraw.Draw(img)

    if not used_photo:
        dot_color = _lighten(canvas_bg, 20)
        for gy in range(0, h, 46):
            for gx in range(0, w, 46):
                draw.ellipse([gx - 2, gy - 2, gx + 2, gy + 2], fill=dot_color)

    badge_font = _font("bold", 30)
    draw.rounded_rectangle([60, 80, 60 + 400, 80 + 64], radius=32, fill=_lighten(canvas_bg, 24))
    draw.text((90, 96), "FLUJO AUTOMATIZADO", font=badge_font, fill=BRAND["accent"])

    steps = steps[:4]
    node_font = _font("bold", 36)
    num_font = _font("black", 46)
    node_w, node_h = w - 200, 190
    node_x0, start_y, gap = 100, 300, 120
    edges = []
    for i, step in enumerate(steps):
        y0 = start_y + i * (node_h + gap)
        is_first, is_last = i == 0, i == len(steps) - 1
        color = BRAND["accent"] if is_first else ((60, 220, 130) if is_last else _lighten(canvas_bg, 30))
        text_color = (10, 15, 25) if (is_first or is_last) else BRAND["text"]
        draw.rounded_rectangle([node_x0, y0, node_x0 + node_w, y0 + node_h], radius=STYLE["corner_radius"], fill=color)
        draw.text((node_x0 + 40, y0 + 30), str(i + 1), font=num_font, fill=text_color)
        _draw_multiline_centered(
            draw, _clean(step), node_font, node_x0 + node_w // 2 + 40, y0 + node_h // 2,
            max_width=node_w - 180, fill=text_color, line_spacing=1.1,
        )
        edges.append((y0, y0 + node_h))

    for i in range(len(edges) - 1):
        x = node_x0 + node_w // 2
        y_from, y_to = edges[i][1], edges[i + 1][0]
        draw.line([(x, y_from), (x, y_to)], fill=(90, 95, 120), width=6)
        draw.polygon([(x - 16, y_to - 24), (x + 16, y_to - 24), (x, y_to)], fill=(90, 95, 120))

    flow_bottom = start_y + len(steps) * (node_h + gap) - gap
    caption_font = _font("black", 54)
    caption_y = flow_bottom + (h - 90 - flow_bottom) // 2 - 20
    _draw_multiline_centered(
        draw, _clean(caption).upper(), caption_font, w // 2, caption_y, max_width=w - 160,
        fill=BRAND["text"], line_spacing=1.2,
    )

    footer_font = _font("regular", 30)
    fbbox = draw.textbbox((0, 0), HANDLE, font=footer_font)
    draw.text(((w - (fbbox[2] - fbbox[0])) // 2, h - 90), HANDLE, font=footer_font, fill=BRAND["text_dim"])

    img.save(out_path, "PNG")


def render_agente_mockup(items: list[dict], caption: str, out_path: Path) -> None:
    """Slide de solución: mockup dibujado a mano de una interfaz de agente de recomendaciones."""
    w, h = CANVAS_SIZE
    img, _used_photo = _mockup_background("agente")
    draw = ImageDraw.Draw(img)

    header_font = _font("bold", 36)
    draw.rounded_rectangle([60, 80, w - 60, 80 + 90], radius=30, fill=_lighten(BRAND["bg_top"], 24))
    label = "AGENTE DE RECOMENDACIONES"
    bbox = draw.textbbox((0, 0), label, font=header_font)
    draw.text(
        (w // 2 - (bbox[2] - bbox[0]) // 2, 80 + 45 - (bbox[3] - bbox[1]) // 2 - bbox[1]),
        label, font=header_font, fill=BRAND["accent"],
    )

    items = items[:3]
    card_x0, card_x1 = 100, w - 100
    card_h, gap, start_y = 270, 55, 260
    name_font = _font("bold", 46)
    meta_font = _font("regular", 32)
    for i, item in enumerate(items):
        y0 = start_y + i * (card_h + gap)
        draw.rounded_rectangle([card_x0, y0, card_x1, y0 + card_h], radius=STYLE["corner_radius"], fill=(255, 255, 255))
        draw.text((card_x0 + 40, y0 + 35), _clean(item["name"]), font=name_font, fill=(18, 20, 32))
        draw.text((card_x0 + 40, y0 + 100), _clean(item["price"]), font=meta_font, fill=(90, 94, 115))

        match_label = _clean(item["match"])
        digits = "".join(c for c in match_label if c.isdigit())
        pct = int(digits) if digits else 80
        bar_x0, bar_x1 = card_x0 + 40, card_x1 - 220
        bar_y = y0 + card_h - 55
        draw.rounded_rectangle([bar_x0, bar_y, bar_x1, bar_y + 22], radius=11, fill=(230, 232, 240))
        fill_x1 = bar_x0 + int((bar_x1 - bar_x0) * pct / 100)
        draw.rounded_rectangle([bar_x0, bar_y, fill_x1, bar_y + 22], radius=11, fill=BRAND["accent"])
        draw.text((card_x1 - 190, y0 + card_h - 68), match_label, font=meta_font, fill=(40, 42, 58))

    cards_bottom = start_y + len(items) * (card_h + gap) - gap
    caption_font = _font("black", 54)
    caption_y = cards_bottom + (h - 90 - cards_bottom) // 2 - 20
    _draw_multiline_centered(
        draw, _clean(caption).upper(), caption_font, w // 2, caption_y, max_width=w - 160,
        fill=BRAND["text"], line_spacing=1.2,
    )

    footer_font = _font("regular", 30)
    fbbox = draw.textbbox((0, 0), HANDLE, font=footer_font)
    draw.text(((w - (fbbox[2] - fbbox[0])) // 2, h - 90), HANDLE, font=footer_font, fill=BRAND["text_dim"])

    img.save(out_path, "PNG")


def render_solution_mockup(mockup: dict, out_path: Path) -> None:
    """Despacha al render correspondiente según mockup['kind'] (web / bot / agente)."""
    kind = mockup["kind"]
    if kind == "web":
        render_web_mockup(
            mockup["url"], mockup["headline"], mockup["subheadline"], mockup["cta"],
            mockup["features"], mockup["caption"], out_path,
        )
    elif kind == "bot":
        render_bot_mockup(mockup["steps"], mockup["caption"], out_path)
    elif kind == "agente":
        render_agente_mockup(mockup["items"], mockup["caption"], out_path)
    else:
        raise ValueError(f"Tipo de mockup desconocido: {kind!r}")


def render_cta(cta_text: str, cta_line: str, out_path: Path) -> None:
    img = _gradient_background(BRAND["accent_2"], BRAND["accent"])
    draw = ImageDraw.Draw(img)
    w, h = CANVAS_SIZE

    font = _font("black", 96)
    top_h = _draw_multiline_centered(
        draw, _clean(cta_text).upper(), font, w // 2, h // 2 - 60, max_width=w - 160,
        fill=(15, 15, 25), line_spacing=1.05,
    )

    sub_font = _font("bold", 46)
    _draw_multiline_centered(
        draw, _clean(cta_line), sub_font, w // 2, h // 2 - 60 + top_h // 2 + 100, max_width=w - 220,
        fill=(30, 20, 10),
    )

    footer_font = _font("regular", 30)
    bbox = draw.textbbox((0, 0), HANDLE, font=footer_font)
    text_w = bbox[2] - bbox[0]
    draw.text(((w - text_w) // 2, h - 90), HANDLE, font=footer_font, fill=(60, 40, 10))

    img.save(out_path, "PNG")
