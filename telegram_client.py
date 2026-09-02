"""Cliente mínimo de la Bot API de Telegram (HTTP directo, sin librerías extra)
para mandar la vista previa de una pieza y esperar la aprobación manual antes
de publicar. Gratis, sin API key más allá del token del bot que crea @BotFather.
"""

import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE = "https://api.telegram.org/bot{token}/{method}"


def _token() -> str:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "Falta TELEGRAM_BOT_TOKEN en tu .env. Creá un bot hablándole a "
            "@BotFather en Telegram (/newbot) y copiá el token que te da."
        )
    return token


def _chat_id() -> str:
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not chat_id:
        raise RuntimeError(
            "Falta TELEGRAM_CHAT_ID en tu .env. Mandale cualquier mensaje a tu bot "
            "y después entrá a https://api.telegram.org/bot<TOKEN>/getUpdates "
            "para ver tu chat id."
        )
    return chat_id


def _call(method: str, **kwargs) -> dict:
    url = API_BASE.format(token=_token(), method=method)
    # sendMediaGroup sube varias imágenes en un solo POST multipart; con una
    # conexión de subida lenta, 30s no siempre alcanza y corta a mitad de
    # envío. 120s da margen real sin bloquear el resto del bot (no hay nada
    # más corriendo en paralelo mientras se manda la vista previa).
    #
    # Un corte de conexión (ConnectionResetError, wifi que titubea, etc.) es
    # transitorio y reintentar casi siempre alcanza. Con archivos (fotos/
    # video) el reintento es seguro porque son archivos reales en disco, no
    # streams de un solo uso: rebobinarlos (seek(0)) antes de cada intento
    # alcanza para que 'requests' los vuelva a leer desde el principio en
    # vez de mandar algo corrupto/vacío.
    archivos = kwargs.get("files")
    intentos = 3
    ultimo_error: Exception | None = None
    for intento in range(1, intentos + 1):
        if archivos and intento > 1:
            for _, fh, *_resto in archivos.values():
                fh.seek(0)
        try:
            resp = requests.post(url, timeout=120, **kwargs)
            resp.raise_for_status()
            data = resp.json()
            if not data.get("ok"):
                raise RuntimeError(f"Telegram API error en {method}: {data}")
            return data["result"]
        except requests.exceptions.ConnectionError as e:
            ultimo_error = e
            if intento < intentos:
                print(f"  (Telegram: corte de conexión en {method}, reintento {intento}/{intentos - 1} en 3s...)")
                time.sleep(3)
    raise RuntimeError(f"Telegram sin conexión tras {intentos} intento(s) en {method}: {ultimo_error}")


def send_message(text: str) -> None:
    """Manda un mensaje de texto simple (ej: el caption listo para copiar y pegar)."""
    _call("sendMessage", data={"chat_id": _chat_id(), "text": text})


def _mandar_botones_aprobar(pregunta: str) -> int:
    """El mensaje con Aprobar/Cancelar que sigue a la vista previa (imágenes o
    video). Devuelve el message_id, para identificar la respuesta después."""
    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ Aprobar y publicar", "callback_data": "approve"},
            {"text": "❌ Cancelar", "callback_data": "cancel"},
        ]]
    }
    result = _call(
        "sendMessage",
        data={
            "chat_id": _chat_id(),
            "text": pregunta,
            "reply_markup": json.dumps(keyboard),
        },
    )
    return result["message_id"]


def send_preview(images: list[Path], caption: str, pregunta: str = "¿Publico esto en TikTok?") -> int:
    """Manda las imágenes como álbum y un mensaje con botones Aprobar/Cancelar.

    Se mandan como 'document' en vez de 'photo': Telegram recomprime a JPEG
    (con su propio nivel de calidad) todo lo que llega como 'photo' en un
    álbum, lo que se nota como pérdida de nitidez en el texto. Como
    'document' viaja el archivo tal cual, byte a byte, y Telegram igual lo
    muestra como miniatura de imagen dentro del álbum.

    Devuelve el message_id del mensaje con los botones, para poder identificar
    la respuesta en wait_for_approval().
    """
    chat_id = _chat_id()

    if images:
        media = []
        files = {}
        open_files = []
        for i, img in enumerate(images[:10]):  # Telegram permite hasta 10 archivos por álbum
            key = f"photo{i}"
            fh = img.open("rb")
            open_files.append(fh)
            files[key] = (img.name, fh, "image/png")
            item = {"type": "document", "media": f"attach://{key}"}
            if i == 0:
                item["caption"] = caption[:1024]
            media.append(item)
        try:
            _call("sendMediaGroup", data={"chat_id": chat_id, "media": json.dumps(media)}, files=files)
        finally:
            for fh in open_files:
                fh.close()

    return _mandar_botones_aprobar(pregunta)


def send_video_preview(video_path: Path, caption: str, pregunta: str = "¿Publico esto en TikTok?") -> int:
    """Manda el video narrado como vista previa y el mensaje con botones
    Aprobar/Cancelar. Igual que send_preview() pero para el formato de video
    (un solo archivo en vez de álbum de fotos)."""
    with video_path.open("rb") as fh:
        _call(
            "sendVideo",
            data={"chat_id": _chat_id(), "caption": caption[:1024]},
            files={"video": (video_path.name, fh, "video/mp4")},
        )

    return _mandar_botones_aprobar(pregunta)


def send_choice(text: str, rows: list[list[tuple[str, str]]]) -> int:
    """Manda un mensaje con un teclado inline arbitrario, para flujos de
    elección paso a paso (ver el wizard de /generar en bot.py). `rows` es una
    lista de filas, cada fila una lista de (texto_del_botón, callback_data).
    Devuelve el message_id, para poder identificar la respuesta y limpiar el
    teclado después con clear_keyboard()."""
    keyboard = {
        "inline_keyboard": [
            [{"text": label, "callback_data": data} for label, data in row]
            for row in rows
        ]
    }
    result = _call(
        "sendMessage",
        data={"chat_id": _chat_id(), "text": text, "reply_markup": json.dumps(keyboard)},
    )
    return result["message_id"]


def get_updates(offset: int | None = None, timeout: int = 25) -> list[dict]:
    """Long polling crudo sobre getUpdates. Para uso en un loop propio (ver bot.py)."""
    params = {"timeout": timeout}
    if offset is not None:
        params["offset"] = offset
    resp = requests.get(
        API_BASE.format(token=_token(), method="getUpdates"), params=params, timeout=timeout + 10
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API error en getUpdates: {data}")
    return data["result"]


def answer_callback(callback_query_id: str) -> None:
    """Confirma el tap a Telegram (saca el 'cargando...' del botón). No es
    crítico: Telegram rechaza con 400 si el callback ya venció (mensaje
    viejo, doble tap, etc.), y eso NO puede tirar abajo el procesamiento real
    del click — mejor perder el spinner que perder el /generar o el aprobar."""
    try:
        _call("answerCallbackQuery", data={"callback_query_id": callback_query_id})
    except requests.exceptions.RequestException as e:
        print(f"  (no se pudo confirmar el callback a Telegram, sigo igual: {e})")


def clear_keyboard(message_id: int) -> None:
    """Saca los botones de un mensaje (para que no se pueda volver a tocar Aprobar/Cancelar
    o un paso viejo del wizard). Tampoco es crítico: un doble tap o un mensaje
    ya editado hacen que Telegram conteste 400 ('message is not modified' o
    similar) — no tiene sentido que eso crashee el procesamiento del click."""
    try:
        _call(
            "editMessageReplyMarkup",
            data={"chat_id": _chat_id(), "message_id": message_id, "reply_markup": "{}"},
        )
    except requests.exceptions.RequestException as e:
        print(f"  (no se pudo limpiar el teclado del mensaje {message_id}, sigo igual: {e})")


def wait_for_approval(message_id: int, timeout_sec: int = 7200) -> bool:
    """Long polling sobre getUpdates hasta que llegue un click en `message_id`."""
    token = _token()
    offset = None
    deadline = time.time() + timeout_sec
    print(f"  Esperando tu respuesta en Telegram (hasta {timeout_sec // 60} min)...")

    while time.time() < deadline:
        params = {"timeout": 25}
        if offset is not None:
            params["offset"] = offset
        # Un corte de red pasajero no puede tirar abajo toda la espera: se
        # reintenta hasta que venza el plazo.
        try:
            resp = requests.get(API_BASE.format(token=token, method="getUpdates"), params=params, timeout=40)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.RequestException as e:
            print(f"  (problema de red con Telegram: {e}; reintento en 5s)")
            time.sleep(5)
            continue
        for update in data.get("result", []):
            offset = update["update_id"] + 1
            cq = update.get("callback_query")
            if cq and cq.get("message", {}).get("message_id") == message_id:
                approved = cq["data"] == "approve"
                _call("answerCallbackQuery", data={"callback_query_id": cq["id"]})
                _call(
                    "editMessageReplyMarkup",
                    data={"chat_id": _chat_id(), "message_id": message_id, "reply_markup": "{}"},
                )
                return approved

    raise TimeoutError("No hubo respuesta en Telegram a tiempo.")
