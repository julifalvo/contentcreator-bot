"""Generador de contenido 100% local — no llama a ninguna API, no consume créditos."""

import copy
import random

from offline_content import CASES

_last_shown: dict[str, str] = {}  # pillar -> portada_text del último caso usado


def generate_content_offline(pillar_key: str) -> dict:
    """Elige un caso real del banco local para el pilar pedido. Costo: $0."""
    candidates = [c for c in CASES if c["pillar"] == pillar_key] or list(CASES)

    if len(candidates) > 1:
        last = _last_shown.get(pillar_key)
        if last is not None:
            candidates = [c for c in candidates if c["portada_text"] != last] or candidates

    case = random.choice(candidates)
    _last_shown[pillar_key] = case["portada_text"]

    return copy.deepcopy(case)
