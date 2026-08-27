"""Configuración: los pilares de contenido y sus ángulos.

Cada pilar trae varios ÁNGULOS puntuales; generate.py sortea uno por pieza y
se lo pasa a la IA como semilla concreta. Entre los 4 pilares suman ~24.

El resto de la configuración visual (paletas, tipografías, layout) vive ahora
en design.py, que arma el HTML editorial de cada slide.
"""

# Rubros que se sortean como semilla. Sin esto el modelo cae siempre en los
# mismos dos o tres ("taller de reparación" salía en 3 de cada 4 piezas): son
# los ejemplos más frecuentes en sus datos de entrenamiento. La IA sigue
# inventando el caso, el número y la historia; esto solo empuja el escenario.
RUBROS = [
    "una panadería de barrio", "una veterinaria", "un estudio contable",
    "una peluquería", "un gimnasio de barrio", "una óptica",
    "un vivero", "una ferretería", "un consultorio odontológico",
    "una escuela de música", "un local de indumentaria", "una cafetería de especialidad",
    "una inmobiliaria chica", "un centro de estética", "una juguetería",
    "un taller mecánico", "una guardería de mascotas", "un estudio de tatuajes",
    "una casa de repuestos", "un instituto de idiomas", "una florería",
    "un lavadero de autos", "una pinturería", "un estudio de fotografía",
    "una rotisería", "un kinesiólogo", "una mueblería",
    "un club de padel", "una librería", "un corralón de materiales",
]

PILLARS = {
    "automatizacion": {
        "label": "Automatización",
        "emoji": "⚙️",
        "angle": [
            "Cómo un agente de WhatsApp carga pedidos automáticamente sin que nadie tipee nada",
            "Cómo automatizar el recordatorio de turnos para bajar los faltazos",
            "Cómo un bot avisa cuando se está por agotar el stock de un producto",
            "Cómo automatizar el armado de un pedido a partir de un audio de voz",
            "Cómo eliminar las respuestas repetidas a la misma pregunta de siempre",
            "Cómo automatizar el alta de un cliente nuevo sin cargar datos a mano",
        ],
    },
    "eficiencia_comercial": {
        "label": "Eficiencia Comercial",
        "emoji": "📈",
        "angle": [
            "Cómo un agente responde leads al instante para no perder ventas por tardar",
            "Cómo cotizar automáticamente sin que el cliente espere horas",
            "Cómo reservar turnos por WhatsApp sin que se pisen los horarios",
            "Cómo un agente distingue una urgencia real de una consulta común",
            "Cómo recuperar a un cliente que preguntó precio y no volvió a escribir",
            "Cómo cerrar una venta por chat sin que un vendedor esté siempre online",
        ],
    },
    "optimizacion_operativa": {
        "label": "Optimización Operativa",
        "emoji": "🛠️",
        "angle": [
            "Cómo automatizar el cobro de cuotas mensuales sin perseguir a nadie",
            "Cómo cubrir automáticamente un turno cancelado con la lista de espera",
            "Cómo controlar el stock de un negocio sin revisar todo a ojo",
            "Cómo ordenar la agenda de un negocio que antes vivía en un cuaderno",
            "Cómo evitar que un insumo se termine sin que nadie lo note",
            "Cómo automatizar el armado de fichas o legajos de clientes nuevos",
        ],
    },
    "transformacion": {
        "label": "Transformación Digital",
        "emoji": "🚀",
        "angle": [
            "Cómo un negocio de toda la vida empieza a vender también por WhatsApp",
            "Cómo pasar de un cuaderno de turnos a un agente que agenda solo",
            "Cómo un local que dependía solo del mostrador suma un canal digital",
            "Cómo modernizar la atención al cliente sin cambiar todo el negocio",
            "Cómo un negocio chico compite con cadenas más grandes usando IA",
            "Cómo digitalizar un proceso interno sin gastar en sistemas caros",
        ],
    },
    # A diferencia de los demás pilares (caso de un cliente, tercera persona),
    # este usa formato distinto: situación cotidiana en segunda persona con
    # remate cómico. Ver generate_humor() en groq_client.py.
    "humor": {
        "label": "Humor",
        "emoji": "😅",
        "formato": "humor",
        "angle": [
            "Los estados de tu WhatsApp de negocio en un día cualquiera",
            "El ranking de mensajes que te llegan a las 3 de la mañana",
            "Lo que pensás mientras contestás la misma pregunta por décima vez en la semana",
            "La cara que pone un cliente cuando le contestás 6 horas después",
            "Un día típico atendiendo el mostrador y el WhatsApp al mismo tiempo",
            "Las excusas que te decís todos los meses para no automatizar todavía",
        ],
    },
    # Contenido educativo "¿Sabías que...?": no cuenta el caso de un cliente
    # ni plantea una solución puntual (nada de chat/web/flujo), solo un dato o
    # concepto interesante. Cierra invitando a pedir más info, sin pitch. Ver
    # generate_sabias_que() en groq_client.py / content_rules.py.
    "sabias_que": {
        "label": "Sabías que...?",
        "emoji": "💡",
        "formato": "sabias_que",
        "angle": [
            "Cuánto tiempo pierde en promedio un negocio chico respondiendo siempre lo mismo por WhatsApp",
            "Qué es en criollo un agente de IA (sin la jerga técnica)",
            "Por qué la mayoría de las consultas por WhatsApp llegan fuera del horario de atención",
            "Qué diferencia a un chatbot de un agente de IA de verdad",
            "Cuánto cuesta hoy automatizar algo chico en un negocio, en plata real",
            "Por qué responder rápido importa más que responder perfecto",
        ],
    },
    # Mismo formato "caso" que los primeros 4 pilares (nada nuevo que programar):
    # ya exige mostrar la solución funcionando (chat/web/flujo), así que estos
    # ángulos solo empujan a que ESA parte sea explícitamente un demo/tutorial
    # paso a paso en vez de quedar como una mención de pasada. Funciona en
    # carrusel y en video narrado sin cambios, igual que automatizacion/etc.
    "demos_tutoriales": {
        "label": "Demos y Tutoriales",
        "emoji": "🎓",
        "angle": [
            "Tutorial paso a paso: así se conecta un agente de IA a WhatsApp Business",
            "Demo en vivo: así agenda un turno un agente, de punta a punta",
            "Así responde un agente en la página web de un negocio, paso a paso",
            "Tutorial: cómo se arma un flujo que carga un pedido solo",
            "Demo: así consulta un agente el stock real antes de confirmar una venta",
            "Paso a paso: cómo se automatiza el seguimiento de un cliente que preguntó y no volvió",
        ],
    },
}
