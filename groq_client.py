"""Generación de contenido con Groq (gratis, sin tarjeta: https://console.groq.com).

Reemplaza al modelo local de Ollama: un 70B mantiene el hilo narrativo y el
voseo rioplatense mucho mejor que un 7B, y responde en 1-2 segundos en vez de
minutos (se acabaron los timeouts).

Los prompts y la validación viven en content_rules.py (compartidos con
gemini_client.py); este módulo solo se ocupa de hablar con la API de Groq:
autenticación, rate limiting del free tier, y reintentos.
"""

import json
import os
import re
import time

import requests
from dotenv import load_dotenv

import chisme_rules
import content_rules
import impacto_rules
import video_rules

load_dotenv()

API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
MAX_RETRIES = 4


def _api_key() -> str:
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise RuntimeError(
            "Falta GROQ_API_KEY en el .env.\n"
            "Sacala gratis (sin tarjeta) en https://console.groq.com → API Keys."
        )
    return key


# Groq (free tier) rechaza de entrada cualquier pedido cuyo input + max_tokens
# supere este techo — no es un límite de acumulado por minuto (ese es el 429,
# que ya se maneja abajo), es un tope duro por request (413). El SYSTEM_PROMPT
# se edita seguido y cada regla nueva le resta presupuesto a la respuesta, así
# que max_tokens se calcula en cada pedido en vez de ser un número fijo que se
# rompe en silencio la próxima vez que el prompt crezca.
_TOPE_TOKENS_REQUEST = 8000
_MARGEN_SEGURIDAD = 250
_MAX_TOKENS_TECHO = 6000
_MAX_TOKENS_PISO = 3000  # con menos que esto, gpt-oss se queda sin lugar para razonar y cerrar el JSON


def _estimar_tokens(texto: str) -> int:
    """Estimación gruesa (no hay tokenizer real instalado): ~3.3 caracteres
    por token le sale bien al castellano con acentos. Mejor sobreestimar un
    poco que quedarse corto y comerse un 413."""
    return int(len(texto) / 3.3) + 20  # +20 de margen por el overhead de formato del mensaje


def _post_con_espera(system: str, user: str, max_esperas: int = 4) -> requests.Response:
    """Hace el pedido a Groq, respetando el límite de tokens por minuto del
    free tier (8000 TPM). Cuando devuelve 429 avisa cuántos segundos faltan:
    en vez de fallar, esperamos ese rato y reintentamos. Si el 429 es por
    cuota DIARIA agotada (no por minuto), el mensaje trae 'Xm Ys' en vez de
    solo segundos — no vale la pena esperar eso acá (son decenas de minutos),
    así que se detecta y se corta rápido para que ai_providers.py pase al
    otro proveedor en vez de quedarse reintentando en banda."""
    input_tokens = _estimar_tokens(system) + _estimar_tokens(user)
    max_tokens = max(_MAX_TOKENS_PISO, min(_MAX_TOKENS_TECHO, _TOPE_TOKENS_REQUEST - _MARGEN_SEGURIDAD - input_tokens))
    if input_tokens + _MAX_TOKENS_PISO > _TOPE_TOKENS_REQUEST:
        raise RuntimeError(
            f"El system prompt (~{input_tokens} tokens estimados) ya no deja lugar ni para el "
            f"mínimo de {_MAX_TOKENS_PISO} tokens de respuesta. Hay que acortar el prompt."
        )

    for _ in range(max_esperas):
        resp = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {_api_key()}"},
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.85,
                # gpt-oss razona antes de contestar y ese razonamiento consume
                # tokens del mismo presupuesto, así que el techo tiene que ser
                # holgado. Con esfuerzo 'low' aparecían erratas y cuentas que
                # no cerraban; 'medium' es el punto donde el texto sale prolijo.
                "reasoning_effort": "medium",
                "max_tokens": max_tokens,
            },
            timeout=120,
        )
        if resp.status_code == 429:
            if re.search(r"try again in \d+m", resp.text):
                raise RuntimeError(f"Groq sin cuota diaria por ahora: {resp.text[:200]}")
            match = re.search(r"try again in ([\d.]+)s", resp.text)
            espera = min(float(match.group(1)) + 1 if match else 20.0, 65.0)
            print(f"  (límite de tokens por minuto, espero {espera:.0f}s...)")
            time.sleep(espera)
            continue
        if resp.status_code != 200:
            raise RuntimeError(f"Groq respondió {resp.status_code}: {resp.text[:400]}")
        return resp

    raise RuntimeError("Groq siguió rechazando por límite de tokens tras varias esperas.")


def _sumar_contexto(user: str, contexto: str | None) -> str:
    """Le pega al mensaje el contexto estratégico de ESTA pieza: para qué está
    hecha (intención) y contra qué tensión de la audiencia se escribe (ver
    audiencia.py). Va en el mensaje del usuario y no en el system prompt
    porque cambia en cada pedido — el system prompt es lo que no cambia
    nunca, y mezclarlos rompería el caché de prompt de los proveedores."""
    return f"{user}\n\n{contexto}" if contexto else user


def generate_carousel(pilar: str, angulo: str, rubro: str, con_foto: bool = False, contexto: str | None = None) -> dict:
    """Pide a Groq un carrusel completo y coherente. Costo: $0 (free tier)."""
    user = (
        f"Pilar: {pilar}.\n"
        f"Ángulo de esta pieza: {angulo}\n"
        f"Rubro del negocio: {rubro} (usá este, no lo cambies por otro).\n\n"
        "Armá el carrusel siguiendo tu método: primero el ancla, después la "
        "historia completa, y recién ahí las slides."
    )
    user = _sumar_contexto(user, contexto)
    system = content_rules.get_system_prompt(con_foto)

    last_error: Exception | None = None
    for intento in range(1, MAX_RETRIES + 1):
        resp = _post_con_espera(system, user)
        raw = resp.json()["choices"][0]["message"]["content"]
        try:
            data = content_rules.normalizar(json.loads(raw))
            content_rules.validate(data, con_foto)
            return data
        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
            print(f"  (intento {intento}/{MAX_RETRIES}: {e}, reintentando...)")

    raise RuntimeError(f"Groq no devolvió un carrusel válido tras {MAX_RETRIES} intentos: {last_error}")


def generate_humor(pilar: str, angulo: str, con_foto: bool = False, contexto: str | None = None) -> dict:
    """Pide a Groq un carrusel de humor situacional (segunda persona, sin caso
    de cliente). Costo: $0 (free tier)."""
    user = (
        f"Pilar: {pilar}.\n"
        f"Situación/ángulo de esta pieza: {angulo}\n\n"
        "Armá el carrusel siguiendo tu método: elegí el momento cómico concreto "
        "y armá la secuencia de slides que lo cuenta, hablándole directo a quien mira."
    )
    user = _sumar_contexto(user, contexto)
    system = content_rules.get_humor_system_prompt(con_foto)

    last_error: Exception | None = None
    for intento in range(1, MAX_RETRIES + 1):
        resp = _post_con_espera(system, user)
        raw = resp.json()["choices"][0]["message"]["content"]
        try:
            data = content_rules.normalizar(json.loads(raw))
            content_rules.validate_humor(data, con_foto)
            return data
        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
            print(f"  (intento {intento}/{MAX_RETRIES}: {e}, reintentando...)")

    raise RuntimeError(f"Groq no devolvió un carrusel de humor válido tras {MAX_RETRIES} intentos: {last_error}")


def generate_sabias_que(pilar: str, angulo: str, con_foto: bool = False, contexto: str | None = None) -> dict:
    """Pide a Groq un carrusel educativo '¿Sabías que...?' (sin caso de
    cliente, sin solución puntual). Costo: $0 (free tier)."""
    user = (
        f"Pilar: {pilar}.\n"
        f"Ángulo/dato de esta pieza: {angulo}\n\n"
        "Armá el carrusel siguiendo tu método: elegí el dato concreto y "
        "armá las slides que lo desarrollan, sin plantear un caso ni una solución puntual."
    )
    user = _sumar_contexto(user, contexto)
    system = content_rules.get_sabias_que_system_prompt(con_foto)

    last_error: Exception | None = None
    for intento in range(1, MAX_RETRIES + 1):
        resp = _post_con_espera(system, user)
        raw = resp.json()["choices"][0]["message"]["content"]
        try:
            data = content_rules.normalizar(json.loads(raw))
            content_rules.validate_sabias_que(data, con_foto)
            return data
        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
            print(f"  (intento {intento}/{MAX_RETRIES}: {e}, reintentando...)")

    raise RuntimeError(f"Groq no devolvió un carrusel 'sabías que' válido tras {MAX_RETRIES} intentos: {last_error}")


def generate_chisme(pilar: str, angulo: str, contexto: str | None = None) -> dict:
    """Pide a Groq un carrusel de puro fun content (formato 'chisme': ranking/
    lista graciosa que mezcla IA/tech con costumbres argentinas, con ícono
    pixel art por ítem). Costo: $0 (free tier)."""
    user = (
        f"Pilar: {pilar}.\n"
        f"Concepto de la lista/ranking: {angulo}\n\n"
        "Armá el carrusel siguiendo tu método: elegí entre 3 y 6 ítems para ESE "
        "concepto, con su nombre, comentario gracioso e icono_prompt cada uno."
    )
    user = _sumar_contexto(user, contexto)

    last_error: Exception | None = None
    for intento in range(1, MAX_RETRIES + 1):
        resp = _post_con_espera(chisme_rules.SYSTEM_PROMPT_CHISME, user)
        raw = resp.json()["choices"][0]["message"]["content"]
        try:
            data = content_rules.normalizar(json.loads(raw))
            chisme_rules.validate(data)
            return data
        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
            print(f"  (intento {intento}/{MAX_RETRIES}: {e}, reintentando...)")

    raise RuntimeError(f"Groq no devolvió un carrusel 'chisme' válido tras {MAX_RETRIES} intentos: {last_error}")


def generate_impacto(pilar: str, angulo: str, contexto: str | None = None) -> dict:
    """Pide a Groq un carrusel del formato 'impacto' (confesión en primera
    persona sobre un error de negocio + lista de acciones con IA, con foto de
    fondo llamativa por slide). Costo: $0 (free tier)."""
    user = (
        f"Pilar: {pilar}.\n"
        f"Error puntual de 30 minutos no invertidos: {angulo}\n\n"
        "Armá el carrusel siguiendo tu método: la portada confiesa ese error, después "
        "3 a 6 'punto' con la acción concreta con IA que se desprende de él (mezclando "
        "automatizar/generar impacto/atraer clientes), y el cierre con el remate."
    )
    user = _sumar_contexto(user, contexto)

    last_error: Exception | None = None
    for intento in range(1, MAX_RETRIES + 1):
        resp = _post_con_espera(impacto_rules.SYSTEM_PROMPT_IMPACTO, user)
        raw = resp.json()["choices"][0]["message"]["content"]
        try:
            data = content_rules.normalizar(json.loads(raw))
            impacto_rules.validate(data)
            return data
        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
            print(f"  (intento {intento}/{MAX_RETRIES}: {e}, reintentando...)")

    raise RuntimeError(f"Groq no devolvió un carrusel 'impacto' válido tras {MAX_RETRIES} intentos: {last_error}")


def generate_angulos(pilar: str, formato: str | None, existentes: list[str], n: int,
                     rendimiento: str | None = None, contexto: str | None = None) -> dict:
    """Pide a Groq `n` ángulos nuevos para `pilar`, evitando repetir
    `existentes`. Usado por refrescar_angulos.py para ampliar el pool sin
    tocar código. `rendimiento` es el bloque opcional con las métricas reales
    de la cuenta (ver rendimiento.py), para empujar los ángulos nuevos hacia
    lo que ya funcionó en la cuenta. Costo: $0 (free tier)."""
    lista_existentes = "\n".join(f"- {a}" for a in existentes) or "(ninguno todavía)"
    bloque_rendimiento = f"\n{rendimiento}\n" if rendimiento else ""
    user = (
        f"Pilar: {pilar}.\n"
        f"{bloque_rendimiento}\n"
        f"Ángulos ya existentes (no los repitas ni los parafrasees):\n{lista_existentes}\n\n"
        f"Generá {n} ángulos nuevos."
    )
    user = _sumar_contexto(user, contexto)
    system = content_rules.get_angulos_system_prompt(formato, con_rendimiento=bool(rendimiento))

    last_error: Exception | None = None
    for intento in range(1, MAX_RETRIES + 1):
        resp = _post_con_espera(system, user)
        raw = resp.json()["choices"][0]["message"]["content"]
        try:
            data = content_rules.normalizar(json.loads(raw))
            content_rules.validate_angulos(data, n)
            return data
        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
            print(f"  (intento {intento}/{MAX_RETRIES}: {e}, reintentando...)")

    raise RuntimeError(f"Groq no devolvió ángulos válidos tras {MAX_RETRIES} intentos: {last_error}")


def generate_video_script(pilar: str, angulo: str, rubro: str, contexto: str | None = None) -> dict:
    """Pide a Groq el guion de un video narrado (formato con voz en off real,
    ver video_rules.py). Costo: $0 (free tier)."""
    user = (
        f"Pilar: {pilar}.\n"
        f"Ángulo de esta pieza: {angulo}\n"
        f"Rubro del negocio: {rubro} (usá este, no lo cambies por otro).\n\n"
        "Armá el guion siguiendo tu método: primero el ancla, después la "
        "historia completa, y recién ahí las escenas."
    )
    user = _sumar_contexto(user, contexto)

    last_error: Exception | None = None
    for intento in range(1, MAX_RETRIES + 1):
        resp = _post_con_espera(video_rules.SYSTEM_PROMPT_VIDEO, user)
        raw = resp.json()["choices"][0]["message"]["content"]
        try:
            data = content_rules.normalizar(json.loads(raw))
            video_rules.validate(data)
            return data
        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
            print(f"  (intento {intento}/{MAX_RETRIES}: {e}, reintentando...)")

    raise RuntimeError(f"Groq no devolvió un guion de video válido tras {MAX_RETRIES} intentos: {last_error}")
