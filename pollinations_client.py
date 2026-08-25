"""Fondos fotorrealistas gratis para los mockups, vía Pollinations.ai (modelo
Flux), sin API key ni registro: https://image.pollinations.ai/prompt/...

Es un servicio externo gratuito de terceros, no necesariamente rápido ni
siempre disponible — por eso todo acá está pensado para fallar en silencio:
si no se puede traer el fondo a tiempo, quien llama se queda con el fondo de
gradiente de siempre. Nunca debe romper la generación de una pieza.

Ojo: estos modelos no escriben texto nítido de forma confiable, por eso esto
se usa SOLO como fondo ambiental (foto sin texto) — todo el contenido legible
(títulos, precios, features) lo sigue dibujando Pillow encima.
"""

import io
import random
import urllib.parse

import requests
from PIL import Image

BASE_URL = "https://image.pollinations.ai/prompt/"
TIMEOUT_SEC = 20

_PROMPTS = {
    "web": [
        "modern minimalist office desk with laptop, screen glowing softly, blurred background, photography, bokeh",
        "close up of hands typing on a laptop keyboard, coffee shop blurred background, warm light, photography",
    ],
    "bot": [
        "smartphone on a wooden desk showing a messaging app screen glow, soft bokeh background, photography",
        "person's hand holding a smartphone, blurred modern office background, warm light, photography",
    ],
    "agente": [
        "modern smartphone on a desk with a small plant and coffee cup, soft natural light, photography, bokeh",
        "tablet on a minimalist desk, soft shadows, plant in the background, photography",
    ],
    # Para slides 100% foto, sin texto ni pantalla encima: ambiente de negocio,
    # nada de dispositivos con pantalla (así no hay riesgo de texto ilegible).
    "ambiente": [
        "small modern business storefront exterior, warm afternoon light, photography, bokeh",
        "cozy small business interior with plants, warm natural light, photography",
        "entrepreneur working at a wooden desk, notebook and coffee, warm light, photography, bokeh",
        "small team having a friendly meeting in a modern office, natural light, photography",
        "hands packing a small business order into a box, warm light, photography, bokeh",
        "modern minimalist workspace with plants and natural light, photography",
    ],
}


def fetch_background(kind: str, width: int, height: int) -> Image.Image | None:
    """Intenta traer una foto de fondo para el mockup `kind`. Devuelve None si
    falla por cualquier motivo (red, rate limit, timeout, etc.) — nunca tira
    excepción, para que el pipeline siga con el fondo normal si esto falla."""
    prompt = random.choice(_PROMPTS.get(kind, _PROMPTS["web"]))
    seed = random.randint(0, 999_999)
    url = f"{BASE_URL}{urllib.parse.quote(prompt)}?width={width}&height={height}&nologo=true&seed={seed}"

    try:
        resp = requests.get(url, timeout=TIMEOUT_SEC)
        resp.raise_for_status()
        return Image.open(io.BytesIO(resp.content)).convert("RGB")
    except Exception as e:
        print(f"  (fondo con IA no disponible ahora: {e}; sigo con el fondo normal)")
        return None
