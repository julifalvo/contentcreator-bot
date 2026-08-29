"""Reglas de marca compartidas por todos los proveedores de IA de texto
(groq_client.py, gemini_client.py): los system prompts y la validación de lo
que devuelven. Vive en un módulo aparte para que Groq y Gemini generen con
las mismas reglas exactas — duplicarlas en cada cliente las habría hecho
divergir la primera vez que se ajuste una regla en uno y no en el otro.
"""

import re

# La slide 'foto' (imagen real vía Pollinations.ai) es opcional: la calidad de
# un generador de imágenes gratis y sin curar es despareja (a veces sale una
# escena genérica que no cuenta nada, sin nadie en cuadro) y quien usa el bot
# tiene que poder elegir si la quiere o no en cada pieza — por eso el bloque
# de "foto" en el prompt se arma con get_system_prompt(con_foto)/
# get_humor_system_prompt(con_foto) en vez de estar siempre presente.
_FOTO_TIPO_CASO = '- foto     → {"tipo":"foto","titular":"máx 8 palabras, el pie de foto","prompt_imagen":"descripción visual en INGLÉS para un generador de imágenes: escena fotorrealista concreta anclada en la historia (ej: \'a woman in her 40s organizing handwritten appointment notes at a small business counter, natural light, realistic photo\'), sin texto ni letras en la imagen, sin marcas ni logos inventados"}\n'
_FOTO_ESTRUCTURA_CASO = ' "foto" es opcional, sumala solo si un momento puntual de la historia se beneficia de verse en una imagen real.'

_FOTO_TIPO_HUMOR = '- foto    → {"tipo":"foto","titular":"máx 8 palabras, el pie de foto, liviano/gracioso","prompt_imagen":"descripción visual en INGLÉS para un generador de imágenes: escena cotidiana fotorrealista y reconocible (ej: \'a tired small business owner checking phone late at night behind a counter, realistic photo\'), sin texto ni letras en la imagen"}\n'
_FOTO_LISTA_HUMOR = ', "foto"'

_SYSTEM_PROMPT_TEMPLATE = """Armás carruseles para TikTok para rootbusinessai, una agencia que construye agentes de IA y automatizaciones para negocios chicos de Argentina. Contás casos reales de clientes, no vendés un curso.

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
- codigo   → {"tipo":"codigo","titular":"máx 6 palabras","lenguaje":"una palabra para la pestaña del editor, ej: python","codigo":["3 a 6 líneas cortas de pseudocódigo ilustrativo (no hace falta que compile) que muestren por dentro cómo el agente procesa el mensaje/pedido de ESTA historia — una línea puede ser un comentario que arranca con #"]}
- comparacion → {"tipo":"comparacion","titular":"máx 6 palabras, ej: 'No es lo mismo'","chatbot":["3 strings cortos (máx 6 palabras), lo que un chatbot común NO hace o hace mal"],"agente":["3 strings cortos (máx 6 palabras), lo que sí hace un agente de IA real, relacionado con ESTA historia"]}
<<FOTO_TIPO>>- cierre   → {"tipo":"cierre","titular":"máx 6 palabras, retoma el ancla","accion":"qué hacer, concreto, máx 10 palabras"}

ESTRUCTURA: entre 6 y 8 slides. La primera SIEMPRE "portada", la última SIEMPRE "cierre". En el medio elegís vos, pero el carrusel tiene que mostrar el problema, cuánto cuesta, y la solución funcionando (con al menos un "chat", "web" o "flujo" que la haga concreta). "codigo" y "comparacion" son opcionales, sumalas solo si le aportan concreción a ESTA historia puntual (no las metas siempre de relleno).<<FOTO_ESTRUCTURA>> No repitas el mismo tipo dos veces seguidas.

HASHTAGS — máximo 5 (regla dura, ni uno más): priorizá los más usados y buscados dentro de negocios/tecnología/IA en español (ej: negocios, pymes, emprendedores, tecnologia, ia, innovacion, marketingdigital, automatizacion, startups, negociodigital) por encima de tags de nicho o inventados. Elegí los 5 que mejor describan ESTA pieza puntual, no repitas la misma lista siempre.

RESPONDÉ SOLO con este JSON, sin texto ni markdown alrededor:
{"negocio":"...","ancla":"...","historia":"...","slides":[...],"caption":"2-4 líneas en tercera persona (el caso de un cliente de la agencia, nunca 'mi negocio'), sin hashtags adentro, cierra con una pregunta concreta a quien mira","hashtags":["máximo 5, sin #, una palabra cada uno, los más usados en negocios/tecnología que apliquen a esta pieza"]}"""


def get_system_prompt(con_foto: bool = False) -> str:
    return (
        _SYSTEM_PROMPT_TEMPLATE
        .replace("<<FOTO_TIPO>>", _FOTO_TIPO_CASO if con_foto else "")
        .replace("<<FOTO_ESTRUCTURA>>", _FOTO_ESTRUCTURA_CASO if con_foto else "")
    )


_HUMOR_SYSTEM_PROMPT_TEMPLATE = """Armás carruseles de humor para TikTok para rootbusinessai, una agencia que construye agentes de IA y automatizaciones para negocios chicos de Argentina. El objetivo es que quien mira se sienta identificado y se ría, no que se lo eduque con un caso ajeno.

FORMATO: carrusel de imágenes con música, SIN voz en off. Todo lo que se entiende tiene que estar escrito en las slides.

CÓMO TRABAJÁS:
1. Elegís una situación cotidiana bien puntual y reconocible para cualquier dueño de negocio chico (el WhatsApp que se llena mientras atendés el mostrador, el cliente que escribe a las 3 de la mañana, el audio de 4 minutos que empieza pidiendo disculpas...).
2. Le hablás DIRECTO a quien mira, en segunda persona ("vos"), no contás el caso de un cliente ajeno.
3. Armás una secuencia de 3 a 6 momentos que escalan en humor — formato lista, ranking o mini-sketch — cada uno reconocible y un poco exagerado, pero verosímil (nada de situaciones absurdas o imposibles).
4. Cerrás con un remate que pasa de la situación graciosa a la solución (un agente que responde/agenda/cotiza), sin perder el tono liviano, y una acción concreta y breve.

REGLAS DURAS (no negociables, se comparten con el resto de la marca):
- Voseo rioplatense siempre (perdés, tenés, escribime, contame). Nunca tú/tienes/pierdes ni español neutro.
- PROHIBIDO inventar ofertas, precios, descuentos o estadísticas generales inventadas ("el 87% de los negocios...").
- PROHIBIDO lenguaje de marketing vacío (revolucioná, siguiente nivel, solución integral, en la era digital, potenciá).
- Es humor sobre una situación cotidiana real, nunca un chiste a costa del cliente ni humor negro.
- El remate SIEMPRE conecta con lo que resuelve la agencia, pero como guiño liviano, no como pitch de venta.

TIPOS DE SLIDE disponibles (elegí los que le sirvan a TU secuencia):
- portada → {"tipo":"portada","titular":"máx 9 palabras, el gancho de la situación, en segunda persona","epigrafe":"1 oración liviana que ubica la escena"}
- texto   → {"tipo":"texto","titular":"máx 6 palabras (ej: la hora, o un mini-título del momento)","cuerpo":"1-2 oraciones que describen ESE momento puntual"}
- dato    → {"tipo":"dato","numero":"solo el número, ej: 14","unidad":"máx 4 palabras, ej: mensajes sin leer","detalle":"1 oración liviana que explica de dónde sale"}
- chat    → {"tipo":"chat","titular":"máx 5 palabras","quien_entra":"ej: Cliente · 23:40","entrada":"lo que escribe, máx 16 palabras","quien_responde":"ej: Vos, mañana","respuesta":"máx 20 palabras","pie":"1 oración de remate"}
- cita    → {"tipo":"cita","texto":"una frase que vos mismo pensás en ese momento, máx 14 palabras","autor":"ej: Vos, a las 3 AM"}
<<FOTO_TIPO>>- cierre  → {"tipo":"cierre","titular":"máx 6 palabras, el remate que pivotea a la solución","accion":"qué hacer, concreto y liviano, máx 10 palabras"}

ESTRUCTURA: entre 5 y 8 slides. La primera SIEMPRE "portada" (el gancho de la secuencia). La última SIEMPRE "cierre" (el remate + acción). En el medio, los momentos de la secuencia (mayormente "texto", podés sumar un "dato", "chat"<<FOTO_LISTA>> o "cita" si suma sin romper el ritmo cómico). No repitas el mismo tipo dos veces seguidas. No uses "web" ni "flujo" acá, son para el contenido de casos, no para humor.

HASHTAGS — máximo 5 (regla dura, ni uno más): priorizá los más usados y buscados dentro de negocios/tecnología/IA en español (ej: negocios, pymes, emprendedores, tecnologia, ia, innovacion, marketingdigital, automatizacion, startups, negociodigital) por encima de tags de nicho o inventados. Elegí los 5 que mejor describan ESTA pieza puntual, no repitas la misma lista siempre.

RESPONDÉ SOLO con este JSON, sin texto ni markdown alrededor:
{"tema":"la situación cotidiana elegida, en pocas palabras","slides":[...],"caption":"2-4 líneas con el mismo tono liviano, en segunda persona, sin hashtags adentro, termina invitando a comentar o escribir","hashtags":["máximo 5, sin #, una palabra cada uno, los más usados en negocios/tecnología que apliquen a esta pieza"]}"""


def get_humor_system_prompt(con_foto: bool = False) -> str:
    return (
        _HUMOR_SYSTEM_PROMPT_TEMPLATE
        .replace("<<FOTO_TIPO>>", _FOTO_TIPO_HUMOR if con_foto else "")
        .replace("<<FOTO_LISTA>>", _FOTO_LISTA_HUMOR if con_foto else "")
    )


_FOTO_TIPO_SABIAS_QUE = '- foto    → {"tipo":"foto","titular":"máx 8 palabras, el pie de foto","prompt_imagen":"descripción visual en INGLÉS para un generador de imágenes: escena fotorrealista genérica que ilustra el dato (ej: \'a small business owner checking a smartphone at a shop counter, realistic photo\'), sin texto ni letras en la imagen"}\n'
_FOTO_LISTA_SABIAS_QUE = ', "foto"'

_SABIAS_QUE_SYSTEM_PROMPT_TEMPLATE = """Armás carruseles informativos tipo "¿Sabías que...?" para TikTok para rootbusinessai, una agencia que construye agentes de IA y automatizaciones para negocios chicos de Argentina. El objetivo es enseñar un dato o concepto interesante sobre automatización/IA/negocios — NO contar el caso de un cliente ni plantear una solución puntual.

FORMATO: carrusel de imágenes con música, SIN voz en off. Todo lo que se entiende tiene que estar escrito en las slides.

CÓMO TRABAJÁS:
1. Elegís UN dato, número o concepto concreto e interesante relacionado con el ángulo de esta pieza (ej: cuánto tiempo pierde en promedio un negocio respondiendo lo mismo una y otra vez, qué es en criollo un agente de IA, por qué la mayoría de las consultas por WhatsApp llegan fuera de horario).
2. Desarrollás ESE dato: de dónde sale, por qué importa, qué implica para un negocio chico. Es contenido educativo, no un caso — está BIEN que no haya un cliente puntual ni una historia de "antes y después" con una solución que se implementa.
3. Cerrás invitando a seguir la conversación, SIN ofrecer una solución específica ni un producto: "si querés más información, escribime", "contame si te pasa y lo hablamos" — nunca "agendá una demo", nunca un pitch de venta.

REGLAS DURAS (compartidas con el resto de la marca):
- Voseo rioplatense siempre (perdés, tenés, escribime, contame). Nunca tú/tienes/pierdes ni español neutro.
- PROHIBIDO inventar ofertas, precios, descuentos ("probá gratis", "50% off", "agendá una demo").
- PROHIBIDO lenguaje de marketing vacío (revolucioná, siguiente nivel, solución integral, en la era digital, potenciá).
- El dato tiene que sonar creíble y estar anclado en algo concreto (un cálculo simple, una observación típica del rubro) — nunca una estadística general inventada tipo "el 87% de los negocios...".
- Si usás un negocio como ejemplo ilustrativo, dejalo claro como ejemplo genérico (por rubro, "una peluquería" o similar) — no es EL caso de un cliente puntual con nombre e historia propia.

TIPOS DE SLIDE disponibles (elegí los que le sirvan a TU dato):
- portada → {"tipo":"portada","titular":"máx 9 palabras, arranca con '¿Sabías que...?' o una variante, el gancho del dato","epigrafe":"1 oración que lo ubica"}
- texto   → {"tipo":"texto","titular":"máx 6 palabras","cuerpo":"2 oraciones que desarrollan el dato"}
- dato    → {"tipo":"dato","numero":"solo el número, ej: 47","unidad":"máx 4 palabras","detalle":"1 oración que explica de dónde sale ese número"}
- cita    → {"tipo":"cita","texto":"una frase que resume la idea central, máx 14 palabras","autor":"ej: Algo para pensar"}
- codigo  → {"tipo":"codigo","titular":"máx 6 palabras","lenguaje":"una palabra para la pestaña del editor, ej: python","codigo":["3 a 6 líneas cortas de pseudocódigo ilustrativo (no hace falta que compile) que muestren en general cómo funciona por dentro un agente de IA — una línea puede ser un comentario que arranca con #"]}
- comparacion → {"tipo":"comparacion","titular":"máx 6 palabras, ej: 'No es lo mismo'","chatbot":["3 strings cortos (máx 6 palabras), lo que un chatbot común NO hace o hace mal"],"agente":["3 strings cortos (máx 6 palabras), lo que sí hace un agente de IA real"]}
<<FOTO_TIPO>>- cierre  → {"tipo":"cierre","titular":"máx 6 palabras","accion":"invitación a pedir más información, SIN ofrecer un producto puntual, ej: 'Escribime si querés más info'"}

ESTRUCTURA: entre 5 y 7 slides. La primera SIEMPRE "portada" (el gancho "¿Sabías que...?"). La última SIEMPRE "cierre" (invita a pedir más información, nunca una oferta ni una demo). En el medio desarrollás el dato (mayormente "texto" y/o "dato", podés sumar "cita", "codigo" o "comparacion"<<FOTO_LISTA>> si suman). No repitas el mismo tipo dos veces seguidas. No uses "chat", "web" ni "flujo" acá: son para mostrar una solución puntual funcionando, y este formato no plantea una solución puntual.

HASHTAGS — máximo 5 (regla dura, ni uno más): priorizá los más usados y buscados dentro de negocios/tecnología/IA en español (ej: negocios, pymes, emprendedores, tecnologia, ia, innovacion, marketingdigital, automatizacion, startups, negociodigital).

RESPONDÉ SOLO con este JSON, sin texto ni markdown alrededor:
{"tema":"el dato o concepto elegido, en pocas palabras","slides":[...],"caption":"2-4 líneas que resumen el dato, sin hashtags adentro, termina invitando a escribir para más información","hashtags":["máximo 5, sin #, una palabra cada uno, los más usados en negocios/tecnología que apliquen a esta pieza"]}"""


def get_sabias_que_system_prompt(con_foto: bool = False) -> str:
    return (
        _SABIAS_QUE_SYSTEM_PROMPT_TEMPLATE
        .replace("<<FOTO_TIPO>>", _FOTO_TIPO_SABIAS_QUE if con_foto else "")
        .replace("<<FOTO_LISTA>>", _FOTO_LISTA_SABIAS_QUE if con_foto else "")
    )


# Guía de estilo por formato para generar ÁNGULOS nuevos (angulos.py /
# refrescar_angulos.py): reemplaza las listas que antes vivían hardcodeadas
# en config.py — acá se define qué hace bueno a un ángulo de CADA formato,
# para que la IA que los inventa mantenga el mismo nivel de puntualidad que
# los ángulos escritos a mano originalmente.
_ANGULOS_ESTILO = {
    None: (  # formato "caso" (default: automatizacion, eficiencia_comercial, etc.)
        "Estos ángulos son para piezas de CASO: una agencia cuenta en tercera persona la historia de un "
        "cliente. Cada ángulo es UNA frase corta, casi siempre arrancando con 'Cómo...', que describe una "
        "mecánica bien puntual — un detalle ancla concreto, nunca un tema genérico: no 'cómo mejorar la "
        "atención al cliente', sino 'cómo automatizar el recordatorio de turnos para bajar los faltazos'. "
        "Tiene que sonar a algo específico que un agente de IA resuelve de verdad, no una promesa vaga."
    ),
    "humor": (
        "Estos ángulos son para piezas de HUMOR: una situación cotidiana reconocible, en segunda persona, "
        "sin caso de cliente. Cada ángulo describe una escena puntual y un poco exagerada (pero verosímil) "
        "de la vida de un dueño de negocio chico: no 'el estrés de atender clientes', sino 'los estados de "
        "tu WhatsApp de negocio en un día cualquiera'. Tiene que sonar reconocible al toque, no un chiste genérico."
    ),
    "sabias_que": (
        "Estos ángulos son para piezas educativas '¿Sabías que...?': un dato o concepto, sin caso de cliente "
        "ni solución puntual. Cada ángulo es un dato o concepto concreto e interesante sobre automatización, "
        "IA o negocios chicos: no 'la importancia de la IA', sino 'por qué la mayoría de las consultas por "
        "WhatsApp llegan fuera del horario de atención'."
    ),
    "chisme": (
        "Estos ángulos son para piezas de puro fun content, tipo ranking/lista graciosa: sin caso de cliente "
        "ni pitch de la agencia. Cada ángulo es UN CONCEPTO de lista que mezcla el mundo IA/tech con "
        "costumbres argentinas — no 'la tecnología en Argentina', sino 'Esenciales 2026 para sobrevivir al "
        "mundo IA (con mate incluido)' o 'Cosas que todo founder argento tiene abiertas en 47 pestañas'. "
        "Tiene que sonar a un título de lista con gancho propio, no un tema genérico."
    ),
    "impacto": (
        "Estos ángulos son para piezas de confesión en primera persona ('el error que cometí en mi negocio "
        "fue no dedicar 30 minutos a esto'), seguidas de una lista de acciones concretas con IA (automatizar/"
        "generar impacto/atraer clientes). Cada ángulo es UN ERROR puntual y accionable de 30 minutos no "
        "invertidos: no 'no usar tecnología', sino 'no armar un agente que responda el WhatsApp fuera de "
        "horario' o 'no automatizar el seguimiento del cliente que preguntó precio y no volvió'. Tiene que "
        "sonar a algo que de verdad le pasó a un dueño de negocio, no una moraleja genérica."
    ),
}


# Instrucción extra que se suma al prompt de ángulos solo cuando
# refrescar_angulos.py consiguió las métricas reales de la cuenta (ver
# rendimiento.py). Sin datos no se manda: a un modelo al que le pedís "guiate
# por lo que funcionó" sin decirle qué funcionó, se inventa el criterio.
_ANGULOS_RENDIMIENTO = """
CÓMO USAR LOS DATOS DE RENDIMIENTO: en el mensaje te paso las vistas reales que hicieron piezas ya publicadas de esta cuenta, junto al ángulo que generó cada una. Fijate qué tienen en común los de arriba —qué tipo de mecánica, qué grado de detalle, qué promesa— y escribí ángulos nuevos que compartan ESO. No los copies ni los reformules: esos ya se usaron. De los de abajo tomá qué evitar. Si un ángulo tuyo se parece más a los de abajo que a los de arriba, cambialo.
"""


def get_angulos_system_prompt(formato: str | None, con_rendimiento: bool = False) -> str:
    estilo = _ANGULOS_ESTILO.get(formato, _ANGULOS_ESTILO[None])
    rendimiento = _ANGULOS_RENDIMIENTO if con_rendimiento else ""
    return f"""Generás ÁNGULOS nuevos para rootbusinessai, una agencia que construye agentes de IA y automatizaciones para negocios chicos de Argentina. Un ángulo es la semilla puntual de UNA pieza de contenido para TikTok — no el texto final, solo la idea concreta que después otra IA desarrolla en un carrusel o video completo.

{estilo}
{rendimiento}
REGLAS:
- Cada ángulo es UNA sola oración, sin numerarla, sin guion ni comillas alrededor.
- Específico y accionable: si dos ángulos de tu respuesta podrían intercambiarse sin que se note, están mal.
- Castellano rioplatense (son descripciones que no le hablan directo a nadie, no hace falta voseo explícito).
- PROHIBIDO repetir o parafrasear cualquiera de los ángulos "ya existentes" que te paso en el mensaje: tienen que ser ideas realmente nuevas, no variaciones de las mismas.
- Nada de lenguaje de marketing vacío (revolucioná, solución integral, en la era digital).

RESPONDÉ SOLO con este JSON, sin texto ni markdown alrededor:
{{"angulos": ["...", "..."]}}"""


def validate_angulos(data: dict, n_pedidos: int) -> None:
    """Valida la respuesta de generate_angulos: limpia duplicados exactos
    (case-insensitive) in-place en data['angulos'] y exige que haya quedado
    al menos la mitad de lo pedido — no vale la pena rechazar y reintentar
    solo porque el modelo repitió un par."""
    angulos_lista = data.get("angulos")
    if not isinstance(angulos_lista, list) or not angulos_lista:
        raise ValueError("Falta 'angulos' o vino vacío")

    limpios = []
    vistos = set()
    for a in angulos_lista:
        if not isinstance(a, str):
            raise ValueError(f"Ángulo inválido (no es texto): {a!r}")
        a = a.strip()
        if len(a.split()) < 4:
            raise ValueError(f"Ángulo demasiado corto: {a!r}")
        clave = a.lower()
        if clave in vistos:
            continue
        vistos.add(clave)
        limpios.append(a)

    minimo = max(1, n_pedidos // 2)
    if len(limpios) < minimo:
        raise ValueError(f"Vinieron muy pocos ángulos únicos ({len(limpios)} de {n_pedidos} pedidos)")
    data["angulos"] = limpios


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

# Alias públicos: video_rules.py (guion narrado) valida el mismo tono/voseo
# que los carruseles, pero no tiene slides ni caption en el mismo formato, así
# que arma su propio validate() reusando estas listas en vez de duplicarlas.
TONO_VENDEDOR = _TONO_VENDEDOR
NARRADOR_DUEÑO = _NARRADOR_DUEÑO
NO_VOSEO = _NO_VOSEO


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


_CAMPOS_EN_INGLES = {"prompt_imagen", "b_roll", "icono_prompt", "fondo_prompt"}


def normalizar(valor):
    """Limpia el texto antes de renderizar: separador de miles al uso argentino
    ('$1 200' -> '$1.200', que con el espacio parece una errata en un titular
    gigante) y los imperativos en tú pasados a voseo. No toca los campos en
    inglés (prompt_imagen, b_roll): no tienen por qué respetar voseo/miles."""
    if isinstance(valor, str):
        valor = valor.replace(" ", " ").replace("\xa0", " ")
        valor = re.sub(r"(\d) (\d{3})\b", r"\1.\2", valor)
        for patron, reemplazo in _IMPERATIVOS:
            valor = re.sub(patron, reemplazo, valor)
        return valor
    if isinstance(valor, list):
        return [normalizar(v) for v in valor]
    if isinstance(valor, dict):
        return {k: (v if k in _CAMPOS_EN_INGLES else normalizar(v)) for k, v in valor.items()}
    return valor


def _texto_completo(data: dict) -> str:
    partes = [data.get("caption", ""), data.get("historia", "")]
    for s in data.get("slides", []):
        partes += [str(v) for k, v in s.items() if k not in ("tipo", "prompt_imagen") and isinstance(v, str)]
        partes += [str(x) for x in s.get("pasos", []) or []]
        partes += [str(x) for x in s.get("chips", []) or []]
    return " ".join(partes).lower()


def validate(data: dict, con_foto: bool = False) -> None:
    """Valida un carrusel del formato 'caso' (el default: historia de un
    cliente en tercera persona). con_foto tiene que coincidir con lo que se
    le pidió al prompt: si no se ofreció 'foto' como opción, tampoco puede
    aparecer en la respuesta (defensa extra por si el modelo la inventa)."""
    from design import BUILDERS, SLIDE_TYPES

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
    if not con_foto and "foto" in tipos:
        raise ValueError("Se generó una slide 'foto' pero con_foto=False para esta pieza")
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
    if not isinstance(data["hashtags"], list) or not (3 <= len(data["hashtags"]) <= 5):
        raise ValueError(f"Tienen que ser entre 3 y 5 hashtags, llegaron {len(data.get('hashtags') or [])}")
    for h in data["hashtags"]:
        limpio = h.lstrip("#").strip()
        # 'ia' y 'pyme' son hashtags legítimos y cortos; lo que hay que
        # descartar son los cortados a la mitad o con espacios adentro.
        if len(limpio) < 2 or " " in limpio or not limpio.replace("ñ", "n").isalnum():
            raise ValueError(f"Hashtag inválido: {h!r}")


def validate_humor(data: dict, con_foto: bool = False) -> None:
    """Igual que validate() pero para el formato humor: sin caso/historia/ancla,
    slides en segunda persona, y sin exigir una slide de tipo web/flujo."""
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
    permitidos = {"portada", "texto", "dato", "chat", "cita", "cierre"}
    if con_foto:
        permitidos = permitidos | {"foto"}
    for tipo in tipos:
        if tipo not in permitidos:
            raise ValueError(f"Tipo de slide inválido para humor: {tipo!r}")
    for a, b in zip(tipos, tipos[1:]):
        if a == b:
            raise ValueError(f"Dos slides seguidas del mismo tipo: {a}")

    for s in slides:
        faltan = BUILDERS[s["tipo"]][1] - s.keys()
        if faltan:
            raise ValueError(f"A la slide '{s['tipo']}' le faltan campos: {faltan}")

    texto = _texto_completo(data)
    vendedor = [f for f in _TONO_VENDEDOR if f in texto]
    if vendedor:
        raise ValueError(f"Tono de vendedor / oferta inventada: {vendedor}")
    neutro = [f for f in _NO_VOSEO if re.search(rf"\b{re.escape(f)}\b", texto)]
    if neutro:
        raise ValueError(f"No está en voseo rioplatense: {neutro}")
    if len(data["caption"].split()) < 12:
        raise ValueError("El caption quedó demasiado corto")
    if not isinstance(data["hashtags"], list) or not (3 <= len(data["hashtags"]) <= 5):
        raise ValueError(f"Tienen que ser entre 3 y 5 hashtags, llegaron {len(data.get('hashtags') or [])}")
    for h in data["hashtags"]:
        limpio = h.lstrip("#").strip()
        if len(limpio) < 2 or " " in limpio or not limpio.replace("ñ", "n").isalnum():
            raise ValueError(f"Hashtag inválido: {h!r}")


def validate_sabias_que(data: dict, con_foto: bool = False) -> None:
    """Formato educativo '¿Sabías que...?': sin negocio/ancla/historia (no es
    un caso), y sin chat/web/flujo (no plantea una solución puntual) — solo
    portada/texto/dato/cita/(foto)/cierre."""
    from design import BUILDERS

    for campo in ("tema", "slides", "caption", "hashtags"):
        if not data.get(campo):
            raise ValueError(f"Falta '{campo}'")

    slides = data["slides"]
    if not isinstance(slides, list) or not (5 <= len(slides) <= 7):
        raise ValueError(f"Se esperaban entre 5 y 7 slides, llegaron {len(slides)}")
    if slides[0].get("tipo") != "portada":
        raise ValueError("La primera slide tiene que ser 'portada'")
    if slides[-1].get("tipo") != "cierre":
        raise ValueError("La última slide tiene que ser 'cierre'")

    tipos = [s.get("tipo") for s in slides]
    permitidos = {"portada", "texto", "dato", "cita", "codigo", "comparacion", "cierre"}
    if con_foto:
        permitidos = permitidos | {"foto"}
    for tipo in tipos:
        if tipo not in permitidos:
            raise ValueError(f"Tipo de slide inválido para 'sabías que': {tipo!r} (no plantea una solución puntual, nada de chat/web/flujo)")
    for a, b in zip(tipos, tipos[1:]):
        if a == b:
            raise ValueError(f"Dos slides seguidas del mismo tipo: {a}")

    for s in slides:
        faltan = BUILDERS[s["tipo"]][1] - s.keys()
        if faltan:
            raise ValueError(f"A la slide '{s['tipo']}' le faltan campos: {faltan}")

    texto = _texto_completo(data)
    vendedor = [f for f in _TONO_VENDEDOR if f in texto]
    if vendedor:
        raise ValueError(f"Tono de vendedor / oferta inventada: {vendedor}")
    neutro = [f for f in _NO_VOSEO if re.search(rf"\b{re.escape(f)}\b", texto)]
    if neutro:
        raise ValueError(f"No está en voseo rioplatense: {neutro}")
    if len(data["caption"].split()) < 12:
        raise ValueError("El caption quedó demasiado corto")
    if not isinstance(data["hashtags"], list) or not (3 <= len(data["hashtags"]) <= 5):
        raise ValueError(f"Tienen que ser entre 3 y 5 hashtags, llegaron {len(data.get('hashtags') or [])}")
    for h in data["hashtags"]:
        limpio = h.lstrip("#").strip()
        if len(limpio) < 2 or " " in limpio or not limpio.replace("ñ", "n").isalnum():
            raise ValueError(f"Hashtag inválido: {h!r}")
