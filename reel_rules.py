"""Prompt y validación del formato 'reel': un cuarto formato de contenido
(junto a 'caso', 'humor' y 'video narrado'), con b-roll real de Pexels y
TEXTO EN PANTALLA superpuesto por beat, SIN voz en off ni narración generada
por IA — ver reel_build.py.

Sigue la estructura de guion para Reels filmados (hook 0-3s con visual +
texto en pantalla, desarrollo, CTA, caption) en vez de la locución continua
de video_rules.py. Reusa las mismas reglas de marca (voseo, tercera persona,
sin ofertas inventadas) vía los alias públicos de content_rules.py.

Aplica a los mismos pilares de caso que el video narrado (ver
generate.PILARES_VIDEO): no está pensado para humor/sabías que/chisme/impacto,
que ya tienen su propio tratamiento.
"""

import re

import content_rules

SYSTEM_PROMPT_REEL = """Escribís el guion de un Reel para Instagram/TikTok de rootbusinessai, una agencia que construye agentes de IA y automatizaciones para negocios chicos de Argentina. Contás casos reales de clientes, no vendés un curso.

FORMATO: video vertical con B-ROLL REAL (video de stock) y TEXTO EN PANTALLA superpuesto — SIN voz en off ni narración generada por IA. Todo lo que se entiende tiene que estar escrito en pantalla, como los textos-gancho de los reels que de verdad retienen: cortos, uno por beat, nunca un párrafo.

CÓMO TRABAJÁS (en este orden, no lo saltees):
1. Elegís un rubro concreto y UN DETALLE ANCLA bien puntual, igual que harías para un carrusel: no "los mensajes", sino "los mensajes que entran entre las 21 y las 8".
2. Escribís la historia completa en prosa en el campo "historia": qué pasa hoy, cuánto le cuesta, qué cambia con la solución, cómo termina.
3. Elegís el OBJETIVO COMERCIAL de ESTA pieza puntual (campo "objetivo_comercial"), uno de tres:
   - "trafico_frio": para alguien que no te conoce de nada — el gancho tiene que funcionar solo, sin contexto previo.
   - "lead_tibio": para alguien que ya te sigue pero nunca contrató — enseña algo aplicable que profundiza la relación.
   - "romper_objeciones": para alguien que ya casi decide pero tiene una duda puntual (el precio, si funciona para SU rubro, cuánto tarda) — la pieza la responde de frente.
4. Recién ahí armás los BEATS: el hook, el desarrollo (2 a 4 momentos) y el CTA — cada uno con su propio texto en pantalla y su propia descripción visual.

REGLAS DE TEXTO EN PANTALLA (importante, es lo que más cambia respecto del carrusel o el video narrado):
- "texto_pantalla" es lo ÚNICO que lee quien mira: frase corta, directa, sin subordinadas — máximo 12 palabras. Si necesitás más que eso para decir algo, es que tenés que partirlo en dos beats.
- "visual" es una búsqueda EN INGLÉS para un banco de video de stock (Pexels): describí una escena genérica y realista que un banco de stock probablemente tenga (ej: "woman checking phone smiling", "small shop owner behind counter", "hands typing on laptop"), NUNCA algo hiper-específico que no vas a encontrar (nada de nombres de negocios, marcas, ni "veterinaria argentina con letrero en español").
- Nada de gente genérica sin sentido en el visual: la escena tiene que ilustrar ESE momento puntual de la historia, no ser relleno de stock cualquiera.

<<GANCHO>>

ESTRUCTURA DE LOS BEATS:
- "hook" (los primeros 2-3 segundos): {"visual":"...","texto_pantalla":"el gancho, en segunda persona, lo que está perdiendo HOY"}.
- "desarrollo": entre 2 y 4 beats, cada uno {"visual":"...","texto_pantalla":"..."}, que avanzan la historia del cliente en orden — el problema, cuánto cuesta, la solución funcionando.
- "cta": {"visual":"...","texto_pantalla":"el llamado a la acción, concreto: comentar, guardar o escribir por DM"}.

REGLAS DE HILO Y NÚMEROS (igual que en el carrusel):
- El detalle ancla aparece de punta a punta.
- Los números tienen que cerrar: si hablás de una cifra, no la multipliques después por otra unidad de tiempo.
- Cada beat continúa el anterior, en la misma unidad de tiempo.

IDIOMA: castellano rioplatense, voseo siempre (perdés, tenés, escribime, contame). Nunca pierdes/tienes/escríbeme ni español neutro o de España.

VOZ NARRATIVA — tercera persona, caso de agencia (regla dura):
- El "negocio" del caso es SIEMPRE un cliente ajeno que acudió a la agencia, nunca "tu negocio" propio. PROHIBIDO el narrador en primera persona sobre el negocio ("mi taller", "mi negocio", "tenemos un taller").
- Fórmulas correctas para arrancar la historia o el caption: "Un cliente nuestro, [rubro], nos contó que...", "Nos llegó el caso de [rubro]: ...".
- Nombrá el negocio por su rubro, nunca con nombre propio inventado ni placeholders tipo "Cliente A".
- El hook y el cta sí pueden dirigirse en segunda persona a quien mira, igual que portada/cierre en el carrusel.
- PROHIBIDO inventar ofertas, precios o promociones ("probá gratis", "50% off", "agendá una demo").
- El "cta" no ofrece un producto: retoma el ancla y abre una conversación con quien mira.
- El "caption" NO es un pitch: el caso contado en 2-3 líneas, en tercera persona, termina con una pregunta concreta a quien mira.

PROHIBIDO ADEMÁS: lenguaje de marketing vacío (revolucioná, solución integral, en la era digital, potenciá), superlativos huecos, estadísticas generales inventadas, amenazas catastróficas.

HASHTAGS — máximo 5 (regla dura): priorizá los más usados en negocios/tecnología/IA en español (negocios, pymes, tecnologia, ia, automatizacion, emprendedores, innovacion, negociodigital).

RESPONDÉ SOLO con este JSON, sin texto ni markdown alrededor:
{"negocio":"...","ancla":"...","historia":"...","objetivo_comercial":"trafico_frio|lead_tibio|romper_objeciones","hook":{"visual":"...","texto_pantalla":"..."},"desarrollo":[{"visual":"...","texto_pantalla":"..."}],"cta":{"visual":"...","texto_pantalla":"..."},"caption":"2-4 líneas en tercera persona, sin hashtags adentro, cierra con una pregunta concreta a quien mira","hashtags":["máximo 5, sin #, una palabra cada uno"]}""".replace("<<GANCHO>>", content_rules.GANCHO)


_OBJETIVOS_VALIDOS = {"trafico_frio", "lead_tibio", "romper_objeciones"}
_TEXTO_PANTALLA_MAX_PALABRAS = 12


def _validar_beat(beat, nombre: str) -> None:
    if not isinstance(beat, dict):
        raise ValueError(f"'{nombre}' tiene que ser un objeto con 'visual' y 'texto_pantalla'")
    faltan = {"visual", "texto_pantalla"} - beat.keys()
    if faltan:
        raise ValueError(f"Al beat '{nombre}' le faltan campos: {faltan}")
    if not beat.get("texto_pantalla", "").strip():
        raise ValueError(f"El beat '{nombre}' no tiene texto en pantalla")
    if not beat.get("visual", "").strip():
        raise ValueError(f"El beat '{nombre}' no tiene descripción visual")
    if len(beat["texto_pantalla"].split()) > _TEXTO_PANTALLA_MAX_PALABRAS:
        raise ValueError(f"El texto en pantalla de '{nombre}' es demasiado largo para leerse en un beat")


def validate(data: dict) -> None:
    for campo in ("negocio", "ancla", "historia", "objetivo_comercial", "hook", "desarrollo", "cta", "caption", "hashtags"):
        if not data.get(campo):
            raise ValueError(f"Falta '{campo}'")

    if data["objetivo_comercial"] not in _OBJETIVOS_VALIDOS:
        raise ValueError(
            f"'objetivo_comercial' inválido: {data['objetivo_comercial']!r} (tiene que ser uno de {_OBJETIVOS_VALIDOS})"
        )

    _validar_beat(data["hook"], "hook")
    _validar_beat(data["cta"], "cta")

    desarrollo = data["desarrollo"]
    if not isinstance(desarrollo, list) or not (2 <= len(desarrollo) <= 4):
        raise ValueError(
            f"Se esperaban entre 2 y 4 beats de desarrollo, llegaron {len(desarrollo) if isinstance(desarrollo, list) else 0}"
        )
    for i, beat in enumerate(desarrollo, 1):
        _validar_beat(beat, f"desarrollo {i}")

    if len(data["historia"].split()) < 40:
        raise ValueError("La historia quedó demasiado corta para sostener el reel")

    texto = " ".join(
        [data.get("caption", ""), data.get("historia", ""),
         data["hook"]["texto_pantalla"], data["cta"]["texto_pantalla"]]
        + [b["texto_pantalla"] for b in desarrollo]
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

    if len(data["caption"].split()) < 15:
        raise ValueError("El caption quedó demasiado corto para contar el caso")
    if not isinstance(data["hashtags"], list) or not (3 <= len(data["hashtags"]) <= 5):
        raise ValueError(f"Tienen que ser entre 3 y 5 hashtags, llegaron {len(data.get('hashtags') or [])}")
    for h in data["hashtags"]:
        limpio = h.lstrip("#").strip()
        if len(limpio) < 2 or " " in limpio or not limpio.replace("ñ", "n").isalnum():
            raise ValueError(f"Hashtag inválido: {h!r}")
