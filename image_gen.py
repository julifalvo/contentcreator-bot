"""Genera imágenes reales con Pollinations.ai (gratis, sin API key, sin cuenta,
sin tarjeta: https://pollinations.ai). Se usa para las slides tipo 'foto': la
IA de texto describe la escena en inglés en el campo 'prompt_imagen' y acá se
le pide la imagen de verdad al modelo de imágenes.

La imagen se devuelve como data URI (base64 embebido), igual que hace
render.py con las fuentes: así design.py no depende de tener un archivo en
disco, y las imágenes quedan autocontenidas en el HTML que arma cada slide.
"""

import base64
import urllib.parse

import requests

BASE_URL = "https://image.pollinations.ai/prompt/{}"
WIDTH, HEIGHT = 1080, 1350  # retrato; el slide la recorta a lo que necesite
MAX_INTENTOS = 3

# Pollinations es un servicio compartido y gratuito: a veces el primer pedido
# tarda porque el modelo estaba "frío". Reintentar con más tiempo de espera
# sale más barato que fallarle la pieza entera al usuario por una demora.
_TIMEOUTS = (40, 70, 90)


def fetch_image_data_uri(prompt: str, seed: int | None = None, width: int = WIDTH, height: int = HEIGHT) -> str:
    """Pide una imagen a Pollinations y la devuelve como data URI lista para
    un <img src="...">. width/height por default dan la foto vertical de las
    slides tipo 'foto'; los íconos pixel art de las slides tipo 'item' piden
    un cuadrado más chico. Tira RuntimeError si los reintentos se agotan."""
    params = {"width": width, "height": height, "nologo": "true"}
    if seed is not None:
        params["seed"] = seed
    url = BASE_URL.format(urllib.parse.quote(prompt, safe=""))

    last_error: Exception | None = None
    for intento, timeout in zip(range(1, MAX_INTENTOS + 1), _TIMEOUTS):
        try:
            resp = requests.get(url, params=params, timeout=timeout)
            resp.raise_for_status()
            content_type = resp.headers.get("Content-Type", "image/jpeg").split(";")[0].strip()
            if not content_type.startswith("image/"):
                raise RuntimeError(f"Pollinations no devolvió una imagen (Content-Type: {content_type})")
            b64 = base64.b64encode(resp.content).decode()
            return f"data:{content_type};base64,{b64}"
        except (requests.RequestException, RuntimeError) as e:
            last_error = e
            print(f"  (imagen intento {intento}/{MAX_INTENTOS} falló: {e}, reintentando...)")

    raise RuntimeError(f"Pollinations no devolvió la imagen tras {MAX_INTENTOS} intentos: {last_error}")
