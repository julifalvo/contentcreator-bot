"""Arma el Reel final (sin voz IA): por cada beat del guion (reel_rules.py)
baja un clip de b-roll de Pexels, le superpone el texto en pantalla (PNG
transparente, ver design.build_reel_overlay_html/render.html_to_png_transparent)
y recorta el clip a una duración calculada por cantidad de palabras — a
diferencia de video_narrado.py, acá no hay locución cuya duración marque el
corte de cada escena. Al final concatena los beats y mezcla música de fondo,
la única pista de audio del video (sin narración que tapar, va bastante más
alta que en video_narrado.py).

build_tip_reel() es una segunda variante ("formato 'reel_tips'", ver
generate.build_tip_reel_piece): en vez de un clip de b-roll distinto por beat,
usa UN SOLO clip "aesthetic" fijo (FONDOS_AESTHETIC: laptop, café, escritorio,
notebook) que se repite atrás de toda la pieza, con el contenido educativo de
'sabías que...?' saliendo como tarjetas flotantes (design.build_popup_overlay_html)
en vez del texto blanco con velo de build_reel().
"""

import random
import subprocess
from pathlib import Path

import imageio_ffmpeg

import design
import pexels_client
import render
from video_gen import pick_music

CANVAS_W, CANVAS_H = 1080, 1920
MUSICA_VOLUMEN = 0.45  # sin narración que tapar, bastante más alta que en video_narrado.py (0.12)

# Fondo "aesthetic" fijo del formato 'reel_tips' (ver build_tip_reel): un solo
# clip de escritorio/laptop/café -o similares, cuidando que todos compartan el
# mismo clima cálido y minimal- que se repite (loop) atrás de TODAS las
# tarjetas del reel, en vez de un clip de b-roll distinto por beat como hace
# el reel de caso (build_reel). Es el look que pidió replicar este formato:
# una sola toma de escritorio con laptop y café, con las tarjetas de consejo
# apareciendo una tras otra encima.
FONDOS_AESTHETIC = [
    "laptop coffee cup desk top view",
    "hands typing laptop coffee mug desk",
    "cozy home office desk coffee morning light",
    "notebook coffee cup flat lay desk",
    "minimal desk setup laptop plant coffee",
    "working from home desk coffee light aesthetic",
    "laptop notebook coffee cup aesthetic desk",
    "coffee cup steam laptop desk workspace",
]

# Tipos de slide de 'sabías que...?' (ver content_rules.get_sabias_que_system_prompt)
# que cuentan como "punto" numerado dentro del reel: portada/cierre abren y
# cierran sin número (son el gancho y el remate, no un ítem de la lista).
_TIPOS_NUMERADOS = {"texto", "dato", "comparacion", "codigo"}

# Velocidad de lectura estimada para calcular cuánto dura en pantalla cada
# beat: ritmo cómodo para leer un texto corto en un feed, ni tan rápido que
# no se alcance a leer ni tan lento que se sienta muerto.
_PALABRAS_POR_SEGUNDO = 2.3
_DURACION_BASE_SEC = 1.0
_DURACION_MIN_SEC = 1.8
_DURACION_MAX_SEC = 4.6


def _duracion_texto(texto: str) -> float:
    palabras = len(texto.split())
    segundos = _DURACION_BASE_SEC + palabras / _PALABRAS_POR_SEGUNDO
    return max(_DURACION_MIN_SEC, min(_DURACION_MAX_SEC, segundos))


def _ffmpeg() -> str:
    return imageio_ffmpeg.get_ffmpeg_exe()


def _armar_beat(bg_path: Path, overlay_path: Path, duracion: float, out_path: Path) -> None:
    vf_bg = f"scale={CANVAS_W}:{CANVAS_H}:force_original_aspect_ratio=increase,crop={CANVAS_W}:{CANVAS_H}"
    cmd = [
        _ffmpeg(), "-y",
        "-stream_loop", "-1", "-i", str(bg_path),
        "-i", str(overlay_path),
        "-t", f"{duracion:.2f}",
        "-filter_complex", f"[0:v]{vf_bg}[bg];[bg][1:v]overlay=0:0[v]",
        "-map", "[v]",
        "-an",
        "-r", "30",
        "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
        str(out_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg falló armando el beat {out_path.name}:\n{result.stderr[-2000:]}")


def _concat(archivos: list[Path], out_path: Path, extra_args: list[str]) -> None:
    """`archivos` vive en tmp/ (subcarpeta de beats), no al lado de
    `out_path` — por eso el concat list usa la ruta relativa a
    out_path.parent (el cwd del proceso ffmpeg) en vez de solo el nombre, o
    ffmpeg no los encuentra ('Impossible to open ...')."""
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


def _beats(data: dict) -> list[dict]:
    """Aplana hook + desarrollo + cta en una sola lista de beats, en orden."""
    return [data["hook"], *data["desarrollo"], data["cta"]]


def _mezclar_musica_y_cerrar(folder: Path, tmp: Path, video_mudo: Path, out_path: Path) -> Path:
    """Cola compartida por build_reel/build_tip_reel: mezcla música de fondo
    (si hay alguna disponible, ver pick_music) sobre el video ya concatenado
    y limpia los archivos temporales de `tmp`. Devuelve `out_path`."""
    musica = pick_music()
    if musica:
        cmd = [
            _ffmpeg(), "-y",
            "-i", str(video_mudo),
            "-stream_loop", "-1", "-i", str(musica.resolve()),
            "-filter_complex", f"[1:a]volume={MUSICA_VOLUMEN}[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            str(out_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg falló mezclando la música:\n{result.stderr[-2000:]}")
        video_mudo.unlink(missing_ok=True)
    else:
        # replace() y no rename(): en Windows rename() falla si el destino ya
        # existe (WinError 183), cosa que pasa al rearmar una pieza que ya
        # tenía su video.
        video_mudo.replace(out_path)

    for f in tmp.iterdir():
        f.unlink()
    tmp.rmdir()

    return out_path


def build_reel(folder: Path, data: dict, out_name: str = "video.mp4") -> Path:
    """Arma el Reel completo en `folder` a partir de `data` (el dict validado
    por reel_rules.validate). Devuelve el path del mp4 final."""
    beats = _beats(data)
    tmp = folder / "_beats"
    tmp.mkdir(exist_ok=True)

    clips: list[Path] = []
    for i, beat in enumerate(beats, 1):
        print(f"  Beat {i}/{len(beats)}: b-roll ({beat['visual']!r})...")
        bg_path = tmp / f"{i:02d}_bg.mp4"
        pexels_client.descargar_clip(beat["visual"], bg_path)

        overlay_path = tmp / f"{i:02d}_overlay.png"
        render.html_to_png_transparent(design.build_reel_overlay_html(beat["texto_pantalla"]), overlay_path)

        duracion = _duracion_texto(beat["texto_pantalla"])
        clip_path = tmp / f"{i:02d}_clip.mp4"
        _armar_beat(bg_path, overlay_path, duracion, clip_path)
        clips.append(clip_path)

    print("  Uniendo beats...")
    video_mudo = folder / "_video_mudo.mp4"
    _concat(clips, video_mudo, ["-c", "copy"])

    out_path = folder / out_name
    return _mezclar_musica_y_cerrar(folder, tmp, video_mudo, out_path)


def _slide_a_popup(slide: dict, numero: int | None) -> dict:
    """Traduce una slide del formato 'sabías que...?' (content_rules.py, sin
    caso ni solución puntual -es el que mejor calza con una tarjeta de
    consejo suelta) a los parámetros de design.build_popup_overlay_html.
    Cubre los seis tipos que ese formato puede devolver (ver
    content_rules.validate_sabias_que); el resto ('foto') no aplica acá
    porque el reel 'tips' nunca pide con_foto=True."""
    tipo = slide.get("tipo")
    if tipo == "portada":
        return {"emoji": "🎯", "numero": None, "kicker": "",
                "titulo": slide["titular"], "cuerpo": slide.get("epigrafe", "")}
    if tipo == "cierre":
        return {"emoji": "✅", "numero": None, "kicker": "",
                "titulo": slide["titular"], "cuerpo": slide.get("accion", "")}
    if tipo == "texto":
        return {"emoji": "💡", "numero": numero, "kicker": "TIP",
                "titulo": slide["titular"], "cuerpo": slide.get("cuerpo", "")}
    if tipo == "dato":
        return {"emoji": "📊", "numero": numero, "kicker": "DATO",
                "titulo": f"{slide['numero']} {slide['unidad']}", "cuerpo": slide.get("detalle", "")}
    if tipo == "cita":
        return {"emoji": "💬", "numero": None, "kicker": "",
                "titulo": slide["texto"], "cuerpo": "", "nota": slide.get("autor", "")}
    if tipo == "comparacion":
        cuerpo = " · ".join(slide.get("agente", [])[:3])
        return {"emoji": "⚡", "numero": numero, "kicker": "ASÍ SE HACE",
                "titulo": slide["titular"], "cuerpo": cuerpo}
    if tipo == "codigo":
        return {"emoji": "⚙️", "numero": numero, "kicker": "POR DENTRO",
                "titulo": slide["titular"], "cuerpo": ""}
    # Defensivo: si algún día 'sabías que' suma un tipo nuevo, mejor una
    # tarjeta genérica que un KeyError que tira abajo todo el reel.
    titulo = slide.get("titular") or slide.get("texto") or "..."
    cuerpo = slide.get("cuerpo") or slide.get("detalle") or slide.get("accion") or ""
    return {"emoji": "", "numero": numero, "kicker": "", "titulo": titulo, "cuerpo": cuerpo}


def build_tip_reel(folder: Path, data: dict, out_name: str = "video.mp4") -> Path:
    """Arma el Reel 'aesthetic' (formato 'reel_tips', ver generate.build_tip_reel_piece):
    contenido del formato 'sabías que...?' (data['slides']), pero en vez del
    carrusel de papel editorial cada slide sale como una tarjeta flotante
    (design.build_popup_overlay_html) arriba de UN SOLO clip de b-roll
    "aesthetic" (FONDOS_AESTHETIC) que se repite en todo el video -a
    diferencia de build_reel(), que baja un clip de b-roll distinto por beat."""
    slides = data["slides"]
    tmp = folder / "_beats"
    tmp.mkdir(exist_ok=True)

    query = random.choice(FONDOS_AESTHETIC)
    print(f"  Fondo aesthetic ({query!r}), un solo clip para todo el reel...")
    bg_path = tmp / "00_bg.mp4"
    pexels_client.descargar_clip(query, bg_path)

    palette = design.pick_palette()
    clips: list[Path] = []
    numero = 0
    for i, slide in enumerate(slides, 1):
        if slide.get("tipo") in _TIPOS_NUMERADOS:
            numero += 1
            info = _slide_a_popup(slide, numero)
        else:
            info = _slide_a_popup(slide, None)
        print(f"  Tarjeta {i}/{len(slides)} ({slide.get('tipo')}): {info['titulo'][:60]!r}...")

        overlay_path = tmp / f"{i:02d}_overlay.png"
        html_overlay = design.build_popup_overlay_html(palette=palette, **info)
        render.html_to_png_transparent(html_overlay, overlay_path)

        texto_completo = " ".join(filter(None, [info["titulo"], info.get("cuerpo", ""), info.get("nota", "")]))
        duracion = _duracion_texto(texto_completo)
        clip_path = tmp / f"{i:02d}_clip.mp4"
        _armar_beat(bg_path, overlay_path, duracion, clip_path)
        clips.append(clip_path)

    print("  Uniendo tarjetas...")
    video_mudo = folder / "_video_mudo.mp4"
    _concat(clips, video_mudo, ["-c", "copy"])

    out_path = folder / out_name
    return _mezclar_musica_y_cerrar(folder, tmp, video_mudo, out_path)
