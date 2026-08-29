"""Perfil de la audiencia: qué le duele, qué quiere, qué le da miedo, qué se
pregunta y con qué se defiende un dueño de negocio chico argentino cuando le
aparece la idea de meter un agente de IA, una web o un chatbot.

Por qué existe este archivo: hasta ahora el prompt le decía a la IA PARA QUIÉN
escribía (una agencia que le habla a negocios chicos) pero nunca CONTRA QUÉ
escribía. Sin eso, el modelo elige el problema más obvio del ángulo y siempre
cae en el mismo ("perdés mensajes"), sin rozar nunca el miedo real que frena la
decisión ni la objeción con la que la persona se defiende.

Cómo se usa: generate.py sortea UNA tensión por pieza (un problema, un deseo,
un miedo, una pregunta y una objeción) y se la pasa a la IA como contexto junto
con la intención de la pieza (educativo/emocional/conexión/venta, ver
config.INTENCIONES). Se sortea una sola de cada categoría y no la lista entera
a propósito: pasarle las cinco listas completas al modelo lo lleva a escribir un
resumen del perfil en vez de una pieza puntual, y además no entra en el
presupuesto de tokens de Groq (ver _TOPE_TOKENS_REQUEST en groq_client.py).

Acá NO se escribe texto final: son insumos para el prompt. Los titulares, los
ganchos y los captions los sigue escribiendo la IA en el momento.
"""

import random

from config import INTENCIONES, elegir_intencion, intenciones_de

# Lo que hoy le pasa y puede describir sin usar una sola palabra técnica. Son
# escenas observables, no categorías: "los mensajes que entran de noche" sirve
# de semilla, "la mala atención al cliente" no.
PROBLEMAS = [
    "el WhatsApp del negocio se le llena de consultas mientras atiende el mostrador, y contesta todo tarde",
    "las consultas que entran de noche o el domingo se responden al otro día, cuando la persona ya compró en otro lado",
    "contesta veinte veces por día la misma pregunta: precio, horario y si hay stock",
    "los presupuestos se arman a mano y tardan dos días en salir",
    "los turnos se anotan en un cuaderno y se pisan entre sí",
    "el que preguntó precio y no volvió: nadie le escribió nunca más",
    "la web se hizo hace cuatro años y no trae un solo mensaje",
    "carga a mano en la planilla datos que ya estaban escritos en los mensajes",
    "no sabe cuántas consultas le llegaron el mes pasado ni cuántas terminaron en venta",
    "si el dueño no está, no avanza nada: todo pasa por su teléfono",
    "los faltazos a turnos que nadie confirmó el día anterior",
    "los mensajes de Instagram sin leer desde hace una semana",
    "el proveedor manda la lista de precios en PDF y hay que pasarla a mano cada vez",
    "atiende consultas mientras cocina, corta el pelo o factura, y termina haciendo mal las dos cosas",
]

# Lo que quiere que pase. Se usa para que el cierre y el remate apunten a algo
# deseable y concreto, no a "mejorar la gestión".
DESEOS = [
    "que el negocio siga atendiendo cuando el local está cerrado",
    "sacarse de encima la parte repetitiva y volver a hacer lo que sabe hacer",
    "contestar en el momento sin tener el teléfono en la mano todo el día",
    "que los turnos y pedidos entren solos a la agenda, sin cargarlos de nuevo",
    "saber cuántas consultas llegan y cuántas se pierden, con un número y no con una sensación",
    "parecer tan prolijo como una empresa grande, siendo dos personas",
    "irse una semana de vacaciones sin que el negocio se frene",
    "que el cliente que preguntó una vez vuelva sin tener que perseguirlo",
    "crecer sin sumar un sueldo más",
    "dejar de arrancar el día con 40 mensajes atrasados",
    "cerrar la venta mientras el cliente todavía tiene ganas de comprar",
]

# Lo que lo frena aunque le interese. La pieza no los nombra: los desactiva
# mostrando lo contrario (un agente que deriva a un humano, algo andando en una
# semana, un caso de un negocio de su tamaño).
MIEDOS = [
    "que un robot conteste cualquier cosa y lo deje mal parado con un cliente",
    "que el cliente se dé cuenta de que le contesta una máquina y se ofenda",
    "gastar en algo que después nadie use, como pasó con la web",
    "quedar atado a quien se lo programó y no poder tocar nada sin llamarlo",
    "no entender cómo funciona y depender de un técnico para cambiar un precio",
    "que la competencia ya lo esté haciendo y enterarse tarde",
    "que sea un sistema más para aprender y mantener, arriba de todo lo que ya hace",
    "que se caiga justo el sábado, que es el día que más vende",
    "perder el trato personal, que es exactamente por lo que sus clientes lo eligen",
    "que le vendan humo y no tenga con qué darse cuenta a tiempo",
]

# Lo que se pregunta antes de decidir. Sirven como semilla del pilar educativo
# ('sabias_que', 'demos_tutoriales'): cada una es una pieza entera.
PREGUNTAS = [
    "¿esto sirve para un negocio del tamaño del mío o es para empresas grandes?",
    "¿cuánto tarda en estar funcionando de verdad?",
    "¿lo puedo probar con una sola cosa antes de meter todo?",
    "¿qué pasa cuando el agente no sabe la respuesta?",
    "¿lo tengo que entrenar yo o ya entiende de mi rubro?",
    "¿se conecta con lo que ya uso: el WhatsApp, la agenda, la planilla?",
    "¿en qué se diferencia esto de un chatbot de los de antes?",
    "¿quién lo mantiene cuando cambian los precios o los horarios?",
    "¿me queda a mí si mañana dejo de trabajar con la agencia?",
    "¿cómo sé si está funcionando o si solo me está gastando tiempo?",
    "¿de qué depende lo que sale por mes?",
]

# Con qué se defiende cuando ya entendió y todavía no se decide. Una pieza que
# desarma una objeción concreta rinde más que una que explica otra vez qué es
# un agente.
OBJECIONES = [
    "ya tengo un chatbot y contesta cualquier cosa",
    "yo contesto rápido, no necesito nada de esto",
    "mis clientes son grandes y quieren hablar con una persona",
    "para el tamaño de mi negocio esto tiene que salir carísimo",
    "no tengo tiempo de ponerme a implementar nada ahora",
    "mi rubro es distinto, lo mío no se puede automatizar",
    "prefiero esperar a ver cómo le va a otro que lo haya puesto",
    "ya probé una herramienta de IA y no me sirvió para nada",
    "lo tengo que hablar con mi socio",
    "en dos meses esto va a estar obsoleto y hay que hacerlo todo de nuevo",
    "yo con el boca en boca vengo bien, nunca necesité nada digital",
]

CATEGORIAS = {
    "problema": PROBLEMAS,
    "deseo": DESEOS,
    "miedo": MIEDOS,
    "pregunta": PREGUNTAS,
    "objecion": OBJECIONES,
}


def elegir_tension() -> dict:
    """Sortea una combinación puntual del perfil: un problema, un deseo, un
    miedo, una pregunta y una objeción. Es lo que hace que dos piezas del mismo
    ángulo no salgan iguales — el ángulo dice DE QUÉ se habla, la tensión dice
    contra qué se está escribiendo."""
    return {clave: random.choice(opciones) for clave, opciones in CATEGORIAS.items()}


def bloque_audiencia(tension: dict) -> str:
    """El bloque de texto que se le suma al mensaje del usuario. Se le pide al
    modelo que lo use como brújula, no que lo cite: si se lo deja suelto,
    escribe una slide por cada línea y la pieza queda como un folleto de FAQ."""
    return f"""A QUIÉN LE ESTÁS HABLANDO (perfil real de la audiencia; usalo como brújula, NO lo cites ni lo conviertas en una lista de slides):
- Lo que hoy le pasa: {tension['problema']}
- Lo que quiere que pase: {tension['deseo']}
- Lo que lo frena: {tension['miedo']}
- Lo que se pregunta antes de decidir: {tension['pregunta']}
- Con lo que se defiende: "{tension['objecion']}"

Esta pieza tiene que rozar ESE problema y ESE deseo, y dejar desactivado de taquito el miedo o la objeción — mostrándolo resuelto en la historia, nunca nombrándolos ni respondiéndolos de frente."""


def bloque_intencion(intencion_key: str) -> str:
    intencion = INTENCIONES[intencion_key]
    return f"INTENCIÓN DE ESTA PIEZA — {intencion['label'].upper()}: {intencion['guia']}"


def contexto_de_pieza(pillar_key: str) -> dict:
    """Todo el contexto estratégico de UNA pieza: qué intención tiene y contra
    qué tensión de la audiencia se escribe. Devuelve también 'bloque', el texto
    ya armado para pegarle al mensaje del usuario en groq/gemini_client.

    generate.py guarda 'intencion' y 'tension' en contenido.json, así que
    rendimiento.py puede después cruzarlos con las vistas reales igual que ya
    hace con el pilar y el ángulo.
    """
    intencion = elegir_intencion(pillar_key)
    tension = elegir_tension()
    return {
        "intencion": intencion,
        "tension": tension,
        "bloque": f"{bloque_intencion(intencion)}\n\n{bloque_audiencia(tension)}",
    }


def bloque_para_angulos(pillar_key: str, n: int = 3) -> str:
    """Versión resumida para refrescar_angulos.py: en vez de una tensión sola,
    una muestra de cada categoría, porque ahí se piden 15 ángulos de una y con
    una sola tensión saldrían las 15 variaciones del mismo problema.

    Suma además las intenciones que soporta el pilar, para que el lote no salga
    todo servible para lo mismo: un pool donde los 40 ángulos solo dan piezas
    de venta hace que el sorteo de intención de contexto_de_pieza() no tenga
    con qué trabajar."""
    def muestra(opciones: list[str]) -> str:
        return "; ".join(random.sample(opciones, min(n, len(opciones))))

    posibles = intenciones_de(pillar_key)
    if len(posibles) > 1:
        detalle = ", ".join(f"{INTENCIONES[i]['label'].upper()} ({INTENCIONES[i]['resumen']})" for i in posibles)
        mezcla = (f"\n\nREPARTÍ EL LOTE: las piezas de este pilar se cuentan con distinta intención — {detalle}. "
                  "Que haya ángulos que sirvan para cada una, no quince que solo den la misma pieza.")
    else:
        mezcla = ""

    return f"""LA AUDIENCIA (dueños de negocios chicos en Argentina) — una muestra de lo que le pasa por la cabeza:
- Problemas: {muestra(PROBLEMAS)}
- Deseos: {muestra(DESEOS)}
- Miedos: {muestra(MIEDOS)}
- Preguntas: {muestra(PREGUNTAS)}
- Objeciones: {muestra(OBJECIONES)}

Cada ángulo nuevo tiene que nacer de UNO de esos puntos (no de todos): que se note contra qué problema, miedo u objeción puntual está escrito.{mezcla}"""
