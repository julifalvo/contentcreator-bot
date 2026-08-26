"""Renderiza HTML/CSS a PNG usando Chrome/Chromium en modo headless.

Reemplaza el dibujo a mano con Pillow (rectángulos y texto sueltos, que se
veían planos y armados con formas geométricas): acá el diseño se escribe como
una página web real y la rinde el mismo motor que usa el navegador, así que
salen sombras, degradés, tipografía real, grid/flex y todo lo que CSS sabe
hacer. Costo: $0, corre local, sin API ni servicios de terceros.
"""

import base64
import platform
import shutil
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path

from PIL import Image

CANVAS_W, CANVAS_H = 1080, 1920
FONTS_DIR = Path(__file__).parent / "assets" / "fonts"

_WINDOWS_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]
# En Ubuntu server: sudo apt install chromium-browser  (o chromium)
_LINUX_CANDIDATES = ["chromium", "chromium-browser", "google-chrome", "google-chrome-stable"]


@lru_cache(maxsize=1)
def _find_browser() -> str:
    candidates = _WINDOWS_CANDIDATES if platform.system() == "Windows" else _LINUX_CANDIDATES
    for cand in candidates:
        if Path(cand).exists():
            return cand
        found = shutil.which(cand)
        if found:
            return found
    raise RuntimeError(
        "No encontré Chrome ni Chromium para renderizar las imágenes.\n"
        "  Windows: instalá Google Chrome (o Microsoft Edge).\n"
        "  Ubuntu:  sudo apt install chromium-browser"
    )


@lru_cache(maxsize=8)
def font_data_uri(filename: str) -> str:
    """Devuelve la fuente embebida como data: URI. Se embebe (en vez de
    referenciar el archivo) para que el HTML sea autocontenido y se vea igual
    en Windows y en el server Ubuntu, sin depender de fuentes del sistema."""
    raw = (FONTS_DIR / filename).read_bytes()
    return f"data:font/ttf;base64,{base64.b64encode(raw).decode()}"


def image_data_uri(path: Path) -> str:
    """Embebe una imagen local (ej: una foto de fondo ya descargada) para que
    el HTML no dependa de rutas ni de la red al momento de renderizar."""
    suffix = path.suffix.lstrip(".").lower()
    mime = "jpeg" if suffix in ("jpg", "jpeg") else suffix
    return f"data:image/{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def html_to_png(html: str, out_path: Path) -> Path:
    """Rinde `html` a un PNG de 1080x1920 (formato TikTok) en `out_path`."""
    # Chrome escribe el screenshot relativo a SU cwd, no al nuestro: si no le
    # pasamos la ruta absoluta, falla con "no puede encontrar la ruta".
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path = out_path.resolve()

    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "slide.html"
        src.write_text(html, encoding="utf-8")

        result = subprocess.run(
            [
                _find_browser(),
                "--headless",
                "--disable-gpu",
                "--hide-scrollbars",
                "--no-sandbox",  # necesario para correr como servicio en Ubuntu
                "--force-device-scale-factor=1",
                "--default-background-color=00000000",
                f"--window-size={CANVAS_W},{CANVAS_H}",
                f"--screenshot={out_path}",
                src.resolve().as_uri(),
            ],
            capture_output=True,
            text=True,
            timeout=90,
        )

    if not out_path.exists():
        raise RuntimeError(f"Chrome no generó la imagen:\n{result.stderr[-800:]}")

    _recomprimir(out_path)
    return out_path


def _recomprimir(path: Path) -> None:
    """Chrome guarda el screenshot como PNG sin optimizar: ~1.7MB por slide,
    contra los ~50-90KB que salían dibujando con Pillow. Con 6-8 slides eso
    tira abajo el envío del carrusel a Telegram por timeout. Estas piezas son
    texto + colores planos + degradés suaves (nunca fotos con ruido real), así
    que una paleta de 256 colores no se nota y pesa una fracción."""
    img = Image.open(path).convert("RGB")
    img = img.quantize(colors=256, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG)
    img.save(path, "PNG", optimize=True)
