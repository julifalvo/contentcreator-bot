"""Arma el video del formato 'demo': demostraciones gráficas ANIMADAS de un
producto funcionando (ver demo_designs.py para las escenas y demo_rules.py
para el guion que las llena).

CÓMO SE ANIMA, en concreto:
Chrome headless no graba video, saca una foto por HTML. Así que cada escena
de demo_designs.py está escrita como función del tiempo —`build_escena_html(escena, acento, t)`
con t de 0 a 1— y acá se la llama muchas veces con t distinto. Cada resultado
es un frame, y ffmpeg los junta como secuencia de imágenes.

Todos los frames de todas las escenas se numeran en UNA sola secuencia
correlativa a FPS fijo. Eso deja armar el video entero con una única llamada a
ffmpeg (una secuencia de imágenes a `-framerate`), en vez de un clip por escena
más un concat como hace reel_build.py — ahí cada beat dura lo que dura su clip
de b-roll y hay que cortarlos por separado; acá el tiempo lo controlamos
nosotros frame a frame, así que la duración de cada escena es simplemente
cuántos frames le tocan.

El costo real de la pieza es el render de los frames (~1s de Chrome cada uno),
por eso van en paralelo: es lo único que separa un demo de 25 segundos de
tardar medio minuto o cinco.
"""

import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import imageio_ffmpeg

import demo_designs
import render
from video_gen import pick_music

CANVAS_W, CANVAS_H = 1080, 1920

# FPS de la ANIMACIÓN (cuántos frames se rinden por segundo de escena) y FPS
# del archivo final. Rendir a 30 sería 3x el costo de Chrome para una ganancia
# que no se ve: son animaciones de interfaz (barras, contadores, burbujas),
# no movimiento real de cámara, y a 12 leen fluidas. ffmpeg reexpande a 30
# para que las plataformas no lo traten como video raro.
FPS_ANIM = 12
FPS_SALIDA = 30

# Cuánto dura cada escena en pantalla. El pedido de este formato es que las
# demostraciones "ocurran rápido": son cortas a propósito, lo justo para leer
# el titular y ver la animación cerrar.
_DUR_BASE_SEC = 1.5
_PALABRAS_POR_SEGUNDO = 3.2
_DUR_MIN_SEC = 2.2
_DUR_MAX_SEC = 3.6

# Chrome es un proceso por frame: el cuello es esperar a que arranque y pinte,
# no CPU nuestra, así que conviene tener varios volando a la vez. 6 es el punto
# donde deja de mejorar en una máquina de escritorio común y todavía no se come
# toda la RAM.
_WORKERS = 6

MUSICA_VOLUMEN = 0.5  # sin voz que tapar, igual que reel_build.py


def _ffmpeg() -> str:
    return imageio_ffmpeg.get_ffmpeg_exe()


def _texto_de_escena(escena: dict) -> str:
    """Todo el texto que quien mira tiene que alcanzar a leer en esa escena.
    Sirve para calcular cuánto dejarla en pantalla: una escena con un titular
    largo y cinco ítems necesita más tiempo que una con un número grande."""
    partes = [escena.get("titular", ""), escena.get("bajada", "")]
    for valor in escena.values():
        if isinstance(valor, str):
            partes.append(valor)
        elif isinstance(valor, list):
            for item in valor:
                if isinstance(item, str):
                    partes.append(item)
                elif isinstance(item, dict):
                    partes += [str(v) for v in item.values() if isinstance(v, str)]
    return " ".join(partes)


def _duracion(escena: dict) -> float:
    palabras = len(_texto_de_escena(escena).split())
    segundos = _DUR_BASE_SEC + palabras / _PALABRAS_POR_SEGUNDO
    return max(_DUR_MIN_SEC, min(_DUR_MAX_SEC, segundos))


def _plan_de_frames(escenas: list[dict]) -> list[tuple[dict, float]]:
    """Devuelve la lista completa de (escena, t) a rendir, en orden de video.

    `t` recorre 0..1 dentro de cada escena. El último frame se calcula sobre
    n-1 y no sobre n para que toda escena termine exactamente en t=1 (su
    estado final, con la animación cerrada): si se dividiera por n, la última
    imagen quedaría siempre un pelito antes de terminar y las animaciones se
    verían cortadas justo antes del final."""
    plan: list[tuple[dict, float]] = []
    for escena in escenas:
        n = max(2, int(round(_duracion(escena) * FPS_ANIM)))
        for i in range(n):
            plan.append((escena, i / (n - 1)))
    return plan


def _render_frames(plan: list[tuple[dict, float]], acento: dict, destino: Path) -> None:
    """Rinde en paralelo todos los frames del plan a destino/f00001.png..."""
    def _uno(args) -> None:
        i, (escena, t) = args
        html = demo_designs.build_escena_html(escena, acento, t)
        render.html_to_png_frame(html, destino / f"f{i:05d}.png")

    with ThreadPoolExecutor(max_workers=_WORKERS) as pool:
        # list() fuerza a consumir el iterador: sin esto las excepciones de los
        # workers se tragarían en silencio y el video saldría con frames faltantes.
        list(pool.map(_uno, enumerate(plan, 1)))


def _armar_video(frames_dir: Path, out_path: Path) -> None:
    """Junta la secuencia de PNGs en un mp4. Una sola llamada a ffmpeg para
    todo el video: la secuencia ya está numerada en orden y a FPS constante."""
    cmd = [
        _ffmpeg(), "-y",
        "-framerate", str(FPS_ANIM),
        "-i", str(frames_dir / "f%05d.png"),
        "-r", str(FPS_SALIDA),
        "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
        # Las plataformas recomprimen todo: un GOP corto y sin B-frames raros
        # hace que el primer frame (la miniatura) no salga con artefactos.
        "-g", str(FPS_SALIDA * 2),
        str(out_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg falló armando el demo:\n{result.stderr[-2000:]}")


def _mezclar_musica(video_mudo: Path, out_path: Path) -> None:
    musica = pick_music()
    if not musica:
        # replace() y no rename(): en Windows rename() explota si el destino ya
        # existe (WinError 183), y rearmar el video sobre una carpeta que ya
        # tenía uno es justo lo que se hace al reprocesar una pieza.
        video_mudo.replace(out_path)
        return
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


def build_demo(folder: Path, data: dict, out_name: str = "video.mp4") -> Path:
    """Arma el video de demo completo en `folder` a partir de `data` (el dict
    ya validado por demo_rules.validate). Devuelve el path del mp4 final."""
    escenas = data["escenas"]
    acento = demo_designs.pick_acento()
    plan = _plan_de_frames(escenas)

    tmp = folder / "_frames"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)

    segundos = len(plan) / FPS_ANIM
    print(f"  Rindiendo {len(plan)} frames ({len(escenas)} escenas, ~{segundos:.0f}s de video, acento {acento['name']})...")
    _render_frames(plan, acento, tmp)

    print("  Codificando video...")
    video_mudo = folder / "_video_mudo.mp4"
    _armar_video(tmp, video_mudo)

    out_path = folder / out_name
    _mezclar_musica(video_mudo, out_path)
    shutil.rmtree(tmp, ignore_errors=True)
    return out_path


def paleta_fija(i_acento: int = 0, i_chasis: int = 0) -> dict:
    """Arma una paleta puntual (acento + chasis) en vez de sortearla. Sólo
    para las vistas previas: sortear haría que dos corridas seguidas no se
    puedan comparar entre sí."""
    return {
        **demo_designs.CHASIS[i_chasis % len(demo_designs.CHASIS)],
        **demo_designs.ESTADO,
        **demo_designs.ACENTOS[i_acento % len(demo_designs.ACENTOS)],
        "name": "preview",
    }


def preview_escenas(destino: Path, t: float = 1.0, acento: dict | None = None) -> list[Path]:
    """Rinde UNA imagen de cada escena disponible (demo_designs.ESCENAS) con
    datos de muestra, para revisar todos los diseños de un vistazo sin tener
    que generar piezas de verdad. Se usa desde `python demo_build.py`."""
    acento = acento or paleta_fija()
    destino.mkdir(parents=True, exist_ok=True)
    escenas = [{**muestra, "tipo": tipo} for tipo, muestra in EJEMPLOS.items()]

    def _uno(escena: dict) -> Path:
        salida = destino / f"{escena['tipo']}.png"
        render.html_to_png_frame(demo_designs.build_escena_html(escena, acento, t), salida)
        return salida

    with ThreadPoolExecutor(max_workers=_WORKERS) as pool:
        return list(pool.map(_uno, escenas))


# Datos de muestra por escena: sólo para la vista previa de diseños
# (preview_escenas). El contenido real de una pieza lo escribe la IA con las
# reglas de demo_rules.py — esto es el equivalente a un "lorem ipsum" con la
# forma exacta que cada escena espera recibir.
EJEMPLOS = {
    "chat_agente": {
        "kicker": "atención 24/7", "titular": "Un turno que entró a las 23:40",
        "bajada": "Nadie del local estaba despierto.",
        "mensajes": [
            {"quien": "Cliente · 23:40", "texto": "Hola! Tienen lugar mañana a la mañana?"},
            {"bot": True, "quien": "Agente", "texto": "Sí, tengo 9:30 y 11:00 libres. ¿Cuál te queda mejor?"},
            {"texto": "9:30 me sirve"},
            {"bot": True, "texto": "Listo, te agendé 9:30. Te mando el recordatorio a la mañana."},
        ],
        "resultado": "Turno confirmado sin que nadie contestara",
    },
    "dashboard_kpi": {
        "kicker": "resultados", "titular": "El mes después de automatizar",
        "kpis": [
            {"label": "Consultas respondidas", "valor": 412, "unidad": "por mes", "barra": 88, "delta": "antes se perdían de noche"},
            {"label": "Turnos confirmados", "valor": 96, "unidad": "por mes", "barra": 72, "delta": "sin llamados de ida y vuelta"},
            {"label": "Tiempo de respuesta", "valor": 30, "prefijo": "", "unidad": "segundos", "barra": 94, "delta": "antes: al otro día"},
        ],
    },
    "web_widget": {
        "kicker": "la web que cotiza sola", "titular": "El agente vive adentro del sitio",
        "url": "tallersanmartin.com.ar", "headline": "Turnos para tu auto en 1 minuto",
        "bajada": "Diagnóstico, service y chapa y pintura.", "boton": "Pedir turno",
        "agente": "Asistente del taller",
        "mensajes": [
            {"texto": "Cuánto sale un service completo?"},
            {"bot": True, "texto": "Para tu modelo arranca en $85.000. ¿Querés que te reserve un turno?"},
            {"texto": "Dale, el jueves"},
        ],
        "resultado": "Lead capturado con teléfono",
    },
    "embudo": {
        "kicker": "dónde se caían", "titular": "De la consulta a la venta",
        "etapas": [
            {"label": "Consultas que entran", "valor": 240},
            {"label": "Respondidas a tiempo", "valor": 240},
            {"label": "Piden presupuesto", "valor": 96},
            {"label": "Compran", "valor": 38},
        ],
        "resultado": "Ninguna consulta se queda sin respuesta",
    },
    "agenda": {
        "kicker": "agenda", "titular": "Se llenó sola mientras cerraban",
        "turnos": [
            {"hora": "09:00", "detalle": "Corte y color", "cliente": "Sofía"},
            {"hora": "10:30", "detalle": "Brushing", "cliente": "Marina"},
            {"hora": "12:00", "detalle": "Corte", "cliente": "Juli"},
            {"hora": "15:00", "detalle": "Color raíz", "cliente": "Ana"},
            {"hora": "16:30", "detalle": "Peinado", "cliente": "Vicky"},
            {"hora": "18:00", "detalle": "Corte", "cliente": "Delfi"},
        ],
        "total": 6, "total_label": "turnos cargados solos",
    },
    "crm_pipeline": {
        "kicker": "seguimiento", "titular": "El que preguntó y no volvió",
        "columnas": ["Preguntó", "Seguimiento", "Cerrado"],
        "tarjetas": [
            {"nombre": "Consulta cocina", "detalle": "pidió precio el martes"},
            {"nombre": "Placard a medida", "detalle": "pidió medidas"},
            {"nombre": "Mesada", "detalle": "comparaba con otro"},
            {"nombre": "Vestidor", "detalle": "quería ver fotos"},
        ],
    },
    "grafico_ingresos": {
        "kicker": "facturación", "titular": "Lo que cambió en seis meses",
        "label": "Facturación mensual", "prefijo": "$", "valor": 1840000,
        "puntos": [22, 30, 27, 44, 58, 76, 95],
        "nota": "Mismo local, mismo equipo",
    },
    "inbox_cero": {
        "kicker": "bandeja de entrada", "titular": "De 5 sin leer a cero",
        "label": "sin responder",
        "mensajes": [
            "Hola, hacen envíos a Córdoba?",
            "Cuánto sale el modelo azul?",
            "Están abiertos el sábado?",
            "Me guardás uno hasta mañana?",
            "Aceptan transferencia?",
        ],
    },
    "flujo_nodos": {
        "kicker": "cómo funciona", "titular": "Lo que pasa cuando llega un mensaje",
        "pasos": [
            "Entra la consulta por WhatsApp",
            "El agente entiende qué está pidiendo",
            "Busca precio y disponibilidad reales",
            "Responde y ofrece el turno",
            "Deja el contacto cargado en la agenda",
        ],
    },
    "antes_despues": {
        "kicker": "antes y después", "titular": "El mismo martes, con y sin agente",
        "label_antes": "Antes", "label_despues": "Ahora",
        "antes": ["Contestaba entre cliente y cliente", "Los de la noche quedaban para el otro día",
                  "Turnos anotados en un cuaderno", "Se pisaban dos en el mismo horario"],
        "despues": ["Responde solo, al toque", "La noche también queda cubierta",
                    "Todo cargado en la agenda", "Nunca dos en el mismo horario"],
    },
    "captacion": {
        "kicker": "de dónde llegan", "titular": "Tres puertas, un solo lugar",
        "fuentes": [
            {"icono": "💬", "label": "WhatsApp", "valor": 128},
            {"icono": "📸", "label": "Instagram", "valor": 74},
            {"icono": "🌐", "label": "La web", "valor": 39},
        ],
        "total": 241, "total_label": "contactos atendidos este mes",
    },
    "checkout": {
        "kicker": "venta cerrada", "titular": "Del mensaje al pago, sin llamados",
        "titulo": "Pedido #1042", "prefijo": "$", "monto": 47500,
        "pasos": ["Eligió el producto por chat", "El agente confirmó stock",
                  "Mandó el link de pago", "Pagó desde el celular"],
        "resultado": "Pago aprobado",
    },
    "ranking_barras": {
        "kicker": "cuándo escriben", "titular": "Las horas que nadie atendía",
        "sufijo": " msj",
        "items": [
            {"label": "20 a 23 h", "valor": 96},
            {"label": "13 a 15 h", "valor": 61},
            {"label": "9 a 12 h", "valor": 44},
            {"label": "15 a 18 h", "valor": 38},
            {"label": "Después de las 23", "valor": 27},
        ],
    },
    "mapa_horarios": {
        "kicker": "mapa de demanda", "titular": "Cuándo entran las consultas",
        "horas": ["9h", "12h", "15h", "18h", "21h", "23h"],
        "filas": [
            {"label": "Lunes", "valores": [3, 5, 4, 7, 9, 6]},
            {"label": "Martes", "valores": [2, 4, 5, 8, 9, 7]},
            {"label": "Miércoles", "valores": [3, 4, 4, 7, 10, 8]},
            {"label": "Jueves", "valores": [2, 5, 6, 8, 10, 7]},
            {"label": "Viernes", "valores": [4, 6, 5, 9, 10, 9]},
        ],
        "nota": "El pico cae cuando el local ya cerró",
    },
    "consola": {
        "kicker": "por dentro", "titular": "Lo que hace el agente en 4 segundos",
        "titulo": "agente · en vivo",
        "lineas": [
            {"marca": "23:41:02", "texto": "mensaje nuevo · whatsapp"},
            {"marca": "23:41:02", "texto": "intención: pedir turno"},
            {"marca": "23:41:03", "texto": "consultando agenda del jueves"},
            {"marca": "23:41:04", "texto": "9:30 y 11:00 disponibles"},
            {"marca": "23:41:05", "texto": "turno reservado · confirmado", "ok": True},
        ],
    },
    "costos": {
        "kicker": "cuánto cuesta", "titular": "Perder el turno sale más caro",
        "prefijo": "$",
        "opcion_a": {"label": "Los turnos que se pierden", "detalle": "consultas de noche sin responder", "valor": 320000},
        "opcion_b": {"label": "Con el agente atendiendo", "detalle": "esas mismas consultas, agendadas", "valor": 38000},
        "ahorro": "La diferencia se paga sola el primer mes",
    },
    "resenas": {
        "kicker": "reputación", "titular": "La nota que subió sin pedir nada",
        "puntaje": 4.8, "label": "de 5",
        "resenas": [
            {"estrellas": 5, "texto": "Escribí un domingo y me contestaron al toque.", "autor": "Nadia P."},
            {"estrellas": 5, "texto": "Me confirmaron el turno en dos minutos.", "autor": "Ramiro V."},
            {"estrellas": 4, "texto": "Muy práctico, no tuve que llamar.", "autor": "Carla M."},
        ],
    },
    "stock": {
        "kicker": "inventario", "titular": "Se avisa antes de quedarse sin nada",
        "items": [
            {"label": "Cristales antirreflex", "nivel": 18, "repuesto": 82},
            {"label": "Armazones metal", "nivel": 64},
            {"label": "Líquido de limpieza", "nivel": 45},
            {"label": "Estuches", "nivel": 78},
        ],
    },
    "cotizacion": {
        "kicker": "presupuesto", "titular": "El precio que antes tardaba dos días",
        "titulo": "Presupuesto #318", "prefijo": "$",
        "items": [
            {"label": "Cristales monofocales", "monto": 38000},
            {"label": "Antirreflex", "monto": 12000},
            {"label": "Armazón", "monto": 26000},
            {"label": "Armado y ajuste", "monto": 4000},
        ],
        "resultado": "Enviado por WhatsApp",
    },
    "notificaciones": {
        "kicker": "lo que entra", "titular": "Todo esto llegó fuera de horario",
        "avisos": [
            {"icono": "💬", "titulo": "WhatsApp", "hora": "21:14", "texto": "Hacen envíos a Rosario?"},
            {"icono": "📸", "titulo": "Instagram", "hora": "22:03", "texto": "Cuánto sale el modelo de la foto?"},
            {"icono": "🌐", "titulo": "La web", "hora": "23:40", "texto": "Quiero turno para el jueves"},
            {"icono": "💬", "titulo": "WhatsApp", "hora": "07:12", "texto": "Buen día, abren hoy?"},
        ],
    },
    "roi": {
        "kicker": "la cuenta", "titular": "Lo que se recupera en un mes",
        "prefijo": "$",
        "entradas": [
            {"label": "Consultas sin responder por mes", "valor": 62},
            {"label": "De esas, las que compraban", "valor": 9},
            {"label": "Ticket promedio", "prefijo": "$", "valor": 46000},
        ],
        "resultado": 414000, "resultado_label": "Lo que volvía a entrar",
        "nota": "Con las mismas consultas que ya llegaban",
    },
    "crecimiento": {
        "kicker": "seis meses", "titular": "Turnos por mes, sin sumar gente",
        "total": 128, "total_label": "turnos el último mes",
        "meses": [
            {"label": "Abr", "valor": 54}, {"label": "May", "valor": 63},
            {"label": "Jun", "valor": 71}, {"label": "Jul", "valor": 92},
            {"label": "Ago", "valor": 108}, {"label": "Sep", "valor": 128},
        ],
    },
}


if __name__ == "__main__":
    # Vista previa de todos los diseños, sin gastar una generación de IA:
    #     python demo_build.py             -> estado final de cada escena
    #     python demo_build.py 0.45        -> a mitad de la animación
    #     python demo_build.py 1.0 5 2     -> con el acento 5 y el chasis 2
    import sys

    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8", errors="replace")

    t = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
    i_a = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    i_c = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    paleta = paleta_fija(i_a, i_c)
    destino = Path(__file__).parent / "_preview_real" / "demos"
    print(f"Rindiendo {len(EJEMPLOS)} escenas a t={t} en {destino} ...")
    salidas = preview_escenas(destino, t, paleta)
    for s in salidas:
        print(f"  ✓ {s.name}")
