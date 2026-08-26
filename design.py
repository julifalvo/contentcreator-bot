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
  position:absolute; inset:0; padding:118px 100px 96px;
  display:flex; flex-direction:column;
}}
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
/* --- Chat --- */
.chat {{ display:flex; flex-direction:column; gap:30px; }}
.msg {{ max-width:74%; padding:38px 46px; font-size:42px; line-height:1.42; }}
.msg-in {{
  align-self:flex-start; background:#FFFFFF; color:{p['ink']};
  border:1px solid {p['rule']}; border-radius:8px 30px 30px 30px;
  box-shadow:0 18px 44px rgba(28,23,20,.09);
}}
.msg-out {{
  align-self:flex-end; background:{p['accent']}; color:#FFF9F2;
  border-radius:30px 8px 30px 30px;
  box-shadow:0 20px 48px rgba(28,23,20,.17);
}}
.msg-tag {{
  font-size:20px; letter-spacing:.24em; text-transform:uppercase;
  color:{p['dim']}; margin-bottom:12px;
}}
/* --- Navegador --- */
.browser {{
  border-radius:20px; overflow:hidden; background:#FFFFFF;
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
    pie = (
        f'<div class="body-l" style="margin-top:56px; font-size:32px">{html.escape(s["pie"])}</div>'
        if s.get("pie") else ""
    )
    return f"""<div>
<h2 style="font-size:64px">{html.escape(s['titular'])}</h2>
<div class="chat" style="margin-top:70px">
<div><div class="msg-tag">{html.escape(s['quien_entra'])}</div>
<div class="msg msg-in">{html.escape(s['entrada'])}</div></div>
<div style="align-self:flex-end; text-align:right">
<div class="msg-tag">{html.escape(s['quien_responde'])}</div>
<div class="msg msg-out" style="text-align:left">{html.escape(s['respuesta'])}</div></div>
</div>{pie}</div>"""


def _web(s: dict, p: dict) -> str:
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
</div></div></div>"""


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


BUILDERS = {
    "portada": (_portada, {"titular"}),
    "dato": (_dato, {"numero", "unidad", "detalle"}),
    "texto": (_texto, {"titular", "cuerpo"}),
    "chat": (_chat, {"titular", "quien_entra", "entrada", "quien_responde", "respuesta"}),
    "web": (_web, {"titular", "url", "headline", "bajada", "boton"}),
    "flujo": (_flujo, {"titular", "pasos"}),
    "cita": (_cita, {"texto", "autor"}),
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
