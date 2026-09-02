"""Cliente de la Instagram Graph API (Content Publishing) para Reels, Stories
y carrusel de feed.

Requiere haber corrido instagram_auth.py una vez para generar ig_tokens.json
(el access token de la Página de Facebook vinculada a la cuenta de Instagram
Business/Creator, más el id de esa cuenta).

A diferencia de TikTok, esta API NO tiene un modo "borrador al inbox": crear
el contenedor y publicarlo lo sube directo a la cuenta, sin paso manual en la
app. Por eso el flujo de aprobación de Telegram (bot.py) recién llama a estas
funciones después de que tocás Aprobar — no hay forma de mandarlo "a
revisar" a Instagram como sí se puede con TikTok.

Los tokens de Página derivados de un token de usuario de larga duración no
vencen mientras sigas siendo admin de la Página y no revoques el acceso, así
que a diferencia de tiktok_client.py acá no hay refresco automático. Si Meta
lo invalida igual (revocación manual, cambio de contraseña de la cuenta,
etc.), el error de abajo te va a decir explícitamente que corras
instagram_auth.py de nuevo.
"""

import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

TOKENS_PATH = Path(__file__).parent / "ig_tokens.json"
# Meta va deprecando versiones viejas de la Graph API cada tanto (~2 años de
# vida cada una): si en algún momento empieza a tirar error de versión no
# soportada, subí este número en el .env con META_GRAPH_API_VERSION.
GRAPH_VERSION = os.environ.get("META_GRAPH_API_VERSION", "v26.0")
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"

# Los contenedores de video (Reels, Stories de video) procesan async del lado
# de Meta antes de poder publicarse.
_STATUS_POLL_SEC = 5
_STATUS_TIMEOUT_SEC = 300


def _load_tokens() -> dict:
    if not TOKENS_PATH.exists():
        raise RuntimeError(
            "No hay sesión de Instagram guardada. Corré 'python instagram_auth.py' una vez "
            "para autorizarla (necesita una cuenta de Instagram Business o Creator vinculada "
            "a una Página de Facebook)."
        )
    return json.loads(TOKENS_PATH.read_text(encoding="utf-8"))


def get_access_token() -> str:
    return _load_tokens()["access_token"]


def get_ig_user_id() -> str:
    return _load_tokens()["ig_user_id"]


def _error_msg(status_code: int, data: dict) -> str:
    err = data.get("error", {})
    msg = f"Instagram respondió {status_code}: {err.get('message', data)}"
    if err.get("code") == 190:
        msg += "\nEl token venció o fue revocado — corré 'python instagram_auth.py' de nuevo."
    return msg


def _get(path: str, access_token: str, **params) -> dict:
    resp = requests.get(f"{GRAPH_BASE}/{path}", params={"access_token": access_token, **params}, timeout=30)
    data = resp.json()
    if "error" in data:
        raise RuntimeError(_error_msg(resp.status_code, data))
    return data


def _post(path: str, access_token: str, **params) -> dict:
    resp = requests.post(f"{GRAPH_BASE}/{path}", data={"access_token": access_token, **params}, timeout=30)
    data = resp.json()
    if "error" in data:
        raise RuntimeError(_error_msg(resp.status_code, data))
    return data


def _wait_container_ready(creation_id: str, access_token: str) -> None:
    deadline = time.time() + _STATUS_TIMEOUT_SEC
    while time.time() < deadline:
        data = _get(creation_id, access_token, fields="status_code")
        status = data.get("status_code")
        if status == "FINISHED":
            return
        if status == "ERROR":
            raise RuntimeError(f"Instagram falló procesando el contenedor {creation_id}: {data}")
        time.sleep(_STATUS_POLL_SEC)
    raise TimeoutError(f"El contenedor {creation_id} no terminó de procesar a tiempo.")


def _publish(creation_id: str, access_token: str, ig_user_id: str) -> str:
    data = _post(f"{ig_user_id}/media_publish", access_token, creation_id=creation_id)
    return data["id"]


def publish_feed_carousel(image_urls: list[str], caption: str) -> str:
    """Publica un carrusel de fotos en el feed. Cada imagen tiene que estar en
    una URL pública (content_hosting.publish_images) y en 4:5, la proporción
    que exige la Graph API para carrusel (instagram_render.build_feed_images).
    Devuelve el id del media ya publicado."""
    access_token = get_access_token()
    ig_user_id = get_ig_user_id()

    hijos = []
    for url in image_urls[:10]:  # 10 es el máximo que admite un carrusel
        data = _post(f"{ig_user_id}/media", access_token, image_url=url, is_carousel_item="true")
        hijos.append(data["id"])

    contenedor = _post(
        f"{ig_user_id}/media", access_token,
        media_type="CAROUSEL", caption=caption[:2200], children=",".join(hijos),
    )
    return _publish(contenedor["id"], access_token, ig_user_id)


def publish_reel(video_url: str, caption: str) -> str:
    """Publica un Reel. video_url tiene que ser pública
    (content_hosting.publish_video). Devuelve el id del media ya publicado."""
    access_token = get_access_token()
    ig_user_id = get_ig_user_id()

    contenedor = _post(
        f"{ig_user_id}/media", access_token,
        media_type="REELS", video_url=video_url, caption=caption[:2200],
    )
    _wait_container_ready(contenedor["id"], access_token)
    return _publish(contenedor["id"], access_token, ig_user_id)


def publish_story_image(image_url: str) -> str:
    """Publica una Story de imagen (9:16 nativo, no admite carrusel — se
    manda solo la portada, ver instagram_render.story_image)."""
    access_token = get_access_token()
    ig_user_id = get_ig_user_id()

    contenedor = _post(f"{ig_user_id}/media", access_token, media_type="STORIES", image_url=image_url)
    return _publish(contenedor["id"], access_token, ig_user_id)


def publish_story_video(video_url: str) -> str:
    """Publica una Story de video (el mismo Reel, ver content_hosting.publish_video)."""
    access_token = get_access_token()
    ig_user_id = get_ig_user_id()

    contenedor = _post(f"{ig_user_id}/media", access_token, media_type="STORIES", video_url=video_url)
    _wait_container_ready(contenedor["id"], access_token)
    return _publish(contenedor["id"], access_token, ig_user_id)
