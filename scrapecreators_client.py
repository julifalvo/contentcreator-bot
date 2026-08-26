"""Cliente de ScrapeCreators (scrapecreators.com) para investigar contenido
de la competencia: trae perfil + posts recientes de cuentas de TikTok del
mismo rubro, para inspirar ángulos nuevos en config.py.

Es un servicio de PAGO por request (no tiene free tier sostenible como los
otros clientes de este proyecto) — por eso la consigna de "batchear" se
resolvió así: investigar_competencia() procesa una lista de cuentas en una
sola corrida y cachea cada resultado en research/_cache/ por unos días, para
no volver a pagar la misma cuenta si la corrés de nuevo esta semana.

Probado en vivo: el endpoint /v1/tiktok/profile funciona (autenticación,
datos de perfil, campo 'credits_remaining' para ver cuánto queda del plan).
Ese mismo response trae un 'itemList' que en teoría son los posts recientes,
pero en las dos cuentas grandes que probé (@tiktok, @mrbeast) vino vacío —
puede ser una particularidad de cuentas gigantes/globales en este scraper.
Probalo con una cuenta chica real del rubro que te interesa investigar antes
de asumir que siempre viene vacío.
"""

import json
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.environ.get("SCRAPECREATORS_BASE_URL", "https://api.scrapecreators.com")
CACHE_DIR = Path(__file__).parent / "research" / "_cache"
CACHE_TTL_HORAS = 24 * 3  # la competencia no cambia de contenido tan seguido


def _api_key() -> str:
    key = os.environ.get("SCRAPECREATORS_API_KEY")
    if not key:
        raise RuntimeError(
            "Falta SCRAPECREATORS_API_KEY en el .env. Es un servicio de pago "
            "(no free tier sostenible): https://scrapecreators.com"
        )
    return key


def _cache_path(handle: str) -> Path:
    limpio = handle.lstrip("@").strip().lower()
    return CACHE_DIR / f"tiktok_{limpio}.json"


def _desde_cache(handle: str) -> dict | None:
    path = _cache_path(handle)
    if not path.exists():
        return None
    edad_horas = (time.time() - path.stat().st_mtime) / 3600
    if edad_horas > CACHE_TTL_HORAS:
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _guardar_cache(handle: str, data: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _cache_path(handle).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def perfil_tiktok(handle: str, usar_cache: bool = True) -> dict:
    """Trae perfil + posts recientes de una cuenta de TikTok. Usa caché local
    (CACHE_TTL_HORAS) para no volver a pagar la misma cuenta en poco tiempo."""
    if usar_cache:
        cacheado = _desde_cache(handle)
        if cacheado is not None:
            return cacheado

    handle_limpio = handle.lstrip("@").strip()
    resp = requests.get(
        f"{BASE_URL}/v1/tiktok/profile",
        headers={"x-api-key": _api_key()},
        params={"handle": handle_limpio},
        timeout=30,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"ScrapeCreators respondió {resp.status_code}: {resp.text[:300]}")
    data = resp.json()
    _guardar_cache(handle, data)
    return data


def investigar_competencia(handles: list[str]) -> list[dict]:
    """Batchea la investigación de varias cuentas en una sola corrida:
    perfil + posts de cada una (con caché), para usar como inspiración de
    ángulos nuevos. No falla toda la corrida si UNA cuenta da error — la
    marca y sigue con el resto."""
    resultados = []
    for handle in handles:
        print(f"  Investigando @{handle.lstrip('@')}...")
        try:
            resultados.append({"handle": handle, "data": perfil_tiktok(handle)})
        except (RuntimeError, requests.RequestException) as e:
            print(f"  ({handle}: {e})")
            resultados.append({"handle": handle, "error": str(e)})
    return resultados


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scrapecreators_client.py @cuenta1 @cuenta2 ...")
        sys.exit(1)
    for r in investigar_competencia(sys.argv[1:]):
        print(f"\n=== {r['handle']} ===")
        if "error" in r:
            print(f"  ERROR: {r['error']}")
        else:
            print(json.dumps(r["data"], ensure_ascii=False, indent=2)[:2000])
