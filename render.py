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

# El lienzo es 1080x1920 (9:16): es el tamano que TikTok recomienda
# explicitamente para carruseles de fotos, no el nativo de la pantalla.
#
# Esto corrige un cambio anterior mal fundado: se probo pasar el lienzo a 20:9
# (nativo de los celulares de hoy) razonando por analogia con el VIDEO -que
# TikTok si escala "cover" a pantalla completa, recortando lo que sobra-. Para
# FOTOS no es asi: TikTok documenta 1080x1920 como el tamano optimo y advierte
# que cualquier otra proporcion (4:5, 1:1, horizontal) se muestra con
# letterbox/recorte en su propio visor. El resultado del 20:9 fue justamente
# eso: la app lo forzo a su contenedor y termino recortando el kicker de
# arriba, distinto al problema original pero igual de roto.
#
# Lo que SI hacia falta arreglar (y sigue arreglado abajo) es la zona segura:
# TikTok pinta sobre la imagen una franja de UI de ~200px arriba (tabs
# Siguiendo/Para ti, buscador) y una mas grande abajo (caption, usuario,
# like/comentar/compartir), documentadas como zona de peligro del 9:16
# estandar. design.py ahora deja mas aire en las dos puntas que el minimo
# documentado, para no repetir el kicker tapado.
CANVAS_W, CANVAS_H = 1080, 1920

# Se rinde al doble (2160x3840) y se baja a ANCHO_FINAL con Lanczos, en vez de
# rendir directo al tamano final: el supersampling le da al texto un
# antialiasing mucho mas limpio que el del rasterizador a 1x, y eso sobrevive
# mejor al JPEG y al recompresor de TikTok. El entregable queda exactamente en
# el tamano que TikTok recomienda (1080x1920), sin ambiguedad.
ESCALA_RENDER = 2
ANCHO_FINAL = 1080

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
    """Rinde `html` a un PNG de 1080x1920 (9:16, el tamano que TikTok recomienda para carruseles de fotos)."""
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
                f"--force-device-scale-factor={ESCALA_RENDER}",
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

    _bajar_a_final(out_path)
    _recomprimir(out_path)
    return out_path


def _bajar_a_final(path: Path) -> None:
    """Baja el render de 2x al tamano de entrega con Lanczos (el remuestreo mas
    limpio de Pillow para reducir). Es el paso que convierte el supersampling
    en nitidez real: sin esto el archivo pesaria cuatro veces mas sin verse
    mejor en un telefono."""
    img = Image.open(path)
    if img.width != ANCHO_FINAL:
        alto = round(img.height * ANCHO_FINAL / img.width)
        img = img.resize((ANCHO_FINAL, alto), Image.LANCZOS)
        img.save(path, "PNG")


def _recomprimir(path: Path) -> None:
    """Chrome guarda el screenshot como PNG sin optimizar: ~500KB-1MB por
    slide. Antes se cuantizaba a paleta de 256 colores para bajar eso a
    ~150-200KB, pero esa pieza queda tal cual como fuente para el JPEG que
    sube a TikTok (content_hosting.py) y para la vista previa de Telegram —
    256 colores mete banding visible en degradés y sobre todo en las fotos
    reales (slide tipo 'foto'), que dejan de verse HD. La recompresión
    lossless (mismo color verdadero, solo re-empaqueta los bytes con zlib al
    máximo) evita eso y sigue pesando una fracción de lo que tira Chrome."""
    img = Image.open(path).convert("RGB")
    img.save(path, "PNG", optimize=True, compress_level=9)
