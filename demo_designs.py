"""Escenas ANIMADAS del formato 'demo' (ver demo_build.py y demo_rules.py):
demostraciones gráficas rápidas de un producto funcionando —un agente
respondiendo, un dashboard llenándose, una venta cerrándose— en vez de las
slides estáticas de papel editorial del resto de la marca (design.py).

CÓMO SE ANIMA (esto es lo que lo hace distinto de design.py):
Chrome headless saca UNA foto por HTML, no graba video, así que no sirven las
animaciones de CSS: no habría quién las filme. Acá cada escena es una FUNCIÓN
DEL TIEMPO — `render(datos, p, t)` con `t` de 0 a 1 — y demo_build.py la llama
muchas veces con t distinto, rinde cada resultado a PNG y los junta como
frames de video. O sea: la animación se calcula en Python (cuánto creció esa
barra, cuántas burbujas ya entraron, en qué número va el contador) y el HTML
sólo dibuja el estado congelado de ESE instante.

Los helpers de abajo (_ease, _tramo, _escalonado, _entero, _reveal) son las
piezas con las que se escribe ese movimiento; casi toda escena es una
combinación de ellos.

PALETA: estas escenas NO usan el papel crema del resto de la marca. Un demo de
producto tiene que leerse como software real, así que van sobre un fondo
oscuro tipo panel/consola, con el color de acento de la paleta sorteada como
único color de marca. Es deliberado que se distingan del carrusel editorial.
"""

import html
import random
import re

from render import CANVAS_H, CANVAS_W, font_data_uri

# Acentos de las escenas: el par de colores de marca de la pieza. `accent` es
# el protagonista (números grandes, barras, botones) y `accent2` el que cierra
# los degradés. Se sortea uno por pieza, igual que la paleta del carrusel en
# design.py: la variedad está ENTRE piezas, nunca adentro de una.
#
# Todos son colores claros y saturados a propósito: van siempre sobre un
# chasis oscuro, así que tienen que tener contraste suficiente para leerse
# como texto chico (una etiqueta de KPI) y no sólo como manchón de color.
ACENTOS = [
    {"name": "verde",     "accent": "#34D399", "accent2": "#0EA5E9"},
    {"name": "violeta",   "accent": "#A78BFA", "accent2": "#F472B6"},
    {"name": "ambar",     "accent": "#FBBF24", "accent2": "#FB7185"},
    {"name": "cyan",      "accent": "#22D3EE", "accent2": "#818CF8"},
    {"name": "lima",      "accent": "#A3E635", "accent2": "#22D3EE"},
    {"name": "coral",     "accent": "#FB7185", "accent2": "#FBBF24"},
    {"name": "indigo",    "accent": "#818CF8", "accent2": "#22D3EE"},
    {"name": "turquesa",  "accent": "#2DD4BF", "accent2": "#A3E635"},
    {"name": "naranja",   "accent": "#FB923C", "accent2": "#FACC15"},
    {"name": "rosa",      "accent": "#F472B6", "accent2": "#A78BFA"},
    {"name": "celeste",   "accent": "#38BDF8", "accent2": "#2DD4BF"},
    {"name": "durazno",   "accent": "#FDBA74", "accent2": "#F472B6"},
]

# Chasis: el fondo y los paneles sobre los que se apoya todo. Son tres climas
# oscuros distintos (azul noche, grafito neutro, ciruela) en vez de uno solo,
# para que dos demos seguidos no se vean calcados aunque compartan escenas.
#
# Los tres son deliberadamente oscuros y desaturados: el color de la pieza lo
# pone el acento, no el fondo. Si el chasis compitiera, los números grandes
# —que es lo único que hay que leer rápido— dejarían de destacar.
CHASIS = [
    {  # Azul noche: el original, el más "panel de software"
        "chasis": "noche",
        "bg": "#0B1020", "bg2": "#141B2E", "panel": "#182036", "panel2": "#1F2942",
        "ink": "#F8FAFC", "dim": "#94A3B8", "line": "#2B3550",
    },
    {  # Grafito: neutro, más sobrio, deja al acento todo el protagonismo
        "chasis": "grafito",
        "bg": "#0C0D11", "bg2": "#16181F", "panel": "#1B1E27", "panel2": "#232734",
        "ink": "#F5F6F8", "dim": "#9AA0AE", "line": "#313542",
    },
    {  # Ciruela: cálido, funciona muy bien con los acentos rosa/coral/durazno
        "chasis": "ciruela",
        "bg": "#120B18", "bg2": "#1D1226", "panel": "#241730", "panel2": "#2E1E3C",
        "ink": "#F9F5FB", "dim": "#A99BB4", "line": "#3C2A4C",
    },
]

# Verde/rojo de estado (✓ resuelto, ✕ pendiente). NO salen del acento: son
# semáforo, y tienen que significar lo mismo en todas las piezas aunque el
# acento de esta sea rojo o verde. Si el "listo" se pintara con el acento, un
# demo de acento coral mostraría los ✓ en rojo.
ESTADO = {"ok": "#34D399", "bad": "#F87171"}

HANDLE = "@rootbusinessai"


def pick_acento() -> dict:
    """Sortea la paleta completa de UNA pieza: un acento, un chasis y los
    colores de estado. Se devuelve todo aplanado en un solo dict porque es lo
    que reciben las escenas como `p` — así una escena pide p['accent'] o
    p['panel'] sin tener que saber de dónde salió cada cosa."""
    acento = random.choice(ACENTOS)
    chasis = random.choice(CHASIS)
    return {**chasis, **ESTADO, **acento, "name": f"{acento['name']}/{chasis['chasis']}"}


# --- Helpers de animación ---------------------------------------------------

def _clamp(x: float) -> float:
    return 0.0 if x < 0 else (1.0 if x > 1 else x)


def _ease(x: float) -> float:
    """Suavizado ease-out cúbico: arranca rápido y frena al final. Es la curva
    que hace que un elemento que entra se sienta 'colocado' y no disparado."""
    x = _clamp(x)
    return 1 - pow(1 - x, 3)


def _tramo(t: float, inicio: float, fin: float) -> float:
    """Reescala el tiempo global `t` al subtramo [inicio, fin] y lo devuelve
    como un 0..1 propio. Es lo que permite que dentro de una escena cada
    elemento tenga su propia ventana de tiempo ('la barra crece entre el 20% y
    el 60% de la escena')."""
    if fin <= inicio:
        return 1.0 if t >= fin else 0.0
    return _clamp((t - inicio) / (fin - inicio))


def _escalonado(t: float, i: int, n: int, inicio: float = 0.05, fin: float = 0.8,
                solape: float = 0.55) -> float:
    """Progreso del elemento `i` de `n` que entran en cascada entre `inicio` y
    `fin`. `solape` es cuánto se pisa cada uno con el siguiente (1 = todos a
    la vez, 0 = estrictamente uno después del otro); un poco de solape es lo
    que hace que la cascada se vea fluida y no robótica."""
    if n <= 0:
        return 1.0
    total = fin - inicio
    paso = total / max(1, (n - (n - 1) * solape))
    ini_i = inicio + i * paso * (1 - solape)
    return _tramo(t, ini_i, ini_i + paso)


def _entero(valor: float, progreso: float) -> int:
    """Contador que sube hasta `valor` según `progreso` (con ease). Se redondea
    a entero porque un número que cambia de decimales en cada frame se lee
    como ruido, no como un contador."""
    return int(round(valor * _ease(progreso)))


def _reveal(prog: float, dy: int = 26) -> str:
    """Estilo inline de 'entrar apareciendo desde abajo'. El desplazamiento
    arranca en `dy` px y termina en 0; la opacidad va más rápido que el
    movimiento para que nada se lea a medio camino."""
    e = _ease(prog)
    return f"opacity:{min(1.0, prog * 1.6):.3f}; transform:translateY({(1 - e) * dy:.1f}px);"


def _num(valor) -> str:
    """Formatea números al uso argentino (punto de miles) para que un
    resultado financiero no se lea como un número de otro país."""
    if isinstance(valor, float) and valor != int(valor):
        return f"{valor:,.1f}".replace(",", "@").replace(".", ",").replace("@", ".")
    return f"{int(valor):,}".replace(",", ".")


def _esc(x) -> str:
    return html.escape(str(x))


_NUMERACION = re.compile(r"^\s*\d+\s*[.)\-–]\s+")


def _sin_numeracion(texto: str) -> str:
    """Saca el '1. ' / '2) ' del principio de un paso. Las escenas que muestran
    pasos ya dibujan el número aparte (el círculo del nodo, el chip del
    checkout), así que cuando la IA lo escribe además adentro del texto queda
    '⓵ 1. Subís la tabla' — se ve como un error de armado."""
    return _NUMERACION.sub("", str(texto)).strip()


# --- Chasis compartido ------------------------------------------------------

def _css(p: dict) -> str:
    a, a2 = p["accent"], p["accent2"]
    return f"""
@font-face {{ font-family:'Display'; src:url('{font_data_uri("PlayfairDisplay-Bold.ttf")}') format('truetype'); font-weight:400 900; }}
@font-face {{ font-family:'Body'; src:url('{font_data_uri("Inter-Regular.ttf")}') format('truetype'); font-weight:100 900; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:{CANVAS_W}px; height:{CANVAS_H}px; overflow:hidden; background:{p['bg']}; }}
body {{
  font-family:'Body', sans-serif; color:{p['ink']}; -webkit-font-smoothing:antialiased;
  background:
    radial-gradient(70% 45% at 78% 6%, {a}22 0%, transparent 60%),
    radial-gradient(60% 40% at 12% 96%, {a2}1c 0%, transparent 62%),
    linear-gradient(170deg, {p['bg2']} 0%, {p['bg']} 55%);
  position:relative;
}}
/* Grilla técnica de fondo: da sensación de "panel de producto" sin robar
   atención. Tile chico y repetido, igual que la textura de design.py, para
   que el PNG siga comprimiendo bien. */
body::before {{
  content:''; position:absolute; inset:0; pointer-events:none; opacity:.5;
  background-image:
    linear-gradient(to right, {p['line']}22 1px, transparent 1px),
    linear-gradient(to bottom, {p['line']}22 1px, transparent 1px);
  background-size:60px 60px;
}}
.page {{ position:absolute; inset:0; padding:250px 74px 360px; display:flex; flex-direction:column; }}
/* Mismas zonas seguras que design.py: TikTok tapa ~200px arriba y bastante
   más abajo. Ver el comentario largo en design.py / render.py. */
.head {{ margin-bottom:34px; }}
.kicker {{
  display:inline-flex; align-items:center; gap:14px; font-size:24px; font-weight:700;
  letter-spacing:.2em; text-transform:uppercase; color:{a};
  background:{a}16; border:1px solid {a}3a; padding:14px 24px; border-radius:999px;
}}
.kicker .dot {{ width:12px; height:12px; border-radius:50%; background:{a}; box-shadow:0 0 0 5px {a}25; }}
h1 {{
  font-family:'Display', serif; font-weight:800; font-size:74px; line-height:1.08;
  letter-spacing:-.02em; margin-top:26px;
}}
.sub {{ font-size:33px; line-height:1.45; color:{p['dim']}; margin-top:18px; }}
.stage {{ flex:1; display:flex; flex-direction:column; justify-content:center; min-height:0; }}
.foot {{
  display:flex; justify-content:space-between; align-items:center;
  font-size:23px; letter-spacing:.16em; text-transform:uppercase; color:{p['dim']};
  border-top:1px solid {p['line']}; padding-top:26px;
}}
/* --- Piezas reutilizadas por varias escenas --- */
.card {{ background:{p['panel']}; border:1px solid {p['line']}; border-radius:28px; }}
.pill {{ display:inline-block; padding:10px 20px; border-radius:999px; font-size:24px; }}
.chip-ok {{ background:{p['ok']}1f; color:{p['ok']}; border:1px solid {p['ok']}44; }}
.chip-bad {{ background:{p['bad']}1f; color:{p['bad']}; border:1px solid {p['bad']}44; }}
.mono {{ font-family:'Consolas','Courier New',monospace; font-variant-numeric:tabular-nums; }}
.big-num {{
  font-family:'Display', serif; font-weight:800; letter-spacing:-.03em; line-height:1;
  color:{a};
}}
.bar-track {{ background:{p['panel2']}; border-radius:999px; overflow:hidden; }}
.bar-fill {{ height:100%; border-radius:999px; background:linear-gradient(90deg, {a2}, {a}); }}
"""


def _capitalizar(texto: str) -> str:
    """Primera letra en mayúscula, sin tocar el resto. La IA a veces escribe
    los titulares enteros en minúscula ('la agenda se actualiza sola') y a
    veces no; en un titular de 74px la diferencia entre una pieza y la
    siguiente se nota como descuido de marca. Ojo: NO se usa .capitalize(),
    que además bajaría a minúscula todo lo demás y arruinaría las siglas y
    los nombres propios ('KPIs', 'WhatsApp')."""
    texto = str(texto).strip()
    return texto[:1].upper() + texto[1:] if texto else texto


def _page(p: dict, kicker: str, titular: str, cuerpo: str, t: float, sub: str = "") -> str:
    """Marco común de toda escena: encabezado (kicker + titular + bajada), el
    escenario animado, y el pie con el handle. El encabezado entra al arranque
    de la escena para que nunca aparezca de golpe junto con el contenido."""
    p_head = _tramo(t, 0.0, 0.22)
    p_sub = _tramo(t, 0.08, 0.32)
    sub_html = f'<div class="sub" style="{_reveal(p_sub, 16)}">{_esc(_capitalizar(sub))}</div>' if sub else ""
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><style>{_css(p)}</style></head>
<body><div class="page">
<div class="head" style="{_reveal(p_head, 20)}">
<div class="kicker"><span class="dot"></span>{_esc(kicker)}</div>
<h1>{_esc(_capitalizar(titular))}</h1>{sub_html}
</div>
<div class="stage">{cuerpo}</div>
<div class="foot"><span>{HANDLE}</span><span>demo en vivo</span></div>
</div></body></html>"""


# --- 1. Chat con el agente --------------------------------------------------

def _chat_agente(d: dict, p: dict, t: float) -> str:
    """Conversación real con el agente: las burbujas entran una por una, con
    puntitos de 'escribiendo' antes de cada respuesta del bot, y al final un
    acuse de que la acción quedó hecha (turno agendado, presupuesto enviado)."""
    msgs = d.get("mensajes", [])[:5]
    n = len(msgs)
    filas = ""
    for i, m in enumerate(msgs):
        prog = _escalonado(t, i, n, 0.16, 0.82, 0.35)
        if prog <= 0:
            continue
        es_bot = bool(m.get("bot"))
        lado = "flex-end" if es_bot else "flex-start"
        # Los puntitos ocupan el primer tercio de la ventana de una burbuja del
        # bot: es lo que vende que la respuesta la está pensando una máquina.
        if es_bot and prog < 0.34:
            filas += f"""<div style="display:flex; justify-content:{lado}; {_reveal(prog * 3, 12)}">
<div style="background:{p['accent']}22; border:1px solid {p['accent']}44; border-radius:26px 8px 26px 26px; padding:26px 30px; display:flex; gap:10px;">
<span style="width:14px;height:14px;border-radius:50%;background:{p['accent']};opacity:.9"></span>
<span style="width:14px;height:14px;border-radius:50%;background:{p['accent']};opacity:.55"></span>
<span style="width:14px;height:14px;border-radius:50%;background:{p['accent']};opacity:.3"></span>
</div></div>"""
            continue
        burbuja_prog = _tramo(prog, 0.34, 1.0) if es_bot else prog
        fondo = f"background:linear-gradient(135deg,{p['accent']}, {p['accent2']}); color:#08111F;" if es_bot \
            else f"background:{p['panel2']}; color:{p['ink']};"
        radio = "26px 8px 26px 26px" if es_bot else "8px 26px 26px 26px"
        quien = f'<div style="font-size:21px; opacity:.75; margin-bottom:10px;">{_esc(m.get("quien", ""))}</div>' if m.get("quien") else ""
        filas += f"""<div style="display:flex; justify-content:{lado}; {_reveal(burbuja_prog, 18)}">
<div style="max-width:80%; {fondo} border-radius:{radio}; padding:28px 32px; font-size:33px; line-height:1.35;
box-shadow:0 18px 40px rgba(0,0,0,.35);">{quien}{_esc(m.get("texto", ""))}</div></div>"""

    p_ok = _tramo(t, 0.84, 0.97)
    ok = ""
    if p_ok > 0 and d.get("resultado"):
        ok = f"""<div style="margin-top:30px; text-align:center; {_reveal(p_ok, 16)}">
<span class="pill chip-ok" style="font-size:28px; padding:16px 32px;">✓ {_esc(d['resultado'])}</span></div>"""

    return f"""<div class="card" style="padding:38px 34px; display:flex; flex-direction:column; gap:22px;">
{filas}</div>{ok}"""


# --- 2. Dashboard de KPIs ---------------------------------------------------

def _dashboard_kpi(d: dict, p: dict, t: float) -> str:
    """Tres métricas del negocio subiendo a la vez, con su barra de avance.
    Es la escena de 'esto es lo que cambió', en versión panel de control."""
    kpis = d.get("kpis", [])[:3]
    n = len(kpis)
    tiles = ""
    for i, k in enumerate(kpis):
        prog = _escalonado(t, i, n, 0.18, 0.85, 0.6)
        valor = _entero(float(k.get("valor", 0)), prog)
        barra = _ease(prog) * float(k.get("barra", 78))
        tiles += f"""<div class="card" style="padding:34px 32px; {_reveal(prog, 24)}">
<div style="font-size:25px; color:{p['dim']}; text-transform:uppercase; letter-spacing:.1em;">{_esc(k.get('label',''))}</div>
<div style="display:flex; align-items:baseline; gap:12px; margin:16px 0 20px;">
<span class="big-num mono" style="font-size:82px;">{_esc(k.get('prefijo',''))}{_num(valor)}</span>
<span style="font-size:30px; color:{p['dim']};">{_esc(k.get('unidad',''))}</span></div>
<div class="bar-track" style="height:14px;"><div class="bar-fill" style="width:{barra:.1f}%"></div></div>
<div style="margin-top:16px; font-size:24px; color:{p['ok']};">▲ {_esc(k.get('delta',''))}</div>
</div>"""
    return f'<div style="display:flex; flex-direction:column; gap:24px;">{tiles}</div>'


# --- 3. Widget de chat en la web --------------------------------------------

def _web_widget(d: dict, p: dict, t: float) -> str:
    """El sitio del negocio con el agente instalado: la página está desde el
    principio y el widget se abre solo, atiende y captura el lead. Muestra el
    producto en su contexto real (una web común), no como diagrama."""
    p_page = _tramo(t, 0.05, 0.3)
    p_widget = _tramo(t, 0.3, 0.5)
    escala = 0.86 + 0.14 * _ease(p_widget)
    msgs = d.get("mensajes", [])[:3]
    chat = ""
    for i, m in enumerate(msgs):
        prog = _escalonado(t, i, len(msgs), 0.5, 0.86, 0.35)
        if prog <= 0:
            continue
        es_bot = bool(m.get("bot"))
        fondo = f"background:linear-gradient(135deg,{p['accent']},{p['accent2']}); color:#08111F;" if es_bot else f"background:#E9EEF7; color:#0B1020;"
        alineado = "flex-end" if es_bot else "flex-start"
        chat += f"""<div style="display:flex; justify-content:{alineado}; {_reveal(prog, 12)}">
<div style="max-width:86%; {fondo} border-radius:16px; padding:16px 20px; font-size:22px; line-height:1.35;">{_esc(m.get('texto',''))}</div></div>"""

    p_lead = _tramo(t, 0.86, 0.98)
    lead = f"""<div style="position:absolute; left:36px; bottom:36px; {_reveal(p_lead, 14)}">
<span class="pill chip-ok" style="font-size:24px;">✓ {_esc(d.get('resultado','Lead capturado'))}</span></div>""" if p_lead > 0 else ""

    return f"""<div style="position:relative; {_reveal(p_page, 26)}">
<div style="background:#FFFFFF; border-radius:26px; overflow:hidden; box-shadow:0 40px 90px rgba(0,0,0,.5);">
  <div style="display:flex; align-items:center; gap:10px; padding:22px 26px; background:#EEF2F8; border-bottom:1px solid #DCE3EE;">
    <span style="width:14px;height:14px;border-radius:50%;background:#FF5F57"></span>
    <span style="width:14px;height:14px;border-radius:50%;background:#FEBC2E"></span>
    <span style="width:14px;height:14px;border-radius:50%;background:#28C840"></span>
    <span style="margin-left:14px; flex:1; background:#FFF; border-radius:999px; padding:12px 22px; font-size:21px; color:#5A6577;">🔒 {_esc(d.get('url','tunegocio.com.ar'))}</span>
  </div>
  <!-- El texto de la página se queda en la mitad izquierda (width:56%): el
       widget flota abajo a la derecha y, sin ese límite, un headline largo se
       metía abajo del widget y quedaba cortado a la mitad. -->
  <div style="padding:44px 40px 60px; color:#0B1020; min-height:600px;">
    <div style="width:56%;">
      <div style="font-family:'Display',serif; font-weight:800; font-size:44px; line-height:1.12; letter-spacing:-.02em;">{_esc(d.get('headline',''))}</div>
      <div style="font-size:23px; color:#5A6577; margin-top:16px; line-height:1.45;">{_esc(d.get('bajada',''))}</div>
      <div style="display:inline-block; margin-top:28px; background:{p['accent']}; color:#08111F; font-weight:700; font-size:23px; padding:17px 32px; border-radius:999px;">{_esc(d.get('boton','Pedir turno'))}</div>
    </div>
  </div>
</div>
<div style="position:absolute; right:30px; bottom:30px; width:400px; transform:scale({escala:.3f}); transform-origin:100% 100%;
     background:#0F1626; border:1px solid {p['accent']}55; border-radius:22px; overflow:hidden; box-shadow:0 30px 70px rgba(0,0,0,.6);
     opacity:{min(1.0, p_widget * 2):.2f};">
  <div style="display:flex; align-items:center; gap:12px; padding:20px 22px; background:linear-gradient(135deg,{p['accent']},{p['accent2']}); color:#08111F;">
    <span style="width:12px;height:12px;border-radius:50%;background:#08111F"></span>
    <span style="font-size:22px; font-weight:700;">{_esc(d.get('agente','Asistente'))}</span>
    <span style="margin-left:auto; font-size:18px; opacity:.75;">en línea</span>
  </div>
  <div style="padding:22px; display:flex; flex-direction:column; gap:14px; min-height:250px;">{chat}</div>
</div>
{lead}
</div>"""


# --- 4. Embudo de conversión ------------------------------------------------

def _embudo(d: dict, p: dict, t: float) -> str:
    """Embudo que se llena de arriba abajo: cuánta gente entra y cuánta llega
    al final. Cada etapa se pinta cuando le toca y su número sube contando."""
    etapas = d.get("etapas", [])[:4]
    n = len(etapas)
    filas = ""
    for i, e in enumerate(etapas):
        prog = _escalonado(t, i, n, 0.16, 0.86, 0.45)
        ancho = 100 - i * (46 / max(1, n - 1) if n > 1 else 0)
        valor = _entero(float(e.get("valor", 0)), prog)
        ultimo = i == n - 1
        fondo = (f"linear-gradient(90deg,{p['accent']},{p['accent2']})" if ultimo
                 else f"linear-gradient(90deg,{p['accent']}{'cc' if i == 0 else '88'},{p['accent2']}55)")
        filas += f"""<div style="display:flex; justify-content:center; {_reveal(prog, 20)}">
<div style="width:{ancho:.1f}%; background:{fondo}; border-radius:18px; padding:30px 34px;
     display:flex; align-items:center; justify-content:space-between; color:#08111F;
     box-shadow:0 16px 36px rgba(0,0,0,.34);">
<span style="font-size:29px; font-weight:700;">{_esc(e.get('label',''))}</span>
<span class="mono" style="font-size:44px; font-weight:800;">{_num(valor)}</span></div></div>"""

    p_res = _tramo(t, 0.86, 0.98)
    res = ""
    if p_res > 0 and d.get("resultado"):
        res = f"""<div style="margin-top:32px; text-align:center; {_reveal(p_res, 16)}">
<span class="pill chip-ok" style="font-size:30px; padding:18px 34px;">{_esc(d['resultado'])}</span></div>"""
    return f'<div style="display:flex; flex-direction:column; gap:18px;">{filas}</div>{res}'


# --- 5. Agenda de turnos ----------------------------------------------------

def _agenda(d: dict, p: dict, t: float) -> str:
    """Una grilla de turnos que se va llenando sola. Los huecos vacíos se
    reemplazan por reservas confirmadas, que es exactamente lo que ve el dueño
    del negocio a la mañana siguiente."""
    turnos = d.get("turnos", [])[:6]
    n = len(turnos)
    filas = ""
    for i, tu in enumerate(turnos):
        prog = _escalonado(t, i, n, 0.16, 0.86, 0.4)
        lleno = prog > 0.5
        borde = f"{p['accent']}66" if lleno else p["line"]
        fondo = f"{p['accent']}14" if lleno else "transparent"
        etiqueta = (f'<span class="pill chip-ok" style="font-size:22px;">✓ {_esc(tu.get("cliente","Reservado"))}</span>'
                    if lleno else f'<span style="font-size:24px; color:{p["dim"]};">libre</span>')
        filas += f"""<div style="display:flex; align-items:center; justify-content:space-between;
     border:1px solid {borde}; background:{fondo}; border-radius:18px; padding:26px 30px;
     {_reveal(_escalonado(t, i, n, 0.06, 0.4, 0.7), 14)}">
<span class="mono" style="font-size:32px; color:{p['ink']};">{_esc(tu.get('hora',''))}</span>
<span style="font-size:27px; color:{p['dim']}; flex:1; margin-left:26px;">{_esc(tu.get('detalle',''))}</span>
{etiqueta}</div>"""

    p_tot = _tramo(t, 0.82, 0.97)
    total = ""
    if p_tot > 0:
        total = f"""<div style="margin-top:30px; display:flex; align-items:baseline; justify-content:center; gap:16px; {_reveal(p_tot, 16)}">
<span class="big-num mono" style="font-size:76px;">{_entero(float(d.get('total', n)), p_tot)}</span>
<span style="font-size:30px; color:{p['dim']};">{_esc(d.get('total_label','turnos cargados solos'))}</span></div>"""
    return f'<div style="display:flex; flex-direction:column; gap:16px;">{filas}</div>{total}'


# --- 6. Pipeline de CRM -----------------------------------------------------

def _crm_pipeline(d: dict, p: dict, t: float) -> str:
    """Tablero de oportunidades: las tarjetas arrancan en la primera columna y
    se van moviendo hasta 'Ganado'. Muestra el seguimiento comercial que nadie
    hace a mano cuando está atendiendo el mostrador."""
    cols = d.get("columnas", ["Nuevo", "En charla", "Ganado"])[:3]
    tarjetas = d.get("tarjetas", [])[:4]
    n = len(tarjetas)
    ultima = len(cols) - 1
    cols_html = ""
    for ci, c in enumerate(cols):
        cuerpo = ""
        for i, tj in enumerate(tarjetas):
            prog = _escalonado(t, i, n, 0.2, 0.88, 0.5)
            # Cada tarjeta arranca en la primera columna y viaja hasta SU
            # columna destino. El destino se reparte (0,1,2,2...) en vez de
            # mandarlas todas al final: un tablero que termina con las dos
            # primeras columnas vacías se lee como un error de render, no como
            # un pipeline. La IA puede fijarlo con el campo 'columna'.
            destino = tj.get("columna")
            destino = min(ultima, max(0, int(destino))) if isinstance(destino, (int, float)) else min(ultima, i)
            col_actual = round(destino * _ease(prog))
            if col_actual != ci or prog <= 0:
                continue
            ganada = col_actual == ultima
            borde = f"{p['ok']}66" if ganada else p["line"]
            cuerpo += f"""<div style="background:{p['panel2']}; border:1px solid {borde}; border-radius:16px; padding:20px 18px; {_reveal(prog, 10)}">
<div style="font-size:23px; font-weight:600;">{_esc(tj.get('nombre',''))}</div>
<div style="font-size:20px; color:{p['dim']}; margin-top:8px;">{_esc(tj.get('detalle',''))}</div>
{'<div style="margin-top:12px;"><span class="pill chip-ok" style="font-size:18px; padding:6px 14px;">✓ cerrado</span></div>' if ganada else ''}
</div>"""
        activa = ci == ultima
        cols_html += f"""<div style="flex:1; background:{p['panel']}; border:1px solid {f"{p['ok']}44" if activa else p['line']};
     border-radius:22px; padding:22px 16px; display:flex; flex-direction:column; gap:14px; min-height:420px;">
<div style="font-size:22px; letter-spacing:.1em; text-transform:uppercase; color:{p['ok'] if activa else p['dim']}; text-align:center;">{_esc(c)}</div>
{cuerpo}</div>"""
    return f'<div style="display:flex; gap:16px; align-items:stretch;">{cols_html}</div>'


# --- 7. Gráfico de ingresos -------------------------------------------------

def _grafico_ingresos(d: dict, p: dict, t: float) -> str:
    """Curva de facturación dibujándose de izquierda a derecha, con el número
    grande subiendo al mismo ritmo. Es la escena de resultado financiero."""
    puntos = d.get("puntos", [20, 32, 28, 46, 58, 74, 92])[:8]
    p_draw = _tramo(t, 0.2, 0.86)
    n = len(puntos)
    vistos = max(2, int(round(n * _ease(p_draw))))
    w, h = 900.0, 420.0
    maximo = max(puntos) or 1
    coords = []
    for i, v in enumerate(puntos[:vistos]):
        x = (i / max(1, n - 1)) * w
        y = h - (v / maximo) * (h - 40) - 20
        coords.append((x, y))
    linea = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(coords))
    area = linea + f" L{coords[-1][0]:.1f},{h:.1f} L0,{h:.1f} Z" if coords else ""
    ultimo = coords[-1] if coords else (0, h)
    valor = _entero(float(d.get("valor", 0)), p_draw)

    p_tag = _tramo(t, 0.84, 0.97)
    tag = ""
    if p_tag > 0 and d.get("nota"):
        tag = f"""<div style="margin-top:26px; text-align:center; {_reveal(p_tag, 14)}">
<span class="pill chip-ok" style="font-size:27px; padding:16px 30px;">{_esc(d['nota'])}</span></div>"""

    return f"""<div class="card" style="padding:38px 34px;">
<div style="display:flex; align-items:baseline; justify-content:space-between; margin-bottom:26px;">
<span style="font-size:26px; color:{p['dim']}; text-transform:uppercase; letter-spacing:.1em;">{_esc(d.get('label','Facturación'))}</span>
<span class="big-num mono" style="font-size:66px;">{_esc(d.get('prefijo','$'))}{_num(valor)}</span></div>
<svg viewBox="0 0 {w:.0f} {h:.0f}" style="width:100%; height:420px; display:block;">
<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
<stop offset="0%" stop-color="{p['accent']}" stop-opacity=".55"/><stop offset="100%" stop-color="{p['accent']}" stop-opacity="0"/></linearGradient></defs>
<path d="{area}" fill="url(#g)"/>
<path d="{linea}" fill="none" stroke="{p['accent']}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="{ultimo[0]:.1f}" cy="{ultimo[1]:.1f}" r="15" fill="{p['accent']}"/>
<circle cx="{ultimo[0]:.1f}" cy="{ultimo[1]:.1f}" r="26" fill="{p['accent']}" opacity=".28"/>
</svg></div>{tag}"""


# --- 8. Inbox a cero --------------------------------------------------------

def _inbox_cero(d: dict, p: dict, t: float) -> str:
    """El contador de mensajes sin responder bajando hasta cero mientras el
    agente los va tildando. Es la versión visual del alivio."""
    msgs = d.get("mensajes", [])[:5]
    n = len(msgs)
    pendientes = n
    filas = ""
    for i, m in enumerate(msgs):
        prog = _escalonado(t, i, n, 0.24, 0.86, 0.42)
        hecho = prog > 0.55
        if hecho:
            pendientes -= 1
        filas += f"""<div style="display:flex; align-items:center; gap:22px; border:1px solid {p['line']};
     background:{p['panel'] if not hecho else f"{p['accent']}12"}; border-radius:18px; padding:24px 28px;
     {_reveal(_escalonado(t, i, n, 0.06, 0.34, 0.7), 14)}">
<span style="width:44px; height:44px; border-radius:50%; flex:none; display:flex; align-items:center; justify-content:center;
      background:{p['accent'] if hecho else p['panel2']}; color:{'#08111F' if hecho else p['dim']}; font-size:24px; font-weight:800;">{'✓' if hecho else '•'}</span>
<span style="flex:1; font-size:27px; color:{p['dim'] if hecho else p['ink']}; {'text-decoration:line-through; opacity:.6;' if hecho else ''}">{_esc(m)}</span>
{'<span class="pill chip-ok" style="font-size:20px;">respondido</span>' if hecho else f'<span style="font-size:22px; color:{p["bad"]};">sin leer</span>'}
</div>"""

    p_cont = _tramo(t, 0.1, 0.3)
    return f"""<div style="display:flex; align-items:center; justify-content:center; gap:20px; margin-bottom:30px; {_reveal(p_cont, 16)}">
<span class="big-num mono" style="font-size:96px; color:{p['bad'] if pendientes else p['accent']};">{pendientes}</span>
<span style="font-size:30px; color:{p['dim']};">{_esc(d.get('label','sin responder'))}</span></div>
<div style="display:flex; flex-direction:column; gap:14px;">{filas}</div>"""


# --- 9. Flujo de nodos ------------------------------------------------------

def _flujo_nodos(d: dict, p: dict, t: float) -> str:
    """La automatización por dentro: los pasos se encienden en orden y la
    línea que los une se va pintando. Explica el 'cómo funciona' sin texto."""
    pasos = d.get("pasos", [])[:5]
    n = len(pasos)
    filas = ""
    for i, paso in enumerate(pasos):
        prog = _escalonado(t, i, n, 0.16, 0.88, 0.4)
        on = prog > 0.4
        conector = ""
        if i < n - 1:
            # El conector se llena con el progreso del paso SIGUIENTE: así la
            # línea viaja hacia el nodo justo antes de que se encienda.
            sig = _escalonado(t, i + 1, n, 0.16, 0.88, 0.4)
            conector = f"""<div style="width:4px; height:36px; margin:0 0 0 34px; background:{p['line']}; border-radius:2px; overflow:hidden;">
<div style="width:100%; height:{_ease(sig) * 100:.0f}%; background:{p['accent']};"></div></div>"""
        filas += f"""<div style="{_reveal(_escalonado(t, i, n, 0.05, 0.4, 0.7), 14)}">
<div style="display:flex; align-items:center; gap:26px;">
<span style="width:72px; height:72px; flex:none; border-radius:22px; display:flex; align-items:center; justify-content:center;
      font-family:'Display',serif; font-weight:800; font-size:32px;
      background:{f'linear-gradient(135deg,{p["accent"]},{p["accent2"]})' if on else p['panel2']};
      color:{'#08111F' if on else p['dim']};
      box-shadow:{f'0 0 0 10px {p["accent"]}1e' if on else 'none'};">{i + 1}</span>
<div style="flex:1; background:{p['panel']}; border:1px solid {p['accent'] + '55' if on else p['line']};
     border-radius:18px; padding:24px 28px; font-size:29px; line-height:1.3;">{_esc(_sin_numeracion(paso))}</div></div>
{conector}</div>"""
    return f'<div style="display:flex; flex-direction:column;">{filas}</div>'


# --- 10. Antes / después ----------------------------------------------------

def _antes_despues(d: dict, p: dict, t: float) -> str:
    """Dos columnas: cómo era y cómo quedó. La de la derecha entra después, y
    cada ítem cae en cascada, para que la comparación se lea en ese orden."""
    antes = d.get("antes", [])[:4]
    despues = d.get("despues", [])[:4]

    def _items(items, ok, inicio):
        out = ""
        for i, x in enumerate(items):
            prog = _escalonado(t, i, len(items), inicio, inicio + 0.34, 0.45)
            color = p["ok"] if ok else p["bad"]
            out += f"""<div style="display:flex; gap:14px; align-items:flex-start; font-size:26px; line-height:1.35; margin-top:20px; {_reveal(prog, 12)}">
<span style="color:{color}; font-weight:800; flex:none;">{'✓' if ok else '✕'}</span><span>{_esc(x)}</span></div>"""
        return out

    p_izq = _tramo(t, 0.12, 0.3)
    p_der = _tramo(t, 0.44, 0.62)
    return f"""<div style="display:flex; gap:20px; align-items:stretch;">
<div style="flex:1; background:{p['panel']}; border:1px solid {p['bad']}33; border-radius:24px; padding:32px 28px; {_reveal(p_izq, 22)}">
<div style="font-size:24px; letter-spacing:.12em; text-transform:uppercase; color:{p['bad']};">{_esc(d.get('label_antes','Antes'))}</div>
{_items(antes, False, 0.2)}</div>
<div style="flex:1; background:linear-gradient(160deg,{p['accent']}1c,{p['panel']} 60%); border:1px solid {p['accent']}55; border-radius:24px; padding:32px 28px; {_reveal(p_der, 22)}">
<div style="font-size:24px; letter-spacing:.12em; text-transform:uppercase; color:{p['accent']};">{_esc(d.get('label_despues','Después'))}</div>
{_items(despues, True, 0.52)}</div></div>"""


# --- 11. Captación de clientes ----------------------------------------------

def _captacion(d: dict, p: dict, t: float) -> str:
    """De dónde viene la gente y cuántos terminan siendo contactos reales:
    las fuentes entran primero, después baja el flujo al contador."""
    fuentes = d.get("fuentes", [])[:3]
    chips = ""
    for i, f in enumerate(fuentes):
        prog = _escalonado(t, i, len(fuentes), 0.14, 0.46, 0.4)
        chips += f"""<div style="flex:1; background:{p['panel']}; border:1px solid {p['line']}; border-radius:20px;
     padding:26px 20px; text-align:center; {_reveal(prog, 18)}">
<div style="font-size:36px;">{_esc(f.get('icono','•'))}</div>
<div style="font-size:23px; color:{p['dim']}; margin-top:10px;">{_esc(f.get('label',''))}</div>
<div class="mono" style="font-size:32px; font-weight:700; margin-top:8px;">{_num(_entero(float(f.get('valor', 0)), prog))}</div></div>"""

    p_flecha = _tramo(t, 0.46, 0.62)
    p_total = _tramo(t, 0.58, 0.9)
    total = _entero(float(d.get("total", 0)), p_total)
    return f"""<div style="display:flex; gap:16px;">{chips}</div>
<div style="text-align:center; font-size:44px; color:{p['accent']}; margin:22px 0; opacity:{_ease(p_flecha):.2f};">↓</div>
<div style="background:linear-gradient(135deg,{p['accent']},{p['accent2']}); border-radius:26px; padding:40px 34px; text-align:center;
     color:#08111F; box-shadow:0 24px 60px rgba(0,0,0,.4); {_reveal(p_total, 24)}">
<div class="mono" style="font-family:'Display',serif; font-weight:800; font-size:100px; line-height:1;">{_num(total)}</div>
<div style="font-size:29px; font-weight:600; margin-top:12px;">{_esc(d.get('total_label','contactos nuevos'))}</div></div>"""


# --- 12. Checkout / venta cerrada -------------------------------------------

def _checkout(d: dict, p: dict, t: float) -> str:
    """Una venta cerrándose paso a paso en el teléfono, hasta el 'pago
    aprobado' y el monto entrando. Es el final del recorrido comercial."""
    pasos = d.get("pasos", [])[:4]
    n = len(pasos)
    filas = ""
    for i, paso in enumerate(pasos):
        prog = _escalonado(t, i, n, 0.18, 0.74, 0.35)
        hecho = prog > 0.6
        filas += f"""<div style="display:flex; align-items:center; gap:18px; padding:20px 0; border-bottom:1px solid {p['line']};
     {_reveal(_escalonado(t, i, n, 0.08, 0.42, 0.6), 12)}">
<span style="width:38px;height:38px;border-radius:50%;flex:none;display:flex;align-items:center;justify-content:center;
      background:{p['accent'] if hecho else p['panel2']}; color:{'#08111F' if hecho else p['dim']}; font-size:20px; font-weight:800;">{'✓' if hecho else i + 1}</span>
<span style="font-size:26px; color:{p['ink'] if hecho else p['dim']};">{_esc(_sin_numeracion(paso))}</span></div>"""

    p_ok = _tramo(t, 0.76, 0.94)
    monto = _entero(float(d.get("monto", 0)), _tramo(t, 0.78, 0.97))
    return f"""<div style="display:flex; justify-content:center;">
<div style="width:78%; background:{p['panel']}; border:1px solid {p['line']}; border-radius:40px; padding:36px 32px;
     box-shadow:0 34px 80px rgba(0,0,0,.5);">
<div style="text-align:center; font-size:25px; color:{p['dim']}; letter-spacing:.1em; text-transform:uppercase;">{_esc(d.get('titulo','Checkout'))}</div>
<div style="margin-top:24px;">{filas}</div>
<div style="margin-top:28px; text-align:center; {_reveal(p_ok, 18)}">
<span class="pill chip-ok" style="font-size:26px; padding:16px 30px;">✓ {_esc(d.get('resultado','Pago aprobado'))}</span>
<div class="big-num mono" style="font-size:78px; margin-top:22px;">{_esc(d.get('prefijo','$'))}{_num(monto)}</div></div>
</div></div>"""


# --- 13. Ranking de barras --------------------------------------------------

def _ranking_barras(d: dict, p: dict, t: float) -> str:
    """Barras horizontales creciendo a distinto ritmo: sirve para comparar
    canales, horarios o rubros de un vistazo, sin leer una tabla."""
    items = d.get("items", [])[:5]
    n = len(items)
    maximo = max([float(x.get("valor", 0)) for x in items] or [1]) or 1
    filas = ""
    for i, it in enumerate(items):
        prog = _escalonado(t, i, n, 0.16, 0.88, 0.62)
        valor = float(it.get("valor", 0))
        ancho = (valor / maximo) * 100 * _ease(prog)
        lider = valor >= maximo
        fondo = (f"linear-gradient(90deg,{p['accent2']},{p['accent']})" if lider
                 else f"linear-gradient(90deg,{p['accent']}66,{p['accent']}aa)")
        filas += f"""<div style="{_reveal(_escalonado(t, i, n, 0.05, 0.4, 0.72), 14)}">
<div style="display:flex; justify-content:space-between; align-items:baseline; margin-bottom:10px;">
<span style="font-size:27px; color:{p['ink'] if lider else p['dim']};">{_esc(it.get('label',''))}</span>
<span class="mono" style="font-size:30px; font-weight:700; color:{p['accent'] if lider else p['dim']};">{_esc(d.get('prefijo',''))}{_num(_entero(valor, prog))}{_esc(d.get('sufijo',''))}</span></div>
<div class="bar-track" style="height:30px;"><div style="height:100%; border-radius:999px; width:{ancho:.1f}%; background:{fondo};"></div></div></div>"""
    return f'<div style="display:flex; flex-direction:column; gap:24px;">{filas}</div>'


# --- 14. Mapa de calor de horarios ------------------------------------------

def _mapa_horarios(d: dict, p: dict, t: float) -> str:
    """Grilla que se enciende celda por celda mostrando cuándo entra la
    demanda. La lectura es inmediata: las horas calientes caen fuera del
    horario en que hay alguien atendiendo."""
    filas_datos = d.get("filas", [])[:5]
    horas = d.get("horas", ["9h", "12h", "15h", "18h", "21h", "23h"])[:6]
    ncols = len(horas)
    cuerpo = ""
    total_celdas = max(1, len(filas_datos) * ncols)
    idx = 0
    for r, fila in enumerate(filas_datos):
        valores = (fila.get("valores") or [])[:ncols]
        celdas = ""
        for c in range(ncols):
            prog = _escalonado(t, idx, total_celdas, 0.14, 0.84, 0.94)
            idx += 1
            v = float(valores[c]) if c < len(valores) else 0.0
            intensidad = min(1.0, max(0.0, v / 10.0)) * _ease(prog)
            alfa = 0.06 + intensidad * 0.94
            color = p["accent"] if intensidad < 0.62 else p["accent2"]
            celdas += f"""<div style="flex:1; aspect-ratio:1/1; border-radius:12px; background:{color};
                 opacity:{alfa:.2f}; border:1px solid {p['line']};"></div>"""
        cuerpo += f"""<div style="display:flex; align-items:center; gap:12px; {_reveal(_escalonado(t, r, len(filas_datos), 0.05, 0.35, 0.6), 12)}">
<span style="width:120px; flex:none; font-size:24px; color:{p['dim']};">{_esc(fila.get('label',''))}</span>
<div style="flex:1; display:flex; gap:12px;">{celdas}</div></div>"""

    encabezado = "".join(f'<div style="flex:1; text-align:center; font-size:21px; color:{p["dim"]};">{_esc(h)}</div>' for h in horas)
    p_nota = _tramo(t, 0.84, 0.97)
    nota = ""
    if p_nota > 0 and d.get("nota"):
        nota = f"""<div style="margin-top:28px; text-align:center; {_reveal(p_nota, 14)}">
<span class="pill chip-ok" style="font-size:26px; padding:16px 30px;">{_esc(d['nota'])}</span></div>"""
    return f"""<div style="display:flex; flex-direction:column; gap:14px;">
<div style="display:flex; align-items:center; gap:12px;"><span style="width:120px; flex:none;"></span>
<div style="flex:1; display:flex; gap:12px;">{encabezado}</div></div>
{cuerpo}</div>{nota}"""


# --- 15. Consola / log del agente -------------------------------------------

def _consola(d: dict, p: dict, t: float) -> str:
    """Las líneas de log del agente apareciendo como si corriera en vivo, con
    el cursor titilando al final. Es la escena de credibilidad técnica: mostrar
    que atrás hay un sistema, no una persona copiando y pegando."""
    lineas = d.get("lineas", [])[:6]
    n = len(lineas)
    filas = ""
    for i, l in enumerate(lineas):
        prog = _escalonado(t, i, n, 0.14, 0.86, 0.25)
        if prog <= 0:
            continue
        texto = l.get("texto", "") if isinstance(l, dict) else str(l)
        marca = l.get("marca", "") if isinstance(l, dict) else ""
        ok = bool(l.get("ok")) if isinstance(l, dict) else False
        # Máquina de escribir: la línea se revela carácter por carácter en el
        # primer tramo de su ventana. Es lo que hace que se lea como consola.
        visible = texto[:max(1, int(len(texto) * _clamp(prog * 2.2)))]
        color = p["ok"] if ok else p["ink"]
        filas += f"""<div style="display:flex; gap:18px; align-items:baseline; padding:12px 0; {_reveal(prog, 8)}">
<span class="mono" style="font-size:22px; color:{p['dim']}; flex:none; min-width:96px;">{_esc(marca)}</span>
<span class="mono" style="font-size:26px; color:{color}; line-height:1.35;">{_esc(visible)}</span></div>"""

    p_cursor = _tramo(t, 0.86, 1.0)
    cursor = f'<span style="display:inline-block; width:16px; height:28px; background:{p["accent"]}; opacity:{0.25 + 0.75 * (t * 12 % 1 > 0.5):.2f};"></span>'
    return f"""<div style="background:{p['bg2']}; border:1px solid {p['line']}; border-radius:24px; overflow:hidden;
     box-shadow:0 30px 70px rgba(0,0,0,.45);">
<div style="display:flex; align-items:center; gap:10px; padding:22px 26px; background:{p['panel']}; border-bottom:1px solid {p['line']};">
<span style="width:13px;height:13px;border-radius:50%;background:#FF5F57"></span>
<span style="width:13px;height:13px;border-radius:50%;background:#FEBC2E"></span>
<span style="width:13px;height:13px;border-radius:50%;background:#28C840"></span>
<span class="mono" style="margin-left:14px; font-size:22px; color:{p['dim']};">{_esc(d.get('titulo','agente · en vivo'))}</span></div>
<div style="padding:30px 30px 34px;">{filas}{cursor if p_cursor > 0 else ''}</div></div>"""


# --- 16. Comparación de costos ----------------------------------------------

def _costos(d: dict, p: dict, t: float) -> str:
    """Dos columnas de costo enfrentadas, creciendo cada una hasta su número,
    con el ahorro cantado abajo. Responde la objeción de precio sin decir el
    precio de la agencia: compara el costo de SEGUIR COMO ESTÁ."""
    izq, der = d.get("opcion_a", {}), d.get("opcion_b", {})
    val_a = float(izq.get("valor", 0))
    val_b = float(der.get("valor", 0))
    maximo = max(val_a, val_b) or 1
    p_a = _tramo(t, 0.16, 0.55)
    p_b = _tramo(t, 0.34, 0.74)

    def _col(op, prog, valor, es_caro):
        # Piso de 70px: cuando una opción es diez veces más barata que la otra
        # su barra proporcional queda en un hilo de 30px que se lee como un
        # error de render en vez de como "esto cuesta poco".
        alto = (70 + 260 * (valor / maximo)) * _ease(prog)
        color = p["bad"] if es_caro else p["accent"]
        return f"""<div style="flex:1; display:flex; flex-direction:column; align-items:center; {_reveal(prog, 20)}">
<div class="mono" style="font-size:46px; font-weight:800; color:{color}; margin-bottom:16px;">{_esc(d.get('prefijo','$'))}{_num(_entero(valor, prog))}</div>
<div style="width:100%; height:{alto:.0f}px; border-radius:20px 20px 0 0;
     background:linear-gradient(180deg,{color},{color}44); box-shadow:0 -8px 30px {color}33;"></div>
<div style="margin-top:18px; font-size:27px; text-align:center; line-height:1.3;">{_esc(op.get('label',''))}</div>
<div style="font-size:22px; color:{p['dim']}; margin-top:8px; text-align:center;">{_esc(op.get('detalle',''))}</div></div>"""

    p_ahorro = _tramo(t, 0.78, 0.96)
    ahorro = ""
    if p_ahorro > 0 and d.get("ahorro"):
        ahorro = f"""<div style="margin-top:34px; text-align:center; {_reveal(p_ahorro, 16)}">
<span class="pill chip-ok" style="font-size:29px; padding:18px 34px;">{_esc(d['ahorro'])}</span></div>"""

    return f"""<div style="display:flex; gap:40px; align-items:flex-end; min-height:440px;">
{_col(izq, p_a, val_a, True)}{_col(der, p_b, val_b, False)}</div>{ahorro}"""


# --- 17. Reseñas y reputación -----------------------------------------------

def _resenas(d: dict, p: dict, t: float) -> str:
    """La calificación subiendo estrella por estrella y las reseñas entrando
    abajo. Sirve para el ángulo de reputación: responder rápido y hacer
    seguimiento es lo que mueve la nota, y eso se ve."""
    puntaje = float(d.get("puntaje", 4.8))
    p_estrellas = _tramo(t, 0.12, 0.5)
    mostrado = puntaje * _ease(p_estrellas)
    estrellas = ""
    for i in range(5):
        lleno = _clamp(mostrado - i)
        # Cada estrella se "llena" con un degradé cortado en el porcentaje
        # exacto: así la última puede quedar a medias (4,6 de 5) en vez de
        # saltar de vacía a llena.
        estrellas += f"""<span style="font-size:64px; line-height:1;
     background:linear-gradient(90deg,{p['accent']} {lleno * 100:.0f}%, {p['panel2']} {lleno * 100:.0f}%);
     -webkit-background-clip:text; background-clip:text; color:transparent;">★</span>"""

    cards = d.get("resenas", [])[:3]
    filas = ""
    for i, r in enumerate(cards):
        prog = _escalonado(t, i, len(cards), 0.5, 0.9, 0.4)
        filas += f"""<div style="background:{p['panel']}; border:1px solid {p['line']}; border-radius:18px; padding:24px 26px; {_reveal(prog, 16)}">
<div style="font-size:24px; color:{p['accent']};">{'★' * int(r.get('estrellas', 5))}</div>
<div style="font-size:26px; line-height:1.4; margin-top:12px;">{_esc(r.get('texto',''))}</div>
<div style="font-size:21px; color:{p['dim']}; margin-top:12px;">{_esc(r.get('autor',''))}</div></div>"""

    return f"""<div style="text-align:center; {_reveal(_tramo(t, 0.06, 0.28), 18)}">
<div style="display:flex; gap:10px; justify-content:center;">{estrellas}</div>
<div style="display:flex; align-items:baseline; justify-content:center; gap:14px; margin-top:20px;">
<span class="big-num mono" style="font-size:72px;">{mostrado:.1f}</span>
<span style="font-size:28px; color:{p['dim']};">{_esc(d.get('label','de 5'))}</span></div></div>
<div style="display:flex; flex-direction:column; gap:16px; margin-top:34px;">{filas}</div>"""


# --- 18. Stock / inventario -------------------------------------------------

def _stock(d: dict, p: dict, t: float) -> str:
    """Niveles de stock que se actualizan solos, con el que está en rojo
    resolviéndose. Para negocios de producto, donde el problema no son los
    turnos sino quedarse sin lo que más se vende."""
    items = d.get("items", [])[:5]
    n = len(items)
    filas = ""
    for i, it in enumerate(items):
        prog = _escalonado(t, i, n, 0.16, 0.84, 0.5)
        nivel = float(it.get("nivel", 50))
        critico = nivel < 25
        color = p["bad"] if critico else p["accent"]
        ancho = nivel * _ease(prog)
        # El ítem crítico se "repone" en el último tramo: la barra salta al
        # valor repuesto y el chip cambia de alerta a resuelto.
        repuesto = it.get("repuesto")
        p_rep = _tramo(t, 0.72, 0.92) if critico and repuesto is not None else 0.0
        if p_rep > 0:
            ancho = nivel + (float(repuesto) - nivel) * _ease(p_rep)
            color = p["accent"] if p_rep > 0.5 else p["bad"]
        chip = (f'<span class="pill chip-ok" style="font-size:20px;">repuesto</span>' if p_rep > 0.5
                else (f'<span class="pill chip-bad" style="font-size:20px;">se acaba</span>' if critico else ""))
        filas += f"""<div style="{_reveal(_escalonado(t, i, n, 0.05, 0.38, 0.7), 14)}">
<div style="display:flex; justify-content:space-between; align-items:baseline; margin-bottom:10px;">
<span style="font-size:26px;">{_esc(it.get('label',''))}</span>
<span style="display:flex; align-items:center; gap:14px;">{chip}
<span class="mono" style="font-size:26px; color:{color};">{_entero(ancho, 1.0)}%</span></span></div>
<div class="bar-track" style="height:22px;"><div style="height:100%; border-radius:999px; width:{ancho:.1f}%; background:{color};"></div></div></div>"""
    return f'<div style="display:flex; flex-direction:column; gap:22px;">{filas}</div>'


# --- 19. Presupuesto armándose ----------------------------------------------

def _cotizacion(d: dict, p: dict, t: float) -> str:
    """Un presupuesto que se arma solo, ítem por ítem, hasta el total. Es la
    escena para el clásico 'me pasás precio?' que hoy tarda dos días."""
    items = d.get("items", [])[:5]
    n = len(items)
    filas = ""
    acumulado = 0.0
    for i, it in enumerate(items):
        prog = _escalonado(t, i, n, 0.16, 0.72, 0.35)
        monto = float(it.get("monto", 0))
        acumulado += monto * _ease(prog)
        filas += f"""<div style="display:flex; justify-content:space-between; align-items:baseline;
     padding:22px 0; border-bottom:1px solid {p['line']}; {_reveal(prog, 14)}">
<span style="font-size:27px;">{_esc(it.get('label',''))}</span>
<span class="mono" style="font-size:29px; color:{p['dim']};">{_esc(d.get('prefijo','$'))}{_num(_entero(monto, prog))}</span></div>"""

    p_total = _tramo(t, 0.7, 0.92)
    p_env = _tramo(t, 0.88, 1.0)
    enviado = ""
    if p_env > 0:
        enviado = f"""<div style="margin-top:26px; text-align:center; {_reveal(p_env, 14)}">
<span class="pill chip-ok" style="font-size:25px;">✓ {_esc(d.get('resultado','Enviado por WhatsApp'))}</span></div>"""

    return f"""<div class="card" style="padding:36px 34px;">
<div style="font-size:25px; color:{p['dim']}; text-transform:uppercase; letter-spacing:.1em;">{_esc(d.get('titulo','Presupuesto'))}</div>
<div style="margin-top:20px;">{filas}</div>
<div style="display:flex; justify-content:space-between; align-items:baseline; margin-top:28px; {_reveal(p_total, 16)}">
<span style="font-size:30px; font-weight:700;">Total</span>
<span class="big-num mono" style="font-size:64px;">{_esc(d.get('prefijo','$'))}{_num(int(round(acumulado)))}</span></div>
</div>{enviado}"""


# --- 20. Notificaciones entrando --------------------------------------------

def _notificaciones(d: dict, p: dict, t: float) -> str:
    """Notificaciones apilándose en el teléfono, una atrás de otra. Muestra el
    volumen real de lo que entra —el problema— o el flujo de avisos que ahora
    llegan resueltos, según cómo lo escriba la IA."""
    avisos = d.get("avisos", [])[:5]
    n = len(avisos)
    filas = ""
    for i, a in enumerate(avisos):
        prog = _escalonado(t, i, n, 0.14, 0.86, 0.42)
        if prog <= 0:
            continue
        # Entran desde la derecha, como una notificación de verdad.
        e = _ease(prog)
        filas += f"""<div style="display:flex; gap:18px; align-items:flex-start;
     background:{p['panel']}cc; border:1px solid {p['line']}; border-radius:22px; padding:24px 26px;
     opacity:{min(1.0, prog * 1.8):.2f}; transform:translateX({(1 - e) * 60:.0f}px);
     box-shadow:0 16px 40px rgba(0,0,0,.32);">
<span style="width:52px; height:52px; border-radius:14px; flex:none; display:flex; align-items:center; justify-content:center;
      background:linear-gradient(135deg,{p['accent']},{p['accent2']}); font-size:26px;">{_esc(a.get('icono','💬'))}</span>
<div style="flex:1;">
<div style="display:flex; justify-content:space-between; align-items:baseline;">
<span style="font-size:24px; font-weight:700;">{_esc(a.get('titulo',''))}</span>
<span class="mono" style="font-size:20px; color:{p['dim']};">{_esc(a.get('hora',''))}</span></div>
<div style="font-size:24px; color:{p['dim']}; margin-top:8px; line-height:1.35;">{_esc(a.get('texto',''))}</div></div></div>"""
    return f'<div style="display:flex; flex-direction:column; gap:16px;">{filas}</div>'


# --- 21. Calculadora de retorno ---------------------------------------------

def _roi(d: dict, p: dict, t: float) -> str:
    """Dos entradas (lo que se pierde hoy, lo que se recupera) que bajan a un
    resultado grande. Es la escena de 'cuánto te cuesta no hacerlo', armada
    como cuenta transparente y no como promesa."""
    entradas = d.get("entradas", [])[:3]
    filas = ""
    for i, e in enumerate(entradas):
        prog = _escalonado(t, i, len(entradas), 0.14, 0.5, 0.4)
        filas += f"""<div style="flex:1; background:{p['panel']}; border:1px solid {p['line']}; border-radius:20px;
     padding:26px 22px; text-align:center; {_reveal(prog, 18)}">
<div style="font-size:22px; color:{p['dim']}; line-height:1.3; min-height:58px;">{_esc(e.get('label',''))}</div>
<div class="mono" style="font-size:40px; font-weight:800; margin-top:12px; color:{p['ink']};">{_esc(e.get('prefijo',''))}{_num(_entero(float(e.get('valor', 0)), prog))}{_esc(e.get('sufijo',''))}</div></div>"""

    p_flecha = _tramo(t, 0.5, 0.64)
    p_res = _tramo(t, 0.6, 0.92)
    return f"""<div style="display:flex; gap:16px;">{filas}</div>
<div style="text-align:center; font-size:46px; color:{p['accent']}; margin:24px 0; opacity:{_ease(p_flecha):.2f};">↓</div>
<div style="background:linear-gradient(135deg,{p['accent']},{p['accent2']}); border-radius:28px; padding:40px 32px; text-align:center;
     color:#08111F; box-shadow:0 26px 64px rgba(0,0,0,.42); {_reveal(p_res, 24)}">
<div style="font-size:26px; font-weight:700; opacity:.8;">{_esc(d.get('resultado_label','Lo que se recupera'))}</div>
<div class="mono" style="font-family:'Display',serif; font-weight:800; font-size:96px; line-height:1; margin-top:10px;">{_esc(d.get('prefijo','$'))}{_num(_entero(float(d.get('resultado', 0)), p_res))}</div>
<div style="font-size:25px; margin-top:12px; opacity:.85;">{_esc(d.get('nota',''))}</div></div>"""


# --- 22. Crecimiento de la cuenta -------------------------------------------

def _crecimiento(d: dict, p: dict, t: float) -> str:
    """Barras verticales mes a mes creciendo, con el número grande arriba. Es
    la escena de resultado sostenido: no un pico, una curva que se mantiene."""
    meses = d.get("meses", [])[:6]
    n = len(meses)
    maximo = max([float(m.get("valor", 0)) for m in meses] or [1]) or 1
    barras = ""
    for i, m in enumerate(meses):
        prog = _escalonado(t, i, n, 0.18, 0.86, 0.55)
        valor = float(m.get("valor", 0))
        alto = 320 * (valor / maximo) * _ease(prog)
        ultimo = i == n - 1
        fondo = (f"linear-gradient(180deg,{p['accent']},{p['accent2']})" if ultimo
                 else f"linear-gradient(180deg,{p['accent']}99,{p['accent']}33)")
        barras += f"""<div style="flex:1; display:flex; flex-direction:column; align-items:center; justify-content:flex-end;">
<div class="mono" style="font-size:22px; color:{p['ink'] if ultimo else p['dim']}; margin-bottom:10px;
     opacity:{min(1.0, prog * 1.6):.2f};">{_num(_entero(valor, prog))}</div>
<div style="width:100%; height:{alto:.0f}px; border-radius:14px 14px 0 0; background:{fondo};"></div>
<div style="font-size:21px; color:{p['dim']}; margin-top:12px;">{_esc(m.get('label',''))}</div></div>"""

    p_tot = _tramo(t, 0.1, 0.34)
    total = _entero(float(d.get("total", 0)), p_tot)
    return f"""<div style="display:flex; align-items:baseline; justify-content:center; gap:16px; margin-bottom:30px; {_reveal(p_tot, 16)}">
<span class="big-num mono" style="font-size:84px;">{_esc(d.get('prefijo',''))}{_num(total)}</span>
<span style="font-size:29px; color:{p['dim']};">{_esc(d.get('total_label',''))}</span></div>
<div style="display:flex; gap:14px; align-items:flex-end; min-height:380px;">{barras}</div>"""


# Registro de escenas: nombre -> (builder, campos obligatorios que tiene que
# traer la IA). demo_rules.py valida contra esto y demo_build.py rutea acá.
ESCENAS = {
    "chat_agente":      (_chat_agente,      {"mensajes"}),
    "dashboard_kpi":    (_dashboard_kpi,    {"kpis"}),
    "web_widget":       (_web_widget,       {"headline", "mensajes"}),
    "embudo":           (_embudo,           {"etapas"}),
    "agenda":           (_agenda,           {"turnos"}),
    "crm_pipeline":     (_crm_pipeline,     {"tarjetas"}),
    "grafico_ingresos": (_grafico_ingresos, {"valor"}),
    "inbox_cero":       (_inbox_cero,       {"mensajes"}),
    "flujo_nodos":      (_flujo_nodos,      {"pasos"}),
    "antes_despues":    (_antes_despues,    {"antes", "despues"}),
    "captacion":        (_captacion,        {"fuentes", "total"}),
    "checkout":         (_checkout,         {"pasos", "monto"}),
    "ranking_barras":   (_ranking_barras,   {"items"}),
    "mapa_horarios":    (_mapa_horarios,    {"filas"}),
    "consola":          (_consola,          {"lineas"}),
    "costos":           (_costos,           {"opcion_a", "opcion_b"}),
    "resenas":          (_resenas,          {"puntaje", "resenas"}),
    "stock":            (_stock,            {"items"}),
    "cotizacion":       (_cotizacion,       {"items"}),
    "notificaciones":   (_notificaciones,   {"avisos"}),
    "roi":              (_roi,              {"entradas", "resultado"}),
    "crecimiento":      (_crecimiento,      {"meses", "total"}),
}

TIPOS_ESCENA = tuple(ESCENAS)


def build_escena_html(escena: dict, acento: dict, t: float) -> str:
    """Arma el HTML de UNA escena en el instante `t` (0 a 1). demo_build.py
    llama esto una vez por frame; todo lo que se mueve sale de `t`."""
    tipo = escena.get("tipo")
    if tipo not in ESCENAS:
        raise ValueError(f"Tipo de escena de demo desconocido: {tipo!r}")
    builder, _ = ESCENAS[tipo]
    cuerpo = builder(escena, acento, t)
    return _page(acento, escena.get("kicker", "demo"), escena.get("titular", ""),
                 cuerpo, t, escena.get("bajada", ""))
