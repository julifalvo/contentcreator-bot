"""Arma un MP4 vertical (formato TikTok) a partir de las imágenes ya generadas
por generate.py y una pista de música local, usando ffmpeg.

No hace falta instalar ffmpeg aparte: imageio-ffmpeg trae un binario estático
que se descarga solo la primera vez que se usa (gratis, sin registro).

Música: poné tus propios archivos .mp3/.m4a/.wav (libres de derechos, ej. de la
YouTube Audio Library o Pixabay Music) en la carpeta music/. Se elige uno al
azar y se recorta/repite para que dure lo mismo que el video. Si no hay ningún
archivo en music/, el video sale sin audio.
"""

import random
import subprocess
from pathlib import Path

import imageio_ffmpeg

SLIDE_DURATION_SEC = 3.2
MUSIC_DIR = Path(__file__).parent / "music"
MUSIC_EXTS = {".mp3", ".m4a", ".wav", ".aac"}


def _pick_music() -> Path | None:
    if not MUSIC_DIR.exists():
        return None
    tracks = [p for p in MUSIC_DIR.iterdir() if p.suffix.lower() in MUSIC_EXTS]
    return random.choice(tracks) if tracks else None


def build_video(folder: Path, out_name: str = "video.mp4") -> Path:
    """Arma el video a partir de las imágenes NN_*.png de `folder`, en orden de nombre."""
    images = sorted(folder.glob("[0-9][0-9]_*.png"))
    if not images:
        raise RuntimeError(f"No se encontraron imágenes numeradas (NN_*.png) en {folder}")

    concat_path = folder / "_concat.txt"
    lines = []
    for img in images:
        lines.append(f"file '{img.name}'")
        lines.append(f"duration {SLIDE_DURATION_SEC}")
    lines.append(f"file '{images[-1].name}'")  # ffmpeg exige repetir el último frame sin duration
    concat_path.write_text("\n".join(lines), encoding="utf-8")

    music = _pick_music()
    out_path = folder / out_name
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    cmd = [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_path.name)]
    if music:
        cmd += ["-stream_loop", "-1", "-i", str(music.resolve())]
    cmd += [
        "-vf", "scale=1080:1920,format=yuv420p",
        "-r", "30",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
    ]
    if music:
        cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += [out_name]

    result = subprocess.run(cmd, cwd=folder, capture_output=True, text=True)
    concat_path.unlink(missing_ok=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg falló armando el video:\n{result.stderr[-2000:]}")

    return out_path
