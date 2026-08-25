"""Aloja las imágenes de una pieza en GitHub Pages (repo rootbusinessai-legal,
carpeta content/) para poder usarlas como URL pública en el carrusel de fotos
de TikTok — la API de fotos (PULL_FROM_URL) exige que cada imagen esté en una
URL pública de un dominio/prefijo que ya verificaste ante TikTok, no admite
subir el archivo directo como el video.

Requiere tener clonado localmente el repo (una vez):
    git clone https://github.com/julifa/rootbusinessai-legal.git _legal_repo
Con permisos de push ya autenticados en esta máquina (vía git/gh).
"""

import subprocess
import time
from pathlib import Path

import requests
from PIL import Image

REPO_DIR = Path(__file__).parent / "_legal_repo"
CONTENT_DIR = REPO_DIR / "content"
PUBLIC_BASE_URL = "https://julifa.github.io/rootbusinessai-legal/content"


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
    en el mismo orden que image_paths. Pisa el contenido anterior de content/
    para no hacer crecer el repo sin límite (solo hace falta la pieza vigente)."""
    if not REPO_DIR.exists():
        raise RuntimeError(
            f"No existe {REPO_DIR}. Cloná el repo de hosting una vez con:\n"
            f"  git clone https://github.com/julifa/rootbusinessai-legal.git {REPO_DIR}"
        )

    _run_git("pull", "--ff-only", "origin", "main")

    CONTENT_DIR.mkdir(exist_ok=True)
    for old in CONTENT_DIR.glob("*.jpg"):
        old.unlink()

    urls = []
    for i, path in enumerate(image_paths):
        img = Image.open(path).convert("RGB")
        name = f"slide-{i + 1:02d}.jpg"
        img.save(CONTENT_DIR / name, "JPEG", quality=92)
        urls.append(f"{PUBLIC_BASE_URL}/{name}")

    _run_git("add", "content")
    commit = _run_git("commit", "-m", "Actualiza imágenes de contenido para publicar")
    if commit.returncode != 0 and "nothing to commit" not in commit.stdout:
        raise RuntimeError(f"git commit falló:\n{commit.stderr}")

    push = _run_git("push", "origin", "main")
    if push.returncode != 0:
        raise RuntimeError(f"git push falló:\n{push.stderr}")

    _wait_until_live(urls[0])
    return urls
