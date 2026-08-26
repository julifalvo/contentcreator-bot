"""Hook PostToolUse: si se edita un archivo del pipeline en vivo del bot,
recuerda que hay que reiniciar 'python bot.py' para que tome el cambio.

Nace de esta misma sesión: reiniciamos el bot a mano como 6 veces después de
editar bot.py/generate.py/design.py/groq_client.py/etc, porque el proceso
corriendo tiene el código viejo cargado en memoria hasta que se lo reinicia.
No bloquea nada (exit 0 siempre) — es solo un recordatorio.
"""

import json
import os
import sys

# La consola de Windows suele usar cp1252, que no soporta tildes/eñes.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

PIPELINE_FILES = {
    "bot.py", "generate.py", "groq_client.py", "gemini_client.py",
    "ai_providers.py", "design.py", "config.py", "content_rules.py", "image_gen.py",
    "video_rules.py", "video_narrado.py", "video_gen.py", "pexels_client.py",
    "elevenlabs_client.py", "telegram_client.py", "tiktok_client.py",
    "content_hosting.py", "render.py", "scrapecreators_client.py",
}

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

file_path = (data.get("tool_input") or {}).get("file_path", "") or ""
name = os.path.basename(file_path)

if name in PIPELINE_FILES:
    print(
        f"Recordatorio: se editó {name}, parte del pipeline en vivo del bot. "
        "Si bot.py ya está corriendo, hace falta reiniciarlo (mata el proceso "
        "python bot.py y volvelo a lanzar) para que tome este cambio — el "
        "proceso viejo se queda con el código cargado en memoria."
    )

sys.exit(0)
