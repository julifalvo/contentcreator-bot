"""Generación de guiones/textos para TikTok usando Claude (Anthropic API)."""

import json
import os

import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-opus-5"

SYSTEM_PROMPT = (
    "Sos alguien que arma agentes de IA y automatizaciones para negocios chicos y medianos, "
    "y contás en TikTok lo que vas aprendiendo en el camino. No sos un community manager ni "
    "una agencia de marketing: hablás como hablarías con un cliente en un café, contando un "
    "caso concreto, no vendiendo un curso.\n\n"
    "IMPORTANTE sobre el formato: el video NO tiene voz en off ni guion hablado. Es un carrusel "
    "de imágenes con música de fondo — la persona no lee nada en voz alta. Eso significa que "
    "TODO lo que el espectador va a entender tiene que estar en el texto de las slides. No hay "
    "una narración por afuera que explique o agregue contexto: la portada y cada slide tienen "
    "que sostenerse solas.\n\n"
    "Reglas duras de estilo:\n"
    "- Prohibido el lenguaje de marketing vacío: 'revolucioná tu negocio', 'llevá tu negocio "
    "al siguiente nivel', 'en la era digital', 'maximizá resultados', 'impulsá tu crecimiento', "
    "'no te quedes atrás', 'transformá tu negocio', 'la clave del éxito', 'potenciá', "
    "'optimizá tus procesos' (sin decir CUÁLES), o cualquier frase que sonaría igual en "
    "cualquier rubro. Si una frase serviría para vender cualquier cosa, está prohibida.\n"
    "- Cada pieza tiene que incluir un DEMO real y específico: un intercambio concreto de "
    "mensajes (cliente escribe algo puntual, el agente responde algo puntual), con un rubro "
    "de negocio específico (ej: un local de indumentaria, un consultorio odontológico, una "
    "inmobiliaria, un gimnasio) — no 'un negocio' genérico.\n"
    "- Usá números y detalles concretos siempre que se pueda (tiempos, cantidad de mensajes, "
    "horarios), nunca 'mucho', 'rápido' o 'fácil' sin un dato al lado.\n"
    "- Texto natural, como lo escribiría una persona, no un folleto corporativo. Frases cortas.\n"
    "- Nunca prometas resultados exagerados ni uses superlativos vacíos ('el mejor', 'increíble', "
    "'revolucionario')."
)

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "negocio_ejemplo": {
            "type": "string",
            "description": "Rubro concreto usado como ejemplo en este video (ej: 'un local de indumentaria', 'un consultorio odontológico'). Nunca 'un negocio' genérico.",
        },
        "demo": {
            "type": "object",
            "description": "Intercambio real y específico de mensajes que se muestra como demo visual (formato chat).",
            "properties": {
                "canal": {
                    "type": "string",
                    "description": "Canal donde ocurre, ej: 'WhatsApp', 'DM de Instagram'.",
                },
                "mensaje_cliente": {
                    "type": "string",
                    "description": "Mensaje realista que escribiría un cliente de ese rubro. Máx 18 palabras.",
                },
                "respuesta_bot": {
                    "type": "string",
                    "description": "Respuesta concreta y específica del agente de IA a ese mensaje. Máx 22 palabras.",
                },
                "tiempo_respuesta": {
                    "type": "string",
                    "description": "Tiempo de respuesta concreto, ej: 'en 4 segundos', 'al instante, 3am incluido'.",
                },
            },
            "required": ["canal", "mensaje_cliente", "respuesta_bot", "tiempo_respuesta"],
            "additionalProperties": False,
        },
        "portada_text": {
            "type": "string",
            "description": (
                "Texto grande para la portada/miniatura. Es el gancho del video (no hay voz que "
                "lo diga, así que tiene que atrapar solo con el texto). Máx 8 palabras, concreto "
                "y específico, no una frase de marketing genérica."
            ),
        },
        "slides": {
            "type": "array",
            "description": (
                "4 slides tipo carrusel que cuentan la historia completa (problema concreto -> "
                "consecuencia -> solución -> resultado con número). Como no hay narración hablada, "
                "estas slides son la ÚNICA fuente de información del video: tienen que alcanzar "
                "por sí solas para entender el caso."
            ),
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Máx 6 palabras"},
                    "text": {"type": "string", "description": "Máx 14 palabras, con un detalle concreto, no relleno"},
                },
                "required": ["title", "text"],
                "additionalProperties": False,
            },
        },
        "cta_slide_text": {
            "type": "string",
            "description": "Texto corto para la slide final de llamado a la acción. Concreto, no genérico.",
        },
        "caption": {
            "type": "string",
            "description": "Caption para TikTok, tono natural (como si lo escribiera una persona real), 2-4 líneas, termina con una pregunta concreta relacionada al demo.",
        },
        "hashtags": {
            "type": "array",
            "description": "8 a 10 hashtags relevantes sin el símbolo #.",
            "items": {"type": "string"},
        },
    },
    "required": [
        "negocio_ejemplo", "demo", "portada_text", "slides",
        "cta_slide_text", "caption", "hashtags",
    ],
    "additionalProperties": False,
}


def _client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "No se encontró ANTHROPIC_API_KEY. Creá un archivo .env (copiá .env.example) "
            "con tu API key de Anthropic, o exportala como variable de entorno."
        )
    return anthropic.Anthropic(api_key=api_key)


def generate_content(pillar_label: str, angle: str) -> dict:
    """Pide a Claude un paquete completo de contenido para un TikTok (sin voz en off)."""
    client = _client()

    user_prompt = (
        f"Pilar de contenido: {pillar_label}.\n"
        f"Ángulo del video: {angle}\n\n"
        "Elegí un rubro de negocio concreto y específico (distinto cada vez que te lo pidan) "
        "y armá el contenido para un video sin voz en off (carrusel de imágenes + música de "
        "fondo), contado a través de ese rubro y de un demo real de conversación cliente-agente. "
        "Nada de lenguaje de marketing genérico: si al leerlo suena a anuncio, reescribilo como "
        "lo dirías charlando con un amigo que tiene ese negocio."
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        output_config={"format": {"type": "json_schema", "schema": OUTPUT_SCHEMA}},
        messages=[{"role": "user", "content": user_prompt}],
    )

    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)
