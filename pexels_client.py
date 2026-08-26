"""Cliente de Pexels Video API (gratis, sin límite diario fijo — solo pide
atribución, que no hace falta para uso normal en redes: https://www.pexels.com/api/).

Se usa como fuente de b-roll de fondo para el formato 'video narrado': cada
escena del guion trae una query en inglés (armada por la IA de texto) y acá
se busca un clip vertical real que la ilustre.
"""

import os
import random
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

SEARCH_URL = "https://api.pexels.com/videos/search"
MAX_INTENTOS = 3


def _api_key() -> str:
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        raise RuntimeError(
            "Falta PEXELS_API_KEY en el .env.\n"
            "Sacala gratis en https://www.pexels.com/api/ (aprobación instantánea)."
        )
    return key


def _elegir_archivo(video: dict) -> dict | None:
    """De los video_files que trae cada resultado, prioriza vertical (HD si
    hay) porque el feed es 1080x1920; si no hay ninguno vertical, se usa el
    que haya (video_narrado.py lo recorta igual con scale+crop)."""
    archivos = video.get("video_files", [])
    if not archivos:
        return None
    verticales = [a for a in archivos if (a.get("height") or 0) > (a.get("width") or 0)]
    candidatos = verticales or archivos
    # Entre los candidatos, preferimos algo cercano a 1080p de ancho: ni un
    # archivo de 320px (se ve pixelado escalado a 1080) ni uno de 4K (tarda
    # mucho en bajar para un clip de unos segundos).
    candidatos = sorted(candidatos, key=lambda a: abs((a.get("width") or 0) - 1080))
    return candidatos[0]


def buscar_clip(query: str, per_page: int = 5) -> dict:
    """Busca clips para `query` y devuelve un dict con 'url' (del archivo de
    video elegido) y 'pagina' (link a la página de Pexels, para atribución si
    hiciera falta). Elige al azar entre los primeros resultados para no repetir
    siempre el mismo clip con la misma query."""
    resp = requests.get(
        SEARCH_URL,
        headers={"Authorization": _api_key()},
        params={"query": query, "orientation": "portrait", "per_page": per_page, "size": "medium"},
        timeout=30,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Pexels respondió {resp.status_code}: {resp.text[:300]}")
    data = resp.json()
    videos = data.get("videos", [])
    if not videos:
        raise RuntimeError(f"Pexels no encontró clips para: {query!r}")

    video = random.choice(videos)
    archivo = _elegir_archivo(video)
    if archivo is None:
        raise RuntimeError(f"El clip elegido para {query!r} no trae archivos de video")

    return {"url": archivo["link"], "pagina": video.get("url", "")}


def descargar_clip(query: str, destino: Path) -> Path:
    """Busca un clip para `query` y lo descarga a `destino`. Reintenta con
    otra query genérica de respaldo si la búsqueda puntual no da resultados
    (mejor un b-roll genérico que hacer fallar toda la pieza)."""
    last_error: Exception | None = None
    for intento in range(1, MAX_INTENTOS + 1):
        try:
            clip = buscar_clip(query)
            resp = requests.get(clip["url"], timeout=90, stream=True)
            resp.raise_for_status()
            destino.parent.mkdir(parents=True, exist_ok=True)
            with destino.open("wb") as f:
                for chunk in resp.iter_content(chunk_size=1 << 16):
                    f.write(chunk)
            return destino
        except (requests.RequestException, RuntimeError) as e:
            last_error = e
            print(f"  (b-roll intento {intento}/{MAX_INTENTOS} falló para {query!r}: {e})")
            if intento == 1:
                query = "small business, people working"  # respaldo genérico

    raise RuntimeError(f"No se pudo conseguir b-roll de Pexels tras {MAX_INTENTOS} intentos: {last_error}")
