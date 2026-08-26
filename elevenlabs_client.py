"""Cliente de ElevenLabs Text-to-Speech (free tier: ~10.000 caracteres/mes,
sin tarjeta: https://elevenlabs.io/app/settings/api-keys).

Se usa para la locución del formato 'video narrado'. El modelo multilingüe
soporta español; para que salga con acento rioplatense conviene elegir una
voz en español en tu cuenta de ElevenLabs y poner su ID en
ELEVENLABS_VOICE_ID — si no lo configurás, usa una voz premade genérica
(funciona, pero no está pensada para voseo argentino).
"""

import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
# OJO: el free tier de ElevenLabs NO deja usar voces de la librería completa
# vía API (tira 402 "paid_plan_required") — solo las que ya están en "My
# Voices" de tu cuenta. Las premade que vienen por default sí valen. "Liam"
# es una de esas premade (habla multilingüe con el modelo de abajo, aunque
# el nombre/descripción esté en inglés). Pisala con ELEVENLABS_VOICE_ID si
# agregás una voz en español a tu cuenta desde la Voice Library.
DEFAULT_VOICE_ID = "TX3LPaxmHKxFdv7VOQHJ"  # Liam
MODEL_ID = "eleven_multilingual_v2"


def _api_key() -> str:
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        raise RuntimeError(
            "Falta ELEVENLABS_API_KEY en el .env.\n"
            "Sacala gratis (free tier, sin tarjeta) en "
            "https://elevenlabs.io/app/settings/api-keys."
        )
    return key


def sintetizar(texto: str, destino: Path) -> Path:
    """Convierte `texto` a audio y lo guarda en `destino` (mp3). Tira
    RuntimeError con el motivo si la cuenta se quedó sin caracteres del free
    tier o si la voz configurada no existe."""
    voice_id = os.environ.get("ELEVENLABS_VOICE_ID", DEFAULT_VOICE_ID)
    resp = requests.post(
        API_URL.format(voice_id=voice_id),
        headers={
            "xi-api-key": _api_key(),
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
        },
        json={
            "text": texto,
            "model_id": MODEL_ID,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        },
        timeout=90,
    )
    if resp.status_code == 401:
        raise RuntimeError(f"ElevenLabs rechazó la key o se agotó el free tier del mes: {resp.text[:300]}")
    if resp.status_code != 200:
        raise RuntimeError(f"ElevenLabs respondió {resp.status_code}: {resp.text[:300]}")

    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(resp.content)
    return destino
