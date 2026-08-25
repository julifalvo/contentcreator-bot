"""Publica en TikTok una pieza ya generada por generate.py — pero antes manda
la vista previa (imágenes + caption) a Telegram y espera que la apruebes con
un botón. Si la cancelás, no se sube nada.

Requiere haber corrido tiktok_auth.py una vez (autoriza tu cuenta de TikTok)
y tener TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID en tu .env.

Por default sube las imágenes como CARRUSEL DE FOTOS (el usuario desliza entre
ellas en TikTok, no es un video armado). Para eso las imágenes se alojan
primero en GitHub Pages (repo rootbusinessai-legal/content, dominio ya
verificado ante TikTok) porque la API de fotos solo admite URLs públicas, no
archivos subidos directo. Con --video se arma un .mp4 con música y se sube
como video en cambio.

En ambos casos, mientras tu app no tenga aprobado el scope video.publish, se
manda al inbox de TikTok como borrador — hay que abrir la app y tocar
"Publicar" una vez. Con --direct se salta ese paso (requiere video.publish
ya aprobado).

Uso:
    python publish.py                       # toma la carpeta más reciente en output/, sube como fotos
    python publish.py --folder output/xxx   # publica una carpeta puntual
    python publish.py --video               # arma un .mp4 y lo sube como video en vez de fotos
    python publish.py --direct              # publicación directa (requiere video.publish aprobado)
    python publish.py --privacy SELF_ONLY   # fuerza un privacy_level puntual (solo con --direct)
"""

import argparse
import json
import sys
from pathlib import Path

# La consola de Windows suele usar cp1252, que no soporta emojis/flechas.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

import content_hosting
import telegram_client
import tiktok_client

OUTPUT_DIR = Path(__file__).parent / "output"


def _latest_folder() -> Path:
    folders = sorted((p for p in OUTPUT_DIR.iterdir() if p.is_dir()), key=lambda p: p.name)
    if not folders:
        raise RuntimeError("No hay contenido en output/. Corré generate.py primero.")
    return folders[-1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Publica una pieza en TikTok, con aprobación previa por Telegram")
    parser.add_argument("--folder", type=Path, default=None, help="Carpeta de output/ a publicar (default: la más reciente)")
    parser.add_argument("--video", action="store_true", help="Arma un .mp4 y lo sube como video, en vez de carrusel de fotos (default)")
    parser.add_argument("--privacy", default=None, help="privacy_level de TikTok (ej: SELF_ONLY, PUBLIC_TO_EVERYONE). Default: el primero disponible según tu cuenta")
    parser.add_argument("--direct", action="store_true", help="Publica directo (DIRECT_POST, requiere el scope video.publish ya aprobado). Default: manda al inbox como borrador (video.upload)")
    args = parser.parse_args()

    folder = args.folder or _latest_folder()
    content = json.loads((folder / "contenido.json").read_text(encoding="utf-8"))

    hashtags = " ".join(f"#{h.lstrip('#')}" for h in content.get("hashtags", []))
    caption = f"{content['caption']}\n\n{hashtags}".strip()

    images = sorted(folder.glob("[0-9][0-9]_*.png"))
    print("→ Mandando vista previa a Telegram...")
    message_id = telegram_client.send_preview(images, caption)

    approved = telegram_client.wait_for_approval(message_id)
    if not approved:
        print("✗ Cancelado desde Telegram. No se publica nada.")
        sys.exit(0)

    print("→ Aprobado. Subiendo a TikTok...")
    access_token = tiktok_client.get_access_token()

    if args.video:
        from video_gen import build_video

        print("→ Armando el video a partir de: " + folder.name)
        video_path = build_video(folder)
        print(f"  Video listo: {video_path}")

        if args.direct:
            creator = tiktok_client.query_creator_info(access_token)
            privacy = args.privacy or creator["privacy_level_options"][0]
            print(f"  Publicando directo como: {creator['creator_username']} (privacy_level={privacy})")
            publish_id = tiktok_client.upload_video(video_path, access_token, title=caption[:2200], privacy_level=privacy)
        else:
            print("  Mandando al inbox de TikTok como borrador (scope video.upload, sin auditar)...")
            publish_id = tiktok_client.upload_video_to_inbox(video_path, access_token)
    else:
        print("→ Alojando las imágenes en GitHub Pages...")
        image_urls = content_hosting.publish_images(images)
        print(f"  {len(image_urls)} imágenes públicas y accesibles.")

        if args.direct:
            creator = tiktok_client.query_creator_info(access_token)
            privacy = args.privacy or creator["privacy_level_options"][0]
            print(f"  Publicando directo como: {creator['creator_username']} (privacy_level={privacy})")
            publish_id = tiktok_client.post_photos_to_inbox(image_urls, content["portada_text"], caption, access_token)
        else:
            print("  Mandando al inbox de TikTok como borrador (scope video.upload, sin auditar)...")
            publish_id = tiktok_client.post_photos_to_inbox(image_urls, content["portada_text"], caption, access_token)

    print(f"  publish_id: {publish_id}")

    print("→ Esperando confirmación de TikTok...")
    status = tiktok_client.wait_for_publish(publish_id, access_token)
    if status == "PUBLISH_COMPLETE":
        print("✓ Publicado en TikTok.")
    elif status == "SEND_TO_USER_INBOX":
        print("✓ Contenido enviado al inbox de TikTok.")
        print("  Abrí la app de TikTok, fijate en tu bandeja de notificaciones/inbox,")
        print("  y tocá 'Publicar' para terminar de subirlo.")
    else:
        print(f"✗ Estado final: {status}. Revisá el log_id en la respuesta si hizo falta.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
