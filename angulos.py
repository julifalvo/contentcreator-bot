"""Pool de ángulos por pilar, persistido en angulos_pool.json.

Reemplaza las listas que antes vivían hardcodeadas en config.py: en vez de
editar código para sumar ideas, se corre `python refrescar_angulos.py` de vez
en cuando y ese script le pide a la IA (Groq/Gemini, con el mismo fallback
que usa generate.py) que invente ángulos nuevos, evitando repetir los que ya
están. Este módulo solo lee/escribe el archivo — no habla con ninguna API.
"""

import json
import random
from pathlib import Path

POOL_PATH = Path(__file__).parent / "angulos_pool.json"

# Techo por pilar: sin este límite el pool crece para siempre y el prompt de
# "no repitas estos" de refrescar_angulos.py se vuelve cada vez más largo (y
# más caro en tokens) sin aportar variedad real. Al pasarse, se descartan los
# más viejos (FIFO) — los nuevos siempre entran.
CAP_POR_PILAR = 60


def _cargar() -> dict:
    if not POOL_PATH.exists():
        return {}
    return json.loads(POOL_PATH.read_text(encoding="utf-8"))


def _guardar(pool: dict) -> None:
    POOL_PATH.write_text(json.dumps(pool, ensure_ascii=False, indent=2), encoding="utf-8")


def angulos_de(pillar_key: str) -> list[str]:
    return _cargar().get(pillar_key, [])


def elegir_angulo(pillar_key: str) -> str:
    disponibles = angulos_de(pillar_key)
    if not disponibles:
        raise RuntimeError(
            f"No hay ángulos generados todavía para '{pillar_key}'. "
            f"Corré: python refrescar_angulos.py {pillar_key}"
        )
    return random.choice(disponibles)


def muestra(pillar_key: str, n: int) -> list[str]:
    """Subconjunto al azar del pool (no la lista entera, que puede tener 40+
    y no entra cómodo como botones de Telegram). Se re-sortea en cada llamada,
    así el wizard se siente distinto aunque el pool no haya crecido."""
    disponibles = angulos_de(pillar_key)
    return random.sample(disponibles, min(n, len(disponibles)))


def agregar(pillar_key: str, nuevos: list[str]) -> int:
    """Suma `nuevos` al pool de `pillar_key`, sin duplicar (case-insensitive)
    y respetando CAP_POR_PILAR. Devuelve cuántos se agregaron de verdad."""
    pool = _cargar()
    actuales = pool.get(pillar_key, [])
    vistos = {a.lower() for a in actuales}

    agregados = 0
    for a in nuevos:
        if a.lower() not in vistos:
            actuales.append(a)
            vistos.add(a.lower())
            agregados += 1

    if len(actuales) > CAP_POR_PILAR:
        actuales = actuales[-CAP_POR_PILAR:]

    pool[pillar_key] = actuales
    _guardar(pool)
    return agregados
