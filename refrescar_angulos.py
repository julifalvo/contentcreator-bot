"""Amplía el pool de ángulos (angulos_pool.json) pidiéndole a la IA (Groq o
Gemini, con el mismo fallback que usa generate.py) que invente ángulos nuevos
por pilar, evitando repetir los que ya están.

Esta es la forma de "agregar más ángulos" ahora: correr este script de vez en
cuando, no editar config.py a mano.

Uso:
    python refrescar_angulos.py                  # todos los pilares, 15 c/u
    python refrescar_angulos.py automatizacion    # solo ese pilar
    python refrescar_angulos.py --n 25            # pide más por pilar
"""

import argparse
import sys

from dotenv import load_dotenv

load_dotenv()

import angulos
from ai_providers import generate_angulos
from config import PILLARS

N_DEFAULT = 15


def _refrescar_pilar(pillar_key: str, n: int) -> None:
    pillar = PILLARS[pillar_key]
    formato = pillar.get("formato")  # None = formato "caso" (default)
    existentes = angulos.angulos_de(pillar_key)
    print(f"→ {pillar['label']} ({len(existentes)} ya en el pool)...")
    try:
        data = generate_angulos(pillar["label"], formato, existentes, n)
    except Exception as e:
        print(f"  ✗ Falló: {e}")
        return

    agregados = angulos.agregar(pillar_key, data["angulos"])
    total = len(angulos.angulos_de(pillar_key))
    print(f"  ✓ +{agregados} ángulos nuevos (pedidos: {n}, pool total: {total})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Amplía el pool de ángulos con la IA")
    parser.add_argument("pilar", nargs="?", default=None, help="Pilar puntual (default: todos)")
    parser.add_argument("--n", type=int, default=N_DEFAULT, help=f"Ángulos nuevos a pedir por pilar (default: {N_DEFAULT})")
    args = parser.parse_args()

    if args.pilar:
        if args.pilar not in PILLARS:
            sys.exit(f"Pilar inválido: '{args.pilar}'. Opciones: {', '.join(PILLARS)}")
        _refrescar_pilar(args.pilar, args.n)
    else:
        for pillar_key in PILLARS:
            _refrescar_pilar(pillar_key, args.n)


if __name__ == "__main__":
    main()
