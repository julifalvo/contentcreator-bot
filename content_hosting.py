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


def _commit_and_push(mensaje: str) -> None:
    _run_git("add", "content")
    commit = _run_git("commit", "-m", mensaje)
    if commit.returncode != 0 and "nothing to commit" not in commit.stdout:
        raise RuntimeError(f"git commit falló:\n{commit.stderr}")

    push = _run_git("push", "origin", "main")
    if push.returncode != 0:
        raise RuntimeError(f"git push falló:\n{push.stderr}")


def _purgar_tandas_viejas() -> None:
    """Conserva las _CONSERVAR tandas más recientes (de cualquier tipo,
    fotos o video) además de la que se acaba de crear."""
    tandas = sorted((p for p in CONTENT_DIR.iterdir() if p.is_dir()), key=lambda p: p.name)
    for vieja in tandas[:-(_CONSERVAR + 1)]:
        shutil.rmtree(vieja, ignore_errors=True)


def publish_video(video_path: Path) -> str:
    """Sube un .mp4 al mismo repo de hosting que publish_images() y devuelve
    su URL pública. Hace falta para Instagram (Reels y Stories de video): a
    diferencia de TikTok (que acepta subir el archivo directo), la Graph API
    de contenido solo admite video_url apuntando a una URL pública, igual que
    ya exige para las fotos del carrusel."""
    if not REPO_DIR.exists():
        raise RuntimeError(
            f"No existe {REPO_DIR}. Cloná el repo de hosting una vez con:\n"
            f"  git clone https://github.com/julifalvo/rootbusinessai-legal.git {REPO_DIR}"
        )

    _run_git("pull", "--ff-only", "origin", "main")

    CONTENT_DIR.mkdir(exist_ok=True)
    # Sufijo "-v" para no colisionar con una tanda de fotos creada en el
    # mismo segundo cuando una pieza se publica en TikTok e Instagram juntos.
    tanda = datetime.now().strftime("%Y%m%d-%H%M%S") + "-v"
    tanda_dir = CONTENT_DIR / tanda
    tanda_dir.mkdir(exist_ok=True)

    name = "video.mp4"
    shutil.copyfile(video_path, tanda_dir / name)
    url = f"{PUBLIC_BASE_URL}/{tanda}/{name}"

    _purgar_tandas_viejas()
    _commit_and_push(f"Publica video {tanda}")
    _wait_until_live(url)
    return url


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
        # Sin subsampling de croma (4:4:4): nuestras imágenes son texto nítido
        # sobre colores planos, no fotos — el 4:2:0 por default de JPEG le mete
        # "ringing" a los bordes del texto y a simple vista se ve borroso y con
        # artefactos de color. Eso es lo que NO se negocia.
        #
        # La calidad, en cambio, bajó de 100 a 95 cuando el render pasó a
        # 1440x3200 (ver render.py): a q100 cada slide pesaba ~3 MB y una
        # publicación de 8 slides metía 24 MB en un repo de git, que no olvida
        # nunca. Medido contra q100 sobre piezas reales, q95 da PSNR ~46 dB
        # -bien arriba del umbral de "visualmente sin pérdida", ~40 dB- y pesa
        # un tercio. O sea: el archivo pesa lo mismo que antes del cambio de
        # resolución, pero con el doble de píxeles adentro.
        img.save(tanda_dir / name, "JPEG", quality=95, subsampling=0)
        urls.append(f"{PUBLIC_BASE_URL}/{tanda}/{name}")

    _purgar_tandas_viejas()
    _commit_and_push(f"Publica tanda {tanda}")
    _wait_until_live(urls[0])
    return urls
