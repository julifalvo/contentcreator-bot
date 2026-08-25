"""Bot de Telegram que corre todo el pipeline (generar -> vista previa -> aprobar ->
publicar) a demanda, sin tocar la terminal. Es el mismo bot que ya usás para las
aprobaciones — ahora también entiende comandos.

Dejalo corriendo (python bot.py) y desde el chat de Telegram mandale:

    /generar                                pieza al azar, modo gratis
    /generar automatizacion                 pilar puntual, modo gratis
    /generar automatizacion ollama          pilar + modo (gratis / ollama / ia)
    /generar automatizacion ollama siempre  + fuerza foto real en los mockups (auto/siempre/nunca)
    /pilares                                lista los pilares disponibles
    /ayuda                                  este mensaje

Solo responde al chat configurado en TELEGRAM_CHAT_ID; cualquier otro chat se
ignora (por si alguien más le escribe al bot).
"""

import json
import os
import random
import sys
import time
import traceback

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv

load_dotenv()

import content_hosting
import telegram_client
import tiktok_client
from config import PILLARS
from generate import build_piece
from image_gen import set_photo_bg_chance

ALLOWED_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
MODOS_VALIDOS = ("gratis", "ollama", "ia")
FONDOS_VALIDOS = {"auto": 0.5, "siempre": 1.0, "nunca": 0.0}

HELP_TEXT = (
    "Comandos:\n"
    "/generar [pilar] [modo] [fondos] - genera una pieza y la manda a aprobar\n"
    f"  pilar: {', '.join(list(PILLARS.keys()) + ['random'])} (default: random)\n"
    f"  modo: {', '.join(MODOS_VALIDOS)} (default: gratis)\n"
    f"  fondos: {', '.join(FONDOS_VALIDOS)} (default: auto) - foto real (gratis) en mockups de bot/agente\n"
    "/pilares - lista los pilares\n"
    "/ayuda - este mensaje"
)

# Pieza generada esperando aprobación (una a la vez, es un bot personal de un solo uso).
_pending: dict | None = None


def _handle_generar(args: list[str]) -> None:
    global _pending
    if _pending is not None:
        telegram_client.send_message(
            "Ya hay una pieza esperando tu aprobación. Aprobala o cancelala antes de generar otra."
        )
        return

    pillar_key = args[0] if len(args) >= 1 else "random"
    modo = args[1] if len(args) >= 2 else "gratis"
    fondos = args[2] if len(args) >= 3 else "auto"

    if pillar_key == "random":
        pillar_key = random.choice(list(PILLARS.keys()))
    if pillar_key not in PILLARS:
        telegram_client.send_message(f"Pilar inválido: '{pillar_key}'. Usá /pilares para ver las opciones.")
        return
    if modo not in MODOS_VALIDOS:
        telegram_client.send_message(f"Modo inválido: '{modo}'. Usá: {', '.join(MODOS_VALIDOS)}.")
        return
    if fondos not in FONDOS_VALIDOS:
        telegram_client.send_message(f"Fondos inválido: '{fondos}'. Usá: {', '.join(FONDOS_VALIDOS)}.")
        return

    set_photo_bg_chance(FONDOS_VALIDOS[fondos])
    telegram_client.send_message(f"Generando ({PILLARS[pillar_key]['label']}, modo {modo}, fondos {fondos})...")
    try:
        folder = build_piece(pillar_key, modo)
    except Exception as e:
        telegram_client.send_message(f"Falló la generación: {e}")
        return

    content = json.loads((folder / "contenido.json").read_text(encoding="utf-8"))
    hashtags = " ".join(f"#{h.lstrip('#')}" for h in content.get("hashtags", []))
    caption = f"{content['caption']}\n\n{hashtags}".strip()

    images = sorted(folder.glob("[0-9][0-9]_*.png"))
    message_id = telegram_client.send_preview(images, caption)
    _pending = {
        "message_id": message_id,
        "folder": folder,
        "images": images,
        "title": content["portada_text"],
        "caption": caption,
    }


def _handle_callback(cq: dict) -> None:
    global _pending

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

    telegram_client.send_message("Aprobado. Alojando las imágenes y subiendo a TikTok...")
    try:
        image_urls = content_hosting.publish_images(pending["images"])
        access_token = tiktok_client.get_access_token()
        publish_id = tiktok_client.post_photos_to_inbox(image_urls, pending["title"], pending["caption"], access_token)
        status = tiktok_client.wait_for_publish(publish_id, access_token)
    except Exception as e:
        telegram_client.send_message(f"Falló la subida a TikTok: {e}")
        return

    if status == "SEND_TO_USER_INBOX":
        telegram_client.send_message(
            "Carrusel de fotos enviado al inbox de TikTok, con caption y descripción ya cargados. "
            "Abrí la app y tocá 'Publicar' para terminarlo."
        )
    elif status == "PUBLISH_COMPLETE":
        telegram_client.send_message("Publicado en TikTok.")
    else:
        telegram_client.send_message(f"Estado final: {status}")


def _handle_message(message: dict) -> None:
    text = message.get("text", "").strip()
    if text.startswith("/generar"):
        _handle_generar(text.split()[1:])
    elif text.startswith("/pilares"):
        listado = "\n".join(f"- {k}: {p['label']}" for k, p in PILLARS.items())
        telegram_client.send_message(listado)
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
