"""Generación de contenido con Google Gemini (gratis, límite diario, sin
tarjeta: https://aistudio.google.com/apikey). Segundo proveedor de texto,
para alternar con Groq (groq_client.py) vía ai_providers.py — así ninguno de
los dos free tiers se agota solo y hay margen para generar más piezas por día.

Misma interfaz pública que groq_client.py (generate_carousel/generate_humor)
y mismos prompts/validación (content_rules.py), para que a ai_providers.py le
dé exactamente lo mismo cuál de los dos haya respondido.
"""

import json
import os
import re
import time

import requests
from dotenv import load_dotenv

import chisme_rules
import content_rules
import video_rules

load_dotenv()

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
MAX_RETRIES = 4


def _api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError(
            "Falta GEMINI_API_KEY en el .env.\n"
            "Sacala gratis (sin tarjeta) en https://aistudio.google.com/apikey."
        )
    return key


def _post(system: str, user: str) -> dict:
    """Hace el pedido a Gemini. Si devuelve 429 por límite de minuto, o 503
    porque el modelo está saturado (Google lo describe como "temporary"),
    reintenta una vez con una espera corta; si persiste (o es cuota diaria)
    tira RuntimeError para que ai_providers.py pruebe con el otro proveedor
    en vez de quedarse esperando en banda."""
    url = API_URL.format(model=MODEL)
    body = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {
            "temperature": 0.85,
            "response_mime_type": "application/json",
        },
    }

    for intento in range(2):
        resp = requests.post(url, params={"key": _api_key()}, json=body, timeout=120)
        if resp.status_code == 429:
            espera = 20.0
            match = re.search(r'"retryDelay":\s*"(\d+)s"', resp.text)
            if match:
                espera = min(float(match.group(1)) + 1, 30.0)
            if intento == 0:
                print(f"  (Gemini: límite de tasa, espero {espera:.0f}s...)")
                time.sleep(espera)
                continue
            raise RuntimeError(f"Gemini sin cuota disponible por ahora: {resp.text[:200]}")
        if resp.status_code == 503:
            if intento == 0:
                print("  (Gemini: modelo saturado, espero 10s y reintento...)")
                time.sleep(10)
                continue
            raise RuntimeError(f"Gemini saturado tras reintentar: {resp.text[:200]}")
        if resp.status_code != 200:
            raise RuntimeError(f"Gemini respondió {resp.status_code}: {resp.text[:400]}")
        return resp.json()

    raise RuntimeError("Gemini siguió rechazando por límite de tasa tras reintentar.")


def _extraer_texto(payload: dict) -> str:
    candidatos = payload.get("candidates") or []
    if not candidatos:
        motivo = payload.get("promptFeedback", {}).get("blockReason", "sin candidatos")
        raise RuntimeError(f"Gemini no devolvió contenido ({motivo})")
    partes = candidatos[0].get("content", {}).get("parts", [])
    texto = "".join(p.get("text", "") for p in partes)
    if not texto:
        raise RuntimeError(f"Gemini devolvió una respuesta vacía (finishReason: {candidatos[0].get('finishReason')})")
    return texto


def generate_carousel(pilar: str, angulo: str, rubro: str, con_foto: bool = False) -> dict:
    """Pide a Gemini un carrusel completo y coherente. Costo: $0 (free tier)."""
    user = (
        f"Pilar: {pilar}.\n"
        f"Ángulo de esta pieza: {angulo}\n"
        f"Rubro del negocio: {rubro} (usá este, no lo cambies por otro).\n\n"
        "Armá el carrusel siguiendo tu método: primero el ancla, después la "
        "historia completa, y recién ahí las slides."
    )
    system = content_rules.get_system_prompt(con_foto)

    last_error: Exception | None = None
    for intento in range(1, MAX_RETRIES + 1):
        payload = _post(system, user)
        raw = _extraer_texto(payload)
        try:
            data = content_rules.normalizar(json.loads(raw))
            content_rules.validate(data, con_foto)
            return data
        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
            print(f"  (intento {intento}/{MAX_RETRIES}: {e}, reintentando...)")

    raise RuntimeError(f"Gemini no devolvió un carrusel válido tras {MAX_RETRIES} intentos: {last_error}")


def generate_humor(pilar: str, angulo: str, con_foto: bool = False) -> dict:
    """Pide a Gemini un carrusel de humor situacional. Costo: $0 (free tier)."""
    user = (
        f"Pilar: {pilar}.\n"
        f"Situación/ángulo de esta pieza: {angulo}\n\n"
        "Armá el carrusel siguiendo tu método: elegí el momento cómico concreto "
        "y armá la secuencia de slides que lo cuenta, hablándole directo a quien mira."
    )
    system = content_rules.get_humor_system_prompt(con_foto)

    last_error: Exception | None = None
    for intento in range(1, MAX_RETRIES + 1):
        payload = _post(system, user)
        raw = _extraer_texto(payload)
        try:
            data = content_rules.normalizar(json.loads(raw))
            content_rules.validate_humor(data, con_foto)
            return data
        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
            print(f"  (intento {intento}/{MAX_RETRIES}: {e}, reintentando...)")

    raise RuntimeError(f"Gemini no devolvió un carrusel de humor válido tras {MAX_RETRIES} intentos: {last_error}")


def generate_sabias_que(pilar: str, angulo: str, con_foto: bool = False) -> dict:
    """Pide a Gemini un carrusel educativo '¿Sabías que...?' (sin caso de
    cliente, sin solución puntual). Costo: $0 (free tier)."""
    user = (
        f"Pilar: {pilar}.\n"
        f"Ángulo/dato de esta pieza: {angulo}\n\n"
        "Armá el carrusel siguiendo tu método: elegí el dato concreto y "
        "armá las slides que lo desarrollan, sin plantear un caso ni una solución puntual."
    )
    system = content_rules.get_sabias_que_system_prompt(con_foto)

    last_error: Exception | None = None
    for intento in range(1, MAX_RETRIES + 1):
        payload = _post(system, user)
        raw = _extraer_texto(payload)
        try:
            data = content_rules.normalizar(json.loads(raw))
            content_rules.validate_sabias_que(data, con_foto)
            return data
        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
            print(f"  (intento {intento}/{MAX_RETRIES}: {e}, reintentando...)")

    raise RuntimeError(f"Gemini no devolvió un carrusel 'sabías que' válido tras {MAX_RETRIES} intentos: {last_error}")


def generate_chisme(pilar: str, angulo: str) -> dict:
    """Pide a Gemini un carrusel de puro fun content (formato 'chisme':
    ranking/lista graciosa que mezcla IA/tech con costumbres argentinas, con
    ícono pixel art por ítem). Costo: $0 (free tier)."""
    user = (
        f"Pilar: {pilar}.\n"
        f"Concepto de la lista/ranking: {angulo}\n\n"
        "Armá el carrusel siguiendo tu método: elegí entre 3 y 6 ítems para ESE "
        "concepto, con su nombre, comentario gracioso e icono_prompt cada uno."
    )

    last_error: Exception | None = None
    for intento in range(1, MAX_RETRIES + 1):
        payload = _post(chisme_rules.SYSTEM_PROMPT_CHISME, user)
        raw = _extraer_texto(payload)
        try:
            data = content_rules.normalizar(json.loads(raw))
            chisme_rules.validate(data)
            return data
        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
            print(f"  (intento {intento}/{MAX_RETRIES}: {e}, reintentando...)")

    raise RuntimeError(f"Gemini no devolvió un carrusel 'chisme' válido tras {MAX_RETRIES} intentos: {last_error}")


def generate_angulos(pilar: str, formato: str | None, existentes: list[str], n: int) -> dict:
    """Pide a Gemini `n` ángulos nuevos para `pilar`, evitando repetir
    `existentes`. Usado por refrescar_angulos.py para ampliar el pool sin
    tocar código. Costo: $0 (free tier)."""
    lista_existentes = "\n".join(f"- {a}" for a in existentes) or "(ninguno todavía)"
    user = (
        f"Pilar: {pilar}.\n\n"
        f"Ángulos ya existentes (no los repitas ni los parafrasees):\n{lista_existentes}\n\n"
        f"Generá {n} ángulos nuevos."
    )
    system = content_rules.get_angulos_system_prompt(formato)

    last_error: Exception | None = None
    for intento in range(1, MAX_RETRIES + 1):
        payload = _post(system, user)
        raw = _extraer_texto(payload)
        try:
            data = content_rules.normalizar(json.loads(raw))
            content_rules.validate_angulos(data, n)
            return data
        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
            print(f"  (intento {intento}/{MAX_RETRIES}: {e}, reintentando...)")

    raise RuntimeError(f"Gemini no devolvió ángulos válidos tras {MAX_RETRIES} intentos: {last_error}")


def generate_video_script(pilar: str, angulo: str, rubro: str) -> dict:
    """Pide a Gemini el guion de un video narrado (formato con voz en off
    real, ver video_rules.py). Costo: $0 (free tier)."""
    user = (
        f"Pilar: {pilar}.\n"
        f"Ángulo de esta pieza: {angulo}\n"
        f"Rubro del negocio: {rubro} (usá este, no lo cambies por otro).\n\n"
        "Armá el guion siguiendo tu método: primero el ancla, después la "
        "historia completa, y recién ahí las escenas."
    )

    last_error: Exception | None = None
    for intento in range(1, MAX_RETRIES + 1):
        payload = _post(video_rules.SYSTEM_PROMPT_VIDEO, user)
        raw = _extraer_texto(payload)
        try:
            data = content_rules.normalizar(json.loads(raw))
            video_rules.validate(data)
            return data
        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
            print(f"  (intento {intento}/{MAX_RETRIES}: {e}, reintentando...)")

    raise RuntimeError(f"Gemini no devolvió un guion de video válido tras {MAX_RETRIES} intentos: {last_error}")
