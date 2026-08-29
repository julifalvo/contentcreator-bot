"""Amplía el pool de ángulos (angulos_pool.json) pidiéndole a la IA (Groq o
Gemini, con el mismo fallback que usa generate.py) que invente ángulos nuevos
por pilar, evitando repetir los que ya están.

Esta es la forma de "agregar más ángulos" ahora: correr este script de vez en
cuando, no editar config.py a mano.

A la IA se le pasan dos cosas más que la lista de lo que ya hay: el perfil de
la audiencia (audiencia.py — problemas, deseos, miedos, preguntas y objeciones
reales) para que cada ángulo nazca de un punto concreto y no de la intuición
del modelo, y las intenciones que soporta el pilar, para que el lote no salga
entero servible para una sola cosa.

Antes de pedirlos consulta las métricas reales de la cuenta (rendimiento.py:
vistas de TikTok cruzadas con el pilar y el ángulo que generó cada pieza) y se
las pasa a la IA, así los ángulos nuevos empujan hacia lo que de verdad
funcionó en vez de salir solo de la intuición del modelo. Es best-effort: si
no hay tokens de TikTok, si al token le faltan los scopes de lectura o si la
API se cae, se avisa y se generan igual sin ese dato.

Uso:
    python refrescar_angulos.py                   # todos los pilares, 15 c/u
    python refrescar_angulos.py automatizacion    # solo ese pilar
    python refrescar_angulos.py --n 25            # pide más por pilar
    python refrescar_angulos.py --sin-metricas    # ni consulta TikTok
"""

import argparse
import sys
from pathlib import Path

# La consola de Windows escribe en cp1252 y las flechas/tildes de los mensajes
# de abajo la hacen explotar con UnicodeEncodeError. Mismo arreglo que en
# generate.py y bot.py.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv

load_dotenv()

import angulos
import audiencia
import rendimiento
import tiktok_client
from ai_providers import generate_angulos
from config import PILLARS

N_DEFAULT = 15
TOKENS_PATH = Path(__file__).parent / "tiktok_tokens.json"


def _traer_metricas() -> list[dict]:
    """Videos publicados con su pilar y su ángulo atribuidos. Devuelve [] ante
    cualquier problema: ampliar el pool tiene que seguir funcionando aunque la
    cuenta de TikTok no esté conectada."""
    if not TOKENS_PATH.exists():
        print("(sin métricas: no hay tiktok_tokens.json — corré 'python tiktok_auth.py')")
        return []
    try:
        atribuidos = rendimiento.traer(tiktok_client.get_access_token())
    except Exception as e:
        print(f"(sin métricas: {e})")
        if "scope" in str(e).lower():
            print("  Faltan los scopes de lectura: ver el encabezado de tiktok_metrics.py.")
        return []

    con_pilar = [v for v in atribuidos if v.get("pilar")]
    print(f"Métricas: {len(atribuidos)} videos publicados, {len(con_pilar)} atribuidos a un pilar.")
    if atribuidos and not con_pilar:
        print("  Ninguno matcheó con una pieza de output/, así que se generan ángulos a ciegas.")
    return atribuidos


def _refrescar_pilar(pillar_key: str, n: int, metricas: list[dict]) -> None:
    pillar = PILLARS[pillar_key]
    formato = pillar.get("formato")  # None = formato "caso" (default)
    existentes = angulos.angulos_de(pillar_key)
    bloque = rendimiento.bloque_para_prompt(metricas, pillar_key) if metricas else ""
    guia = " · guiado por métricas" if bloque else ""
    print(f"→ {pillar['label']} ({len(existentes)} ya en el pool{guia})...")
    try:
        data = generate_angulos(pillar["label"], formato, existentes, n, bloque or None,
                                audiencia.bloque_para_angulos(pillar_key))
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
    parser.add_argument("--sin-metricas", action="store_true",
                        help="No consulta TikTok: genera los ángulos sin mirar qué funcionó")
    args = parser.parse_args()

    metricas = [] if args.sin_metricas else _traer_metricas()

    if args.pilar:
        if args.pilar not in PILLARS:
            sys.exit(f"Pilar inválido: '{args.pilar}'. Opciones: {', '.join(PILLARS)}")
        _refrescar_pilar(args.pilar, args.n, metricas)
    else:
        for pillar_key in PILLARS:
            _refrescar_pilar(pillar_key, args.n, metricas)


if __name__ == "__main__":
    main()
