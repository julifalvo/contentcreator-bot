"""Bot de Telegram que corre todo el pipeline (generar -> vista previa -> aprobar ->
publicar) a demanda, sin tocar la terminal. Es el mismo bot que ya usás para las
aprobaciones — ahora también entiende comandos.

Dejalo corriendo (python bot.py) y desde el chat de Telegram mandale:

    /generar                 abre un wizard: formato -> pilar -> ángulo -> ¿foto IA? (solo carrusel)
    /generar automatizacion  atajo rápido: carrusel con ese pilar, ángulo y rubro al azar, sin foto
    /publicar                manda a aprobar la última pieza, sin regenerar
    /pilares                 lista los pilares disponibles
    /ayuda                   este mensaje

El wizard de /generar (ver _iniciar_wizard / _handle_wizard_callback) deja
elegir primero dónde publicás (TikTok, Instagram, o ambas), después el
formato (carrusel de imágenes o video narrado con voz de ElevenLabs + b-roll
de Pexels), el pilar, el ángulo puntual, y — solo para carrusel — si la pieza
incluye o no una foto generada por IA (gratis, ver image_gen.py, pero de
calidad despareja, así que es opt-in en vez de automático). El formato video
no está disponible para el pilar humor todavía.

Cuando la pieza va a Instagram, un carrusel se publica como carrusel de feed
(las mismas slides, adaptadas a 4:5 — ver instagram_render.py) más una Story
con la portada; un video se publica como Reel más esa misma Story. La Graph
API de Instagram no tiene modo borrador: aprobar publica directo ahí, a
diferencia de TikTok que cae al inbox de la app mientras la app no esté
auditada (ver tiktok_client.py). El atajo rápido /generar [pilar] sigue
siendo solo TikTok — para Instagram hace falta el wizard completo.

El texto completo de /ayuda (y la lista de /pilares) se arma solo a partir de
config.PILLARS, así que no hace falta tocar este archivo cuando se agrega o
saca un pilar.

Todo paso del wizard tiene un botón "❌ Cancelar", y una falla al subir a
TikTok o Instagram deja un botón "🔁 Reintentar" que repite SOLO esa
plataforma sin tener que generar ni aprobar de nuevo (ver _ultima_publicacion).
El estado (pieza pendiente de aprobación, wizard a mitad de camino, última
publicación) se persiste en bot_state.json en cada update procesado: si el
bot se reinicia con algo pendiente, lo retoma solo al arrancar en vez de
dejar botones viejos en Telegram que no hacen nada.

Solo responde al chat configurado en TELEGRAM_CHAT_ID; cualquier otro chat se
ignora (por si alguien más le escribe al bot).
"""

import json
import os
import random
import sys
import time
import traceback
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

import requests
from dotenv import load_dotenv

load_dotenv()

import angulos
import content_hosting
import instagram_client
import instagram_render
import rendimiento
import telegram_client
import tiktok_client
import tiktok_metrics
from config import INTENCIONES, PILLARS, intenciones_de
from generate import (
    PILARES_VIDEO, asegurar_caption_ig, build_demo_piece, build_piece, build_reel_piece,
    build_tip_reel_piece, build_video_piece,
)

_LABEL_PLATAFORMA = {"tiktok": "TikTok", "instagram": "Instagram"}

ALLOWED_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


_NOTAS_FORMATO = {
    "humor": "  (formato humor: situación graciosa en 2da persona, no un caso)",
    "sabias_que": "  (formato educativo: dato o concepto, sin caso ni solución puntual)",
    "chisme": "  (fun content: ranking/lista graciosa IA + cultura argenta, con íconos pixel art, sin caso ni pitch)",
    "impacto": "  (confesión en 1ra persona de un error de negocio + lista de acciones con IA, fotos de fondo llamativas)",
}


def _pilares_listado() -> str:
    """Lista de pilares con emoji y label, sacada de config.PILLARS. Los que
    usan un formato distinto al caso de cliente en tercera persona se marcan
    aparte, para que quien elige sepa de entrada qué va a salir. Al final de
    cada línea van las intenciones que ese pilar puede tomar: no se eligen en
    el wizard (se sortean por pieza, ver audiencia.py), pero saberlas explica
    por qué dos piezas del mismo pilar salen tan distintas."""
    lineas = []
    for key, p in PILLARS.items():
        nota = _NOTAS_FORMATO.get(p.get("formato"), "")
        intenciones = " / ".join(INTENCIONES[i]["label"].lower() for i in intenciones_de(key))
        lineas.append(f"- {key} {p.get('emoji', '')} — {p['label']}{nota}\n    intención: {intenciones}")
    return "\n".join(lineas)


def _build_help_text() -> str:
    return (
        "Comandos:\n\n"
        "/generar — abre un wizard: primero dónde publicás (TikTok, Instagram o ambas), después "
        "formato (carrusel o video narrado), pilar, ángulo puntual, y (solo carrusel) si querés o no "
        "una foto generada por IA\n"
        "/generar [pilar] — atajo rápido: genera ya mismo un carrusel con ese pilar, ángulo y rubro al "
        "azar, sin foto, solo para TikTok (para Instagram hace falta el wizard completo)\n"
        f"{_pilares_listado()}\n"
        "- random — elige un pilar al azar (solo válido con el atajo rápido)\n\n"
        "Formato video narrado: voz real (ElevenLabs) sobre b-roll de video real (Pexels), en vez de "
        "slides estáticas. No disponible para el pilar humor. Tarda bastante más que un carrusel.\n\n"
        "Formato reel: b-roll real (Pexels) con texto en pantalla superpuesto por beat (hook, desarrollo, "
        "CTA), SIN voz generada por IA. Mismos pilares que el video narrado.\n\n"
        "Formato reel aesthetic: mismo contenido de 'Sabías que...?' (sin caso de cliente), pero en vez "
        "del carrusel cada dato sale como una tarjeta flotante arriba de UN SOLO clip de b-roll fijo "
        "(laptop, café, escritorio — look 'aesthetic' de escritorio) que se repite en todo el video, en "
        "vez de un clip distinto por beat. Fijo al pilar sabias_que, no pide elegir pilar en el wizard.\n\n"
        "Formato demo animado: demostraciones GRÁFICAS rápidas de la solución funcionando (un chat que se "
        "contesta solo, un panel de métricas que sube, una agenda que se llena, la facturación creciendo). "
        "Sin fotos ni b-roll: son interfaces animadas frame a frame, con 14 diseños distintos que la IA "
        "combina según el caso. Mismos pilares que el video narrado; tarda un par de minutos.\n\n"
        "Instagram: un carrusel se publica como carrusel de feed (4:5) + una Story con la portada; un "
        "video, como Reel + esa misma Story. El caption se reescribe aparte para Instagram (no es el "
        "mismo texto que TikTok — se muestra en un mensaje antes de aprobar). Requiere haber corrido "
        "'python instagram_auth.py' una vez; a diferencia de TikTok, la Graph API publica directo, sin "
        "pasar por el inbox de la app.\n\n"
        "/publicar — manda a aprobar la última pieza que quedó en output/, sin volver a generarla "
        "(a las plataformas que se hayan elegido al generarla)\n"
        "/pilares — lista de pilares (lo mismo que arriba)\n"
        "/metricas — seguidores, likes totales y los videos con más vistas de la cuenta (requiere haber "
        "reautorizado con los scopes user.info.stats y video.list, ver tiktok_metrics.py)\n"
        "/ayuda — este mensaje\n\n"
        "Cómo se aprueba: llega la vista previa (imágenes o video) con botones ✅ Aprobar y publicar / "
        "❌ Cancelar. Solo se publica si tocás Aprobar; con Cancelar no se publica nada. "
        "Mientras haya una pieza esperando aprobación, no se puede generar otra — aprobala o cancelala primero."
    )


HELP_TEXT = _build_help_text()

# Pieza generada esperando aprobación (una a la vez, es un bot personal de un solo uso).
_pending: dict | None = None

# Wizard de /generar en curso (plataforma -> formato -> pilar -> ángulo -> foto),
# también de a uno. Guarda el message_id del último paso para poder ignorar
# taps en botones viejos (si se reinicia el wizard) y para sacarle el teclado
# una vez usado.
_wizard: dict | None = None

# Última pieza que se mandó a publicar (aprobada), para que el botón
# "🔁 Reintentar" de una falla de subida (ver _publicar_en_tiktok/_instagram)
# pueda repetir el intento sin tener que generar ni aprobar de nuevo.
_ultima_publicacion: dict | None = None

# Los tres de arriba viven en memoria y se persisten acá (ver _guardar_estado/
# _cargar_estado): sin esto, reiniciar el bot mientras había una pieza
# esperando aprobación (o un wizard a mitad de camino) hacía que tocar un
# botón viejo en Telegram no hiciera nada — ni error ni éxito — porque el
# estado en memoria se había perdido pero el mensaje con los botones seguía
# ahí. No se commitea (es estado de corrida, no config).
STATE_PATH = Path(__file__).parent / "bot_state.json"

_ANGULO_MAX_LEN = 60
# Cuántas opciones de ángulo mostrar como botones en el wizard: es un
# subconjunto al azar del pool (angulos.py), que puede tener 40+ y no entra
# cómodo entero como botones de Telegram.
_ANGULO_OPCIONES_WIZARD = 8

# Se agrega a cada paso del wizard: sin esto, una vez que arrancabas /generar
# no había forma de abortar antes de llegar al último paso (o simplemente
# dejarlo colgado, que no rompe nada pero tampoco avisa).
_BOTON_CANCELAR = [("❌ Cancelar", "wz|cancelar|_")]


def _truncar(texto: str, n: int) -> str:
    return texto if len(texto) <= n else texto[: n - 1].rstrip() + "…"


def _serializar_pieza(pieza: dict) -> dict:
    """`_pending`/`_ultima_publicacion` guardan Path (folder, images,
    video_path), que json no serializa directo."""
    out = dict(pieza)
    out["folder"] = str(pieza["folder"])
    if "images" in out:
        out["images"] = [str(p) for p in out["images"]]
    if out.get("video_path") is not None:
        out["video_path"] = str(out["video_path"])
    return out


def _deserializar_pieza(data: dict) -> dict:
    out = dict(data)
    out["folder"] = Path(out["folder"])
    if "images" in out:
        out["images"] = [Path(p) for p in out["images"]]
    if out.get("video_path") is not None:
        out["video_path"] = Path(out["video_path"])
    return out


def _guardar_estado() -> None:
    estado = {
        "pending": _serializar_pieza(_pending) if _pending else None,
        "wizard": _wizard,
        "ultima_publicacion": _serializar_pieza(_ultima_publicacion) if _ultima_publicacion else None,
    }
    STATE_PATH.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")


def _cargar_estado() -> None:
    global _pending, _wizard, _ultima_publicacion
    if not STATE_PATH.exists():
        return
    try:
        estado = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"  (no pude leer {STATE_PATH.name}, arranco sin estado previo: {e})")
        return

    if estado.get("pending"):
        _pending = _deserializar_pieza(estado["pending"])
        print(f"  (retomando pieza pendiente de aprobación de antes del reinicio: {_pending['folder'].name})")
    if estado.get("wizard"):
        _wizard = estado["wizard"]
        print("  (retomando un wizard de /generar a mitad de camino de antes del reinicio)")
    if estado.get("ultima_publicacion"):
        _ultima_publicacion = _deserializar_pieza(estado["ultima_publicacion"])


def _iniciar_wizard() -> None:
    global _wizard
    botones = [
        [("🎵 Solo TikTok", "wz|plataforma|tiktok")],
        [("📸 Solo Instagram", "wz|plataforma|instagram")],
        [("🎵📸 Ambas", "wz|plataforma|ambas")],
        _BOTON_CANCELAR,
    ]
    message_id = telegram_client.send_choice("¿Dónde publicás esta pieza?", botones)
    _wizard = {"message_id": message_id, "plataformas": None, "formato": None, "pilar_key": None, "angulo": None}


def _guardar_plataformas(folder, plataformas: list[str]) -> None:
    """Persiste en contenido.json las plataformas elegidas en el wizard, para
    que /publicar (que retoma la última pieza generada sin recordar por qué
    canal se pidió) sepa a dónde mandarla."""
    content_path = folder / "contenido.json"
    data = json.loads(content_path.read_text(encoding="utf-8"))
    data["plataformas"] = plataformas
    content_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _lanzar_generacion(pillar_key: str, angulo: str | None, con_foto: bool,
                        plataformas: list[str] | None = None) -> None:
    if _pending is not None:
        telegram_client.send_message(
            "Ya hay una pieza esperando tu aprobación. Aprobala o cancelala antes de generar otra."
        )
        return
    plataformas = plataformas or ["tiktok"]

    pillar = PILLARS[pillar_key]
    extra = " (con foto IA)" if con_foto else ""
    telegram_client.send_message(f"Generando carrusel ({pillar['label']}){extra}...")
    try:
        folder = build_piece(pillar_key, angulo=angulo, con_foto=con_foto)
    except Exception as e:
        telegram_client.send_message(f"Falló la generación: {e}")
        return

    _guardar_plataformas(folder, plataformas)
    _enviar_a_aprobar(folder, plataformas)


def _lanzar_generacion_video(pillar_key: str, angulo: str | None, plataformas: list[str] | None = None) -> None:
    if _pending is not None:
        telegram_client.send_message(
            "Ya hay una pieza esperando tu aprobación. Aprobala o cancelala antes de generar otra."
        )
        return
    plataformas = plataformas or ["tiktok"]

    pillar = PILLARS[pillar_key]
    telegram_client.send_message(
        f"Generando video narrado ({pillar['label']})... esto tarda más que un carrusel "
        "(locución + b-roll por cada escena)."
    )
    try:
        folder = build_video_piece(pillar_key, angulo=angulo)
    except Exception as e:
        telegram_client.send_message(f"Falló la generación: {e}")
        return

    _guardar_plataformas(folder, plataformas)
    _enviar_a_aprobar(folder, plataformas)


def _lanzar_generacion_reel(pillar_key: str, angulo: str | None, plataformas: list[str] | None = None) -> None:
    if _pending is not None:
        telegram_client.send_message(
            "Ya hay una pieza esperando tu aprobación. Aprobala o cancelala antes de generar otra."
        )
        return
    plataformas = plataformas or ["tiktok"]

    pillar = PILLARS[pillar_key]
    telegram_client.send_message(
        f"Generando reel ({pillar['label']})... b-roll real + texto en pantalla, sin voz generada."
    )
    try:
        folder = build_reel_piece(pillar_key, angulo=angulo)
    except Exception as e:
        telegram_client.send_message(f"Falló la generación: {e}")
        return

    _guardar_plataformas(folder, plataformas)
    _enviar_a_aprobar(folder, plataformas)


def _lanzar_generacion_demo(pillar_key: str, angulo: str | None, plataformas: list[str] | None = None) -> None:
    if _pending is not None:
        telegram_client.send_message(
            "Ya hay una pieza esperando tu aprobación. Aprobala o cancelala antes de generar otra."
        )
        return
    plataformas = plataformas or ["tiktok"]

    pillar = PILLARS[pillar_key]
    telegram_client.send_message(
        f"Generando demo animado ({pillar['label']})... escenas gráficas de la solución "
        "funcionando. Tarda un par de minutos porque se rinde frame por frame."
    )
    try:
        folder = build_demo_piece(pillar_key, angulo=angulo)
    except Exception as e:
        telegram_client.send_message(f"Falló la generación: {e}")
        return

    _guardar_plataformas(folder, plataformas)
    _enviar_a_aprobar(folder, plataformas)


def _lanzar_generacion_tip_reel(angulo: str | None, plataformas: list[str] | None = None) -> None:
    if _pending is not None:
        telegram_client.send_message(
            "Ya hay una pieza esperando tu aprobación. Aprobala o cancelala antes de generar otra."
        )
        return
    plataformas = plataformas or ["tiktok"]

    telegram_client.send_message(
        "Generando reel aesthetic (fondo laptop+café fijo + tarjetas de 'sabías que...?')..."
    )
    try:
        folder = build_tip_reel_piece(angulo=angulo)
    except Exception as e:
        telegram_client.send_message(f"Falló la generación: {e}")
        return

    _guardar_plataformas(folder, plataformas)
    _enviar_a_aprobar(folder, plataformas)


def _handle_generar(args: list[str]) -> None:
    if _pending is not None:
        telegram_client.send_message(
            "Ya hay una pieza esperando tu aprobación. Aprobala o cancelala antes de generar otra."
        )
        return

    if not args:
        _iniciar_wizard()
        return

    pillar_key = args[0]
    if pillar_key == "random":
        pillar_key = random.choice(list(PILLARS.keys()))
    if pillar_key not in PILLARS:
        telegram_client.send_message(f"Pilar inválido: '{pillar_key}'. Usá /pilares para ver las opciones.")
        return

    _lanzar_generacion(pillar_key, angulo=None, con_foto=False)


def _enviar_a_aprobar(folder, plataformas: list[str]) -> None:
    """Manda la vista previa de `folder` (imágenes o video, según el formato
    con el que se haya generado) y la deja pendiente de aprobación. Si
    `plataformas` incluye Instagram, antes pide (y muestra) el caption nativo
    de Instagram — distinto del de TikTok, ver content_rules.SYSTEM_PROMPT_IG_CAPTION."""
    global _pending
    content = json.loads((folder / "contenido.json").read_text(encoding="utf-8"))
    hashtags = " ".join(f"#{h.lstrip('#')}" for h in content.get("hashtags", []))
    caption_tiktok = f"{content['caption']}\n\n{hashtags}".strip()
    # Piezas de antes de que existiera el formato video no tienen la clave
    # 'formato' en su contenido.json: son todas carrusel.
    formato = content.get("formato", "carrusel")

    # La ficha va aparte y no pegada al caption: el caption de este mensaje es
    # exactamente el texto que se publica en TikTok si aprobás, así que
    # meterle la intención adentro lo subiría a TikTok.
    intencion = content.get("intencion")
    if intencion in INTENCIONES:
        ficha = INTENCIONES[intencion]
        telegram_client.send_message(
            f"{ficha['emoji']} Intención: {ficha['label']} — {ficha['resumen']}\n"
            f"Ángulo: {content.get('angulo', '?')}"
        )

    caption_ig = None
    if "instagram" in plataformas:
        telegram_client.send_message("Escribiendo el caption de Instagram...")
        try:
            ig = asegurar_caption_ig(folder)
            hashtags_ig = " ".join(f"#{h.lstrip('#')}" for h in ig.get("hashtags_ig", []))
            caption_ig = f"{ig['caption_ig']}\n\n{hashtags_ig}".strip()
            telegram_client.send_message(f"📸 Caption Instagram:\n\n{caption_ig}")
        except Exception as e:
            telegram_client.send_message(
                f"No pude escribir el caption de Instagram ({e}). Sigo solo con las "
                "plataformas restantes; cancelá y reintentá si lo querés incluir."
            )
            plataformas = [p for p in plataformas if p != "instagram"]
            if not plataformas:
                telegram_client.send_message("No quedó ninguna plataforma para publicar. Nada más que hacer acá.")
                return

    pregunta = "¿Publico esto en " + " y ".join(_LABEL_PLATAFORMA[p] for p in plataformas) + "?"

    if formato in ("video", "reel", "reel_tips", "demo"):
        video_path = folder / "video.mp4"
        message_id = telegram_client.send_video_preview(video_path, caption_tiktok, pregunta=pregunta)
        # 'reel_tips' usa el contenido de 'sabías que...?' (sin caso de
        # cliente): trae 'tema' en vez de 'negocio', a diferencia de video/reel.
        _pending = {
            "message_id": message_id,
            "folder": folder,
            "formato": formato,
            "video_path": video_path,
            "title": content.get("negocio") or content.get("tema", ""),
            "caption_tiktok": caption_tiktok,
            "caption_ig": caption_ig,
            "plataformas": plataformas,
        }
        return

    images = sorted(folder.glob("[0-9][0-9]_*.png"))
    message_id = telegram_client.send_preview(images, caption_tiktok, pregunta=pregunta)
    _pending = {
        "message_id": message_id,
        "folder": folder,
        "formato": "carrusel",
        "images": images,
        "title": content["slides"][0]["titular"],
        "caption_tiktok": caption_tiktok,
        "caption_ig": caption_ig,
        "plataformas": plataformas,
    }


def _pieza_incompleta(folder, content: dict) -> str | None:
    """Devuelve un mensaje de error si a `folder` le faltan los archivos que
    su contenido.json dice que debería tener (por ejemplo, una generación que
    se cortó a mitad de camino por un error de red o de la IA de imágenes),
    o None si está completa y lista para mandar a aprobar."""
    formato = content.get("formato", "carrusel")
    if formato in ("video", "reel", "reel_tips", "demo"):
        video_path = folder / "video.mp4"
        if not video_path.exists() or video_path.stat().st_size == 0:
            return f"falta o quedó vacío {video_path.name}"
        return None

    esperadas = len(content.get("slides", []))
    encontradas = sorted(folder.glob("[0-9][0-9]_*.png"))
    if not encontradas:
        return "no hay ninguna slide renderizada"
    if esperadas and len(encontradas) != esperadas:
        return f"debería tener {esperadas} slides y solo hay {len(encontradas)}"
    return None


def _handle_publicar() -> None:
    """Manda a aprobar la última pieza ya generada y completa, sin volver a
    generarla. Si la más reciente quedó a medio generar, la saltea y sigue
    buscando hacia atrás en vez de romper al mandar la vista previa."""
    if _pending is not None:
        telegram_client.send_message(
            "Ya hay una pieza esperando tu aprobación. Aprobala o cancelala primero."
        )
        return

    output_dir = Path(__file__).parent / "output"
    carpetas = sorted((p for p in output_dir.iterdir() if p.is_dir() and (p / "contenido.json").exists()),
                      key=lambda p: p.name) if output_dir.exists() else []
    if not carpetas:
        telegram_client.send_message("No hay ninguna pieza generada en output/. Usá /generar primero.")
        return

    for folder in reversed(carpetas):
        content = json.loads((folder / "contenido.json").read_text(encoding="utf-8"))
        error = _pieza_incompleta(folder, content)
        if error is None:
            # Piezas generadas antes de que existiera Instagram (o vía el
            # atajo rápido /generar [pilar], que sigue siendo solo TikTok) no
            # tienen esta clave: default a TikTok para no cambiarles el
            # comportamiento.
            plataformas = content.get("plataformas", ["tiktok"])
            telegram_client.send_message(f"Mandando a aprobar: {folder.name}")
            _enviar_a_aprobar(folder, plataformas)
            return
        print(f"  (/publicar: salteo {folder.name}, {error})")

    telegram_client.send_message(
        "Ninguna pieza en output/ está completa (todas parecen haberse cortado a mitad de "
        "generación). Usá /generar para crear una nueva."
    )


def _handle_metricas() -> None:
    """Trae seguidores/likes totales de la cuenta y el rendimiento de lo ya
    publicado, cruzado con el pilar y el ángulo que generó cada video
    (rendimiento.py). Falla con un mensaje claro si el token todavía no tiene
    los scopes user.info.stats/video.list."""
    try:
        access_token = tiktok_client.get_access_token()
        cuenta = tiktok_metrics.get_account_stats(access_token)
        videos = rendimiento.traer(access_token)
    except Exception as e:
        telegram_client.send_message(
            f"No pude traer las métricas: {e}\n\n"
            "Si el error dice 'scope_not_authorized', hace falta habilitar 'user.info.stats' "
            "y 'video.list' en developers.tiktok.com → tu app → Login Kit → Scopes, y después "
            "correr 'python tiktok_auth.py' de nuevo para reautorizar con esos scopes."
        )
        return

    lineas = [
        f"📊 {cuenta.get('display_name', '')}",
        f"Seguidores: {cuenta.get('follower_count', '?')} · Likes totales: {cuenta.get('likes_count', '?')} · "
        f"Videos: {cuenta.get('video_count', '?')}",
        "",
        "Top 5 por vistas:",
    ]
    if not videos:
        lineas.append("(todavía no hay videos publicados en la cuenta)")
    for v in sorted(videos, key=lambda v: v.get("view_count", 0), reverse=True)[:5]:
        etiqueta = v.get("angulo") or (v.get("video_description") or "").strip().replace("\n", " ")
        pilar = PILLARS.get(v.get("pilar"), {}).get("label", "sin atribuir")
        lineas.append(
            f"- {v.get('view_count', '?')} vistas · {v.get('like_count', '?')} likes · "
            f"{v.get('comment_count', '?')} coment. · {v.get('share_count', '?')} compartidos\n"
            f"  {_truncar(etiqueta, 70)} ({pilar})"
        )

    filas = rendimiento.por_pilar(videos)
    if filas:
        atribuidos = sum(f["piezas"] for f in filas)
        lineas += ["", f"Por pilar ({atribuidos} de {len(videos)} videos cruzados con output/):"]
        for f in filas:
            lineas.append(
                f"- {PILLARS.get(f['pilar'], {}).get('emoji', '•')} {f['label']}: {f['vistas_mediana']:.0f} vistas medianas "
                f"({f['piezas']} pieza{'s' if f['piezas'] != 1 else ''}, {f['vistas_total']} en total)"
            )
    filas_int = rendimiento.por_intencion(videos)
    if filas_int:
        lineas += ["", "Por intención (para qué estaba hecha la pieza):"]
        for f in filas_int:
            lineas.append(
                f"- {f['emoji']} {f['label']}: {f['vistas_mediana']:.0f} vistas medianas "
                f"({f['piezas']} pieza{'s' if f['piezas'] != 1 else ''}, {f['vistas_total']} en total)"
            )

    if filas or filas_int:
        lineas += ["", "Los ángulos nuevos ya salen guiados por esto: python refrescar_angulos.py"]
    telegram_client.send_message("\n".join(lineas))


def _mostrar_opciones_angulo(pillar_key: str) -> bool:
    """Paso compartido del wizard: sortea una muestra de ángulos para
    `pillar_key`, la deja en _wizard y manda los botones para elegir uno.
    Usado tanto tras elegir pilar (campo 'pilar') como en el atajo de
    'reel_tips' (campo 'formato'), que se salta la pantalla de pilar porque
    está fijo a 'sabias_que'. Devuelve False (y avisa por Telegram) si el
    pilar todavía no tiene ángulos generados — el caller decide qué hacer con
    el wizard en ese caso (cerrarlo)."""
    pillar = PILLARS[pillar_key]
    _wizard["pilar_key"] = pillar_key

    opciones = angulos.muestra(pillar_key, _ANGULO_OPCIONES_WIZARD)
    if not opciones:
        telegram_client.send_message(
            f"Todavía no hay ángulos generados para '{pillar['label']}'. "
            f"Corré: python refrescar_angulos.py {pillar_key}"
        )
        return False

    _wizard["angulo_opciones"] = opciones
    botones = [
        [(f"{i + 1}. {_truncar(a, _ANGULO_MAX_LEN)}", f"wz|angulo|{i}")]
        for i, a in enumerate(opciones)
    ]
    botones.append([("🎲 Cualquiera", "wz|angulo|random")])
    botones.append(_BOTON_CANCELAR)
    _wizard["message_id"] = telegram_client.send_choice(f"Pilar: {pillar['label']}. ¿Qué ángulo?", botones)
    return True


def _handle_wizard_callback(cq: dict) -> None:
    global _wizard
    telegram_client.answer_callback(cq["id"])

    if _wizard is None or cq.get("message", {}).get("message_id") != _wizard["message_id"]:
        return
    telegram_client.clear_keyboard(_wizard["message_id"])

    _, campo, valor = cq["data"].split("|", 2)

    if campo == "cancelar":
        _wizard = None
        telegram_client.send_message("Wizard cancelado.")
        return

    if campo == "plataforma":
        _wizard["plataformas"] = ["tiktok", "instagram"] if valor == "ambas" else [valor]
        botones = [
            [("🖼️ Carrusel de imágenes", "wz|formato|carrusel")],
            [("🎬 Video narrado (voz + b-roll)", "wz|formato|video")],
            [("📱 Reel (texto en pantalla, sin voz)", "wz|formato|reel")],
            [("🎨 Reel aesthetic (fondo laptop+café + tarjetas)", "wz|formato|reel_tips")],
            [("⚡ Demo animado (gráficos del producto andando)", "wz|formato|demo")],
            _BOTON_CANCELAR,
        ]
        _wizard["message_id"] = telegram_client.send_choice("¿Qué formato querés generar?", botones)
        return

    if campo == "formato":
        _wizard["formato"] = valor
        if valor == "reel_tips":
            # Fijo al pilar 'sabias_que' (el único cuyo contenido, un dato o
            # consejo suelto sin caso de cliente, calza con una tarjeta
            # individual): no tiene sentido preguntar el pilar acá.
            _mostrar_opciones_angulo("sabias_que")
            return
        pilares = PILARES_VIDEO if valor in ("video", "reel", "demo") else list(PILLARS.keys())
        botones = [
            [(f"{PILLARS[key].get('emoji', '')} {PILLARS[key]['label']}".strip(), f"wz|pilar|{key}")]
            for key in pilares
        ]
        botones.append([("🎲 Sorpréndeme", "wz|pilar|random")])
        botones.append(_BOTON_CANCELAR)
        _wizard["message_id"] = telegram_client.send_choice("¿Qué querés generar?", botones)
        return

    if campo == "pilar":
        pilares = PILARES_VIDEO if _wizard["formato"] in ("video", "reel", "demo") else list(PILLARS.keys())
        pillar_key = random.choice(pilares) if valor == "random" else valor
        if not _mostrar_opciones_angulo(pillar_key):
            _wizard = None
        return

    if campo == "angulo":
        pillar = PILLARS[_wizard["pilar_key"]]
        angulo = angulos.elegir_angulo(_wizard["pilar_key"]) if valor == "random" else _wizard["angulo_opciones"][int(valor)]

        if _wizard["formato"] == "video":
            pillar_key = _wizard["pilar_key"]
            plataformas = _wizard["plataformas"]
            _wizard = None
            _lanzar_generacion_video(pillar_key, angulo, plataformas)
            return

        if _wizard["formato"] == "reel":
            pillar_key = _wizard["pilar_key"]
            plataformas = _wizard["plataformas"]
            _wizard = None
            _lanzar_generacion_reel(pillar_key, angulo, plataformas)
            return

        if _wizard["formato"] == "demo":
            pillar_key = _wizard["pilar_key"]
            plataformas = _wizard["plataformas"]
            _wizard = None
            _lanzar_generacion_demo(pillar_key, angulo, plataformas)
            return

        if _wizard["formato"] == "reel_tips":
            plataformas = _wizard["plataformas"]
            _wizard = None
            _lanzar_generacion_tip_reel(angulo, plataformas)
            return

        if pillar.get("formato") in ("chisme", "impacto"):
            # Los íconos pixel art (chisme) y las fotos de fondo (impacto) no
            # son opcionales acá (a diferencia de la slide 'foto' del formato
            # caso/humor/sabías que), así que no tiene sentido preguntar
            # "¿incluir foto IA?": se genera directo.
            pillar_key = _wizard["pilar_key"]
            plataformas = _wizard["plataformas"]
            _wizard = None
            _lanzar_generacion(pillar_key, angulo, con_foto=False, plataformas=plataformas)
            return

        _wizard["angulo"] = angulo
        botones = [[("✅ Sí", "wz|foto|si"), ("🚫 No", "wz|foto|no")], _BOTON_CANCELAR]
        _wizard["message_id"] = telegram_client.send_choice(
            "¿Incluir una foto generada por IA en alguna slide? "
            "(gratis, pero la calidad es despareja)",
            botones,
        )
        return

    if campo == "foto":
        pillar_key = _wizard["pilar_key"]
        angulo = _wizard["angulo"]
        con_foto = valor == "si"
        plataformas = _wizard["plataformas"]
        _wizard = None
        _lanzar_generacion(pillar_key, angulo, con_foto, plataformas)
        return


def _handle_callback(cq: dict) -> None:
    global _pending, _ultima_publicacion

    data = cq.get("data", "")
    if data.startswith("wz|"):
        _handle_wizard_callback(cq)
        return

    if data.startswith("retry|"):
        _handle_retry_callback(cq)
        return

    if _pending is None or cq.get("message", {}).get("message_id") != _pending["message_id"]:
        telegram_client.answer_callback(cq["id"])
        return

    telegram_client.answer_callback(cq["id"])
    telegram_client.clear_keyboard(_pending["message_id"])
    approved = cq["data"] == "approve"
    pending, _pending = _pending, None

    if not approved:
        telegram_client.send_message("Cancelado, no se publica nada.")
        return

    es_video = pending.get("formato") in ("video", "reel", "reel_tips", "demo")
    plataformas = pending.get("plataformas", ["tiktok"])
    # Se guarda para que el botón "🔁 Reintentar" de una falla de subida
    # pueda repetir el intento sin generar ni aprobar de nuevo.
    _ultima_publicacion = pending

    # Cada plataforma se intenta de forma independiente: que falle TikTok no
    # tiene que frenar Instagram, ni al revés (son APIs separadas, con
    # motivos de falla separados).
    if "tiktok" in plataformas:
        _publicar_en_tiktok(pending, es_video)
    if "instagram" in plataformas:
        _publicar_en_instagram(pending, es_video)


def _handle_retry_callback(cq: dict) -> None:
    """Callback del botón "🔁 Reintentar" que se cuelga de un mensaje de falla
    (ver _publicar_en_tiktok/_publicar_en_instagram). Reintenta SOLO esa
    plataforma, reusando _ultima_publicacion en vez de pedir generar o
    aprobar de nuevo."""
    telegram_client.answer_callback(cq["id"])
    message_id = cq.get("message", {}).get("message_id")
    if message_id is not None:
        telegram_client.clear_keyboard(message_id)

    if _ultima_publicacion is None:
        telegram_client.send_message(
            "No tengo nada guardado para reintentar (¿se reinició el bot hace mucho después de la "
            "falla?). Usá /publicar para retomar la última pieza generada."
        )
        return

    _, plataforma = cq["data"].split("|", 1)
    es_video = _ultima_publicacion.get("formato") in ("video", "reel", "reel_tips", "demo")
    if plataforma == "tiktok":
        _publicar_en_tiktok(_ultima_publicacion, es_video)
    elif plataforma == "instagram":
        _publicar_en_instagram(_ultima_publicacion, es_video)


def _publicar_en_tiktok(pending: dict, es_video: bool) -> None:
    telegram_client.send_message(
        "Subiendo el video a TikTok..." if es_video else
        "Alojando las imágenes y subiendo a TikTok..."
    )
    try:
        access_token = tiktok_client.get_access_token()
        if es_video:
            publish_id = tiktok_client.upload_video_to_inbox(pending["video_path"], access_token)
        else:
            image_urls = content_hosting.publish_images(pending["images"])
            publish_id = tiktok_client.post_photos_to_inbox(
                image_urls, pending["title"], pending["caption_tiktok"], access_token
            )
        status = tiktok_client.wait_for_publish(publish_id, access_token)
    except Exception as e:
        telegram_client.send_choice(
            f"Falló la subida a TikTok: {e}", [[("🔁 Reintentar en TikTok", "retry|tiktok")]]
        )
        return

    if status == "SEND_TO_USER_INBOX":
        que = "El video" if es_video else "El carrusel de fotos"
        telegram_client.send_message(
            f"{que} se envió al inbox de TikTok, con caption y descripción ya cargados. "
            "Abrí la app y tocá 'Publicar' para terminarlo."
        )
    elif status == "PUBLISH_COMPLETE":
        telegram_client.send_message("Publicado en TikTok.")
    else:
        telegram_client.send_choice(
            f"TikTok, estado final: {status}", [[("🔁 Reintentar en TikTok", "retry|tiktok")]]
        )


def _publicar_en_instagram(pending: dict, es_video: bool) -> None:
    """A diferencia de TikTok, la Graph API de Instagram no tiene modo
    borrador: esto publica directo. Un carrusel sube como carrusel de feed
    (4:5, ver instagram_render.build_feed_images) + una Story con la
    portada; un video sube como Reel + esa misma Story."""
    telegram_client.send_message("Subiendo a Instagram...")
    caption_ig = pending.get("caption_ig") or pending["caption_tiktok"]
    try:
        if es_video:
            video_url = content_hosting.publish_video(pending["video_path"])
            instagram_client.publish_reel(video_url, caption_ig)
            instagram_client.publish_story_video(video_url)
        else:
            content = json.loads((pending["folder"] / "contenido.json").read_text(encoding="utf-8"))
            feed_images = instagram_render.build_feed_images(pending["folder"], content.get("paleta", ""))
            feed_urls = content_hosting.publish_images(feed_images)
            instagram_client.publish_feed_carousel(feed_urls, caption_ig)
            story_path = instagram_render.story_image(pending["folder"])
            story_url = content_hosting.publish_images([story_path])[0]
            instagram_client.publish_story_image(story_url)
    except Exception as e:
        telegram_client.send_choice(
            f"Falló la subida a Instagram: {e}", [[("🔁 Reintentar en Instagram", "retry|instagram")]]
        )
        return

    telegram_client.send_message(
        "Publicado en Instagram (Reel + Story)." if es_video else
        "Publicado en Instagram (carrusel de feed + Story)."
    )


def _handle_message(message: dict) -> None:
    text = message.get("text", "").strip()
    if text.startswith("/publicar"):
        _handle_publicar()
    elif text.startswith("/generar"):
        _handle_generar(text.split()[1:])
    elif text.startswith("/pilares"):
        telegram_client.send_message(_pilares_listado())
    elif text.startswith("/metricas"):
        _handle_metricas()
    elif text.startswith("/ayuda") or text.startswith("/start"):
        telegram_client.send_message(HELP_TEXT)


def main() -> None:
    if not ALLOWED_CHAT_ID:
        raise SystemExit("Falta TELEGRAM_CHAT_ID en tu .env.")

    _cargar_estado()
    print("Bot corriendo. Mandale /ayuda al bot de Telegram para ver los comandos. Ctrl+C para frenar.")
    offset = None

    while True:
        try:
            updates = telegram_client.get_updates(offset, timeout=25)
        except requests.exceptions.ReadTimeout:
            # Un long polling que vence sin que Telegram conteste no es un
            # error: pasa seguido con una conexión hogareña y llenaba el log
            # de "Read timed out" cada 35 segundos. Como el offset no avanzó,
            # cualquier update pendiente se vuelve a mandar en el próximo
            # intento — se reintenta al toque y sin ruido.
            continue
        except Exception as e:
            print(f"Error consultando Telegram: {e}, reintentando en 5s...")
            time.sleep(5)
            continue

        for update in updates:
            offset = update["update_id"] + 1

            chat_id = None
            if "message" in update:
                chat_id = str(update["message"]["chat"]["id"])
            elif "callback_query" in update:
                chat_id = str(update["callback_query"]["message"]["chat"]["id"])

            if chat_id != ALLOWED_CHAT_ID:
                continue

            try:
                if "message" in update and "text" in update["message"]:
                    _handle_message(update["message"])
                elif "callback_query" in update:
                    _handle_callback(update["callback_query"])
            except Exception:
                traceback.print_exc()
                telegram_client.send_message("Ocurrió un error inesperado, revisá la consola del bot.")
            finally:
                # Punto único de persistencia: cubre cualquier cambio a
                # _pending/_wizard/_ultima_publicacion que haya hecho el
                # handler de arriba, se haya colgado en una excepción o no.
                _guardar_estado()


if __name__ == "__main__":
    main()
