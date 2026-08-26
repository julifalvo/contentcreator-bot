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
import re
import time

import requests
from dotenv import load_dotenv

from design import SLIDE_TYPES

load_dotenv()

API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
MAX_RETRIES = 4

SYSTEM_PROMPT = """Armás carruseles para TikTok para rootbusinessai, una agencia que construye agentes de IA y automatizaciones para negocios chicos de Argentina. Contás casos reales de clientes, no vendés un curso.

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

NÚMEROS — UNA SOLA CIFRA POR PIEZA (regla dura):
- Elegís UNA cifra protagonista (la que va en el slide "dato") y esa es la única que se repite. Ej: "4 reservas por día".
- Los demás slides pueden nombrar esa misma cifra, pero TIENEN PROHIBIDO derivar otras a partir de ella: nada de "que por semana son 20", "al mes son 80", "eso equivale a 5 horas". Cada vez que multiplicás, te equivocás y el carrusel se contradice solo.
- Si un slide necesita hablar del costo, lo dice en palabras, no con una cuenta nueva: "una mañana entera", "media jornada", "lo que facturás un sábado".
- Como mucho puede aparecer UNA segunda cifra, y sólo si es independiente y directa (un precio, un horario, un tiempo de respuesta), nunca el resultado de multiplicar la primera.
- Antes de cerrar el JSON, releé: si encontrás dos números que se supone que se relacionan, borrá el segundo.

IDIOMA: castellano rioplatense, voseo siempre (perdés, tenés, escribime, contame). Nunca pierdes/tienes/escríbeme ni español neutro o de España. Releé lo que escribiste antes de cerrar el JSON: una errata en un titular gigante se ve muchísimo.

VOZ NARRATIVA — tercera persona, caso de agencia (regla dura):
- El "negocio" del caso es SIEMPRE un cliente ajeno que acudió a la agencia, nunca "tu negocio" propio ni el de quien mira. En "historia" y "caption" contás el caso desde afuera, como lo cuenta la agencia que lo resolvió.
- PROHIBIDO el narrador en primera persona sobre el negocio: nunca "mi taller", "mi negocio", "mi local", "mi consultorio", "en mi rubro", "tenemos un taller", "implementamos en nuestro negocio". El negocio no es tuyo, es del cliente.
- Fórmulas correctas para arrancar la historia o el caption: "Un cliente nuestro, [rubro], nos contó que...", "Nos llegó el caso de [rubro]: ...", "[rubro] que trabaja con nosotros perdía...", "Así llegó a nosotros [rubro]: ...", "La empresa con la que trabajamos hace [rubro] tenía este problema...".
- Nombrá el negocio por su rubro ("el vivero", "la escuela de música"), nunca con un nombre propio inventado ni con placeholders tipo "X", "Cliente A", "el negocio Y": no suena a caso real.
- Dentro de ESE marco (agencia contando el caso de un cliente), el "portada" y el "cierre" sí pueden dirigirse en segunda persona a quien mira ("Perdés turnos...", "Contame tu caso"): son el gancho y la invitación, no la narración del caso. La única voz en primera persona permitida es la de "cita" (autor), que es una frase textual atribuida al cliente por su nombre.
- PROHIBIDO inventar ofertas, precios o promociones: nada de "probá gratis 7 días", "50% off", "plan desde $X", "agendá una demo". No estás vendiendo un producto con free trial.
- El "cierre" no ofrece un producto: retoma el ancla y abre una conversación con quien mira. Ej: "Contame cuántos se te pisan y vemos", "Escribime y lo miramos juntos".
- El "caption" NO es un pitch. Es el caso del cliente contado en dos o tres líneas, en tercera persona, y termina con una pregunta que le haga poner a QUIEN MIRA un número a SU propio problema. Nunca "¿te gustaría probarlo en tu negocio?" ni "revolucioná tu gestión".

PROHIBIDO ADEMÁS: lenguaje de marketing vacío (revolucioná, llevá tu negocio al siguiente nivel, en la era digital, no te quedes atrás, potenciá, solución integral), superlativos huecos, estadísticas generales inventadas ("el 87% de los negocios..."), y amenazas catastróficas. Los números son del caso ilustrativo que estás contando.

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
{"negocio":"...","ancla":"...","historia":"...","slides":[...],"caption":"2-4 líneas en tercera persona (el caso de un cliente de la agencia, nunca 'mi negocio'), sin hashtags adentro, cierra con una pregunta concreta a quien mira","hashtags":["8 a 10, sin #, una palabra cada uno, bien escritos"]}"""


def _api_key() -> str:
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise RuntimeError(
            "Falta GROQ_API_KEY en el .env.\n"
            "Sacala gratis (sin tarjeta) en https://console.groq.com → API Keys."
        )
    return key


# Frases que delatan que el modelo se puso en modo vendedor de SaaS en vez de
# contar el caso. Se chequean sobre todo el texto de la pieza.
_TONO_VENDEDOR = (
    "gratis 7 días", "gratis 30 días", "prueba gratis", "probá gratis", "proba gratis",
    "free trial", "sin costo por", "agendá una demo", "agenda una demo", "pedí una demo",
    "% off", "descuento", "plan desde", "precio especial", "oferta",
    "te gustaría probarlo", "te gustaria probarlo", "revolucion", "siguiente nivel",
    "no te quedes atrás", "no te quedes atras", "potenciá tu", "solución integral",
    "solucion integral", "en la era digital",
)
# El negocio del caso es SIEMPRE un cliente ajeno, nunca el narrador hablando
# en primera persona de "su" negocio. Estas son las formas inequívocas de
# apropiación (no se puede chequear por regla general: el pretérito imperfecto
# es igual en 1ª y 3ª persona -"perdía" sirve para "yo perdía" y "él perdía"-,
# así que solo se bloquean los posesivos que no admiten lectura en 3ª persona).
_NARRADOR_DUEÑO = (
    "mi taller", "mi negocio", "mi local", "mi tienda", "mi empresa", "mi estudio",
    "mi consultorio", "mi peluquería", "mi restaurante", "mi vivero", "mi ferretería",
    "mi kiosco", "mi rubro", "nuestro taller", "nuestro negocio", "nuestro local",
    "nuestra tienda", "en mi rubro",
)
# Formas de español neutro/España que rompen el voseo rioplatense.
_NO_VOSEO = (
    "pierdes", "tienes", "puedes", "quieres", "necesitas", "escríbeme", "cuéntame",
    "contáctame", "tu negocio puede", "vuelves", "sigues", "sabes", "eres", "debes",
    # 'tú' con tilde es el pronombre neutro (en voseo va 'vos'). 'tu' sin tilde
    # es el posesivo y sí es correcto, por eso el \b del regex importa.
    "tú",
    # Formas de voseo a las que se les comió la tilde: no son ni voseo correcto
    # ('perdés') ni forma de tú ('pierdes'), así que no hay ambigüedad — están
    # mal escritas, y en un titular gigante se nota muchísimo.
    "perdes", "tenes", "podes", "queres", "atendes", "entendes",
    "venis", "decis", "escribis", "seguis", "vivis", "salis", "conseguis",
    "elegis", "preferis", "repetis",
)


# Imperativos en tú que aparecen sobre todo en botones y titulares de la slide
# 'web' ("Agenda tu turno"). Pasarlos a voseo es una corrección mecánica, así
# que se arregla en vez de rechazar la pieza y quemar los reintentos. Los
# primeros sólo se tocan cuando siguen con "tu", porque sueltos también son
# sustantivos válidos ("la agenda", "la reserva", "la consulta").
_IMPERATIVOS = [
    (r"\b([Aa])genda(\s+tu\b)", r"\1gendá\2"),
    (r"\b([Rr])eserva(\s+tu\b)", r"\1eservá\2"),
    (r"\b([Cc])onsulta(\s+tu\b)", r"\1onsultá\2"),
    (r"\b([Pp])rueba(\s+tu\b)", r"\1robá\2"),
    (r"\b([Cc])ompra(\s+tu\b)", r"\1omprá\2"),
    (r"\b([Cc])otiza\b", r"\1otizá"),
    (r"\b([Ss])olicita\b", r"\1olicitá"),
    (r"\b([Dd])escubre\b", r"\1escubrí"),
    (r"\b([Ee])mpieza\b", r"\1mpezá"),
    (r"\b([Cc])onoce\b", r"\1onocé"),
    (r"\b([Rr])egistra\b", r"\1egistrá"),
    (r"\b([Ii])ngresa\b", r"\1ngresá"),
]


def _normalizar(valor):
    """Limpia el texto antes de renderizar: separador de miles al uso argentino
    ('$1 200' -> '$1.200', que con el espacio parece una errata en un titular
    gigante) y los imperativos en tú pasados a voseo."""
    if isinstance(valor, str):
        valor = valor.replace(" ", " ").replace("\xa0", " ")
        valor = re.sub(r"(\d) (\d{3})\b", r"\1.\2", valor)
        for patron, reemplazo in _IMPERATIVOS:
            valor = re.sub(patron, reemplazo, valor)
        return valor
    if isinstance(valor, list):
        return [_normalizar(v) for v in valor]
    if isinstance(valor, dict):
        return {k: _normalizar(v) for k, v in valor.items()}
    return valor


def _texto_completo(data: dict) -> str:
    partes = [data.get("caption", ""), data.get("historia", "")]
    for s in data.get("slides", []):
        partes += [str(v) for k, v in s.items() if k != "tipo" and isinstance(v, str)]
        partes += [str(x) for x in s.get("pasos", []) or []]
        partes += [str(x) for x in s.get("chips", []) or []]
    return " ".join(partes).lower()


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

    texto = _texto_completo(data)
    vendedor = [f for f in _TONO_VENDEDOR if f in texto]
    if vendedor:
        raise ValueError(f"Tono de vendedor / oferta inventada: {vendedor}")
    dueño = [f for f in _NARRADOR_DUEÑO if f in texto]
    if dueño:
        raise ValueError(f"Narrador hablando como dueño del negocio, no como agencia: {dueño}")
    if re.search(r"\b(vivero|taller|negocio|empresa|estudio|local|tienda|escuela|cliente) [xyz]\b", texto):
        raise ValueError("Usó un placeholder tipo 'negocio X' en vez de nombrarlo por su rubro")
    neutro = [f for f in _NO_VOSEO if re.search(rf"\b{re.escape(f)}\b", texto)]
    if neutro:
        raise ValueError(f"No está en voseo rioplatense: {neutro}")
    if len(data["caption"].split()) < 15:
        raise ValueError("El caption quedó demasiado corto para contar el caso")
    if not isinstance(data["hashtags"], list) or len(data["hashtags"]) < 6:
        raise ValueError("Faltan hashtags")
    for h in data["hashtags"]:
        limpio = h.lstrip("#").strip()
        # 'ia' y 'pyme' son hashtags legítimos y cortos; lo que hay que
        # descartar son los cortados a la mitad o con espacios adentro.
        if len(limpio) < 2 or " " in limpio or not limpio.replace("ñ", "n").isalnum():
            raise ValueError(f"Hashtag inválido: {h!r}")


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


def _post_con_espera(user: str, max_esperas: int = 4) -> requests.Response:
    """Hace el pedido a Groq, respetando el límite de tokens por minuto del
    free tier (8000 TPM). Cuando devuelve 429 avisa cuántos segundos faltan:
    en vez de fallar, esperamos ese rato y reintentamos."""
    input_tokens = _estimar_tokens(SYSTEM_PROMPT) + _estimar_tokens(user)
    max_tokens = max(_MAX_TOKENS_PISO, min(_MAX_TOKENS_TECHO, _TOPE_TOKENS_REQUEST - _MARGEN_SEGURIDAD - input_tokens))
    if input_tokens + _MAX_TOKENS_PISO > _TOPE_TOKENS_REQUEST:
        raise RuntimeError(
            f"El SYSTEM_PROMPT (~{input_tokens} tokens estimados) ya no deja lugar ni para el "
            f"mínimo de {_MAX_TOKENS_PISO} tokens de respuesta. Hay que acortar el prompt."
        )

    for _ in range(max_esperas):
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
            match = re.search(r"try again in ([\d.]+)s", resp.text)
            espera = min(float(match.group(1)) + 1 if match else 20.0, 65.0)
            print(f"  (límite de tokens por minuto, espero {espera:.0f}s...)")
            time.sleep(espera)
            continue
        if resp.status_code != 200:
            raise RuntimeError(f"Groq respondió {resp.status_code}: {resp.text[:400]}")
        return resp

    raise RuntimeError("Groq siguió rechazando por límite de tokens tras varias esperas.")


def generate_carousel(pilar: str, angulo: str, rubro: str) -> dict:
    """Pide a Groq un carrusel completo y coherente. Costo: $0 (free tier)."""
    user = (
        f"Pilar: {pilar}.\n"
        f"Ángulo de esta pieza: {angulo}\n"
        f"Rubro del negocio: {rubro} (usá este, no lo cambies por otro).\n\n"
        "Armá el carrusel siguiendo tu método: primero el ancla, después la "
        "historia completa, y recién ahí las slides."
    )

    last_error: Exception | None = None
    for intento in range(1, MAX_RETRIES + 1):
        resp = _post_con_espera(user)
        raw = resp.json()["choices"][0]["message"]["content"]
        try:
            data = _normalizar(json.loads(raw))
            _validate(data)
            return data
        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
            print(f"  (intento {intento}/{MAX_RETRIES}: {e}, reintentando...)")

    raise RuntimeError(f"Groq no devolvió un carrusel válido tras {MAX_RETRIES} intentos: {last_error}")
