"""Generación de contenido con Groq (gratis, sin tarjeta: https://console.groq.com).

Reemplaza al modelo local de Ollama: un 70B mantiene el hilo narrativo y el
voseo rioplatense mucho mejor que un 7B, y responde en 1-2 segundos en vez de
minutos (se acabaron los timeouts).

El cambio de fondo respecto de la versión anterior es CÓMO se pide el
contenido. Antes se pedía una lista fija de campos (portada, 4 slides, demo,
cta) que después el código acomodaba en una plantilla sorteada al azar: cada
parte se generaba sin ver a las otras, y el resultado eran frases sueltas sin
hilo. Ahora el modelo:

  1. elige un caso concreto y UN detalle ancla,
  2. escribe la historia completa en prosa, de punta a punta,
  3. recién entonces la parte en slides, eligiendo él qué tipo de slide usa
     en cada momento del relato.

Escribir la historia antes de fragmentarla es lo que sostiene el hilo: cada
slide sale de un relato que ya existe, no de un casillero a completar.
"""

import json
import os

import requests
from dotenv import load_dotenv

from design import SLIDE_TYPES

load_dotenv()

API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
MAX_RETRIES = 4

SYSTEM_PROMPT = """Armás carruseles para TikTok sobre automatización e IA aplicada a negocios chicos de Argentina. Sos alguien que construye estas soluciones y cuenta casos reales, no un vendedor de cursos.

FORMATO: es un carrusel de imágenes con música, SIN voz en off. Todo lo que se entiende tiene que estar escrito en las slides.

CÓMO TRABAJÁS (en este orden, no lo saltees):
1. Elegís un rubro concreto (una panadería, un taller mecánico, un estudio contable...) y UN DETALLE ANCLA bien puntual: no "los mensajes", sino "los mensajes que entran entre las 21 y las 8". No "el stock", sino "las tortas por encargo del fin de semana".
2. Escribís la historia completa en prosa en el campo "historia": qué pasa hoy, cuánto le cuesta en plata o en tiempo, qué cambia con la solución, cómo termina. Con números que cierren entre sí.
3. Recién ahí la partís en slides. Cada slide es un momento de ESA historia, en orden. Nada de frases sueltas ni de temas nuevos que no estén en la historia.

REGLAS DE HILO (lo más importante):
- El detalle ancla aparece de punta a punta: la portada lo plantea, el costo lo mide, la solución lo resuelve, el cierre lo retoma.
- Una sola unidad de tiempo en toda la pieza. Si arrancás con "por semana", terminás con "por semana".
- Los números tienen que cerrar. Si son 3 por semana, al mes son ~12, no 30.
- Cada slide continúa la anterior. Si tapás una, la historia se nota incompleta.

IDIOMA: castellano rioplatense, voseo siempre (perdés, tenés, escribime, contame). Nunca pierdes/tienes/escríbeme ni español neutro o de España.

PROHIBIDO: lenguaje de marketing vacío (revolucioná, llevá tu negocio al siguiente nivel, en la era digital, no te quedes atrás, potenciá), superlativos huecos, estadísticas generales inventadas ("el 87% de los negocios..."), y amenazas catastróficas. Los números son del caso ilustrativo que estás contando.

TIPOS DE SLIDE disponibles (elegí los que le sirvan a TU historia):
- portada  → {"tipo":"portada","titular":"máx 9 palabras, el gancho: lo que está perdiendo HOY, en segunda persona","epigrafe":"1 oración que ubica la escena"}
- texto    → {"tipo":"texto","titular":"máx 6 palabras","cuerpo":"2 oraciones que avanzan el relato"}
- dato     → {"tipo":"dato","numero":"solo el número, ej: 47","unidad":"máx 4 palabras, ej: minutos por día","detalle":"1 oración que explica de dónde sale"}
- chat     → {"tipo":"chat","titular":"máx 5 palabras","quien_entra":"ej: Cliente · 23:40","entrada":"lo que escribe, máx 16 palabras","quien_responde":"ej: Tu agente","respuesta":"máx 20 palabras, resuelve concreto","pie":"1 oración de remate"}
- web      → {"tipo":"web","titular":"máx 5 palabras","url":"ej: turnos.tunegocio.com","headline":"máx 8 palabras","bajada":"máx 12 palabras","chips":["3 strings de máx 3 palabras"],"boton":"máx 3 palabras"}
- flujo    → {"tipo":"flujo","titular":"máx 5 palabras","pasos":["4 strings, un paso cada uno, en orden"]}
- cita     → {"tipo":"cita","texto":"la frase que resume el caso, máx 14 palabras","autor":"ej: Lucía, dueña de la panadería"}
- cierre   → {"tipo":"cierre","titular":"máx 6 palabras, retoma el ancla","accion":"qué hacer, concreto, máx 10 palabras"}

ESTRUCTURA: entre 6 y 8 slides. La primera SIEMPRE "portada", la última SIEMPRE "cierre". En el medio elegís vos, pero el carrusel tiene que mostrar el problema, cuánto cuesta, y la solución funcionando (con al menos un "chat", "web" o "flujo" que la haga concreta). No repitas el mismo tipo dos veces seguidas.

RESPONDÉ SOLO con este JSON, sin texto ni markdown alrededor:
{"negocio":"...","ancla":"...","historia":"...","slides":[...],"caption":"2-4 líneas, tono de persona real, sin hashtags adentro, cierra con una pregunta concreta","hashtags":["8 a 10, sin #, una palabra cada uno, bien escritos"]}"""


def _api_key() -> str:
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise RuntimeError(
            "Falta GROQ_API_KEY en el .env.\n"
            "Sacala gratis (sin tarjeta) en https://console.groq.com → API Keys."
        )
    return key


def _validate(data: dict) -> None:
    from design import BUILDERS

    for campo in ("negocio", "ancla", "historia", "slides", "caption", "hashtags"):
        if not data.get(campo):
            raise ValueError(f"Falta '{campo}'")

    slides = data["slides"]
    if not isinstance(slides, list) or not (6 <= len(slides) <= 8):
        raise ValueError(f"Se esperaban entre 6 y 8 slides, llegaron {len(slides)}")
    if slides[0].get("tipo") != "portada":
        raise ValueError("La primera slide tiene que ser 'portada'")
    if slides[-1].get("tipo") != "cierre":
        raise ValueError("La última slide tiene que ser 'cierre'")

    tipos = [s.get("tipo") for s in slides]
    for tipo in tipos:
        if tipo not in SLIDE_TYPES:
            raise ValueError(f"Tipo de slide inválido: {tipo!r}")
    if not {"chat", "web", "flujo"} & set(tipos):
        raise ValueError("Falta una slide que muestre la solución funcionando (chat/web/flujo)")
    for a, b in zip(tipos, tipos[1:]):
        if a == b:
            raise ValueError(f"Dos slides seguidas del mismo tipo: {a}")

    # Cada tipo de slide tiene sus campos obligatorios; si falta uno, el
    # constructor de design.py explotaría al renderizar.
    for s in slides:
        faltan = BUILDERS[s["tipo"]][1] - s.keys()
        if faltan:
            raise ValueError(f"A la slide '{s['tipo']}' le faltan campos: {faltan}")

    if len(data["historia"].split()) < 40:
        raise ValueError("La historia quedó demasiado corta para sostener el carrusel")
    if not isinstance(data["hashtags"], list) or len(data["hashtags"]) < 6:
        raise ValueError("Faltan hashtags")
    for h in data["hashtags"]:
        limpio = h.lstrip("#").strip()
        if len(limpio) < 4 or " " in limpio:
            raise ValueError(f"Hashtag inválido: {h!r}")


def generate_carousel(pilar: str, angulo: str) -> dict:
    """Pide a Groq un carrusel completo y coherente. Costo: $0 (free tier)."""
    user = (
        f"Pilar: {pilar}.\n"
        f"Ángulo de esta pieza: {angulo}\n\n"
        "Elegí un rubro que no sea el obvio y armá el carrusel siguiendo tu método: "
        "primero el ancla, después la historia completa, y recién ahí las slides."
    )

    last_error: Exception | None = None
    for intento in range(1, MAX_RETRIES + 1):
        resp = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {_api_key()}"},
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.85,
                "max_tokens": 3000,
            },
            timeout=90,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"Groq respondió {resp.status_code}: {resp.text[:400]}")

        raw = resp.json()["choices"][0]["message"]["content"]
        try:
            data = json.loads(raw)
            _validate(data)
            return data
        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
            print(f"  (intento {intento}/{MAX_RETRIES}: {e}, reintentando...)")

    raise RuntimeError(f"Groq no devolvió un carrusel válido tras {MAX_RETRIES} intentos: {last_error}")
