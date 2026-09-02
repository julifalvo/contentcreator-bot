"""Configuración: los pilares de contenido.

Los ÁNGULOS de cada pilar YA NO viven acá hardcodeados: generate.py sortea
uno del pool en angulos_pool.json (vía angulos.py), que se amplía corriendo
`python refrescar_angulos.py` — ahí la IA inventa ángulos nuevos evitando
repetir los que ya están, en vez de tener que editar este archivo a mano.

Además de los pilares (DE QUÉ habla una pieza) están las INTENCIONES (PARA QUÉ
está hecha: educativo, emocional, de conexión o de venta). Cada pilar declara
cuáles le entran, generate.py sortea una por pieza y audiencia.py la traduce a
una instrucción para el prompt. Sin esto todas las piezas terminaban siendo lo
mismo — un caso con su solución — y una cuenta que solo hace eso no engancha ni
convierte.

El resto de la configuración visual (paletas, tipografías, layout) vive ahora
en design.py, que arma el HTML editorial de cada slide.
"""

import random

# Rubros que se sortean como semilla. Sin esto el modelo cae siempre en los
# mismos dos o tres ("taller de reparación" salía en 3 de cada 4 piezas): son
# los ejemplos más frecuentes en sus datos de entrenamiento. La IA sigue
# inventando el caso, el número y la historia; esto solo empuja el escenario.
RUBROS = [
    # Comercio de barrio
    "una panadería de barrio", "una ferretería", "una juguetería",
    "un local de indumentaria", "una librería", "una florería",
    "una pinturería", "una mueblería", "una casa de repuestos",
    "un corralón de materiales", "una vinoteca", "una dietética",
    "una bicicletería", "una pañalera", "una casa de artículos de limpieza",
    "un local de celulares y accesorios", "una perfumería",
    # Gastronomía
    "una cafetería de especialidad", "una rotisería", "una pizzería de barrio",
    "una heladería", "una casa de empanadas", "un bar de tapas",
    "una cervecería artesanal", "una casa de pastas caseras",
    "un servicio de viandas saludables", "un food truck",
    # Salud y bienestar
    "una veterinaria", "un consultorio odontológico", "una óptica",
    "un kinesiólogo", "un centro de estética", "un nutricionista",
    "un consultorio de psicología", "un centro de fonoaudiología",
    "una farmacia de barrio", "un centro de masajes",
    # Servicios personales
    "una peluquería", "una barbería", "un estudio de tatuajes",
    "un salón de uñas", "una guardería de mascotas", "un paseador de perros",
    "una lavandería", "un taller de costura y arreglos",
    # Deporte y formación
    "un gimnasio de barrio", "un club de padel", "una escuela de música",
    "un instituto de idiomas", "un estudio de yoga", "una escuela de manejo",
    "un profesor particular de matemática", "una academia de danza",
    "una colonia de vacaciones",
    # Oficios y servicios técnicos
    "un taller mecánico", "un lavadero de autos", "un gomería",
    "un service de aire acondicionado", "un electricista matriculado",
    "un plomero", "una empresa de fumigación", "un cerrajero",
    "un service de electrodomésticos", "una empresa de mudanzas",
    # Profesionales y B2B
    "un estudio contable", "un estudio jurídico chico", "una inmobiliaria chica",
    "un estudio de arquitectura", "una agencia de seguros",
    "un estudio de fotografía", "una imprenta", "una agencia de viajes",
    "un servicio de catering para eventos", "un salón de fiestas",
    "una distribuidora mayorista", "un centro de coworking",
    # Verde y hogar
    "un vivero", "un paisajista", "una carpintería a medida",
    "una empresa de limpieza de oficinas",
]

PILLARS = {
    "automatizacion": {
        "label": "Automatización",
        "emoji": "⚙️",
        "intenciones": ["educativo", "emocional", "venta"],
    },
    "eficiencia_comercial": {
        "label": "Eficiencia Comercial",
        "emoji": "📈",
        "intenciones": ["emocional", "venta", "educativo"],
    },
    "optimizacion_operativa": {
        "label": "Optimización Operativa",
        "emoji": "🛠️",
        "intenciones": ["educativo", "venta"],
    },
    "transformacion": {
        "label": "Transformación Digital",
        "emoji": "🚀",
        "intenciones": ["emocional", "venta"],
    },
    # A diferencia de los demás pilares (caso de un cliente, tercera persona),
    # este usa formato distinto: situación cotidiana en segunda persona con
    # remate cómico. Ver generate_humor() en groq_client.py.
    "humor": {
        "label": "Humor",
        "emoji": "😅",
        "formato": "humor",
        "intenciones": ["conexion", "emocional"],
    },
    # Contenido educativo "¿Sabías que...?": no cuenta el caso de un cliente
    # ni plantea una solución puntual (nada de chat/web/flujo), solo un dato o
    # concepto interesante. Cierra invitando a pedir más info, sin pitch. Ver
    # generate_sabias_que() en groq_client.py / content_rules.py.
    "sabias_que": {
        "label": "Sabías que...?",
        "emoji": "💡",
        "formato": "sabias_que",
        "intenciones": ["educativo"],
    },
    # Mismo formato "caso" que los primeros 4 pilares (nada nuevo que programar):
    # ya exige mostrar la solución funcionando (chat/web/flujo), así que estos
    # ángulos solo empujan a que ESA parte sea explícitamente un demo/tutorial
    # paso a paso en vez de quedar como una mención de pasada. Funciona en
    # carrusel y en video narrado sin cambios, igual que automatizacion/etc.
    "demos_tutoriales": {
        "label": "Demos y Tutoriales",
        "emoji": "🎓",
        "intenciones": ["educativo", "venta"],
    },
    # Puro fun content, sin caso de cliente ni pitch de la agencia: rankings/
    # listas graciosas tipo "Esenciales 2026" que mezclan herramientas de IA
    # con costumbres argentinas (mate, asado, dólar blue...). Cada ítem de la
    # lista lleva un ícono pixel art generado por IA. Ver chisme_rules.py.
    "chisme": {
        "label": "Chisme Tech Argento",
        "emoji": "🧉",
        "formato": "chisme",
        "intenciones": ["conexion"],
    },
    # Gancho de confesión en primera persona ("el error que cometí en mi
    # negocio...") seguido de una lista de acciones concretas con IA
    # (automatizar / generar impacto / atraer clientes). Cada slide lleva una
    # foto de fondo a página completa generada por IA, pensada para ser
    # llamativa y que el texto se recorte fuerte encima. Ver impacto_rules.py.
    "errores_30min": {
        "label": "El Error de los 30 Minutos",
        "emoji": "⏱️",
        "formato": "impacto",
        "intenciones": ["emocional", "venta"],
    },
}


# PARA QUÉ está hecha una pieza, además de sobre qué habla. Un pilar puede
# sostener las cuatro: el mismo ángulo ("cómo automatizar el recordatorio de
# turnos") da una pieza distinta si se cuenta para enseñar, para que duela,
# para que se sienta visto o para que escriba. Sin esta dimensión el modelo
# elegía siempre el mismo tratamiento (problema -> solución -> cierre) y la
# cuenta entera sonaba a la misma pieza repetida.
#
# La "guia" se le pega tal cual al prompt (audiencia.bloque_intencion), así
# que está escrita como una instrucción, no como una definición de manual; el
# "resumen" es la versión de una línea para listados (el prompt de ángulos,
# /pilares en Telegram).
INTENCIONES = {
    "educativo": {
        "label": "Educativo",
        "emoji": "📚",
        "resumen": "enseñar algo aplicable, aunque nunca contraten nada",
        "guia": (
            "que quien mira aprenda algo aplicable HOY, aunque nunca contrate nada. La pieza deja "
            "una idea concreta y usable (cómo funciona algo, qué mirar, en qué orden hacerlo), no "
            "una promesa. Se gana cuando alguien piensa 'esto no lo sabía' y lo guarda."
        ),
    },
    "emocional": {
        "label": "Emocional",
        "emoji": "❤️‍🔥",
        "resumen": "que duela o alivie: la sensación por encima del dato",
        "guia": (
            "poné el foco en lo que se SIENTE: el cansancio de contestar a las once de la noche, la "
            "bronca de perder algo que ya estaba ganado, el alivio de sacárselo de encima. El dato "
            "está al servicio de esa sensación, no al revés. Se gana cuando alguien se queda pensando."
        ),
    },
    "conexion": {
        "label": "Conexión",
        "emoji": "🤝",
        "resumen": "que se vea a sí mismo y quiera comentar 'soy yo'",
        "guia": (
            "identificación pura: que quien mira se vea a sí mismo y tenga ganas de comentar 'soy yo' "
            "o de mandárselo a un socio. No enseñes ni vendas nada, ni siquiera de costado. Se gana "
            "cuando alguien etiqueta a otro en los comentarios."
        ),
    },
    "venta": {
        "label": "Venta",
        "emoji": "💬",
        "resumen": "la solución funcionando, cerrando en conversación",
        "guia": (
            "mostrá la solución funcionando y qué cambia concretamente, y cerrá abriendo una "
            "conversación, nunca una oferta. Se puede notar que esto lo hace la agencia, pero sin "
            "pitch, sin precios y sin demo. Se gana cuando alguien escribe para contar su caso."
        ),
    },
}

# Intenciones que se le permiten a un pilar que no las declara. Todo pilar de
# formato "caso" (el default) las soporta menos "conexion": una pieza de puro
# 'me pasa igual' no aguanta la estructura de caso de cliente en tercera persona.
_INTENCIONES_DEFAULT = ["educativo", "emocional", "venta"]


def intenciones_de(pillar_key: str) -> list[str]:
    return PILLARS[pillar_key].get("intenciones", _INTENCIONES_DEFAULT)


def elegir_intencion(pillar_key: str) -> str:
    """Sortea la intención de una pieza entre las que soporta su pilar. Al azar
    y sin memoria: llevar una cuenta de qué se usó por última vez pediría
    persistir estado, y con el volumen del bot (unas pocas piezas por día) el
    sorteo ya reparte parejo."""
    return random.choice(intenciones_de(pillar_key))
