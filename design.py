"""Sistema de diseño editorial: convierte cada slide del carrusel en HTML/CSS.

La estética es de revista/editorial impresa: papel crema, serif de alto
contraste (Playfair Display) para los titulares, sans chico y espaciado
(Inter) para bajadas y etiquetas, filetes finos como divisores, márgenes
generosos y números gigantes como ancla visual.

Cada pieza sortea UNA paleta y la mantiene de principio a fin: la variedad
está entre videos, no dentro del mismo carrusel.
"""

import html
import random

from render import CANVAS_H, CANVAS_W, font_data_uri

# Paletas editoriales. Todas comparten la lógica papel + tinta + un acento
# saturado; cambia el clima, no el sistema.
PALETTES = [
    {  # Papel / Terracota
        "name": "terracota",
        "bg": "#F7F2E9", "bg2": "#EFE6D6",
        "ink": "#1C1714", "dim": "#6E6459",
        "accent": "#B04A2A", "rule": "#DCD1BE",
    },
    {  # Papel / Tinta azul
        "name": "tinta",
        "bg": "#F4F4F0", "bg2": "#E6E8E4",
        "ink": "#14181C", "dim": "#5D6670",
        "accent": "#1F3D6B", "rule": "#D2D6D4",
    },
    {  # Papel / Verde inglés
        "name": "verde",
        "bg": "#F5F4EC", "bg2": "#E8E9DC",
        "ink": "#161A15", "dim": "#5F6858",
        "accent": "#2C5540", "rule": "#D6D8C6",
    },
    {  # Lino / Bordó
        "name": "bordo",
        "bg": "#F6F1EE", "bg2": "#EBE2DD",
        "ink": "#1A1416", "dim": "#6B5D60",
        "accent": "#7D2338", "rule": "#DDD0CB",
    },
]

HANDLE = "@rootbusinessai"


def pick_palette() -> dict:
    return random.choice(PALETTES)


def _css(p: dict) -> str:
    """Hoja de estilos base compartida por todos los tipos de slide."""
    return f"""
@font-face {{
  font-family: 'Display';
  src: url('{font_data_uri("PlayfairDisplay-Bold.ttf")}') format('truetype');
  font-weight: 400 900;
}}
@font-face {{
  font-family: 'Body';
  src: url('{font_data_uri("Inter-Regular.ttf")}') format('truetype');
  font-weight: 100 900;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{
  width:{CANVAS_W}px; height:{CANVAS_H}px; overflow:hidden;
  background:{p['bg']};
}}
body {{
  background:
    radial-gradient(120% 80% at 12% 0%, {p['bg']} 0%, {p['bg2']} 100%);
  color:{p['ink']};
  font-family:'Body', sans-serif;
  -webkit-font-smoothing:antialiased;
  position:relative;
}}
/* Textura de papel: antes era ruido SVG (feTurbulence) a baja opacidad, pero
   son píxeles verdaderamente aleatorios y el PNG no los puede comprimir casi
   nada (1.7MB por slide en vez de ~40KB, y eso tiraba abajo el envío a
   Telegram por timeout). Esta textura repite un tile PEQUEÑO y cacheable:
   sigue rompiendo el look "vectorial plano" sin ensuciar la compresión. */
body::before {{
  content:''; position:absolute; inset:0; pointer-events:none; opacity:.05;
  background-image:
    radial-gradient(circle at 1px 1px, {p['ink']} 1px, transparent 0);
  background-size:5px 5px;
}}
.page {{
  position:absolute; inset:0; padding:170px 100px 270px;
  display:flex; flex-direction:column;
}}
/* Zona segura de TikTok: la UI propia de la app (usuario, caption, botones de
   like/comentario, música) tapa ~150px arriba y ~250px abajo del posteo. El
   @handle y el folio quedan dentro de esa franja tapada si no se los sube. */
/* El contenido se centra verticalmente y ocupa el alto disponible entre el
   encabezado y el pie. Si se deja arriba con un spacer abajo, queda medio
   lienzo vacío y la pieza se ve incompleta. */
.content {{
  flex:1; display:flex; flex-direction:column; justify-content:center;
  min-height:0; padding:34px 0;
}}
.kicker {{
  font-size:26px; font-weight:600; letter-spacing:.34em; text-transform:uppercase;
  color:{p['accent']};
}}
.rule {{ height:2px; background:{p['ink']}; opacity:.86; }}
.hair {{ height:1px; background:{p['rule']}; }}
h1 {{
  font-family:'Display', serif; font-weight:800; font-size:134px; line-height:1.0;
  letter-spacing:-.028em;
}}
h2 {{
  font-family:'Display', serif; font-weight:700; font-size:96px; line-height:1.06;
  letter-spacing:-.02em;
}}
.lead {{ font-size:48px; line-height:1.48; color:{p['dim']}; font-weight:400; }}
.body-l {{ font-size:44px; line-height:1.55; color:{p['dim']}; }}
.accent {{ color:{p['accent']}; }}
.spacer {{ flex:1; }}
.foot {{
  display:flex; justify-content:space-between; align-items:baseline;
  font-size:24px; letter-spacing:.2em; text-transform:uppercase; color:{p['dim']};
}}
.folio {{ font-variant-numeric:tabular-nums; }}
/* --- Ficha de dato --- */
.stat {{ display:flex; flex-direction:column; }}
.stat-num {{
  font-family:'Display', serif; font-weight:800; font-size:330px; line-height:1;
  letter-spacing:-.045em; color:{p['accent']};
}}
.stat-unit {{ font-size:46px; font-weight:600; letter-spacing:-.01em; margin-top:18px; }}
/* --- Chat: imita una captura real de WhatsApp, no un diagrama editorial --- */
.chat-app {{
  border-radius:32px; overflow:hidden; background:#E7E0D3;
  border:1px solid {p['rule']}; box-shadow:0 40px 90px rgba(28,23,20,.2);
}}
.chat-head {{
  display:flex; align-items:center; gap:24px; padding:32px 36px;
  background:{p['accent']}; color:#FFF9F2;
}}
.chat-avatar {{
  width:68px; height:68px; border-radius:50%; flex:none;
  background:rgba(255,255,255,.22); display:flex; align-items:center; justify-content:center;
  font-family:'Display', serif; font-weight:700; font-size:32px;
}}
.chat-name {{ font-size:32px; font-weight:600; }}
.chat-status {{ font-size:22px; opacity:.82; margin-top:4px; }}
.chat-body {{ padding:50px 40px; display:flex; flex-direction:column; gap:26px; }}
.bubble {{ max-width:80%; padding:28px 34px; font-size:38px; line-height:1.4; }}
.bubble-in {{
  align-self:flex-start; background:#FFFFFF; color:#1B1B1B;
  border-radius:6px 26px 26px 26px; box-shadow:0 10px 26px rgba(28,23,20,.1);
}}
.bubble-out {{
  align-self:flex-end; background:#DCF8C6; color:#1B1B1B;
  border-radius:26px 6px 26px 26px; box-shadow:0 10px 26px rgba(28,23,20,.1);
}}
.bubble-meta {{
  display:block; margin-top:14px; font-size:22px; opacity:.55; text-align:right;
}}
.bubble-check {{ color:#3DA0E8; margin-left:4px; }}
.chat-inputbar {{
  display:flex; align-items:center; padding:26px 36px;
  background:#F0EAE0; border-top:1px solid rgba(0,0,0,.06);
}}
.chat-inputbar .pill {{
  flex:1; background:#FFFFFF; border-radius:999px; padding:22px 32px;
  font-size:28px; color:#8A8A8A;
}}
/* --- Navegador --- */
.browser {{
  position:relative; border-radius:20px; overflow:hidden; background:#FFFFFF;
  border:1px solid {p['rule']}; box-shadow:0 40px 90px rgba(28,23,20,.17);
}}
.bar {{
  display:flex; align-items:center; gap:12px; padding:26px 30px;
  background:{p['bg2']}; border-bottom:1px solid {p['rule']};
}}
.dot {{ width:16px; height:16px; border-radius:50%; background:{p['rule']}; }}
.url {{
  margin-left:14px; font-size:24px; color:{p['dim']}; background:{p['bg']};
  padding:12px 26px; border-radius:999px; flex:1;
}}
.screen {{ padding:64px 58px; }}
.chips {{ display:flex; flex-wrap:wrap; gap:16px; margin-top:38px; }}
.chip {{
  font-size:30px; padding:16px 30px; border-radius:999px;
  border:1px solid {p['rule']}; color:{p['dim']};
}}
.btn {{
  display:inline-block; margin-top:42px; background:{p['accent']}; color:#FFF9F2;
  font-size:30px; font-weight:600; padding:26px 52px; border-radius:999px;
}}
/* --- Widget de chat flotante sobre la captura del sitio ---
   En flujo normal (no absolute): alineado a la derecha con margin-left:auto
   y un margin-top negativo para que "flote" sobre el borde del botón, sin
   riesgo de taparse con chips/headline como pasaba al posicionarlo absoluto
   (con contenido variable, el absolute terminaba tapando el último chip). */
.web-widget {{
  width:340px; margin:-46px 0 0 auto;
  background:#FFFFFF; border-radius:20px; overflow:hidden;
  box-shadow:0 24px 60px rgba(28,23,20,.28); border:1px solid {p['rule']};
}}
.web-widget-head {{
  display:flex; align-items:center; gap:14px; padding:20px 22px;
  background:{p['accent']}; color:#FFF9F2;
}}
.web-widget-dot {{
  width:14px; height:14px; border-radius:50%; background:#3DDC84;
  box-shadow:0 0 0 4px rgba(61,220,132,.28); flex:none;
}}
.web-widget-title {{ font-size:22px; font-weight:600; }}
.web-widget-sub {{ font-size:17px; opacity:.85; margin-top:2px; }}
.web-widget-body {{ padding:20px 22px; font-size:19px; color:{p['dim']}; line-height:1.4; }}
.web-widget-bubble {{
  background:{p['bg2']}; border-radius:14px; padding:14px 18px; margin-top:10px;
  font-size:19px; color:{p['ink']};
}}
/* --- Flujo de pasos --- */
.steps {{ display:flex; flex-direction:column; gap:0; }}
.step {{ display:flex; gap:44px; padding:52px 0; border-top:1px solid {p['rule']}; }}
.step:last-child {{ border-bottom:1px solid {p['rule']}; }}
.step-n {{
  font-family:'Display', serif; font-size:70px; font-weight:700;
  color:{p['accent']}; line-height:1; min-width:70px;
}}
.step-t {{ font-size:46px; line-height:1.36; padding-top:6px; }}
/* --- Cita --- */
.quote-mark {{
  font-family:'Display', serif; font-size:250px; line-height:.6;
  color:{p['accent']}; opacity:.26;
}}
/* --- Foto (imagen real generada por IA) --- */
.photo-card {{
  position:relative; border-radius:24px; overflow:hidden;
  box-shadow:0 40px 90px rgba(28,23,20,.22);
}}
.photo-card img {{ display:block; width:100%; height:auto; }}
.photo-scrim {{
  position:absolute; left:0; right:0; bottom:0; padding:90px 46px 46px;
  background:linear-gradient(180deg, rgba(0,0,0,0) 0%, rgba(0,0,0,.72) 100%);
}}
.photo-caption {{
  font-family:'Display', serif; font-weight:700; font-size:52px; color:#FFF9F2; line-height:1.14;
}}
/* --- Código (mockup de editor, para transmitir que hay tecnología real) --- */
.code-window {{
  border-radius:20px; overflow:hidden; background:#1E1E1E;
  box-shadow:0 40px 90px rgba(28,23,20,.24);
}}
.code-bar {{
  display:flex; align-items:center; gap:12px; padding:26px 30px;
  background:#2A2A2A; border-bottom:1px solid #383838;
}}
.code-tab {{
  margin-left:14px; font-family:'Body', monospace; font-size:24px; color:#B8B8B8;
  background:#1E1E1E; padding:10px 24px; border-radius:8px 8px 0 0;
}}
.code-body {{ padding:48px 44px; }}
.code-line {{
  display:flex; gap:32px; font-family:'Consolas','Courier New',monospace;
  font-size:34px; line-height:1.7; white-space:pre-wrap; word-break:break-word;
}}
.code-n {{ color:#5A5A5A; min-width:44px; text-align:right; user-select:none; }}
.code-t {{ color:#E8E8E8; }}
.code-t.is-comment {{ color:#6A9955; font-style:italic; }}
/* --- Comparación: chatbot común vs agente IA --- */
.compare {{ display:flex; gap:28px; }}
.compare-col {{ flex:1; border-radius:20px; padding:40px 34px; }}
.compare-col.is-chatbot {{ background:{p['bg2']}; border:1px solid {p['rule']}; }}
.compare-col.is-agente {{
  background:{p['accent']}; box-shadow:0 30px 70px rgba(28,23,20,.2);
}}
.compare-head {{
  font-size:26px; font-weight:700; letter-spacing:.04em;
  margin-bottom:30px;
}}
.compare-col.is-chatbot .compare-head {{ color:{p['dim']}; }}
.compare-col.is-agente .compare-head {{ color:#FFF9F2; }}
.compare-item {{
  display:flex; gap:16px; align-items:flex-start; font-size:30px; line-height:1.35;
  margin-top:26px;
}}
.compare-item:first-of-type {{ margin-top:0; }}
.compare-col.is-chatbot .compare-item {{ color:{p['dim']}; }}
.compare-col.is-agente .compare-item {{ color:#FFF9F2; }}
.compare-mark {{ flex:none; font-weight:700; }}
"""


def _page(p: dict, inner: str, index: int, total: int, kicker: str = "") -> str:
    """Envuelve el contenido de un slide en la página completa, con el
    encabezado (kicker + filete) y el pie (handle + folio) comunes a todos."""
    head = ""
    if kicker:
        head = (
            f'<div class="kicker">{html.escape(kicker)}</div>'
            f'<div class="rule" style="margin:26px 0 0"></div>'
        )
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<style>{_css(p)}</style></head><body><div class="page">
{head}
<div class="content">{inner}</div>
<div class="hair" style="margin-bottom:26px"></div>
<div class="foot"><span>{HANDLE}</span>
<span class="folio">{index:02d} / {total:02d}</span></div>
</div></body></html>"""


# --- Un constructor por tipo de slide -------------------------------------
# Cada uno recibe el dict que devolvió la IA y arma solo su bloque interno;
# _page() se encarga del marco común.

def _portada(s: dict, p: dict) -> str:
    epi = (
        f'<div class="lead" style="margin-top:48px">{html.escape(s["epigrafe"])}</div>'
        if s.get("epigrafe") else ""
    )
    return f"""<div><h1>{html.escape(s['titular'])}</h1>{epi}</div>"""


def _dato(s: dict, p: dict) -> str:
    return f"""<div class="stat">
<div class="stat-num">{html.escape(s['numero'])}</div>
<div class="stat-unit">{html.escape(s['unidad'])}</div>
<div class="hair" style="margin:52px 0 44px"></div>
<div class="body-l" style="max-width:82%">{html.escape(s['detalle'])}</div></div>"""


def _texto(s: dict, p: dict) -> str:
    return f"""<div><h2>{html.escape(s['titular'])}</h2>
<div class="body-l" style="margin-top:44px; max-width:88%">{html.escape(s['cuerpo'])}</div></div>"""


def _chat(s: dict, p: dict) -> str:
    """Slide 'chat': se renderiza como una captura real de WhatsApp (header con
    avatar + estado, burbujas blanca/verde con tail, doble check azul en la
    respuesta), no como el diagrama editorial de antes — que se veía como un
    gráfico armado, no como algo que el espectador reconozca de su propio celular."""
    nombre, _, meta = s["quien_entra"].partition("·")
    nombre = nombre.strip() or s["quien_entra"]
    meta = meta.strip() or "en línea"
    inicial = html.escape((nombre[:1] or "?").upper())
    pie = (
        f'<div class="body-l" style="margin-top:48px; font-size:32px">{html.escape(s["pie"])}</div>'
        if s.get("pie") else ""
    )
    return f"""<div>
<h2 style="font-size:64px">{html.escape(s['titular'])}</h2>
<div class="chat-app" style="margin-top:64px">
<div class="chat-head"><div class="chat-avatar">{inicial}</div>
<div><div class="chat-name">{html.escape(nombre)}</div><div class="chat-status">{html.escape(meta)}</div></div></div>
<div class="chat-body">
<div class="bubble bubble-in">{html.escape(s['entrada'])}<span class="bubble-meta">{html.escape(meta)}</span></div>
<div class="bubble bubble-out">{html.escape(s['respuesta'])}<span class="bubble-meta">{html.escape(s['quien_responde'])} <span class="bubble-check">&#10003;&#10003;</span></span></div>
</div>
<div class="chat-inputbar"><span class="pill">Escribí un mensaje...</span></div>
</div>{pie}</div>"""


def _web(s: dict, p: dict) -> str:
    """Slide 'web': captura de navegador con un widget de chat flotante
    (agente IA 'en línea') superpuesto abajo a la derecha, como el que
    tendría de verdad el sitio de un negocio con un agente instalado."""
    chips = "".join(f'<span class="chip">{html.escape(c)}</span>' for c in s.get("chips", []))
    return f"""<div>
<h2 style="font-size:60px">{html.escape(s['titular'])}</h2>
<div class="browser" style="margin-top:60px">
<div class="bar"><span class="dot"></span><span class="dot"></span><span class="dot"></span>
<span class="url">{html.escape(s['url'])}</span></div>
<div class="screen">
<div style="font-family:'Display',serif; font-size:56px; font-weight:700; line-height:1.14">
{html.escape(s['headline'])}</div>
<div class="body-l" style="margin-top:26px; font-size:32px">{html.escape(s['bajada'])}</div>
<div class="chips">{chips}</div>
<div class="btn">{html.escape(s['boton'])}</div>
</div>
<div class="web-widget">
<div class="web-widget-head"><span class="web-widget-dot"></span>
<div><div class="web-widget-title">Agente IA</div><div class="web-widget-sub">En línea ahora</div></div></div>
<div class="web-widget-body">Hola&#128075; ¿en qué te puedo ayudar?
<div class="web-widget-bubble">Escribime tu consulta y te respondo al toque.</div></div>
</div>
</div></div>"""


def _flujo(s: dict, p: dict) -> str:
    pasos = "".join(
        f'<div class="step"><div class="step-n">{i}</div>'
        f'<div class="step-t">{html.escape(t)}</div></div>'
        for i, t in enumerate(s.get("pasos", []), 1)
    )
    return f"""<div>
<h2 style="font-size:64px">{html.escape(s['titular'])}</h2>
<div class="steps" style="margin-top:60px">{pasos}</div></div>"""


def _cita(s: dict, p: dict) -> str:
    return f"""<div>
<div class="quote-mark">&ldquo;</div>
<h2 style="margin-top:-46px">{html.escape(s['texto'])}</h2>
<div class="lead" style="margin-top:52px; font-size:34px">{html.escape(s['autor'])}</div></div>"""


def _cierre(s: dict, p: dict) -> str:
    return f"""<div>
<h1 style="font-size:104px">{html.escape(s['titular'])}</h1>
<div class="rule" style="margin:56px 0; width:220px"></div>
<div class="lead" style="max-width:84%">{html.escape(s['accion'])}</div></div>"""


def _foto(s: dict, p: dict) -> str:
    """Slide 'foto': una imagen real (generada por IA vía image_gen.py) con
    pie de foto superpuesto. La IA de texto solo elige 'prompt_imagen'; el
    data URI ('_img_data_uri') lo agrega generate.py después de pedirle la
    imagen a Pollinations, antes de llamar a build_slide_html — por eso no es
    un campo obligatorio en BUILDERS (no lo escribe la IA de texto)."""
    img = s.get("_img_data_uri", "")
    return f"""<div class="photo-card">
<img src="{img}" alt="">
<div class="photo-scrim"><div class="photo-caption">{html.escape(s['titular'])}</div></div>
</div>"""


def _codigo(s: dict, p: dict) -> str:
    """Slide 'código': mockup de editor (estilo VS Code) con unas pocas
    líneas de pseudocódigo ilustrativo — no tiene que compilar de verdad,
    solo transmitir que hay tecnología real atrás de la pieza de marketing."""
    lineas = ""
    for i, linea in enumerate(s.get("codigo", []), 1):
        es_comentario = linea.strip().startswith(("#", "//"))
        clase = " is-comment" if es_comentario else ""
        lineas += (
            f'<div class="code-line"><span class="code-n">{i}</span>'
            f'<span class="code-t{clase}">{html.escape(linea)}</span></div>'
        )
    return f"""<div>
<h2 style="font-size:60px">{html.escape(s['titular'])}</h2>
<div class="code-window" style="margin-top:56px">
<div class="code-bar"><span class="dot"></span><span class="dot"></span><span class="dot"></span>
<span class="code-tab">{html.escape(s.get('lenguaje', 'código'))}</span></div>
<div class="code-body">{lineas}</div>
</div></div>"""


def _comparacion(s: dict, p: dict) -> str:
    """Slide 'comparación': dos columnas lado a lado, chatbot básico (dim,
    con ✕) contra agente IA (color de acento, con ✓) — para que la
    diferencia entre uno y otro se vea de un vistazo."""
    chatbot_items = "".join(
        f'<div class="compare-item"><span class="compare-mark">✕</span><span>{html.escape(x)}</span></div>'
        for x in s.get("chatbot", [])
    )
    agente_items = "".join(
        f'<div class="compare-item"><span class="compare-mark">✓</span><span>{html.escape(x)}</span></div>'
        for x in s.get("agente", [])
    )
    return f"""<div>
<h2 style="font-size:60px">{html.escape(s['titular'])}</h2>
<div class="compare" style="margin-top:56px">
<div class="compare-col is-chatbot"><div class="compare-head">CHATBOT COMÚN</div>{chatbot_items}</div>
<div class="compare-col is-agente"><div class="compare-head">AGENTE IA</div>{agente_items}</div>
</div></div>"""


BUILDERS = {
    "portada": (_portada, {"titular"}),
    "dato": (_dato, {"numero", "unidad", "detalle"}),
    "texto": (_texto, {"titular", "cuerpo"}),
    "chat": (_chat, {"titular", "quien_entra", "entrada", "quien_responde", "respuesta"}),
    "web": (_web, {"titular", "url", "headline", "bajada", "boton"}),
    "flujo": (_flujo, {"titular", "pasos"}),
    "cita": (_cita, {"texto", "autor"}),
    "foto": (_foto, {"titular", "prompt_imagen"}),
    "codigo": (_codigo, {"titular", "codigo"}),
    "comparacion": (_comparacion, {"titular", "chatbot", "agente"}),
    "cierre": (_cierre, {"titular", "accion"}),
}

SLIDE_TYPES = tuple(BUILDERS)


def build_slide_html(slide: dict, palette: dict, index: int, total: int, kicker: str = "") -> str:
    """Arma el HTML completo de un slide a partir del dict que devolvió la IA."""
    tipo = slide.get("tipo")
    if tipo not in BUILDERS:
        raise ValueError(f"Tipo de slide desconocido: {tipo!r}")
    builder, _ = BUILDERS[tipo]
    return _page(palette, builder(slide, palette), index, total, kicker)
