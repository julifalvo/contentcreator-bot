"""Elige qué mockups de 'solución' (web, bot de automatización, agente de
recomendaciones) mostrar en una pieza, y le pide su contenido a la IA local
(Ollama) — sin bancos de datos fijos escritos a mano. Costo: $0.

image_gen.py después dibuja ese contenido a mano con Pillow (headline, pasos,
tarjetas): no son screenshots reales ni se descargan de ningún lado.
"""

import random

from ollama_client import generate_mockup_content

KINDS = ("web", "bot", "agente")


def pick_mockups(
    negocio_ejemplo: str, count: int = 2, priority_kind: str | None = None, contexto: str = "",
) -> list[dict]:
    """Sortea `count` tipos de mockup distintos entre sí (sin repetir kind) y
    le pide a la IA el contenido de cada uno, específico para `negocio_ejemplo`.

    `contexto` (el problema/solución puntual de la pieza) se le pasa a la IA
    para que el mockup ilustre ese caso concreto en vez de inventar un
    ejemplo genérico del rubro sin relación con el resto del video.

    Si se pasa `priority_kind`, ese tipo va primero (coincide con el tipo de
    solución -web/chatbot/automatización- que protagoniza la pieza, para que
    la imagen no contradiga lo que cuenta el texto); el resto se completa al
    azar entre los tipos restantes."""
    count = min(count, len(KINDS))
    if priority_kind in KINDS:
        resto = random.sample([k for k in KINDS if k != priority_kind], count - 1)
        kinds = [priority_kind, *resto]
    else:
        kinds = random.sample(KINDS, count)
    return [generate_mockup_content(negocio_ejemplo, kind, contexto) for kind in kinds]
