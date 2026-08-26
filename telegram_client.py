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
    resp = requests.post(url, timeout=30, **kwargs)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API error en {method}: {data}")
    return data["result"]


def send_message(text: str) -> None:
    """Manda un mensaje de texto simple (ej: el caption listo para copiar y pegar)."""
    _call("sendMessage", data={"chat_id": _chat_id(), "text": text})


def send_preview(images: list[Path], caption: str) -> int:
    """Manda las imágenes como álbum y un mensaje con botones Aprobar/Cancelar.

    Devuelve el message_id del mensaje con los botones, para poder identificar
    la respuesta en wait_for_approval().
    """
    chat_id = _chat_id()

    if images:
        media = []
        files = {}
        open_files = []
        for i, img in enumerate(images[:10]):  # Telegram permite hasta 10 fotos por álbum
            key = f"photo{i}"
            fh = img.open("rb")
            open_files.append(fh)
            files[key] = (img.name, fh, "image/png")
            item = {"type": "photo", "media": f"attach://{key}"}
            if i == 0:
                item["caption"] = caption[:1024]
            media.append(item)
        try:
            _call("sendMediaGroup", data={"chat_id": chat_id, "media": json.dumps(media)}, files=files)
        finally:
            for fh in open_files:
                fh.close()

    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ Aprobar y publicar", "callback_data": "approve"},
            {"text": "❌ Cancelar", "callback_data": "cancel"},
        ]]
    }
    result = _call(
        "sendMessage",
        data={
            "chat_id": chat_id,
            "text": "¿Publico esto en TikTok?",
            "reply_markup": json.dumps(keyboard),
        },
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
    _call("answerCallbackQuery", data={"callback_query_id": callback_query_id})


def clear_keyboard(message_id: int) -> None:
    """Saca los botones de un mensaje (para que no se pueda volver a tocar Aprobar/Cancelar)."""
    _call(
        "editMessageReplyMarkup",
        data={"chat_id": _chat_id(), "message_id": message_id, "reply_markup": "{}"},
    )


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
