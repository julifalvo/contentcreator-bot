"""Métricas reales de la cuenta de TikTok (Display API, de solo lectura):
estadísticas de cuenta y de cada video ya publicado — para poder recomendar
qué generar en base a lo que de verdad funciona, no solo en tendencias
generales.

Es una API distinta a la de publicar (tiktok_client.py, Content Posting API):
usa los mismos access_token/refresh_token de tiktok_tokens.json, pero necesita
que ese token tenga además los scopes 'user.info.stats' y 'video.list' — no
alcanza con 'video.upload'. Para habilitarlos:
  1. developers.tiktok.com/apps → tu app → Login Kit → Scopes: agregar
     'user.info.stats' y 'video.list'.
  2. Correr 'python tiktok_auth.py' de nuevo para volver a autorizar con esos
     scopes (el token viejo no los tiene y TikTok lo va a rechazar con
     'scope_not_authorized' hasta que reautorices).
"""

from pathlib import Path

import requests

DISPLAY_API_BASE = "https://open.tiktokapis.com/v2"

_VIDEO_FIELDS = "id,create_time,video_description,view_count,like_count,comment_count,share_count"


def get_account_stats(access_token: str) -> dict:
    """Seguidores, likes totales y cantidad de videos de la cuenta."""
    resp = requests.get(
        f"{DISPLAY_API_BASE}/user/info/",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"fields": "display_name,follower_count,following_count,likes_count,video_count"},
        timeout=30,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"TikTok respondió {resp.status_code} pidiendo estadísticas de cuenta: {resp.text[:500]}")
    data = resp.json()
    if data["error"]["code"] != "ok":
        raise RuntimeError(f"Error consultando estadísticas de cuenta: {data['error']}")
    return data["data"]["user"]


def list_videos(access_token: str, max_count: int = 20) -> list[dict]:
    """Trae hasta `max_count` videos ya publicados (paginando con 'cursor' si
    hace falta), más recientes primero, con sus métricas."""
    videos: list[dict] = []
    cursor = None
    while len(videos) < max_count:
        body = {"max_count": min(20, max_count - len(videos))}
        if cursor is not None:
            body["cursor"] = cursor
        resp = requests.post(
            f"{DISPLAY_API_BASE}/video/list/",
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json; charset=UTF-8"},
            params={"fields": _VIDEO_FIELDS},
            json=body,
            timeout=30,
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"TikTok respondió {resp.status_code} listando videos: {resp.text[:500]}")
        data = resp.json()
        if data["error"]["code"] != "ok":
            raise RuntimeError(f"Error listando videos: {data['error']}")
        pagina = data["data"]
        videos.extend(pagina.get("videos", []))
        if not pagina.get("has_more"):
            break
        cursor = pagina.get("cursor")

    return videos


def top_videos(access_token: str, n: int = 5, max_scan: int = 50) -> list[dict]:
    """Los `n` videos con más vistas de los últimos `max_scan` publicados."""
    videos = list_videos(access_token, max_count=max_scan)
    return sorted(videos, key=lambda v: v.get("view_count", 0), reverse=True)[:n]
