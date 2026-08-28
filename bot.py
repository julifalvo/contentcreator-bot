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
elegir el formato (carrusel de imágenes o video narrado con voz de ElevenLabs
+ b-roll de Pexels), el pilar, el ángulo puntual, y — solo para carrusel — si
la pieza incluye o no una foto generada por IA (Pollinations.ai: gratis pero
de calidad pareja, así que es opt-in en vez de automático). El formato video
no está disponible para el pilar humor todavía.

El texto completo de /ayuda (y la lista de /pilares) se arma solo a partir de
config.PILLARS, así que no hace falta tocar este archivo cuando se agrega o
saca un pilar.

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

from dotenv import load_dotenv

load_dotenv()

import angulos
import content_hosting
import rendimiento
import telegram_client
import tiktok_client
import tiktok_metrics
from config import PILLARS
from generate import PILARES_VIDEO, build_piece, build_video_piece

ALLOWED_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


_NOTAS_FORMATO = {
    "humor": "  (formato humor: situación graciosa en 2da persona, no un caso)",
    "sabias_que": "  (formato educativo: dato o concepto, sin caso ni solución puntual)",
    "chisme": "  (fun content: ranking/lista graciosa IA + cultura argenta, con íconos pixel art, sin caso ni pitch)",
}


def _pilares_listado() -> str:
    """Lista de pilares con emoji y label, sacada de config.PILLARS. Los que
    usan un formato distinto al caso de cliente en tercera persona se marcan
    aparte, para que quien elige sepa de entrada qué va a salir."""
    lineas = []
    for key, p in PILLARS.items():
        nota = _NOTAS_FORMATO.get(p.get("formato"), "")
        lineas.append(f"- {key} {p.get('emoji', '')} — {p['label']}{nota}")
    return "\n".join(lineas)


def _build_help_text() -> str:
    return (
        "Comandos:\n\n"
        "/generar — abre un wizard: elegís formato (carrusel o video narrado), después pilar, "
        "después ángulo puntual, y (solo carrusel) si querés o no una foto generada por IA\n"
        "/generar [pilar] — atajo rápido: genera ya mismo un carrusel con ese pilar, ángulo y rubro al azar, sin foto\n"
        f"{_pilares_listado()}\n"
        "- random — elige un pilar al azar (solo válido con el atajo rápido)\n\n"
        "Formato video narrado: voz real (ElevenLabs) sobre b-roll de video real (Pexels), en vez de "
        "slides estáticas. No disponible para el pilar humor. Tarda bastante más que un carrusel.\n\n"
        "/publicar — manda a aprobar la última pieza que quedó en output/, sin volver a generarla\n"
        "/pilares — lista de pilares (lo mismo que arriba)\n"
        "/metricas — seguidores, likes totales y los videos con más vistas de la cuenta (requiere haber "
        "reautorizado con los scopes user.info.stats y video.list, ver tiktok_metrics.py)\n"
        "/ayuda — este mensaje\n\n"
        "Cómo se aprueba: llega la vista previa (imágenes o video) con botones ✅ Aprobar y publicar / "
        "❌ Cancelar. Solo se sube a TikTok si tocás Aprobar; con Cancelar no se publica nada. "
        "Mientras haya una pieza esperando aprobación, no se puede generar otra — aprobala o cancelala primero."
    )


HELP_TEXT = _build_help_text()

# Pieza generada esperando aprobación (una a la vez, es un bot personal de un solo uso).
_pending: dict | None = None

# Wizard de /generar en curso (pilar -> ángulo -> foto), también de a uno.
# Guarda el message_id del último paso para poder ignorar taps en botones
# viejos (si se reinicia el wizard) y para sacarle el teclado una vez usado.
_wizard: dict | None = None

_ANGULO_MAX_LEN = 60
# Cuántas opciones de ángulo mostrar como botones en el wizard: es un
# subconjunto al azar del pool (angulos.py), que puede tener 40+ y no entra
# cómodo entero como botones de Telegram.
_ANGULO_OPCIONES_WIZARD = 8


def _truncar(texto: str, n: int) -> str:
    return texto if len(texto) <= n else texto[: n - 1].rstrip() + "…"


def _iniciar_wizard() -> None:
    global _wizard
    botones = [
        [("🖼️ Carrusel de imágenes", "wz|formato|carrusel")],
        [("🎬 Video narrado (voz + b-roll)", "wz|formato|video")],
    ]
    message_id = telegram_client.send_choice("¿Qué formato querés generar?", botones)
    _wizard = {"message_id": message_id, "formato": None, "pilar_key": None, "angulo": None}


def _lanzar_generacion(pillar_key: str, angulo: str | None, con_foto: bool) -> None:
    if _pending is not None:
        telegram_client.send_message(
            "Ya hay una pieza esperando tu aprobación. Aprobala o cancelala antes de generar otra."
        )
        return

    pillar = PILLARS[pillar_key]
    extra = " (con foto IA)" if con_foto else ""
    telegram_client.send_message(f"Generando carrusel ({pillar['label']}){extra}...")
    try:
        folder = build_piece(pillar_key, angulo=angulo, con_foto=con_foto)
    except Exception as e:
        telegram_client.send_message(f"Falló la generación: {e}")
        return

    _enviar_a_aprobar(folder)


def _lanzar_generacion_video(pillar_key: str, angulo: str | None) -> None:
    if _pending is not None:
        telegram_client.send_message(
            "Ya hay una pieza esperando tu aprobación. Aprobala o cancelala antes de generar otra."
        )
        return

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

    _enviar_a_aprobar(folder)


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


def _enviar_a_aprobar(folder) -> None:
    """Manda la vista previa de `folder` (imágenes o video, según el formato
    con el que se haya generado) y la deja pendiente de aprobación."""
    global _pending
    content = json.loads((folder / "contenido.json").read_text(encoding="utf-8"))
    hashtags = " ".join(f"#{h.lstrip('#')}" for h in content.get("hashtags", []))
    caption = f"{content['caption']}\n\n{hashtags}".strip()
    # Piezas de antes de que existiera el formato video no tienen la clave
    # 'formato' en su contenido.json: son todas carrusel.
    formato = content.get("formato", "carrusel")

    if formato == "video":
        video_path = folder / "video.mp4"
        message_id = telegram_client.send_video_preview(video_path, caption)
        _pending = {
            "message_id": message_id,
            "folder": folder,
            "formato": "video",
            "video_path": video_path,
            "title": content["negocio"],
            "caption": caption,
        }
        return

    images = sorted(folder.glob("[0-9][0-9]_*.png"))
    message_id = telegram_client.send_preview(images, caption)
    _pending = {
        "message_id": message_id,
        "folder": folder,
        "formato": "carrusel",
        "images": images,
        "title": content["slides"][0]["titular"],
        "caption": caption,
    }


def _handle_publicar() -> None:
    """Manda a aprobar la última pieza ya generada, sin volver a generarla."""
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

    folder = carpetas[-1]
    telegram_client.send_message(f"Mandando a aprobar: {folder.name}")
    _enviar_a_aprobar(folder)


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
        lineas += ["", "Los ángulos nuevos ya salen guiados por esto: python refrescar_angulos.py"]
    telegram_client.send_message("\n".join(lineas))


def _handle_wizard_callback(cq: dict) -> None:
    global _wizard
    telegram_client.answer_callback(cq["id"])

    if _wizard is None or cq.get("message", {}).get("message_id") != _wizard["message_id"]:
        return
    telegram_client.clear_keyboard(_wizard["message_id"])

    _, campo, valor = cq["data"].split("|", 2)

    if campo == "formato":
        _wizard["formato"] = valor
        pilares = PILARES_VIDEO if valor == "video" else list(PILLARS.keys())
        botones = [
            [(f"{PILLARS[key].get('emoji', '')} {PILLARS[key]['label']}".strip(), f"wz|pilar|{key}")]
            for key in pilares
        ]
        botones.append([("🎲 Sorpréndeme", "wz|pilar|random")])
        _wizard["message_id"] = telegram_client.send_choice("¿Qué querés generar?", botones)
        return

    if campo == "pilar":
        pilares = PILARES_VIDEO if _wizard["formato"] == "video" else list(PILLARS.keys())
        if valor == "random":
            pillar_key = random.choice(pilares)
        else:
            pillar_key = valor
        pillar = PILLARS[pillar_key]
        _wizard["pilar_key"] = pillar_key

        opciones = angulos.muestra(pillar_key, _ANGULO_OPCIONES_WIZARD)
        if not opciones:
            telegram_client.send_message(
                f"Todavía no hay ángulos generados para '{pillar['label']}'. "
                f"Corré: python refrescar_angulos.py {pillar_key}"
            )
            _wizard = None
            return

        _wizard["angulo_opciones"] = opciones
        botones = [
            [(f"{i + 1}. {_truncar(a, _ANGULO_MAX_LEN)}", f"wz|angulo|{i}")]
            for i, a in enumerate(opciones)
        ]
        botones.append([("🎲 Cualquiera", "wz|angulo|random")])
        _wizard["message_id"] = telegram_client.send_choice(f"Pilar: {pillar['label']}. ¿Qué ángulo?", botones)
        return

    if campo == "angulo":
        pillar = PILLARS[_wizard["pilar_key"]]
        angulo = angulos.elegir_angulo(_wizard["pilar_key"]) if valor == "random" else _wizard["angulo_opciones"][int(valor)]

        if _wizard["formato"] == "video":
            pillar_key = _wizard["pilar_key"]
            _wizard = None
            _lanzar_generacion_video(pillar_key, angulo)
            return

        if pillar.get("formato") == "chisme":
            # Los íconos pixel art no son opcionales acá (a diferencia de la
            # slide 'foto' del formato caso/humor/sabías que), así que no
            # tiene sentido preguntar "¿incluir foto IA?": se genera directo.
            pillar_key = _wizard["pilar_key"]
            _wizard = None
            _lanzar_generacion(pillar_key, angulo, con_foto=False)
            return

        _wizard["angulo"] = angulo
        botones = [[("✅ Sí", "wz|foto|si"), ("🚫 No", "wz|foto|no")]]
        _wizard["message_id"] = telegram_client.send_choice(
            "¿Incluir una foto generada por IA en alguna slide? "
            "(Pollinations.ai, gratis, pero la calidad es despareja)",
            botones,
        )
        return

    if campo == "foto":
        pillar_key = _wizard["pilar_key"]
        angulo = _wizard["angulo"]
        con_foto = valor == "si"
        _wizard = None
        _lanzar_generacion(pillar_key, angulo, con_foto)
        return


def _handle_callback(cq: dict) -> None:
    global _pending

    if cq.get("data", "").startswith("wz|"):
        _handle_wizard_callback(cq)
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

    es_video = pending.get("formato") == "video"
    telegram_client.send_message(
        "Aprobado. Subiendo el video a TikTok..." if es_video else
        "Aprobado. Alojando las imágenes y subiendo a TikTok..."
    )
    try:
        access_token = tiktok_client.get_access_token()
        if es_video:
            publish_id = tiktok_client.upload_video_to_inbox(pending["video_path"], access_token)
        else:
            image_urls = content_hosting.publish_images(pending["images"])
            publish_id = tiktok_client.post_photos_to_inbox(image_urls, pending["title"], pending["caption"], access_token)
        status = tiktok_client.wait_for_publish(publish_id, access_token)
    except Exception as e:
        telegram_client.send_message(f"Falló la subida a TikTok: {e}")
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
        telegram_client.send_message(f"Estado final: {status}")


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

    print("Bot corriendo. Mandale /ayuda al bot de Telegram para ver los comandos. Ctrl+C para frenar.")
    offset = None

    while True:
        try:
            updates = telegram_client.get_updates(offset, timeout=25)
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


if __name__ == "__main__":
    main()
