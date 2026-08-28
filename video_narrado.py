"""Arma el video narrado final: por cada escena de video_rules.py, baja un
clip de b-roll de Pexels, sintetiza la locución con ElevenLabs y recorta el
clip a la duración exacta de esa locución. Al final concatena todas las
escenas y mezcla la narración completa con música de fondo baja (opcional,
reusa music/ como video_gen.py).

Todo con ffmpeg (vía imageio_ffmpeg, el mismo binario que ya usa video_gen.py
para el carrusel-en-video) y llamadas separadas por escena en vez de un único
filtro gigante: así un fallo en una escena da un error legible en vez de un
filtro complejo ilegible.
"""

import re
import subprocess
from pathlib import Path

import imageio_ffmpeg

import elevenlabs_client
import pexels_client
from video_gen import pick_music

CANVAS_W, CANVAS_H = 1080, 1920
MUSICA_FONDO_VOLUMEN = 0.12  # baja de más: la narración tiene que ganarle siempre


def _ffmpeg() -> str:
    return imageio_ffmpeg.get_ffmpeg_exe()


def _duracion_segundos(path: Path) -> float:
    """ffmpeg -i sin salida igual imprime la duración del archivo en stderr
    (y termina con código de error porque no le dimos un output — es
    esperado, solo nos interesa el texto)."""
    result = subprocess.run([_ffmpeg(), "-i", str(path)], capture_output=True, text=True)
    match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", result.stderr)
    if not match:
        raise RuntimeError(f"No se pudo leer la duración de {path.name}: {result.stderr[-500:]}")
    h, m, s = match.groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


def _armar_escena(bg_path: Path, duracion: float, out_path: Path) -> None:
    vf = f"scale={CANVAS_W}:{CANVAS_H}:force_original_aspect_ratio=increase,crop={CANVAS_W}:{CANVAS_H}"
    cmd = [
        _ffmpeg(), "-y",
        "-stream_loop", "-1", "-i", str(bg_path),
        "-t", f"{duracion:.2f}",
        "-vf", vf,
        "-an",
        "-r", "30",
        "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
        str(out_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg falló armando la escena {out_path.name}:\n{result.stderr[-2000:]}")


def _concat(archivos: list[Path], out_path: Path, extra_args: list[str]) -> None:
    """`archivos` vive en tmp/ (subcarpeta de escenas), no al lado de
    `out_path` — por eso el concat list usa la ruta relativa a
    out_path.parent (que es el cwd del proceso ffmpeg) en vez de solo el
    nombre, o ffmpeg no los encuentra ('Impossible to open ...')."""
    concat_txt = out_path.parent / f"_concat_{out_path.stem}.txt"
    concat_txt.write_text(
        "\n".join(f"file '{a.relative_to(out_path.parent).as_posix()}'" for a in archivos),
        encoding="utf-8",
    )
    cmd = [_ffmpeg(), "-y", "-f", "concat", "-safe", "0", "-i", concat_txt.name, *extra_args, out_path.name]
    result = subprocess.run(cmd, cwd=out_path.parent, capture_output=True, text=True)
    concat_txt.unlink(missing_ok=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg falló concatenando {out_path.name}:\n{result.stderr[-2000:]}")


def build_video(folder: Path, data: dict, out_name: str = "video.mp4") -> Path:
    """Arma el video narrado completo en `folder` a partir de `data`
    (el dict validado por video_rules.validate, con 'escenas'). Devuelve el
    path del mp4 final."""
    escenas = data["escenas"]
    tmp = folder / "_escenas"
    tmp.mkdir(exist_ok=True)

    clips_video: list[Path] = []
    clips_audio: list[Path] = []
    for i, esc in enumerate(escenas, 1):
        print(f"  Escena {i}/{len(escenas)}: locución...")
        voz_path = tmp / f"{i:02d}_voz.mp3"
        elevenlabs_client.sintetizar(esc["narracion"], voz_path)
        duracion = _duracion_segundos(voz_path)

        print(f"  Escena {i}/{len(escenas)}: b-roll ({esc['b_roll']!r})...")
        bg_path = tmp / f"{i:02d}_bg.mp4"
        pexels_client.descargar_clip(esc["b_roll"], bg_path)

        clip_path = tmp / f"{i:02d}_clip.mp4"
        _armar_escena(bg_path, duracion, clip_path)

        clips_video.append(clip_path)
        clips_audio.append(voz_path)

    print("  Uniendo escenas...")
    video_mudo = folder / "_video_mudo.mp4"
    _concat(clips_video, video_mudo, ["-c", "copy"])

    voz_completa = folder / "_voz_completa.mp3"
    _concat(clips_audio, voz_completa, ["-c", "copy"])

    out_path = folder / out_name
    musica = pick_music()
    if musica:
        cmd = [
            _ffmpeg(), "-y",
            "-i", str(video_mudo),
            "-i", str(voz_completa),
            "-stream_loop", "-1", "-i", str(musica.resolve()),
            "-filter_complex",
            f"[2:a]volume={MUSICA_FONDO_VOLUMEN}[bg];[1:a][bg]amix=inputs=2:duration=first:dropout_transition=2[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            str(out_path),
        ]
    else:
        cmd = [
            _ffmpeg(), "-y",
            "-i", str(video_mudo),
            "-i", str(voz_completa),
            "-map", "0:v", "-map", "1:a",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            str(out_path),
        ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg falló mezclando el video final:\n{result.stderr[-2000:]}")

    # Los intermedios (voz/b-roll/clip por escena, video mudo, voz completa)
    # ya están mezclados en out_path — dejarlos tirados infla cada carpeta de
    # pieza varios MB por escena sin aportar nada una vez que el final existe.
    video_mudo.unlink(missing_ok=True)
    voz_completa.unlink(missing_ok=True)
    for f in tmp.iterdir():
        f.unlink()
    tmp.rmdir()

    return out_path
