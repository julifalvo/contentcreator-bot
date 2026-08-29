"""Genera las imágenes reales de las slides ('foto', los íconos pixel art de
'item' y los fondos a página completa del formato 'impacto'). La IA de texto
describe la escena en inglés; acá se le pide la imagen de verdad a un modelo
de imágenes.

DOS PROVEEDORES, con el mismo patrón de fallback que ai_providers.py usa para
el texto:

1. Cloudflare Workers AI con FLUX.1-schnell (`CLOUDFLARE_ACCOUNT_ID` +
   `CLOUDFLARE_API_TOKEN`). Es el bueno. Gratis de verdad y sin tarjeta:
   10.000 neurons por día, y al tamaño que usa el bot cada imagen sale ~25,
   así que entran unas 400 por día.
2. Pollinations.ai (https://pollinations.ai) como red de seguridad. No pide
   API key ni cuenta, así que SIEMPRE está disponible: si Cloudflare no está
   configurado, se quedó sin cuota o se cayó, la pieza se genera igual.

Por qué dejó de ser Pollinations el principal: su endpoint de modelos hoy
devuelve `["sana"]` para usuarios anónimos. SANA es chico y rápido, pero
bastante más flojo que FLUX — las fotos salían genéricas y planas.

Nota sobre el tamaño: flux-1-schnell en Workers AI no acepta width/height,
devuelve cuadrado. No hace falta que lo acepte: design.py sirve la foto con
`width:100%; height:auto` (se adapta al alto que venga, sin deformar), el
fondo con `object-fit:cover` y los íconos con `object-fit:contain`. Los
parámetros width/height que recibe fetch_image_data_uri se siguen respetando
en Pollinations, que sí los soporta.

La imagen se devuelve como data URI (base64 embebido), igual que hace
render.py con las fuentes: así design.py no depende de tener un archivo en
disco, y las imágenes quedan autocontenidas en el HTML que arma cada slide.
"""

import base64
import os
import urllib.parse

import requests
from dotenv import load_dotenv

load_dotenv()

WIDTH, HEIGHT = 1080, 1350  # retrato; el slide la recorta a lo que necesite
MAX_INTENTOS = 3

# --- Cloudflare Workers AI ---------------------------------------------------
CF_URL = "https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{model}"
CF_MODEL = os.environ.get("CLOUDFLARE_IMAGE_MODEL", "@cf/black-forest-labs/flux-1-schnell")
# schnell es la variante destilada de FLUX: está entrenada para dar su mejor
# resultado en pocos pasos. El máximo que acepta la API es 8, pero de 4 para
# arriba la mejora es marginal y cada paso es tiempo de espera del bot.
CF_STEPS = 4
CF_TIMEOUT = 120

# --- Pollinations ------------------------------------------------------------
POLL_URL = "https://image.pollinations.ai/prompt/{}"
# Pollinations es un servicio compartido y gratuito: a veces el primer pedido
# tarda porque el modelo estaba "frío". Reintentar con más tiempo de espera
# sale más barato que fallarle la pieza entera al usuario por una demora.
_POLL_TIMEOUTS = (40, 70, 90)


def _data_uri(raw: bytes) -> str:
    """Empaqueta los bytes de la imagen como data URI. El tipo se saca de los
    bytes y no de la cabecera Content-Type: Cloudflare devuelve el base64
    adentro de un JSON, así que ahí no hay cabecera que mirar."""
    mime = "image/png" if raw[:8] == b"\x89PNG\r\n\x1a\n" else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(raw).decode()}"


def _cloudflare_configurado() -> bool:
    return bool(os.environ.get("CLOUDFLARE_ACCOUNT_ID") and os.environ.get("CLOUDFLARE_API_TOKEN"))


def _cloudflare(prompt: str, seed: int | None, width: int, height: int) -> bytes:
    """Pide la imagen a FLUX.1-schnell en Workers AI. width/height se ignoran
    (el modelo no los acepta, ver el encabezado del módulo)."""
    url = CF_URL.format(account=os.environ["CLOUDFLARE_ACCOUNT_ID"], model=CF_MODEL)
    body: dict = {"prompt": prompt, "steps": CF_STEPS}
    if seed is not None:
        body["seed"] = seed

    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {os.environ['CLOUDFLARE_API_TOKEN']}"},
        json=body,
        timeout=CF_TIMEOUT,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Cloudflare respondió {resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    imagen = (data.get("result") or {}).get("image")
    if not imagen:
        # La API contesta 200 con success=false cuando el prompt se filtra o
        # el modelo falla, así que el código de estado solo no alcanza.
        raise RuntimeError(f"Cloudflare no devolvió imagen: {str(data.get('errors') or data)[:300]}")
    return base64.b64decode(imagen)


def _pollinations(prompt: str, seed: int | None, width: int, height: int, timeout: int) -> bytes:
    params = {"width": width, "height": height, "nologo": "true"}
    if seed is not None:
        params["seed"] = seed
    url = POLL_URL.format(urllib.parse.quote(prompt, safe=""))

    resp = requests.get(url, params=params, timeout=timeout)
    resp.raise_for_status()
    content_type = resp.headers.get("Content-Type", "image/jpeg").split(";")[0].strip()
    if not content_type.startswith("image/"):
        raise RuntimeError(f"Pollinations no devolvió una imagen (Content-Type: {content_type})")
    return resp.content


def fetch_image_data_uri(prompt: str, seed: int | None = None, width: int = WIDTH, height: int = HEIGHT) -> str:
    """Pide una imagen y la devuelve como data URI lista para un <img src="...">.
    width/height por default dan la foto vertical de las slides tipo 'foto';
    los íconos pixel art de las slides tipo 'item' piden un cuadrado más chico.

    Intenta con Cloudflare (si está configurado) y cae a Pollinations ante
    cualquier problema: quedarse sin cuota no puede costarle la pieza entera
    al usuario. Tira RuntimeError solo si fallan los dos."""
    last_error: Exception | None = None

    if _cloudflare_configurado():
        try:
            return _data_uri(_cloudflare(prompt, seed, width, height))
        except (requests.RequestException, RuntimeError, ValueError) as e:
            last_error = e
            print(f"  (imagen: Cloudflare falló: {e} — sigo con Pollinations)")

    for intento, timeout in zip(range(1, MAX_INTENTOS + 1), _POLL_TIMEOUTS):
        try:
            return _data_uri(_pollinations(prompt, seed, width, height, timeout))
        except (requests.RequestException, RuntimeError) as e:
            last_error = e
            print(f"  (imagen intento {intento}/{MAX_INTENTOS} falló: {e}, reintentando...)")

    raise RuntimeError(f"Ningún proveedor devolvió la imagen: {last_error}")


if __name__ == "__main__":
    # Prueba suelta, para verificar las credenciales de Cloudflare sin tener
    # que generar una pieza entera:
    #     python image_gen.py "a cat wearing sunglasses, realistic photo"
    # Deja la imagen en prueba_imagen.png y avisa qué proveedor la hizo.
    import sys
    from pathlib import Path

    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8", errors="replace")

    prompt = " ".join(sys.argv[1:]) or "a small bakery counter at night, realistic photo, no text"
    if _cloudflare_configurado():
        print(f"Cloudflare configurado ({CF_MODEL}). Pidiendo: {prompt}")
    else:
        print("Cloudflare NO configurado (faltan CLOUDFLARE_ACCOUNT_ID y/o "
              "CLOUDFLARE_API_TOKEN en el .env): va a usar Pollinations.")

    uri = fetch_image_data_uri(prompt)
    destino = Path(__file__).parent / "prueba_imagen.png"
    destino.write_bytes(base64.b64decode(uri.split(",", 1)[1]))
    print(f"✓ Listo: {destino} ({destino.stat().st_size // 1024} KB)")
