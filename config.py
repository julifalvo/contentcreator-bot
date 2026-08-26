"""Configuración: los pilares de contenido y sus ángulos.

Cada pilar trae varios ÁNGULOS puntuales; generate.py sortea uno por pieza y
se lo pasa a la IA como semilla concreta. Entre los 4 pilares suman ~24.

El resto de la configuración visual (paletas, tipografías, layout) vive ahora
en design.py, que arma el HTML editorial de cada slide.
"""

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
}
