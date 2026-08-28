"""Setup único: autoriza esta app contra tu cuenta de TikTok (OAuth v2 + PKCE,
flujo "Login Kit for Desktop") y guarda la sesión en tiktok_tokens.json.

Corré esto una sola vez (o de nuevo si revocás el acceso desde TikTok, o si
cambiás de cuenta). Después de esto, tiktok_client.py se encarga solo de
refrescar el token cuando hace falta.

Requiere antes:
  1. Crear una app en https://developers.tiktok.com/apps
  2. Agregarle los productos "Login Kit" y "Content Posting API"
  3. En la config de la app, registrar como redirect URI: http://127.0.0.1:*/callback/
     (o el puerto fijo que pongas en TIKTOK_REDIRECT_URI en tu .env)
  4. Copiar el Client Key y el Client Secret a tu .env
"""

import hashlib
import http.server
import json
import os
import secrets
import string
import sys
import time
import urllib.parse
import webbrowser
from pathlib import Path

import requests
from dotenv import load_dotenv

# La consola de Windows suele usar cp1252, que no soporta emojis/flechas.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TOKENS_PATH = Path(__file__).parent / "tiktok_tokens.json"

_ALPHABET = string.ascii_letters + string.digits + "-._~"


def _random_string(length: int) -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(length))


def _code_challenge(verifier: str) -> str:
    # TikTok pide hex de SHA256, a diferencia del base64url estándar de PKCE.
    return hashlib.sha256(verifier.encode("ascii")).hexdigest()


def main() -> None:
    client_key = os.environ.get("TIKTOK_CLIENT_KEY")
    client_secret = os.environ.get("TIKTOK_CLIENT_SECRET")
    redirect_uri = os.environ.get("TIKTOK_REDIRECT_URI", "http://127.0.0.1:8921/callback/")
    if not client_key or not client_secret:
        raise SystemExit(
            "Faltan TIKTOK_CLIENT_KEY / TIKTOK_CLIENT_SECRET en tu .env. "
            "Registrá una app en https://developers.tiktok.com/apps y copiá esos valores."
        )

    parsed = urllib.parse.urlparse(redirect_uri)
    port = parsed.port or 8921
    path = parsed.path or "/callback/"

    verifier = _random_string(64)
    challenge = _code_challenge(verifier)
    state = _random_string(24)

    # video.upload: publicar (el que ya se usaba). user.info.stats/video.list:
    # sólo lectura, para traer métricas reales (tiktok_metrics.py) — seguidores,
    # likes totales y vistas/likes/comentarios por video ya publicado. Hace
    # falta habilitar esos dos scopes en developers.tiktok.com → tu app →
    # Login Kit → Scopes ANTES de correr este script, o TikTok rechaza el
    # login con un scope que la app no tiene habilitado.
    scopes = os.environ.get("TIKTOK_SCOPES", "video.upload,user.info.basic,user.info.stats,video.list")
    params = {
        "client_key": client_key,
        "response_type": "code",
        "scope": scopes,
        "redirect_uri": redirect_uri,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    result: dict = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            parsed_qs = urllib.parse.urlparse(self.path)
            if parsed_qs.path != path:
                self.send_response(404)
                self.end_headers()
                return
            qs = urllib.parse.parse_qs(parsed_qs.query)
            result["code"] = qs.get("code", [None])[0]
            result["state"] = qs.get("state", [None])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                "<html><body><h2>Listo, ya podés cerrar esta pestaña.</h2></body></html>".encode("utf-8")
            )

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", port), Handler)

    print("Abriendo el navegador para autorizar la app en TikTok...")
    print(f"Si no se abre solo, entrá manualmente a:\n{auth_url}\n")
    webbrowser.open(auth_url)

    print(f"Esperando el redirect en http://127.0.0.1:{port}{path} ...")
    while "code" not in result:
        server.handle_request()

    if result.get("state") != state:
        raise SystemExit("El parámetro 'state' no coincide (posible CSRF). Abortando.")
    if not result.get("code"):
        raise SystemExit("TikTok no devolvió un código de autorización.")

    print("→ Código recibido, pidiendo el token de acceso...")
    resp = requests.post(
        TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_key": client_key,
            "client_secret": client_secret,
            "code": result["code"],
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "code_verifier": verifier,
        },
        timeout=30,
    )
    data = resp.json()
    if "access_token" not in data:
        raise SystemExit(f"TikTok rechazó el intercambio de token: {data}")

    tokens = {
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
        "expires_at": time.time() + data["expires_in"],
        "open_id": data.get("open_id"),
        "scope": data.get("scope"),
    }
    TOKENS_PATH.write_text(json.dumps(tokens, indent=2), encoding="utf-8")
    print(f"✓ Listo. Sesión guardada en {TOKENS_PATH}")
    print(
        "  Nota: mientras tu app no esté auditada por TikTok (scope video.publish), "
        "publish.py va a mandar el video al inbox de tu cuenta de TikTok como "
        "borrador — tenés que abrir la app y tocar 'Publicar' una vez para que "
        "salga. Una vez aprobado el scope video.publish, se puede publicar "
        "directo sin ese paso manual."
    )


if __name__ == "__main__":
    main()
