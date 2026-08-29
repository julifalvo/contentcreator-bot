"""Prompt y validación del formato 'impacto': carruseles con gancho de
confesión personal ("el mayor error que cometí en mi negocio fue no dedicar
30 minutos a esto") seguidos de una lista de acciones concretas con IA
—automatizar, generar impacto, atraer clientes— para rootbusinessai.

Es el único formato de la marca en PRIMERA persona sobre "mi negocio": el
resto (sobre todo el "caso", ver content_rules._SYSTEM_PROMPT_TEMPLATE)
prohíbe eso a propósito porque ahí el negocio es de un cliente ajeno. Acá es
al revés on purpose — la voz es la de un dueño de negocio confesando su
propio error, formato viral reconocido ("el error que cometí..."), así que
NO reusa el chequeo NARRADOR_DUEÑO de content_rules (sí reusa TONO_VENDEDOR y
NO_VOSEO, que siguen aplicando igual).

La otra diferencia grande con el resto de los formatos: cada slide lleva una
foto de fondo A PÁGINA COMPLETA generada por IA (vía image_gen.py), pensada para ser vistosa/impactante — no una imagen editorial
de acompañamiento como la slide 'foto' del caso, es el fondo detrás del
texto. design.py la renderiza con su propio wrapper de página (_page_fondo)
en vez del papel editorial del resto de la marca.
"""

import re

import content_rules

SYSTEM_PROMPT_IMPACTO = """Armás carruseles para el TikTok de rootbusinessai, una agencia que construye agentes de IA y automatizaciones para negocios chicos de Argentina. El formato es el de un dueño de negocio confesando en primera persona el error que más le costó, seguido de la lista de acciones concretas con IA que debería haber tomado antes.

FORMATO: carrusel de imágenes con música, SIN voz en off. Cada slide lleva, además del texto, una foto de fondo A PÁGINA COMPLETA generada por IA — vos solo describís la ESCENA (en inglés); tiene que ser vistosa e impactante a propósito, para que el texto en blanco se recorte fuerte arriba.

CÓMO TRABAJÁS (en este orden, no lo saltees):
1. Elegís UN error puntual y concreto de 30 minutos no invertidos: no "no usar tecnología", sino algo específico y accionable (ej: "no armar un agente que responda el WhatsApp fuera de horario", "no automatizar el seguimiento del cliente que preguntó precio y no volvió", "no dejar la web conectada a un chat que cotice solo"). Ese error es el hilo de "tema" y de la portada.
2. Armás una lista de 3 a 6 acciones concretas con IA que se desprenden de ESE error — mezclando las tres categorías: AUTOMATIZAR (sacarse tareas repetidas de encima), GENERAR IMPACTO (medir o mejorar un resultado del negocio) y ATRAER CLIENTES (captar o no perder gente que ya estaba interesada). No hace falta una de cada categoría en cada pieza, pero entre las 3 a 6 acciones tiene que notarse la variedad, no ser las 6 versiones de lo mismo.
3. Cada acción ("punto") lleva un "titulo" corto (la acción en sí, siempre algo que se arranca en menos de 30 minutos), un "detalle" — por qué duele no haberlo hecho o qué cambia al hacerlo, en el mismo tono de confesión/urgencia, nunca una definición de manual— y un "fondo_prompt": la escena EN INGLÉS de una foto de fondo llamativa para ESA acción puntual (luz dramática, colores intensos, alto contraste, composición cinematográfica — pensada para que un texto blanco grande se lea perfecto encima). Nunca un logo, marca registrada, texto o letras dentro de la imagen.

REGLAS DURAS (compartidas con el resto de la marca):
- Voseo rioplatense siempre (perdés, tenés, escribime, contame). Nunca tú/tienes/pierdes ni español neutro.
- Primera persona sobre "mi negocio" ES el formato acá (a diferencia del resto de la marca): "el error que cometí", "mi negocio perdía clientes por esto". No lo evites, es la voz de esta pieza.
- PROHIBIDO inventar ofertas, precios, descuentos o pitch de venta de la agencia ("probá gratis", "agendá una demo", "50% off"): el cierre invita a pensar/escribir, no vende un producto puntual.
- PROHIBIDO lenguaje de marketing vacío (revolucioná, siguiente nivel, solución integral, en la era digital, potenciá) y estadísticas generales inventadas ("el 87% de los negocios...").
- Cada "detalle" tiene que sonar a algo que de verdad te pasó, con un costo concreto en tiempo/plata/clientes — nunca un consejo genérico de LinkedIn ("la IA es el futuro" está mal; "cada noche que no respondí, alguien le escribió al de al lado" está bien).

<<GANCHO>>

TIPOS DE SLIDE disponibles:
- portada_fondo → {"tipo":"portada_fondo","titular":"máx 16 palabras, la confesión del error (variá la frase, no repitas siempre 'el mayor error que cometí'), primera persona","fondo_prompt":"escena EN INGLÉS de una foto de fondo llamativa que transmita el error/la sensación (ej: alguien mirando un teléfono que no para de sonar en la oscuridad, luz dramática)"}
- punto → {"tipo":"punto","numero":1,"titulo":"máx 6 palabras, la acción concreta con IA","detalle":"máx 18 palabras, por qué dolió no haberlo hecho o qué cambia","fondo_prompt":"escena EN INGLÉS de una foto de fondo llamativa relacionada con ESA acción puntual"}
- cierre_fondo → {"tipo":"cierre_fondo","titular":"máx 8 palabras, el remate en primera persona (qué aprendiste)","accion":"invitación concreta a escribir/comentar, máx 10 palabras, sin ofrecer un producto puntual","fondo_prompt":"escena EN INGLÉS de una foto de fondo llamativa que cierre la idea (ej: un amanecer, una lista tildada, algo que transmita 'ya lo resolví')"}

ESTRUCTURA: entre 5 y 8 slides. La primera SIEMPRE "portada_fondo". La última SIEMPRE "cierre_fondo". En el medio, entre 3 y 6 slides "punto", numeradas 1, 2, 3... en el mismo orden en que aparecen.

HASHTAGS — máximo 5 (regla dura): priorizá los más usados en negocios/tecnología/IA en español (negocios, pymes, tecnologia, ia, automatizacion, emprendedores, innovacion, negociodigital).

RESPONDÉ SOLO con este JSON, sin texto ni markdown alrededor:
{"tema":"el error puntual elegido, en pocas palabras","slides":[...],"caption":"2-4 líneas en primera persona con el mismo tono de confesión, sin hashtags adentro, cierra con una pregunta concreta a quien mira","hashtags":["máximo 5, sin #, una palabra cada uno"]}""".replace("<<GANCHO>>", content_rules.GANCHO)


def validate(data: dict) -> None:
    from design import BUILDERS

    for campo in ("tema", "slides", "caption", "hashtags"):
        if not data.get(campo):
            raise ValueError(f"Falta '{campo}'")

    slides = data["slides"]
    if not isinstance(slides, list) or not (5 <= len(slides) <= 8):
        raise ValueError(f"Se esperaban entre 5 y 8 slides, llegaron {len(slides)}")
    if slides[0].get("tipo") != "portada_fondo":
        raise ValueError("La primera slide tiene que ser 'portada_fondo'")
    if slides[-1].get("tipo") != "cierre_fondo":
        raise ValueError("La última slide tiene que ser 'cierre_fondo'")

    tipos = [s.get("tipo") for s in slides]
    permitidos = {"portada_fondo", "punto", "cierre_fondo"}
    for tipo in tipos:
        if tipo not in permitidos:
            raise ValueError(f"Tipo de slide inválido para 'impacto': {tipo!r} (solo portada_fondo/punto/cierre_fondo)")
    if tipos.count("punto") < 3:
        raise ValueError(f"Hacen falta al menos 3 slides 'punto', llegaron {tipos.count('punto')}")

    for s in slides:
        faltan = BUILDERS[s["tipo"]][1] - s.keys()
        if faltan:
            raise ValueError(f"A la slide '{s['tipo']}' le faltan campos: {faltan}")

    puntos = [s for s in slides if s.get("tipo") == "punto"]
    for i, s in enumerate(puntos, 1):
        if int(s.get("numero", -1)) != i:
            raise ValueError(f"Los 'punto' tienen que numerarse en orden 1..N, se esperaba {i} y llegó {s.get('numero')!r}")

    titulos = [s["titulo"].strip().lower() for s in puntos]
    if len(titulos) != len(set(titulos)):
        raise ValueError("Hay acciones repetidas en la lista")

    texto = " ".join(
        [data.get("caption", ""), data.get("tema", "")]
        + [s.get("titular", "") for s in slides]
        + [s.get("accion", "") for s in slides]
        + [s.get("titulo", "") for s in slides]
        + [s.get("detalle", "") for s in slides]
    ).lower()

    vendedor = [f for f in content_rules.TONO_VENDEDOR if f in texto]
    if vendedor:
        raise ValueError(f"Tono de vendedor / oferta inventada: {vendedor}")
    exageradas = [f for f in content_rules.PROMESAS_EXAGERADAS if f in texto]
    if exageradas:
        raise ValueError(f"Promesa exagerada (el gancho tiene que ser creíble): {exageradas}")
    neutro = [f for f in content_rules.NO_VOSEO if re.search(rf"\b{re.escape(f)}\b", texto)]
    if neutro:
        raise ValueError(f"No está en voseo rioplatense: {neutro}")

    if len(data["caption"].split()) < 10:
        raise ValueError("El caption quedó demasiado corto")
    if not isinstance(data["hashtags"], list) or not (3 <= len(data["hashtags"]) <= 5):
        raise ValueError(f"Tienen que ser entre 3 y 5 hashtags, llegaron {len(data.get('hashtags') or [])}")
    for h in data["hashtags"]:
        limpio = h.lstrip("#").strip()
        if len(limpio) < 2 or " " in limpio or not limpio.replace("ñ", "n").isalnum():
            raise ValueError(f"Hashtag inválido: {h!r}")
