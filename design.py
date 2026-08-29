"""Sistema de diseño editorial: convierte cada slide del carrusel en HTML/CSS.

La estética es de revista/editorial impresa: papel crema, serif de alto
contraste (Playfair Display) para los titulares, sans chico y espaciado
(Inter) para bajadas y etiquetas, filetes finos como divisores, márgenes
generosos y números gigantes como ancla visual.

Cada pieza sortea UNA paleta y la mantiene de principio a fin: la variedad
está entre videos, no dentro del mismo carrusel. Lo mismo vale para las
variantes de los mockups de producto ('chat', 'web', 'flujo'), que viven en
mockups.py y se sortean por pieza: diez de cada tipo, así el mismo ángulo no
rinde siempre la misma lámina.
"""

import html
import random

import mockups

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
  position:absolute; inset:0; padding:430px 150px 540px;
  display:flex; flex-direction:column;
}}
/* Zona segura de TikTok: la UI propia de la app (usuario, caption, botones de
   like/comentario, música) tapa ~150px arriba y ~250px abajo del posteo. El
   @handle y el folio quedan dentro de esa franja tapada si no se los sube.
   El padding vertical es mucho más grande que el lateral por una razón que no
   es estética: el lienzo es 20:9 (ver CANVAS_H en render.py), así que entra
   entero en los celulares de hoy, pero en un 16:9 TikTok recorta ~240px de
   arriba y ~240px de abajo. Esas dos franjas están vacías a propósito y son
   lo único que se pierde; el área útil que queda en el medio es la misma que
   cuando el lienzo era 9:16. El margen lateral sigue siendo generoso porque
   el ancho es lo que menos sobra. */
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
/* --- Ítem (formato 'chisme'): ícono pixel art generado por IA + texto --- */
.item-card {{ display:flex; flex-direction:column; align-items:center; text-align:center; }}
.item-icon-frame {{
  width:420px; height:420px; border-radius:32px; overflow:hidden; flex:none;
  background:{p['bg2']}; border:1px solid {p['rule']};
  display:flex; align-items:center; justify-content:center;
  box-shadow:0 30px 70px rgba(28,23,20,.16);
  margin-bottom:56px;
}}
.item-icon-frame img {{ width:80%; height:80%; object-fit:contain; }}
.item-nombre {{ font-family:'Display', serif; font-weight:800; font-size:88px; line-height:1.05; }}
.item-detalle {{ font-size:38px; line-height:1.5; color:{p['dim']}; margin-top:28px; max-width:88%; }}
/* --- Fondo llamativo (formato 'impacto'): foto generada por IA a página
   completa detrás del texto, en vez del papel editorial del resto de la
   marca. Colores fijos (blanco sobre velo oscuro), no la paleta sorteada:
   una paleta pensada para papel claro no sirve arriba de una foto. El velo
   es más oscuro arriba/abajo (donde van kicker y pie) y más suave al medio,
   para que la foto siga siendo lo llamativo sin perder legibilidad. */
.page-fondo {{ padding:430px 100px 540px; }}
.bg-fondo {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; z-index:0; }}
.scrim-fondo {{
  position:absolute; inset:0; z-index:1;
  background:linear-gradient(180deg, rgba(10,8,6,.60) 0%, rgba(10,8,6,.24) 30%, rgba(10,8,6,.30) 60%, rgba(10,8,6,.88) 100%);
}}
/* Todo lo que va arriba de la foto (kicker, filete, contenido, pie) necesita
   z-index propio: sin esto el orden natural del DOM ya los deja arriba de
   'bg-fondo'/'scrim-fondo', pero position:relative + z-index explícito evita
   que un cambio de orden en _page_fondo() rompa el apilado en silencio. */
.page-fondo .kicker-fondo, .page-fondo .rule-fondo, .page-fondo .content,
.page-fondo .hair-fondo, .page-fondo .foot-fondo {{ position:relative; z-index:2; }}
.kicker-fondo {{
  font-size:26px; font-weight:700; letter-spacing:.34em; text-transform:uppercase; color:#FFD9A8;
}}
.rule-fondo {{ height:2px; background:#FFF9F2; opacity:.55; }}
.hair-fondo {{ height:1px; background:rgba(255,249,242,.35); }}
.foot-fondo {{ color:rgba(255,249,242,.8); }}
.hook-fondo {{
  font-family:'Display', serif; font-weight:800; font-size:104px; line-height:1.1;
  color:#FFF9F2; letter-spacing:-.02em; text-shadow:0 6px 30px rgba(0,0,0,.35);
}}
.punto-numero {{
  font-family:'Display', serif; font-weight:800; font-size:120px; line-height:1; color:#FFD9A8;
  text-shadow:0 6px 30px rgba(0,0,0,.35);
}}
.punto-titulo {{
  font-family:'Display', serif; font-weight:800; font-size:72px; line-height:1.1; color:#FFF9F2;
  margin-top:18px; text-shadow:0 6px 30px rgba(0,0,0,.35);
}}
.punto-detalle {{ font-size:40px; line-height:1.55; color:rgba(255,249,242,.92); margin-top:26px; max-width:92%; }}
.cierre-fondo-titular {{
  font-family:'Display', serif; font-weight:800; font-size:92px; line-height:1.1; color:#FFF9F2;
  text-shadow:0 6px 30px rgba(0,0,0,.35);
}}
.cierre-fondo-accion {{ font-size:40px; color:#FFD9A8; margin-top:36px; font-weight:600; }}
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


def _page_fondo(p: dict, img: str, inner: str, index: int, total: int, kicker: str = "") -> str:
    """Envuelve el contenido en una página con una FOTO llamativa de fondo a
    página completa (formato 'impacto'), en vez del papel editorial de
    _page(): la paleta sorteada no se usa acá, los colores son fijos (blanco/
    acento cálido sobre velo oscuro, ver 'fondo llamativo' en _css) porque
    tienen que funcionar arriba de cualquier foto, no de un papel claro."""
    head = ""
    if kicker:
        head = (
            f'<div class="kicker-fondo">{html.escape(kicker)}</div>'
            f'<div class="rule-fondo" style="margin:26px 0 0"></div>'
        )
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<style>{_css(p)}</style></head><body><div class="page page-fondo">
<img class="bg-fondo" src="{img}" alt="">
<div class="scrim-fondo"></div>
{head}
<div class="content">{inner}</div>
<div class="hair-fondo" style="margin-bottom:26px"></div>
<div class="foot foot-fondo"><span>{HANDLE}</span>
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


def _stat_font_size(numero: str) -> int:
    """El tamaño base (330px) de .stat-num solo entra sin desbordar el canvas
    con números cortos (2-3 caracteres, "87%", "3x"). La IA a veces devuelve
    números más largos ("1.200%", "0,002") que a 330px se salen del margen
    lateral — se achica según la cantidad de caracteres en vez de dejarlo fijo."""
    n = len(numero)
    if n <= 3:
        return 330
    if n == 4:
        return 270
    if n == 5:
        return 230
    if n == 6:
        return 190
    return 160


def _dato(s: dict, p: dict) -> str:
    size = _stat_font_size(s["numero"])
    return f"""<div class="stat">
<div class="stat-num" style="font-size:{size}px">{html.escape(s['numero'])}</div>
<div class="stat-unit">{html.escape(s['unidad'])}</div>
<div class="hair" style="margin:52px 0 44px"></div>
<div class="body-l" style="max-width:82%">{html.escape(s['detalle'])}</div></div>"""


def _texto(s: dict, p: dict) -> str:
    return f"""<div><h2>{html.escape(s['titular'])}</h2>
<div class="body-l" style="margin-top:44px; max-width:88%">{html.escape(s['cuerpo'])}</div></div>"""


def _chat(s: dict, p: dict, skin: str | None = None) -> str:
    """Slide 'chat': captura de teléfono con la conversación real (barra de
    estado, cabecera de la app, wallpaper, burbujas con cola y acuse). El
    layout y los colores del teléfono viven en mockups.py, que tiene diez
    variantes — WhatsApp claro/oscuro/Business/Android, Telegram, iMessage,
    Instagram, Messenger, SMS — sorteadas una por pieza. Antes esto era una
    barra de color con dos rectángulos redondeados: se leía como un diagrama
    armado y todas las piezas de la cuenta salían visualmente iguales."""
    return mockups.chat_html(s, p, skin)


def _web(s: dict, p: dict, skin: str | None = None) -> str:
    """Slide 'web': el sitio del negocio con el agente IA instalado, dentro de
    un navegador de verdad (semaforo, pestana con favicon, URL con candado) o
    del telefono. Diez variantes en mockups.SKINS_WEB, que combinan cromo,
    tema claro/oscuro y tres layouts de pagina (landing, split y panel), asi
    el mismo campo 'headline' no rinde siempre la misma pantalla."""
    return mockups.web_html(s, p, skin)


def _flujo(s: dict, p: dict, skin: str | None = None) -> str:
    """Slide 'flujo': los pasos que corre la automatizacion, en una de las diez
    variantes de mockups.SKINS_FLUJO (nodos conectados, timeline o log de
    consola, en claro y oscuro). Antes era una lista con filetes: correcta,
    pero identica en todas las piezas y con cara de folleto en vez de cara de
    software funcionando."""
    return mockups.flujo_html(s, p, skin)


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
    imagen al generador de imágenes, antes de llamar a build_slide_html — por eso no es
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


def _item(s: dict, p: dict) -> str:
    """Slide 'item' (formato 'chisme'): un ícono pixel art generado por IA
    (vía image_gen.py, agregado por generate.py en '_img_data_uri' igual que
    la slide 'foto') más el nombre del ítem y el comentario gracioso."""
    img = s.get("_img_data_uri", "")
    return f"""<div class="item-card">
<div class="item-icon-frame"><img src="{img}" alt=""></div>
<h2 class="item-nombre">{html.escape(s['nombre'])}</h2>
<div class="item-detalle">{html.escape(s['detalle'])}</div>
</div>"""


# --- Slides 'fondo' (formato 'impacto'): la foto va a página completa, la
# agrega _page_fondo() como fondo de TODA la página, no acá adentro — estos
# builders solo arman el texto que va encima. Ver build_slide_html() para el
# ruteo a _page_fondo() en vez de _page().

def _portada_fondo(s: dict, p: dict) -> str:
    return f"""<div class="hook-fondo">{html.escape(s['titular'])}</div>"""


def _punto(s: dict, p: dict) -> str:
    return f"""<div>
<div class="punto-numero">{int(s['numero']):02d}</div>
<div class="punto-titulo">{html.escape(s['titulo'])}</div>
<div class="punto-detalle">{html.escape(s['detalle'])}</div>
</div>"""


def _cierre_fondo(s: dict, p: dict) -> str:
    return f"""<div>
<div class="cierre-fondo-titular">{html.escape(s['titular'])}</div>
<div class="cierre-fondo-accion">{html.escape(s['accion'])}</div>
</div>"""


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
    "item": (_item, {"nombre", "detalle", "icono_prompt"}),
    "cierre": (_cierre, {"titular", "accion"}),
    "portada_fondo": (_portada_fondo, {"titular", "fondo_prompt"}),
    "punto": (_punto, {"numero", "titulo", "detalle", "fondo_prompt"}),
    "cierre_fondo": (_cierre_fondo, {"titular", "accion", "fondo_prompt"}),
}

SLIDE_TYPES = tuple(BUILDERS)

# Tipos cuyo cuerpo es un mockup de producto con variantes visuales (mockups.py).
_TIPOS_MOCKUP = {"chat", "web", "flujo"}

# Tipos que se renderizan con foto de fondo a página completa (_page_fondo)
# en vez del papel editorial (_page): formato 'impacto'. Ver build_slide_html.
_TIPOS_FONDO = {"portada_fondo", "punto", "cierre_fondo"}


def build_slide_html(slide: dict, palette: dict, index: int, total: int, kicker: str = "",
                     skin: str | None = None) -> str:
    """Arma el HTML completo de un slide a partir del dict que devolvió la IA.

    `skin` es la variante visual del mockup (mockups.py), sorteada una vez por
    pieza en generate.py — igual que la paleta. Solo la reciben los tipos que
    muestran un producto funcionando; al resto no les significa nada."""
    tipo = slide.get("tipo")
    if tipo not in BUILDERS:
        raise ValueError(f"Tipo de slide desconocido: {tipo!r}")
    builder, _ = BUILDERS[tipo]
    inner = builder(slide, palette, skin) if tipo in _TIPOS_MOCKUP else builder(slide, palette)
    if tipo in _TIPOS_FONDO:
        return _page_fondo(palette, slide.get("_img_data_uri", ""), inner, index, total, kicker)
    return _page(palette, inner, index, total, kicker)
