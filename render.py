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


def _screenshot(html: str, out_path: Path, escala: int = ESCALA_RENDER) -> None:
    """Le pide a Chrome headless el screenshot de `html` en `out_path`
    (siempre 1080x1920 a 2x, sin bajar de tamaño ni recomprimir todavía —
    eso lo hace cada función pública según si necesita conservar el canal
    alfa o no). Chrome escribe el screenshot relativo a SU cwd, no al
    nuestro: si no le pasamos la ruta absoluta, falla con "no puede
    encontrar la ruta"."""
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "page.html"
        src.write_text(html, encoding="utf-8")

        result = subprocess.run(
            [
                _find_browser(),
                "--headless",
                "--disable-gpu",
                "--hide-scrollbars",
                "--no-sandbox",  # necesario para correr como servicio en Ubuntu
                # Perfil propio y descartable por render. Sin esto todas las
                # instancias comparten el perfil por defecto y Chrome las
                # serializa esperando el lock: rindiendo frames de video en
                # paralelo (demo_build.py) eso tiraba la ganancia a cero.
                f"--user-data-dir={Path(tmp) / 'chrome'}",
                f"--force-device-scale-factor={escala}",
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


def html_to_png(html: str, out_path: Path) -> Path:
    """Rinde `html` a un PNG de 1080x1920 (9:16, el tamano que TikTok recomienda para carruseles de fotos)."""
    out_path = out_path.resolve()
    _screenshot(html, out_path)
    _bajar_a_final(out_path)
    _recomprimir(out_path)
    return out_path


def html_to_png_transparent(html: str, out_path: Path) -> Path:
    """Como html_to_png(), pero conserva el canal alfa: para overlays de texto
    en pantalla que se superponen sobre un video (reel_build.py) en vez de
    fotos completas. Sin el flatten a RGB de _recomprimir(), que pintaría de
    negro/blanco todo lo transparente."""
    out_path = out_path.resolve()
    _screenshot(html, out_path)

    img = Image.open(out_path)
    if img.width != ANCHO_FINAL:
        alto = round(img.height * ANCHO_FINAL / img.width)
        img = img.resize((ANCHO_FINAL, alto), Image.LANCZOS)
    img.save(out_path, "PNG", optimize=True, compress_level=9)
    return out_path


def html_to_png_frame(html: str, out_path: Path) -> Path:
    """Como html_to_png(), pero para FRAMES DE VIDEO (demo_build.py), donde se
    rinden decenas de imágenes por pieza y después las come ffmpeg.

    Dos atajos respecto de html_to_png(), los dos por costo — acá se rinden
    cientos de imágenes por pieza, no seis:

    1. Rinde a escala 1 (1080x1920 directo) en vez del supersampling a 2x con
       bajada Lanczos. Ese 2x existe para que el texto aguante el JPEG y el
       recompresor de TikTok en una FOTO fija; un frame de video se lo come
       igual el H.264, y rendir cuatro veces menos píxeles es la diferencia
       entre un demo que tarda dos minutos y uno que tarda ocho.
    2. Salta la recompresión lossless de _recomprimir() (zlib al máximo): sirve
       cuando el PNG es el entregable, pero éste vive unos segundos en una
       carpeta temporal y termina adentro del mp4."""
    out_path = out_path.resolve()
    _screenshot(html, out_path, escala=1)
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
