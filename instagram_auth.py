"""Setup único: autoriza esta app contra tu cuenta de Instagram (vía Graph
API de Meta) y guarda la sesión en ig_tokens.json.

A diferencia de tiktok_auth.py, este flujo no abre un navegador ni levanta un
servidor local: Meta exige un redirect URI HTTPS registrado para el login
completo, que es mucho más setup del que hace falta para un bot personal de
una sola cuenta. En cambio, usa el Graph API Explorer (una página que ya te
da Meta) para sacar un token corto a mano, y este script lo cambia por uno de
larga duración.

Requiere antes:
  1. Tener la cuenta de Instagram como Business o Creator, vinculada a una
     Página de Facebook (Configuración de la cuenta de Instagram → Cuentas
     vinculadas → Facebook).
  2. Crear una app en https://developers.facebook.com/apps (tipo "Business"),
     agregarle el producto "Instagram Graph API".
  3. Copiar el App ID y el App Secret (Configuración → Básica) a tu .env como
     META_APP_ID / META_APP_SECRET.
  4. Ir a https://developers.facebook.com/tools/explorer/, elegir tu app
     arriba a la derecha, elegir "Get User Access Token", y tildar estos
     permisos: instagram_basic, instagram_content_publish, pages_show_list,
     pages_read_engagement, business_management. Generar el token y copiarlo
     (dura ~1-2hs, alcanza para correr este script ahora mismo).

Corré esto una sola vez (o de nuevo si el token se revoca, ver el error de
instagram_client.py cuando eso pasa).
"""

import json
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

GRAPH_VERSION = os.environ.get("META_GRAPH_API_VERSION", "v26.0")
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"
TOKENS_PATH = Path(__file__).parent / "ig_tokens.json"


def _get(path: str, **params) -> dict:
    resp = requests.get(f"{GRAPH_BASE}/{path}", params=params, timeout=30)
    data = resp.json()
    if "error" in data:
        raise SystemExit(f"Meta respondió {resp.status_code}: {data['error'].get('message', data)}")
    return data


def main() -> None:
    app_id = os.environ.get("META_APP_ID")
    app_secret = os.environ.get("META_APP_SECRET")
    if not app_id or not app_secret:
        raise SystemExit(
            "Faltan META_APP_ID / META_APP_SECRET en tu .env. Creá una app en "
            "https://developers.facebook.com/apps y copiá esos valores desde "
            "Configuración → Básica."
        )

    short_token = input(
        "Pegá acá el User Access Token que generaste en "
        "https://developers.facebook.com/tools/explorer/ (con los permisos "
        "instagram_basic, instagram_content_publish, pages_show_list, "
        "pages_read_engagement, business_management):\n> "
    ).strip()
    if not short_token:
        raise SystemExit("No pegaste ningún token.")

    print("→ Cambiando el token corto por uno de larga duración (~60 días)...")
    exchange = _get(
        "oauth/access_token",
        grant_type="fb_exchange_token",
        client_id=app_id,
        client_secret=app_secret,
        fb_exchange_token=short_token,
    )
    long_user_token = exchange["access_token"]

    print("→ Buscando las Páginas de Facebook que administrás...")
    pages = _get("me/accounts", access_token=long_user_token, fields="id,name,access_token").get("data", [])
    if not pages:
        raise SystemExit(
            "Tu cuenta no administra ninguna Página de Facebook. La cuenta de Instagram "
            "tiene que estar vinculada a una Página (Instagram → Configuración → Cuentas "
            "vinculadas → Facebook) y vos tenés que ser admin de esa Página."
        )

    if len(pages) == 1:
        page = pages[0]
    else:
        print("Encontré varias Páginas — elegí una:")
        for i, p in enumerate(pages):
            print(f"  {i + 1}. {p['name']}")
        idx = input("Número: ").strip()
        try:
            page = pages[int(idx) - 1]
        except (ValueError, IndexError):
            raise SystemExit("Opción inválida.")

    print(f"→ Buscando la cuenta de Instagram vinculada a '{page['name']}'...")
    ig_info = _get(page["id"], access_token=page["access_token"], fields="instagram_business_account")
    ig_account = ig_info.get("instagram_business_account")
    if not ig_account:
        raise SystemExit(
            f"La Página '{page['name']}' no tiene ninguna cuenta de Instagram Business/Creator "
            "vinculada. Vinculala desde la app de Instagram (Configuración → Cuentas "
            "vinculadas → Facebook → esta Página) y volvé a correr este script."
        )

    tokens = {
        "access_token": page["access_token"],
        "ig_user_id": ig_account["id"],
        "page_id": page["id"],
        "page_name": page["name"],
        "obtained_at": time.time(),
    }
    TOKENS_PATH.write_text(json.dumps(tokens, indent=2), encoding="utf-8")
    print(f"✓ Listo. Sesión guardada en {TOKENS_PATH}")
    print(
        "  El token de Página no vence mientras sigas siendo admin de la Página y no "
        "revoques el acceso — no hace falta refrescarlo como al de TikTok. Si en algún "
        "momento deja de funcionar (revocación, cambio de contraseña), corré este script "
        "de nuevo."
    )


if __name__ == "__main__":
    main()
