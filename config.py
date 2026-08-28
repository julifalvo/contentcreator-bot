"""Configuración: los pilares de contenido.

Los ÁNGULOS de cada pilar YA NO viven acá hardcodeados: generate.py sortea
uno del pool en angulos_pool.json (vía angulos.py), que se amplía corriendo
`python refrescar_angulos.py` — ahí la IA inventa ángulos nuevos evitando
repetir los que ya están, en vez de tener que editar este archivo a mano.

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
    },
    "eficiencia_comercial": {
        "label": "Eficiencia Comercial",
        "emoji": "📈",
    },
    "optimizacion_operativa": {
        "label": "Optimización Operativa",
        "emoji": "🛠️",
    },
    "transformacion": {
        "label": "Transformación Digital",
        "emoji": "🚀",
    },
    # A diferencia de los demás pilares (caso de un cliente, tercera persona),
    # este usa formato distinto: situación cotidiana en segunda persona con
    # remate cómico. Ver generate_humor() en groq_client.py.
    "humor": {
        "label": "Humor",
        "emoji": "😅",
        "formato": "humor",
    },
    # Contenido educativo "¿Sabías que...?": no cuenta el caso de un cliente
    # ni plantea una solución puntual (nada de chat/web/flujo), solo un dato o
    # concepto interesante. Cierra invitando a pedir más info, sin pitch. Ver
    # generate_sabias_que() en groq_client.py / content_rules.py.
    "sabias_que": {
        "label": "Sabías que...?",
        "emoji": "💡",
        "formato": "sabias_que",
    },
    # Mismo formato "caso" que los primeros 4 pilares (nada nuevo que programar):
    # ya exige mostrar la solución funcionando (chat/web/flujo), así que estos
    # ángulos solo empujan a que ESA parte sea explícitamente un demo/tutorial
    # paso a paso en vez de quedar como una mención de pasada. Funciona en
    # carrusel y en video narrado sin cambios, igual que automatizacion/etc.
    "demos_tutoriales": {
        "label": "Demos y Tutoriales",
        "emoji": "🎓",
    },
    # Puro fun content, sin caso de cliente ni pitch de la agencia: rankings/
    # listas graciosas tipo "Esenciales 2026" que mezclan herramientas de IA
    # con costumbres argentinas (mate, asado, dólar blue...). Cada ítem de la
    # lista lleva un ícono pixel art generado por IA. Ver chisme_rules.py.
    "chisme": {
        "label": "Chisme Tech Argento",
        "emoji": "🧉",
        "formato": "chisme",
    },
}
