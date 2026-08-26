"""Elige qué mockups de 'solución' (web, bot de automatización, agente de
recomendaciones) mostrar en una pieza, y le pide su contenido a la IA local
(Ollama) — sin bancos de datos fijos escritos a mano. Costo: $0.

image_gen.py después dibuja ese contenido a mano con Pillow (headline, pasos,
tarjetas): no son screenshots reales ni se descargan de ningún lado.
"""

import random

from ollama_client import generate_mockup_content

KINDS = ("web", "bot", "agente")


def pick_mockups(negocio_ejemplo: str, count: int = 2) -> list[dict]:
    """Sortea `count` tipos de mockup distintos entre sí (sin repetir kind) y
    le pide a la IA el contenido de cada uno, específico para `negocio_ejemplo`."""
    count = min(count, len(KINDS))
    kinds = random.sample(KINDS, count)
    return [generate_mockup_content(negocio_ejemplo, kind) for kind in kinds]
