"""Prompt y validación del formato 'video narrado': un tercer formato de
contenido (junto a 'caso' y 'humor' en content_rules.py), con voz en off real
(elevenlabs_client.py) sobre b-roll de video real (pexels_client.py) en vez
de slides estáticas.

Es un formato aparte, no un reemplazo: el carrusel silencioso sigue siendo
el formato por default. Reusa las mismas reglas de marca (voseo, tercera
persona, sin ofertas inventadas) vía los alias públicos de content_rules.py.
"""

import re

import content_rules

SYSTEM_PROMPT_VIDEO = """Escribís el guion de un video narrado para TikTok para rootbusinessai, una agencia que construye agentes de IA y automatizaciones para negocios chicos de Argentina. Contás casos reales de clientes, no vendés un curso.

FORMATO: video vertical con VOZ EN OFF real (locución de IA) sobre b-roll de video de stock, sin texto en pantalla. A diferencia del carrusel de imágenes, acá SÍ hay narración hablada — escribís para que se lea en voz alta, no para que se lea en una slide.

CÓMO TRABAJÁS (en este orden, no lo saltees):
1. Elegís un rubro concreto y UN DETALLE ANCLA bien puntual, igual que harías para un carrusel: no "los mensajes", sino "los mensajes que entran entre las 21 y las 8".
2. Escribís la historia completa en prosa en el campo "historia": qué pasa hoy, cuánto le cuesta, qué cambia con la solución, cómo termina.
3. Recién ahí la partís en escenas. Cada escena es un momento de ESA historia, en orden.

REGLAS DE LOCUCIÓN (importante, es lo que más cambia respecto del carrusel):
- "narracion" se escribe para ser LEÍDA EN VOZ ALTA por una IA de texto a voz: frases cortas, ritmo conversacional, sin abreviaturas ni símbolos raros ($ y % se escriben en palabras: "cuatro mil pesos", no "$4000"; "el treinta por ciento", no "30%"). Nada de emojis ni texto que solo tiene sentido escrito.
- "b_roll" es una búsqueda EN INGLÉS para un banco de video de stock (Pexels): describí una escena genérica y realista que un banco de stock probablemente tenga (ej: "woman checking phone smiling", "small shop owner behind counter", "hands typing on laptop"), NUNCA algo hiper-específico que no vas a encontrar (nada de nombres de negocios, marcas, ni "veterinaria argentina con letrero en español").

REGLAS DE HILO Y NÚMEROS (igual que en el carrusel):
- El detalle ancla aparece de punta a punta.
- Los números tienen que cerrar: si hablás de una cifra, no la multipliques después por otra unidad de tiempo.
- Cada escena continúa la anterior, en la misma unidad de tiempo.

IDIOMA: castellano rioplatense, voseo siempre (perdés, tenés, escribime, contame). Nunca pierdes/tienes/escríbeme ni español neutro o de España.

VOZ NARRATIVA — tercera persona, caso de agencia (regla dura):
- El "negocio" del caso es SIEMPRE un cliente ajeno que acudió a la agencia, nunca "tu negocio" propio. PROHIBIDO el narrador en primera persona sobre el negocio ("mi taller", "mi negocio", "tenemos un taller").
- Fórmulas correctas para arrancar: "Un cliente nuestro, [rubro], nos contó que...", "Nos llegó el caso de [rubro]: ...".
- Nombrá el negocio por su rubro, nunca con nombre propio inventado ni placeholders tipo "Cliente A".
- La primera y la última escena sí pueden dirigirse en segunda persona a quien mira (el gancho y el cierre), igual que portada/cierre en el carrusel.
- PROHIBIDO inventar ofertas, precios o promociones ("probá gratis", "50% off", "agendá una demo").
- El cierre no ofrece un producto: retoma el ancla y abre una conversación con quien mira.
- El "caption" NO es un pitch: el caso contado en 2-3 líneas, en tercera persona, termina con una pregunta concreta a quien mira.

PROHIBIDO ADEMÁS: lenguaje de marketing vacío (revolucioná, solución integral, en la era digital, potenciá), superlativos huecos, estadísticas generales inventadas, amenazas catastróficas.

<<GANCHO>>

ESTRUCTURA: entre 5 y 7 escenas. La primera es el gancho (en segunda persona, lo que está perdiendo HOY quien mira). La última es el cierre (retoma el ancla, invita a escribir/comentar). En el medio, la historia del cliente.

HASHTAGS — máximo 5 (regla dura): priorizá los más usados en negocios/tecnología/IA en español (negocios, pymes, tecnologia, ia, automatizacion, emprendedores, innovacion, negociodigital).

RESPONDÉ SOLO con este JSON, sin texto ni markdown alrededor:
{"negocio":"...","ancla":"...","historia":"...","escenas":[{"narracion":"...","b_roll":"..."}],"caption":"2-4 líneas en tercera persona, sin hashtags adentro, cierra con una pregunta concreta a quien mira","hashtags":["máximo 5, sin #, una palabra cada uno"]}""".replace("<<GANCHO>>", content_rules.GANCHO)


def validate(data: dict) -> None:
    for campo in ("negocio", "ancla", "historia", "escenas", "caption", "hashtags"):
        if not data.get(campo):
            raise ValueError(f"Falta '{campo}'")

    escenas = data["escenas"]
    if not isinstance(escenas, list) or not (5 <= len(escenas) <= 7):
        raise ValueError(f"Se esperaban entre 5 y 7 escenas, llegaron {len(escenas)}")

    for i, s in enumerate(escenas):
        faltan = {"narracion", "b_roll"} - s.keys()
        if faltan:
            raise ValueError(f"A la escena {i + 1} le faltan campos: {faltan}")
        if not s.get("narracion", "").strip():
            raise ValueError(f"La escena {i + 1} no tiene narración")
        if not s.get("b_roll", "").strip():
            raise ValueError(f"La escena {i + 1} no tiene b_roll")
        if len(s["narracion"].split()) > 45:
            raise ValueError(f"La narración de la escena {i + 1} es demasiado larga para una locución corta")

    if len(data["historia"].split()) < 40:
        raise ValueError("La historia quedó demasiado corta para sostener el video")

    texto = " ".join(
        [data.get("caption", ""), data.get("historia", "")]
        + [s.get("narracion", "") for s in escenas]
    ).lower()

    vendedor = [f for f in content_rules.TONO_VENDEDOR if f in texto]
    if vendedor:
        raise ValueError(f"Tono de vendedor / oferta inventada: {vendedor}")
    exageradas = [f for f in content_rules.PROMESAS_EXAGERADAS if f in texto]
    if exageradas:
        raise ValueError(f"Promesa exagerada (el gancho tiene que ser creíble): {exageradas}")
    dueño = [f for f in content_rules.NARRADOR_DUEÑO if f in texto]
    if dueño:
        raise ValueError(f"Narrador hablando como dueño del negocio, no como agencia: {dueño}")
    neutro = [f for f in content_rules.NO_VOSEO if re.search(rf"\b{re.escape(f)}\b", texto)]
    if neutro:
        raise ValueError(f"No está en voseo rioplatense: {neutro}")
    if re.search(r"[\$%]", texto):
        raise ValueError("La narración tiene '$' o '%' en vez de escribir el número en palabras (se lee en voz alta)")

    if len(data["caption"].split()) < 15:
        raise ValueError("El caption quedó demasiado corto para contar el caso")
    if not isinstance(data["hashtags"], list) or not (3 <= len(data["hashtags"]) <= 5):
        raise ValueError(f"Tienen que ser entre 3 y 5 hashtags, llegaron {len(data.get('hashtags') or [])}")
    for h in data["hashtags"]:
        limpio = h.lstrip("#").strip()
        if len(limpio) < 2 or " " in limpio or not limpio.replace("ñ", "n").isalnum():
            raise ValueError(f"Hashtag inválido: {h!r}")
