"""Aloja las imágenes de una pieza en GitHub Pages (repo rootbusinessai-legal,
carpeta content/) para poder usarlas como URL pública en el carrusel de fotos
de TikTok — la API de fotos (PULL_FROM_URL) exige que cada imagen esté en una
URL pública de un dominio/prefijo que ya verificaste ante TikTok, no admite
subir el archivo directo como el video.

Requiere tener clonado localmente el repo (una vez):
    git clone https://github.com/julifalvo/rootbusinessai-legal.git _legal_repo
Con permisos de push ya autenticados en esta máquina (vía git/gh).
"""

import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path

import requests
from PIL import Image

REPO_DIR = Path(__file__).parent / "_legal_repo"
CONTENT_DIR = REPO_DIR / "content"
PUBLIC_BASE_URL = "https://julifalvo.github.io/rootbusinessai-legal/content"

# Cuántas publicaciones anteriores conservar en el repo antes de purgarlas
# (además de la que se acaba de subir). Solo para no dejar crecer el repo sin
# límite; no hace falta más que esto para servir el post recién publicado.
_CONSERVAR = 3


def _run_git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=REPO_DIR, capture_output=True, text=True)


def _wait_until_live(url: str, timeout_sec: int = 120) -> None:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            if requests.head(url, timeout=10).status_code == 200:
                return
        except requests.exceptions.RequestException:
            pass
        time.sleep(4)
    raise TimeoutError(f"{url} no quedó accesible a tiempo (¿tardó de más en desplegar GitHub Pages?)")


def publish_images(image_paths: list[Path]) -> list[str]:
    """Convierte a JPEG, sube al repo de hosting y devuelve las URLs públicas
    en el mismo orden que image_paths.

    Cada publicación va a una subcarpeta con nombre único (timestamp), NUNCA
    reescribe una URL ya usada. GitHub Pages se sirve por una CDN (Fastly) que
    cachea por URL, y TikTok también cachea las imágenes que trae por
    PULL_FROM_URL: reusar el mismo nombre de archivo ("slide-01.jpg" siempre)
    hacía que a veces se sirviera la foto de una publicación anterior aunque
    el repo ya tuviera la nueva — una URL nunca antes vista no tiene nada
    viejo que servir. Se purgan las publicaciones más viejas para no dejar
    crecer el repo sin límite."""
    if not REPO_DIR.exists():
        raise RuntimeError(
            f"No existe {REPO_DIR}. Cloná el repo de hosting una vez con:\n"
            f"  git clone https://github.com/julifalvo/rootbusinessai-legal.git {REPO_DIR}"
        )

    _run_git("pull", "--ff-only", "origin", "main")

    CONTENT_DIR.mkdir(exist_ok=True)
    tanda = datetime.now().strftime("%Y%m%d-%H%M%S")
    tanda_dir = CONTENT_DIR / tanda
    tanda_dir.mkdir(exist_ok=True)

    urls = []
    for i, path in enumerate(image_paths):
        img = Image.open(path).convert("RGB")
        name = f"slide-{i + 1:02d}.jpg"
        # calidad máxima y sin subsampling de croma: nuestras imágenes son
        # texto nítido sobre colores planos, no fotos — el subsampling 4:2:0
        # por default de JPEG le mete "ringing" a los bordes del texto y a
        # simple vista se ve borroso/con artefactos de color.
        img.save(tanda_dir / name, "JPEG", quality=100, subsampling=0)
        urls.append(f"{PUBLIC_BASE_URL}/{tanda}/{name}")

    # Purga tandas viejas (se conservan las _CONSERVAR más recientes además
    # de la que se acaba de crear) para no acumular publicaciones para siempre.
    tandas = sorted((p for p in CONTENT_DIR.iterdir() if p.is_dir()), key=lambda p: p.name)
    for vieja in tandas[:-(_CONSERVAR + 1)]:
        shutil.rmtree(vieja, ignore_errors=True)

    _run_git("add", "content")
    commit = _run_git("commit", "-m", f"Publica tanda {tanda}")
    if commit.returncode != 0 and "nothing to commit" not in commit.stdout:
        raise RuntimeError(f"git commit falló:\n{commit.stderr}")

    push = _run_git("push", "origin", "main")
    if push.returncode != 0:
        raise RuntimeError(f"git push falló:\n{push.stderr}")

    _wait_until_live(urls[0])
    return urls
