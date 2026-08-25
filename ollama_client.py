"""Generación de guiones/textos para TikTok usando un modelo local con Ollama.

100% gratis: corre en tu PC, sin API key, sin registro, sin créditos de
Anthropic ni de nadie. Requiere tener Ollama instalado y corriendo
(https://ollama.com) y el modelo ya descargado (`ollama pull <modelo>`).

A diferencia de ai_client.py (Claude, con output_config de json_schema
estricto), acá el modelo solo garantiza JSON *válido* (format="json"), no que
respete el esquema exacto — por eso se valida la respuesta y se reintenta un
par de veces si falta algún campo.
"""

import json
import os
import re

import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")
MAX_RETRIES = 5

SYSTEM_PROMPT = (
    "Sos alguien que arma agentes de IA y automatizaciones para negocios chicos y medianos, "
    "y contás en TikTok lo que vas aprendiendo en el camino. No sos un community manager ni "
    "una agencia de marketing: hablás como hablarías con un cliente en un café, contando un "
    "caso concreto, no vendiendo un curso.\n\n"
    "IMPORTANTE sobre el formato: el video NO tiene voz en off ni guion hablado. Es un carrusel "
    "de imágenes con música de fondo — la persona no lee nada en voz alta. Eso significa que "
    "TODO lo que el espectador va a entender tiene que estar en el texto de las slides.\n\n"
    "Reglas duras de estilo:\n"
    "- Prohibido el lenguaje de marketing vacío: 'revolucioná tu negocio', 'llevá tu negocio "
    "al siguiente nivel', 'en la era digital', 'maximizá resultados', 'no te quedes atrás', "
    "'la clave del éxito', o cualquier frase que sonaría igual en cualquier rubro.\n"
    "- Cada pieza tiene que incluir un DEMO real y específico: un intercambio concreto de "
    "mensajes (cliente escribe algo puntual, el agente responde algo puntual), con un rubro "
    "de negocio específico y DISTINTO cada vez (variá el rubro: no repitas 'vivero' ni "
    "'consultorio odontológico' si ya los usaste antes) — no 'un negocio' genérico.\n"
    "- Usá números y detalles concretos siempre que se pueda (tiempos, cantidad de mensajes, "
    "horarios), nunca 'mucho', 'rápido' o 'fácil' sin un dato al lado.\n"
    "- Texto natural, como lo escribiría una persona, no un folleto corporativo. Frases cortas "
    "pero completas (sujeto + verbo): nunca palabras sueltas o fragmentos telegráficos como "
    "'Tarea repetitiva' o 'Demora tiempo'.\n"
    "- 'cta_slide_text' no puede ser genérico ('Ver más', 'Conocé más', 'Info aquí'): tiene que "
    "relacionarse puntualmente con el caso que acabás de contar.\n"
    "- 'caption' es SOLO el texto del posteo, sin hashtags adentro (los hashtags van aparte, en "
    "el campo 'hashtags').\n\n"
    "COHERENCIA (si esto falla, el video no sirve):\n"
    "- La MISMA unidad de medida en toda la pieza. Si la portada dice 'por semana', los slides "
    "y el resultado hablan por semana. Nunca mezcles 'por semana' con 'por mes'.\n"
    "- Los números tienen que cerrar entre sí y con la aritmética. Si son 3 por semana, al año "
    "son ~156, no 270. Si no estás seguro de una cuenta, no la pongas.\n"
    "- Las 4 slides son una sola historia encadenada: (1) la escena del problema, (2) lo que "
    "eso le cuesta, (3) qué cambia con el agente, (4) el resultado con el mismo número del "
    "principio. Cada slide tiene que continuar la anterior, no ser una frase suelta.\n"
    "- El demo tiene que ser el MISMO caso del que venís hablando: si el problema es que "
    "responde tarde, el demo muestra al agente respondiendo al instante ese tipo de consulta. "
    "La respuesta del agente resuelve algo concreto, no inventa excusas ni cambia de tema.\n"
    "- 'tiempo_respuesta' tiene que ser inmediato y creíble: segundos, 'al instante', 'en el "
    "momento'. Nunca minutos ni horas — el punto del agente es justamente que no hace esperar.\n"
    "- Cada frase tiene que agregar información. Nada de muletillas vacías pegadas al final "
    "('sin borrar nada', 'y listo', 'sin problemas') que no significan nada concreto.\n\n"
    "IDIOMA — español rioplatense (Argentina):\n"
    "- Voseo siempre: 'perdés', 'tenés', 'escribime', 'contame'. Nunca 'pierdes', 'tienes', "
    "'escríbeme', 'conéctame', 'te quedas'.\n"
    "- Nada de español de España ni neutro: no uses 'coger', 'ordenador', 'móvil', 'vale'.\n"
    "- Revisá concordancia de género y número antes de responder ('las macetas', no 'los "
    "macetas'). Cada frase tiene que poder leerse en voz alta sin trabarse.\n\n"
    "GANCHO (esto es lo más importante del video):\n"
    "- 'portada_text' tiene que golpear con lo que el negocio ESTÁ PERDIENDO HOY, no con lo que "
    "podría ganar. Comparar el costo de seguir igual contra lo que cuesta resolverlo. Ejemplos "
    "del tipo de gancho: 'Perdés 3 clientes por semana sin enterarte', 'Ese mensaje sin "
    "responder se fue a la competencia', 'Cada noche regalás 40 minutos gratis'.\n"
    "- Escribí en segunda persona ('perdés', 'estás', 'tu negocio'), hablándole directo a quien "
    "mira, no en tercera persona sobre un caso ajeno.\n"
    "- La primera slide después de la portada tiene que hacer que la persona se reconozca en el "
    "problema: describí la escena concreta que vive, no el concepto abstracto.\n"
    "- El 'caption' cierra con una pregunta incómoda pero honesta, que obligue a la persona a "
    "poner un número a su propio problema (ej: '¿cuántos mensajes tenés sin responder ahora "
    "mismo?').\n"
    "- IMPORTANTE — límite ético: los números tienen que ser del CASO ILUSTRATIVO que estás "
    "contando, nunca estadísticas generales inventadas presentadas como estudios ('el 87% de "
    "los negocios...'). Nada de amenazas catastróficas ('vas a fundir'), ni de insultar o "
    "menospreciar a quien mira. Es incomodar con un costo real y concreto, no asustar con "
    "mentiras.\n\n"
    "Tenés que responder ÚNICAMENTE con un objeto JSON válido (nada de texto antes o después, "
    "nada de markdown ni ```), con exactamente esta forma:\n"
    "{\n"
    '  "negocio_ejemplo": "string, ej: \'un local de indumentaria\'",\n'
    '  "demo": {\n'
    '    "canal": "string, ej: \'WhatsApp\'",\n'
    '    "mensaje_cliente": "string, máx 18 palabras",\n'
    '    "respuesta_bot": "string, máx 22 palabras",\n'
    '    "tiempo_respuesta": "string, ej: \'en 4 segundos\'"\n'
    "  },\n"
    '  "portada_text": "string, máx 8 palabras, el gancho del video",\n'
    '  "slides": [\n'
    '    {"title": "string, máx 6 palabras", "text": "string, máx 14 palabras"},\n'
    "    ... exactamente 4 elementos (problema -> consecuencia -> solución -> resultado con número)\n"
    "  ],\n"
    '  "cta_slide_text": "string corto para la slide final",\n'
    '  "cta_final": "string, la línea de acción concreta bajo el CTA (ej: \'Escribime y te digo cuánto estás perdiendo\'). Máx 9 palabras",\n'
    '  "swipe_hint": "string en MAYÚSCULAS, máx 5 palabras, invita a seguir mirando el carrusel (ej: \'MIRÁ LO QUE PASÓ\'). Sin flechas ni emojis",\n'
    '  "demo_caption": "string en MAYÚSCULAS, máx 7 palabras, el remate que va debajo del chat del demo (ej: \'CONTESTÓ ANTES QUE VOS\')",\n'
    '  "caption": "string, 2-4 líneas, termina con una pregunta concreta",\n'
    '  "hashtags": ["8 a 10 strings sin el símbolo #, sin espacios, palabras completas y bien escritas (nunca cortadas tipo tiemposdigi)"]\n'
    "}\n\n"
    "Ejemplo del NIVEL de detalle y tono que se espera (no copies el rubro, "
    "inventá uno distinto, pero imitá exactamente este estilo de oraciones "
    "completas y específicas):\n"
    "{\n"
    '  "negocio_ejemplo": "un consultorio de kinesiología",\n'
    '  "demo": {"canal": "WhatsApp", '
    '"mensaje_cliente": "Hola, no voy a poder ir a mi turno de mañana a las 10", '
    '"respuesta_bot": "Sin problema. Tengo lugar mañana 16hs o el jueves 11hs. ¿Cuál te queda mejor?", '
    '"tiempo_respuesta": "reprogramado en el momento, sin mirar la agenda"},\n'
    '  "portada_text": "Cada noche regalás 40 minutos gratis",\n'
    '  "slides": [\n'
    '    {"title": "Son las 11 de la noche", "text": "Y seguís copiando y pegando el mismo mensaje"},\n'
    '    {"title": "Lo que te cuesta", "text": "40 minutos por noche, 4 faltazos igual por semana"},\n'
    '    {"title": "Lo que cambia", "text": "El agente avisa y reprograma sin que toques nada"},\n'
    '    {"title": "El resultado", "text": "De 4 faltazos por semana a 1"}\n'
    "  ],\n"
    '  "cta_slide_text": "¿Cuántas noches más lo vas a hacer a mano?",\n'
    '  "cta_final": "Contame tu caso y te digo por dónde empezar",\n'
    '  "swipe_hint": "MIRÁ CÓMO SE RESUELVE",\n'
    '  "demo_caption": "RESPONDIÓ SIN QUE NADIE MIRARA",\n'
    '  "caption": "40 minutos cada noche mandando el mismo mensaje con distinto horario, y los faltazos igual seguían. Ese tiempo no vuelve. ¿Cuántos turnos tenés sin confirmar ahora mismo?",\n'
    '  "hashtags": ["automatizacion", "agentesdeia", "consultorios", "pymes", "iaparanegocios", "chatbots", "productividad", "whatsappbusiness"]\n'
    "}"
)

_REQUIRED_TOP = {"negocio_ejemplo", "demo", "portada_text", "slides", "cta_slide_text", "caption", "hashtags"}
_REQUIRED_DEMO = {"canal", "mensaje_cliente", "respuesta_bot", "tiempo_respuesta"}
_REQUIRED_SLIDE = {"title", "text"}

# Formas verbales de español neutro/España que delatan que el modelo se salió
# del voseo rioplatense. Se chequean como palabra entera.
_NO_VOSEO = {
    "pierdes", "tienes", "puedes", "quieres", "haces", "necesitas", "estás perdiendo tú",
    "escríbeme", "cuéntame", "conéctame", "contáctame", "dime", "mírame",
    "tu puedes", "te quedas", "coger", "ordenador", "móvil", "vale",
}
_UNIDADES = ("por semana", "a la semana", "semanal", "por mes", "al mes", "mensual", "por día", "al día", "diario")


def _texto_completo(data: dict) -> str:
    partes = [data.get("portada_text", ""), data.get("caption", ""), data.get("cta_slide_text", ""),
              data.get("cta_final", "")]
    partes += [f'{s.get("title", "")} {s.get("text", "")}' for s in data.get("slides", [])]
    d = data.get("demo", {})
    partes += [d.get("mensaje_cliente", ""), d.get("respuesta_bot", "")]
    return " ".join(partes).lower()


def _validate(data: dict) -> None:
    missing = _REQUIRED_TOP - data.keys()
    if missing:
        raise ValueError(f"Faltan campos: {missing}")
    if _REQUIRED_DEMO - data["demo"].keys():
        raise ValueError("El campo 'demo' está incompleto")
    if not isinstance(data["slides"], list) or len(data["slides"]) < 4:
        raise ValueError("'slides' tiene que ser una lista de al menos 4 elementos")
    for s in data["slides"]:
        if _REQUIRED_SLIDE - s.keys():
            raise ValueError("Alguna slide no tiene 'title'/'text'")
        if len(s["text"].split()) < 4:
            raise ValueError(f"Slide demasiado corta para entenderse sola: {s['text']!r}")
    if not isinstance(data["hashtags"], list) or not data["hashtags"]:
        raise ValueError("'hashtags' tiene que ser una lista no vacía")

    texto = _texto_completo(data)

    encontradas = [p for p in _NO_VOSEO if re.search(rf"\b{re.escape(p)}\b", texto)]
    if encontradas:
        raise ValueError(f"No está en voseo rioplatense: {encontradas}")

    # Mezclar unidades de tiempo es el error más común y rompe la coherencia
    # del carrusel (portada 'por semana' vs resultado 'al mes').
    usadas = {u for u in _UNIDADES if u in texto}
    familias = {
        "semana" if "seman" in u else "mes" if ("mes" in u or "mensual" in u) else "dia"
        for u in usadas
    }
    if len(familias) > 1:
        raise ValueError(f"Mezcla unidades de tiempo distintas: {sorted(usadas)}")

    if len(data["caption"].split()) < 12:
        raise ValueError("El caption quedó demasiado corto/cortado")

    tiempo = data["demo"].get("tiempo_respuesta", "").lower()
    if re.search(r"\b(minutos?|horas?|días?)\b", tiempo):
        raise ValueError(f"tiempo_respuesta no es inmediato: {tiempo!r}")

    # Los hashtags salen mal escritos o cortados seguido ('tiemposdigi'), y en
    # el posteo se notan mucho. Mejor descartar y reintentar.
    for h in data["hashtags"]:
        limpio = h.lstrip("#").strip()
        if len(limpio) < 5 or " " in limpio:
            raise ValueError(f"Hashtag inválido o cortado: {h!r}")


def _ping_ollama() -> None:
    try:
        requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5).raise_for_status()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(
            f"No se pudo conectar a Ollama en {OLLAMA_HOST}. ¿Está corriendo? "
            "Abrí la app de Ollama o corré 'ollama serve'."
        ) from e


def _chat_json(system: str, user: str, validate) -> dict:
    """Le pide al modelo local un JSON, valida con `validate(data)` (debe tirar
    ValueError si falta algo) y reintenta unas veces si sale mal formado."""
    _ping_ollama()
    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        resp = requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "format": "json",
                "stream": False,
                "options": {"temperature": 0.9},
            },
            timeout=300,
        )
        resp.raise_for_status()
        raw = resp.json()["message"]["content"]

        try:
            data = json.loads(raw)
            validate(data)
            return data
        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
            print(f"  (intento {attempt}/{MAX_RETRIES} con Ollama falló: {e}, reintentando...)")

    raise RuntimeError(
        f"El modelo local ({OLLAMA_MODEL}) no devolvió un JSON válido tras {MAX_RETRIES} intentos: {last_error}"
    )


def generate_content(pillar_label: str, angle: str) -> dict:
    """Pide al modelo local (vía Ollama) un paquete completo de contenido. Costo: $0."""
    user_prompt = (
        f"Pilar de contenido: {pillar_label}.\n"
        f"Ángulo del video: {angle}\n\n"
        "Elegí un rubro de negocio concreto y específico (uno distinto cada vez, no siempre el "
        "mismo) y armá el contenido para un video sin voz en off, contado a través de ese rubro "
        "y de un demo real de conversación cliente-agente. Nada de lenguaje de marketing "
        "genérico. Respondé solo con el JSON pedido, sin texto extra."
    )
    return _chat_json(SYSTEM_PROMPT, user_prompt, _validate)


_MOCKUP_SPECS = {
    "web": {
        "campos": (
            '{"url": "string corto, ej: pedidos.tunegocio.com", '
            '"headline": "máx 8 palabras", "subheadline": "máx 10 palabras", '
            '"cta": "máx 4 palabras", "features": ["exactamente 3 strings cortos, máx 4 palabras cada uno"], '
            '"caption": "una sola oración natural que explica qué se ve, mencionando el rubro del negocio"}'
        ),
        "ejemplo": (
            '{"url": "turnos.tunegocio.com", "headline": "Sacá turno sin esperar que atiendan", '
            '"subheadline": "Ves los horarios libres al toque", "cta": "Ver horarios", '
            '"features": ["Horarios reales", "Confirmación automática", "Reprogramar fácil"], '
            '"caption": "Así podría verse la web de un consultorio de kinesiología, directa y sin vueltas"}'
        ),
        "required": {"url", "headline", "subheadline", "cta", "features", "caption"},
    },
    "bot": {
        "campos": (
            '{"steps": ["exactamente 4 strings, cada uno un paso corto del flujo, en orden"], '
            '"caption": "una sola oración natural que explica qué se ve, mencionando el rubro del negocio"}'
        ),
        "ejemplo": (
            '{"steps": ["Se acerca la fecha del turno", "El sistema arma el recordatorio", '
            '"Lo manda por WhatsApp", "Reprograma si hace falta"], '
            '"caption": "Así es el flujo por detrás en un consultorio de kinesiología, nadie lo ve pero corre solo"}'
        ),
        "required": {"steps", "caption"},
    },
    "agente": {
        "campos": (
            '{"items": ["exactamente 3 objetos con name (máx 3 palabras), '
            'price (ej: $8.500), match (ej: 92% match)"], '
            '"caption": "una sola oración natural que explica qué se ve, mencionando el rubro del negocio"}'
        ),
        "ejemplo": (
            '{"items": [{"name": "Plan inicial", "price": "$5.000", "match": "90% match"}, '
            '{"name": "Plan recomendado", "price": "$12.000", "match": "94% match"}, '
            '{"name": "Plan completo", "price": "$19.500", "match": "82% match"}], '
            '"caption": "Así arma las recomendaciones un agente de IA para un consultorio de kinesiología"}'
        ),
        "required": {"items", "caption"},
    },
}


def generate_mockup_content(negocio_ejemplo: str, kind: str) -> dict:
    """Genera el contenido (ficticio, ilustrativo) de un mockup de solución
    ('web', 'bot' o 'agente') con el modelo local. Costo: $0."""
    spec = _MOCKUP_SPECS[kind]

    system = (
        "Generás el contenido de ejemplo (ficticio, ilustrativo) que se muestra dentro de un "
        f"mockup gráfico de tipo '{kind}' para un video de TikTok sobre automatización/IA para "
        "negocios. Respondé ÚNICAMENTE con un objeto JSON válido (nada de texto ni markdown "
        "antes o después), con EXACTAMENTE esta forma (todos los campos son obligatorios, "
        "incluido \"caption\"):\n"
        f"{spec['campos']}\n\n"
        "Ejemplo de estilo (no copies el contenido, inventá otro específico para el rubro indicado, "
        "pero incluí SIEMPRE los mismos campos, caption incluido):\n"
        f"{spec['ejemplo']}"
    )
    user = f"Rubro del negocio: {negocio_ejemplo}."

    def _validate_mockup(data: dict) -> None:
        missing = spec["required"] - data.keys()
        if missing:
            raise ValueError(f"Faltan campos: {missing}")
        if "caption" not in data:
            raise ValueError("Falta 'caption'")

    data = _chat_json(system, user, _validate_mockup)
    data["kind"] = kind
    return data
