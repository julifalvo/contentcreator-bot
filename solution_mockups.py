"""Banco local de mockups de 'solución' (web, bot de automatización, agente de
recomendaciones) — no son screenshots reales ni se descargan de ningún lado.

Son datos de ejemplo (headline, pasos, tarjetas) que image_gen.py dibuja a mano
con Pillow. 100% local, $0, sin API key, sin registro, sin créditos de Anthropic.

pick_mockups() sortea varios tipos distintos (web / bot / agente) en cada
ejecución, cada uno con una variante y una descripción propia, para que el
contenido no se repita entre piezas.
"""

import random

WEB_VARIANTS = [
    {
        "url": "tunegocio.com",
        "headline": "Pedí en 2 minutos, sin llamar",
        "subheadline": "Catálogo, precios y WhatsApp directo",
        "cta": "Escribir por WhatsApp",
        "features": ["Catálogo actualizado", "Precios claros", "Reserva en un clic"],
    },
    {
        "url": "reservas.tunegocio.com",
        "headline": "Reservá tu turno online",
        "subheadline": "Elegís día y horario, sin esperar respuesta",
        "cta": "Reservar ahora",
        "features": ["Agenda en vivo", "Recordatorio automático", "Cancelación fácil"],
    },
    {
        "url": "catalogo.tunegocio.com",
        "headline": "Todo lo que vendés, en un link",
        "subheadline": "Un solo lugar para ver precios y pedir",
        "cta": "Ver catálogo",
        "features": ["Fotos y precios", "Pedido directo", "Sin apps que instalar"],
    },
    {
        "url": "pedidos.tunegocio.com",
        "headline": "Tu menú, siempre actualizado",
        "subheadline": "Sin llamar para saber si hay stock",
        "cta": "Hacer pedido",
        "features": ["Stock en vivo", "Pago desde el link", "Aviso de retiro"],
    },
    {
        "url": "turnos.tunegocio.com",
        "headline": "Sacá turno sin esperar que atiendan",
        "subheadline": "Ves los horarios libres al toque",
        "cta": "Ver horarios",
        "features": ["Horarios reales", "Confirmación automática", "Reprogramar fácil"],
    },
    {
        "url": "info.tunegocio.com",
        "headline": "Toda la info, sin mandar 10 mensajes",
        "subheadline": "Precios, ubicación y horarios en un solo lugar",
        "cta": "Ver todo",
        "features": ["Ubicación y horarios", "Precios sin preguntar", "Contacto directo"],
    },
]

WEB_CAPTIONS = [
    "Así podría verse la web de {negocio}: simple, directa, con un botón a WhatsApp",
    "Un sitio así no necesita ser complicado, solo tiene que dejar pedir rápido",
    "Esto es lo mínimo que necesita hoy {negocio} para no depender solo del boca en boca",
    "Nada de diseño complicado: {negocio} solo necesita que el cliente pueda actuar en un clic",
    "Una página así reemplaza media hora de mensajes explicando lo mismo siempre",
]

BOT_VARIANTS = [
    {"steps": ["Llega el mensaje", "El bot entiende el pedido", "Se carga solo en la planilla", "Confirma al cliente"]},
    {"steps": ["Se acerca la fecha del turno", "El sistema arma el recordatorio", "Lo manda por WhatsApp", "Reprograma si hace falta"]},
    {"steps": ["Baja el stock de un producto", "El sistema lo detecta solo", "Avisa al proveedor", "Actualiza el catálogo"]},
    {"steps": ["Un cliente pregunta precio", "El bot busca en la lista", "Responde con el monto exacto", "Ofrece cerrar la venta"]},
    {"steps": ["Vence una cuota o pago", "El sistema arma el aviso", "Lo manda con el link de pago", "Marca cobrado al confirmar"]},
    {"steps": ["Alguien cancela un turno", "El sistema libera el horario", "Avisa a la lista de espera", "Reasigna el lugar solo"]},
]

BOT_CAPTIONS = [
    "Así es el flujo por detrás: cada paso lo hace el sistema solo, sin que nadie lo toque",
    "Esto corre en segundo plano en {negocio}, nadie lo ve pero pasa cada vez que hace falta",
    "4 pasos, cero intervención humana, así se automatiza de verdad",
    "Nadie en {negocio} tiene que acordarse de hacer esto, el sistema ya lo tiene resuelto",
    "Esto es lo que reemplaza las horas de tareas repetitivas: un flujo que corre solo",
]

AGENTE_VARIANTS = [
    {"items": [
        {"name": "Combo básico", "price": "$8.500", "match": "92% match"},
        {"name": "Plan mensual", "price": "$15.000", "match": "85% match"},
        {"name": "Producto premium", "price": "$22.000", "match": "78% match"},
    ]},
    {"items": [
        {"name": "Opción más pedida", "price": "$6.200", "match": "95% match"},
        {"name": "Alternativa similar", "price": "$9.800", "match": "81% match"},
        {"name": "Upgrade sugerido", "price": "$14.500", "match": "73% match"},
    ]},
    {"items": [
        {"name": "Lo que buscaba", "price": "$11.000", "match": "97% match"},
        {"name": "Complemento útil", "price": "$4.300", "match": "88% match"},
        {"name": "Otra opción", "price": "$18.900", "match": "70% match"},
    ]},
    {"items": [
        {"name": "Plan inicial", "price": "$5.000", "match": "90% match"},
        {"name": "Plan recomendado", "price": "$12.000", "match": "94% match"},
        {"name": "Plan completo", "price": "$19.500", "match": "82% match"},
    ]},
    {"items": [
        {"name": "Servicio exprés", "price": "$7.200", "match": "89% match"},
        {"name": "Servicio estándar", "price": "$10.500", "match": "91% match"},
        {"name": "Servicio premium", "price": "$16.800", "match": "76% match"},
    ]},
]

AGENTE_CAPTIONS = [
    "El agente ordena las opciones según lo que pidió el cliente, no según lo que más le conviene vender",
    "Así arma las recomendaciones un agente de IA, mirando lo que {negocio} realmente puede ofrecer",
    "Nada de listas genéricas, esto se arma distinto en cada conversación",
    "El agente aprende qué preguntó el cliente y ordena las opciones en base a eso, no al azar",
    "Esto es lo que ve {negocio} antes de responder: ya viene ordenado por lo que el cliente busca",
]

_KIND_DATA = {
    "web": (WEB_VARIANTS, WEB_CAPTIONS),
    "bot": (BOT_VARIANTS, BOT_CAPTIONS),
    "agente": (AGENTE_VARIANTS, AGENTE_CAPTIONS),
}


def _build_mockup(kind: str, negocio_ejemplo: str) -> dict:
    variants, captions = _KIND_DATA[kind]
    variant = random.choice(variants)
    caption = random.choice(captions).format(negocio=negocio_ejemplo)
    return {"kind": kind, "caption": caption, **variant}


def pick_mockup(negocio_ejemplo: str) -> dict:
    """Sortea un solo tipo de mockup (web / bot / agente). Costo: $0."""
    return _build_mockup(random.choice(list(_KIND_DATA)), negocio_ejemplo)


def pick_mockups(negocio_ejemplo: str, count: int = 2) -> list[dict]:
    """Sortea `count` mockups de tipos distintos entre sí (sin repetir kind),
    con contenido del banco local fijo. Costo: $0, sin dependencias."""
    count = min(count, len(_KIND_DATA))
    kinds = random.sample(list(_KIND_DATA), count)
    return [_build_mockup(kind, negocio_ejemplo) for kind in kinds]


def pick_mockups_ai(negocio_ejemplo: str, count: int = 2) -> list[dict]:
    """Igual que pick_mockups(), pero el contenido de cada mockup lo decide el
    modelo local de Ollama en vez de salir del banco fijo (headline, pasos,
    tarjetas distintos cada vez). Costo: $0, requiere Ollama corriendo."""
    from ollama_client import generate_mockup_content  # import diferido: no hace falta Ollama salvo que se use esto

    count = min(count, len(_KIND_DATA))
    kinds = random.sample(list(_KIND_DATA), count)
    return [generate_mockup_content(negocio_ejemplo, kind) for kind in kinds]
