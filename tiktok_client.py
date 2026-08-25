"""Cliente de la Content Posting API de TikTok (OAuth v2 + subida de video).

Requiere haber corrido tiktok_auth.py una vez para generar tiktok_tokens.json.
A partir de ahí, get_access_token() se encarga solo de refrescar el token
cuando está por vencer (dura 24hs; el refresh_token dura 365 días y rota en
cada uso, por eso se persiste de nuevo cada vez).
"""

import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

TOKENS_PATH = Path(__file__).parent / "tiktok_tokens.json"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
API_BASE = "https://open.tiktokapis.com/v2/post/publish"

CHUNK_SIZE = 10 * 1024 * 1024  # 10MB por chunk, dentro de los límites de TikTok


def _client_credentials() -> tuple[str, str]:
    key = os.environ.get("TIKTOK_CLIENT_KEY")
    secret = os.environ.get("TIKTOK_CLIENT_SECRET")
    if not key or not secret:
        raise RuntimeError("Falta TIKTOK_CLIENT_KEY / TIKTOK_CLIENT_SECRET en tu .env.")
    return key, secret


def _load_tokens() -> dict:
    if not TOKENS_PATH.exists():
        raise RuntimeError(
            "No hay sesión de TikTok guardada. Corré 'python tiktok_auth.py' una vez "
            "para autorizar tu cuenta."
        )
    return json.loads(TOKENS_PATH.read_text(encoding="utf-8"))


def _save_tokens(tokens: dict) -> None:
    TOKENS_PATH.write_text(json.dumps(tokens, indent=2), encoding="utf-8")


def get_access_token() -> str:
    """Devuelve un access_token válido, refrescándolo si está por vencer."""
    tokens = _load_tokens()
    if tokens["expires_at"] > time.time() + 60:
        return tokens["access_token"]

    key, secret = _client_credentials()
    resp = requests.post(
        TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_key": key,
            "client_secret": secret,
            "grant_type": "refresh_token",
            "refresh_token": tokens["refresh_token"],
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if "access_token" not in data:
        raise RuntimeError(
            f"No se pudo refrescar el token de TikTok: {data}. "
            "Puede que haya que correr tiktok_auth.py de nuevo."
        )

    tokens.update({
        "access_token": data["access_token"],
        "refresh_token": data.get("refresh_token", tokens["refresh_token"]),
        "expires_at": time.time() + data["expires_in"],
    })
    _save_tokens(tokens)
    return tokens["access_token"]


def post_photos_to_inbox(image_urls: list[str], title: str, description: str, access_token: str) -> str:
    """Manda un carrusel de fotos al inbox de TikTok como borrador (scope
    video.upload, sin auditar). El usuario abre la app y termina de publicarlo
    ahí (puede deslizar entre las fotos como slides). Las imágenes tienen que
    estar en una URL pública de un dominio ya verificado ante TikTok
    (PULL_FROM_URL es el único origen que admite la API de fotos)."""
    resp = requests.post(
        f"{API_BASE}/content/init/",
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json; charset=UTF-8"},
        json={
            "post_info": {"title": title[:90], "description": description[:4000]},
            "source_info": {
                "source": "PULL_FROM_URL",
                "photo_cover_index": 0,
                "photo_images": image_urls,
            },
            "post_mode": "MEDIA_UPLOAD",
            "media_type": "PHOTO",
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if data["error"]["code"] != "ok":
        raise RuntimeError(f"Error iniciando la subida de fotos: {data['error']}")
    return data["data"]["publish_id"]


def query_creator_info(access_token: str) -> dict:
    resp = requests.post(
        f"{API_BASE}/creator_info/query/",
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json; charset=UTF-8"},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if data["error"]["code"] != "ok":
        raise RuntimeError(f"Error consultando creator_info: {data['error']}")
    return data["data"]


def upload_video(video_path: Path, access_token: str, title: str, privacy_level: str) -> str:
    """Inicia la publicación y sube el archivo por chunks. Devuelve el publish_id."""
    video_size = video_path.stat().st_size
    total_chunk_count = max(1, -(-video_size // CHUNK_SIZE))  # ceil division
    chunk_size = video_size if total_chunk_count == 1 else CHUNK_SIZE

    init_resp = requests.post(
        f"{API_BASE}/video/init/",
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json; charset=UTF-8"},
        json={
            "post_info": {
                "title": title,
                "privacy_level": privacy_level,
                "disable_duet": False,
                "disable_stitch": False,
                "disable_comment": False,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": video_size,
                "chunk_size": chunk_size,
                "total_chunk_count": total_chunk_count,
            },
        },
        timeout=30,
    )
    init_resp.raise_for_status()
    init_data = init_resp.json()
    if init_data["error"]["code"] != "ok":
        raise RuntimeError(f"Error iniciando la publicación: {init_data['error']}")

    publish_id = init_data["data"]["publish_id"]
    upload_url = init_data["data"]["upload_url"]

    with open(video_path, "rb") as f:
        for i in range(total_chunk_count):
            start = i * chunk_size
            f.seek(start)
            chunk = f.read(chunk_size)
            end = start + len(chunk) - 1
            put_resp = requests.put(
                upload_url,
                headers={
                    "Content-Type": "video/mp4",
                    "Content-Range": f"bytes {start}-{end}/{video_size}",
                    "Content-Length": str(len(chunk)),
                },
                data=chunk,
                timeout=120,
            )
            if put_resp.status_code not in (200, 201):
                raise RuntimeError(f"Error subiendo chunk {i}: {put_resp.status_code} {put_resp.text}")

    return publish_id


def upload_video_to_inbox(video_path: Path, access_token: str) -> str:
    """Manda el video al inbox de TikTok como borrador (scope video.upload, sin
    auditar). El usuario tiene que abrir la app y tocar "Publicar" una vez para
    que salga; no admite post_info (título/privacidad) — eso se completa en la
    app. Devuelve el publish_id."""
    video_size = video_path.stat().st_size
    total_chunk_count = max(1, -(-video_size // CHUNK_SIZE))  # ceil division
    chunk_size = video_size if total_chunk_count == 1 else CHUNK_SIZE

    init_resp = requests.post(
        f"{API_BASE}/inbox/video/init/",
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json; charset=UTF-8"},
        json={
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": video_size,
                "chunk_size": chunk_size,
                "total_chunk_count": total_chunk_count,
            },
        },
        timeout=30,
    )
    init_resp.raise_for_status()
    init_data = init_resp.json()
    if init_data["error"]["code"] != "ok":
        raise RuntimeError(f"Error iniciando la subida al inbox: {init_data['error']}")

    publish_id = init_data["data"]["publish_id"]
    upload_url = init_data["data"]["upload_url"]

    with open(video_path, "rb") as f:
        for i in range(total_chunk_count):
            start = i * chunk_size
            f.seek(start)
            chunk = f.read(chunk_size)
            end = start + len(chunk) - 1
            put_resp = requests.put(
                upload_url,
                headers={
                    "Content-Type": "video/mp4",
                    "Content-Range": f"bytes {start}-{end}/{video_size}",
                    "Content-Length": str(len(chunk)),
                },
                data=chunk,
                timeout=120,
            )
            if put_resp.status_code not in (200, 201):
                raise RuntimeError(f"Error subiendo chunk {i}: {put_resp.status_code} {put_resp.text}")

    return publish_id


# PUBLISH_COMPLETE: quedó publicado (DIRECT_POST). SEND_TO_USER_INBOX: llegó
# como borrador al inbox del usuario (MEDIA_UPLOAD) — ambos son éxito.
_TERMINAL_STATUSES = {"PUBLISH_COMPLETE", "SEND_TO_USER_INBOX", "FAILED"}


def wait_for_publish(publish_id: str, access_token: str, timeout_sec: int = 300) -> str:
    """Hace polling del estado de publicación hasta que termina o pasa el timeout."""
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        resp = requests.post(
            f"{API_BASE}/status/fetch/",
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json; charset=UTF-8"},
            json={"publish_id": publish_id},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()["data"]
        status = data.get("status")
        if status in _TERMINAL_STATUSES:
            return status
        time.sleep(5)
    return "TIMEOUT"
