"""Cruza las métricas reales de TikTok (tiktok_metrics.py) con las piezas que
generó el bot (output/*/contenido.json) para saber qué PILAR, qué ÁNGULO y con
qué INTENCIÓN funcionaron, no solo qué video anduvo bien.

El problema: la Display API de TikTok no devuelve ninguna etiqueta nuestra,
solo id, descripción y números. La solución: cada pieza que genera el bot
guarda en su carpeta de output/ el pilar, el ángulo, la intención y el caption
exacto que después se sube como descripción — así que emparejando la
descripción del video publicado contra los captions locales se recupera la
atribución sin tener que llevar una base de datos aparte.

El emparejamiento es por similitud y no por igualdad: TikTok le agrega los
hashtags al final de la descripción, a veces el caption se retoca a mano
antes de aprobar, y los saltos de línea no siempre sobreviven.

Dos limitaciones conocidas, para no leer de más estos números:
- /video/list lista solo VIDEOS: los carruseles de fotos no aparecen, así que
  la atribución cubre únicamente las piezas en formato video.
- Las vistas dependen muchísimo de cuándo se publicó cada cosa; con pocas
  piezas por pilar esto orienta, no demuestra.
"""

import json
import re
import statistics
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

import tiktok_metrics
from config import INTENCIONES, PILLARS

OUTPUT_DIR = Path(__file__).parent / "output"

# Umbral para dar por emparejados un video de TikTok y una pieza local.
# Permisivo a propósito (la descripción publicada casi nunca es idéntica al
# caption), pero no tanto como para confundir dos piezas del bot entre sí:
# comparten muletillas y estructura, y de ahí para abajo empieza a emparejar
# cualquier cosa con cualquier cosa.
SIMILITUD_MINIMA = 0.55


def _normalizar(texto: str) -> str:
    """Baja el texto a algo comparable: sin acentos, sin hashtags, sin emojis
    ni puntuación y con los espacios colapsados. Sin esto la similitud se va
    en diferencias que no significan nada (una tilde, un signo de pregunta)."""
    texto = unicodedata.normalize("NFKD", texto.lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"#\w+", " ", texto)
    texto = re.sub(r"[^a-z0-9 ]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def piezas_locales() -> list[dict]:
    """Todas las piezas generadas que dejaron rastro en output/, con su pilar
    y su ángulo. Las piezas viejas (anteriores a que generate.py guardara el
    pilar) se saltean: sin pilar no sirven para atribuir nada."""
    piezas = []
    for path in sorted(OUTPUT_DIR.glob("*/contenido.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        caption = (data.get("caption") or "").strip()
        pilar = data.get("pilar")
        if not caption or not pilar:
            continue
        piezas.append({
            "carpeta": path.parent.name,
            "pilar": pilar,
            "angulo": data.get("angulo") or "",
            # Las piezas anteriores a que existieran las intenciones (config.py)
            # no la traen: quedan en None y por_intencion() las saltea, igual
            # que ya pasa con las piezas viejas sin pilar.
            "intencion": data.get("intencion"),
            "formato": data.get("formato") or "",
            "_caption_norm": _normalizar(caption),
        })
    return piezas


def _mejor_match(descripcion: str, piezas: list[dict]) -> dict | None:
    objetivo = _normalizar(descripcion)
    if not objetivo:
        return None
    mejor, mejor_ratio = None, 0.0
    for pieza in piezas:
        ratio = SequenceMatcher(None, objetivo, pieza["_caption_norm"]).ratio()
        if ratio > mejor_ratio:
            mejor, mejor_ratio = pieza, ratio
    return mejor if mejor_ratio >= SIMILITUD_MINIMA else None


def atribuir(videos: list[dict], piezas: list[dict] | None = None) -> list[dict]:
    """Le suma a cada video publicado el pilar, el ángulo y la intención que lo generaron,
    cuando se pudo emparejar (quedan en None si no: videos subidos a mano,
    piezas viejas sin pilar guardado, o captions editados de más)."""
    piezas = piezas_locales() if piezas is None else piezas
    atribuidos = []
    for v in videos:
        pieza = _mejor_match(v.get("video_description") or "", piezas)
        atribuidos.append({
            **v,
            "pilar": pieza["pilar"] if pieza else None,
            "angulo": pieza["angulo"] if pieza else None,
            "intencion": pieza["intencion"] if pieza else None,
            "carpeta": pieza["carpeta"] if pieza else None,
        })
    return atribuidos


def traer(access_token: str, max_scan: int = 50) -> list[dict]:
    """Atajo: trae los videos publicados de la cuenta ya atribuidos."""
    return atribuir(tiktok_metrics.list_videos(access_token, max_count=max_scan))


def por_pilar(atribuidos: list[dict]) -> list[dict]:
    """Resume el rendimiento por pilar, de mejor a peor mediana de vistas. Se
    usa la mediana y no el promedio porque un solo video que pegó bien
    arrastra el promedio de un pilar con 3 piezas y hace parecer ganador a
    algo que anduvo bien una vez."""
    por_clave: dict[str, list[dict]] = {}
    for v in atribuidos:
        if v.get("pilar"):
            por_clave.setdefault(v["pilar"], []).append(v)

    filas = []
    for pilar, vs in por_clave.items():
        vistas = [v.get("view_count", 0) for v in vs]
        filas.append({
            "pilar": pilar,
            "label": PILLARS.get(pilar, {}).get("label", pilar),
            "piezas": len(vs),
            "vistas_mediana": statistics.median(vistas),
            "vistas_total": sum(vistas),
            "mejor": max(vs, key=lambda v: v.get("view_count", 0)),
        })
    return sorted(filas, key=lambda f: f["vistas_mediana"], reverse=True)


def por_intencion(atribuidos: list[dict]) -> list[dict]:
    """Lo mismo que por_pilar() pero cortando por PARA QUÉ estaba hecha la
    pieza (educativo/emocional/conexión/venta, ver config.INTENCIONES). Es el
    corte que dice si la cuenta está enganchando y no vendiendo, o al revés:
    el pilar dice de qué se habló, la intención dice qué se esperaba que
    pasara. Mediana por la misma razón que en por_pilar()."""
    por_clave: dict[str, list[dict]] = {}
    for v in atribuidos:
        if v.get("intencion"):
            por_clave.setdefault(v["intencion"], []).append(v)

    filas = []
    for intencion, vs in por_clave.items():
        vistas = [v.get("view_count", 0) for v in vs]
        filas.append({
            "intencion": intencion,
            "label": INTENCIONES.get(intencion, {}).get("label", intencion),
            "emoji": INTENCIONES.get(intencion, {}).get("emoji", "•"),
            "piezas": len(vs),
            "vistas_mediana": statistics.median(vistas),
            "vistas_total": sum(vistas),
        })
    return sorted(filas, key=lambda f: f["vistas_mediana"], reverse=True)


def _piezas(n: int) -> str:
    return f"{n} pieza" if n == 1 else f"{n} piezas"


def por_angulo(videos: list[dict]) -> list[dict]:
    """Agrupa las piezas publicadas por ángulo, de más a menos vistas. El
    mismo ángulo puede haber generado varias piezas (el pool se sortea al
    azar), y sin agrupar el mismo texto aparece a la vez arriba y abajo del
    ranking — justo el contraste que se le quiere mostrar a la IA. Se usa la
    mediana por la misma razón que en por_pilar()."""
    grupos: dict[str, list[dict]] = {}
    for v in videos:
        clave = (v.get("angulo") or "").strip().lower() or f"_sin_angulo_{v.get('id')}"
        grupos.setdefault(clave, []).append(v)

    filas = []
    for vs in grupos.values():
        vistas = [v.get("view_count", 0) for v in vs]
        descripcion = (vs[0].get("video_description") or "").strip().replace("\n", " ")
        filas.append({
            "angulo": vs[0].get("angulo") or descripcion[:80],
            "pilar": vs[0].get("pilar"),
            "piezas": len(vs),
            "vistas": statistics.median(vistas),
        })
    return sorted(filas, key=lambda f: f["vistas"], reverse=True)


def _linea_angulo(fila: dict) -> str:
    label = PILLARS.get(fila.get("pilar"), {}).get("label", "sin atribuir")
    veces = f", mediana de {fila['piezas']} piezas" if fila["piezas"] > 1 else ""
    return f'  * {fila["vistas"]:.0f} vistas — "{fila["angulo"]}" ({label}{veces})'


def bloque_para_prompt(atribuidos: list[dict], pilar_key: str | None = None,
                       n_top: int = 5, n_flop: int = 3) -> str:
    """Arma el bloque de texto que se le pasa a la IA que inventa ángulos
    (refrescar_angulos.py) para que empuje hacia lo que ya funcionó en la
    cuenta. Devuelve "" si no hay nada atribuido: sin datos es mejor no decir
    nada que mandarle al modelo un bloque vacío que igual va a intentar usar.

    Si `pilar_key` tiene al menos 3 piezas propias, el bloque se arma con las
    de ese pilar (lo más pertinente para los ángulos que se están pidiendo);
    si no, se cae a las de toda la cuenta, que igual marcan qué tono y qué
    tipo de gancho anda.
    """
    con_pilar = [v for v in atribuidos if v.get("pilar")]
    if not con_pilar:
        return ""

    del_pilar = [v for v in con_pilar if v["pilar"] == pilar_key]
    if pilar_key and len(del_pilar) >= 3:
        muestra, alcance = del_pilar, f"del pilar ({_piezas(len(del_pilar))})"
    else:
        muestra, alcance = con_pilar, f"de toda la cuenta ({_piezas(len(con_pilar))})"

    ordenados = por_angulo(muestra)
    mediana = statistics.median([v.get("view_count", 0) for v in muestra])

    # Con pocos ángulos medidos, un top de 5 se come toda la muestra y el
    # bloque queda sin contraste (todo sería "lo que funcionó"). En ese caso
    # se parte al medio: mejor mitad contra peor mitad, que es de donde el
    # modelo saca el criterio.
    if len(ordenados) <= n_top + n_flop:
        n_top = max(1, (len(ordenados) + 1) // 2)
        n_flop = len(ordenados) - n_top

    lineas = [
        f"QUÉ FUNCIONÓ DE VERDAD EN LA CUENTA, datos reales de TikTok {alcance}:",
        f"- Vistas medianas: {mediana:.0f}",
        "- Ángulos que MÁS vistas hicieron:",
    ]
    lineas += [_linea_angulo(f) for f in ordenados[:n_top]]
    peores = sorted(ordenados[n_top:], key=lambda f: f["vistas"])[:n_flop]
    if peores:
        lineas.append("- Ángulos que MENOS vistas hicieron:")
        lineas += [_linea_angulo(f) for f in peores]
    return "\n".join(lineas)
