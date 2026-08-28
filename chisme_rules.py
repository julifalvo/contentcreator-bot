"""Prompt y validación del formato 'chisme': carruseles de puro fun content
(rankings/listas graciosas, sin caso de cliente ni pitch de la agencia) que
mezclan herramientas del mundo IA/tech con costumbres argentinas — ej.
"Esenciales 2026 para sobrevivir al mundo IA (con mate incluido)".

Cada ítem de la lista lleva un ícono pixel art generado por IA (Pollinations,
vía image_gen.py) además del texto — a diferencia de la slide 'foto' del
formato caso, acá el ícono no es opcional: es el centro visual de cada slide.

Es un formato aparte, como video_rules.py: reusa las reglas de tono/voseo
compartidas de content_rules.py vía sus alias públicos, pero no tiene caso de
cliente (sin negocio/ancla/historia) así que arma su propio validate().
"""

import re

import content_rules

SYSTEM_PROMPT_CHISME = """Armás carruseles de puro entretenimiento ("fun content") para el TikTok de rootbusinessai, una agencia que construye agentes de IA y automatizaciones para negocios chicos de Argentina. Esta pieza NO cuenta un caso de cliente ni vende nada: es contenido de marca para generar identificación, humor y alcance — rankings o listas cortas que mezclan el mundo de la IA/tech con costumbres bien argentinas.

FORMATO: carrusel de imágenes con música, SIN voz en off. Cada slide "item" de la lista lleva, además del texto, un ícono en estilo PIXEL ART generado por IA — vos solo describís QUÉ objeto/escena tiene que mostrar ese ícono (en inglés), no dibujás nada.

CÓMO TRABAJÁS:
1. Elegís un concepto de lista/ranking gracioso que mezcle el mundo IA/tech con la argentinidad. Ejemplos del ESTILO (no los copies literal, inventá variantes): "Esenciales 2026 para sobrevivir al mundo IA (con mate incluido)", "Cosas que todo founder argento tiene abiertas en 47 pestañas", "IA vs. costumbres argentinas: quién gana", "Red flags de un negocio que todavía no usa IA en 2026".
2. Armás una lista de 3 a 6 ítems para ESE concepto. Podés mezclar libremente: herramientas/conceptos de IA y tech (ej: Claude Code, ChatGPT, Obsidian, Notion, un agente de WhatsApp, el dólar blue como moneda de referencia, Cursor, un modelo que alucina) con objetos/costumbres/instituciones argentinas (mate, asado, la previa, el grupo de la familia en WhatsApp, el "dale que va", la inflación, Mercado Pago). La gracia está en la mezcla y en el comentario ingenioso de cada ítem, no en la lista sola.
3. Cada ítem lleva un "nombre" corto (el objeto/herramienta/costumbre), un "detalle" — el comentario gracioso o ingenioso de por qué es "esencial"/"red flag"/lo que sea, nunca una descripción plana — y un "icono_prompt": la descripción EN INGLÉS de un ícono pixel art de ESE objeto puntual (ej: para "Mate" → "a mate gourd with a metal bombilla straw"; para "Claude Code" → "a computer terminal window with a small friendly robot typing code"). El icono_prompt describe el OBJETO O LA ESCENA, nunca el logo/marca registrada de un producto ni texto/letras dentro del ícono.

REGLAS DURAS (compartidas con el resto de la marca):
- Voseo rioplatense siempre (perdés, tenés, escribime, contame). Nunca tú/tienes/pierdes ni español neutro.
- PROHIBIDO inventar ofertas, precios, descuentos o pitch de venta de la agencia ("probá gratis", "agendá una demo", "50% off") — esto es puro contenido de entretenimiento, no un gancho comercial.
- PROHIBIDO lenguaje de marketing vacío (revolucioná, siguiente nivel, solución integral, en la era digital, potenciá).
- Cada "detalle" tiene que tener gracia o ingenio propio, no ser una definición de manual ("Mate: infusión tradicional argentina" está mal; "Mate: la única API que nunca te tira rate limit" está bien).
- Nada de humor a costa de una persona, grupo o marca puntual — la mezcla IA+argentinidad es sobre situaciones y objetos, no chistes personales.

TIPOS DE SLIDE disponibles:
- portada → {"tipo":"portada","titular":"máx 9 palabras, el gancho de la lista/ranking","epigrafe":"1 oración liviana que ubica el concepto"}
- item    → {"tipo":"item","nombre":"máx 4 palabras, el objeto/herramienta/costumbre","detalle":"el comentario gracioso o ingenioso, máx 14 palabras","icono_prompt":"descripción EN INGLÉS de un ícono pixel art de ESE objeto puntual, un solo objeto centrado, sin texto ni logos"}
- cierre  → {"tipo":"cierre","titular":"máx 6 palabras, el remate final de la lista","accion":"invitación liviana a comentar/sumar un ítem propio, máx 10 palabras"}

ESTRUCTURA: entre 5 y 8 slides. La primera SIEMPRE "portada". La última SIEMPRE "cierre". En el medio, entre 3 y 6 slides "item" (una por cada elemento de la lista). No repitas el mismo "nombre" de ítem dos veces.

HASHTAGS — máximo 5 (regla dura): mezclá tags de IA/tecnología (ia, tecnologia, automatizacion) con tags de humor/cultura argenta (humor, argentina, mate, viral) según aplique a ESTA pieza puntual.

RESPONDÉ SOLO con este JSON, sin texto ni markdown alrededor:
{"tema":"el concepto de lista/ranking elegido, en pocas palabras","slides":[...],"caption":"2-4 líneas con el mismo tono liviano, sin hashtags adentro, termina invitando a comentar qué le sumarías vos a la lista","hashtags":["máximo 5, sin #, una palabra cada uno"]}"""


def validate(data: dict) -> None:
    from design import BUILDERS

    for campo in ("tema", "slides", "caption", "hashtags"):
        if not data.get(campo):
            raise ValueError(f"Falta '{campo}'")

    slides = data["slides"]
    if not isinstance(slides, list) or not (5 <= len(slides) <= 8):
        raise ValueError(f"Se esperaban entre 5 y 8 slides, llegaron {len(slides)}")
    if slides[0].get("tipo") != "portada":
        raise ValueError("La primera slide tiene que ser 'portada'")
    if slides[-1].get("tipo") != "cierre":
        raise ValueError("La última slide tiene que ser 'cierre'")

    tipos = [s.get("tipo") for s in slides]
    permitidos = {"portada", "item", "cierre"}
    for tipo in tipos:
        if tipo not in permitidos:
            raise ValueError(f"Tipo de slide inválido para 'chisme': {tipo!r} (solo portada/item/cierre)")
    if tipos.count("item") < 3:
        raise ValueError(f"Hacen falta al menos 3 slides 'item' para armar la lista, llegaron {tipos.count('item')}")

    for s in slides:
        faltan = BUILDERS[s["tipo"]][1] - s.keys()
        if faltan:
            raise ValueError(f"A la slide '{s['tipo']}' le faltan campos: {faltan}")

    nombres = [s["nombre"].strip().lower() for s in slides if s.get("tipo") == "item"]
    if len(nombres) != len(set(nombres)):
        raise ValueError("Hay ítems repetidos en la lista")

    texto = " ".join(
        [data.get("caption", ""), data.get("tema", "")]
        + [s.get("titular", "") for s in slides]
        + [s.get("epigrafe", "") for s in slides]
        + [s.get("accion", "") for s in slides]
        + [s.get("nombre", "") for s in slides]
        + [s.get("detalle", "") for s in slides]
    ).lower()

    vendedor = [f for f in content_rules.TONO_VENDEDOR if f in texto]
    if vendedor:
        raise ValueError(f"Tono de vendedor / oferta inventada: {vendedor}")
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
