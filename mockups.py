"""Mockups de producto para las slides 'chat', 'web' y 'flujo': lo que la
pieza usa para MOSTRAR la solución funcionando.

Por qué existe este módulo aparte de design.py: hasta ahora cada uno de esos
tres tipos tenía UN layout fijo, así que lo único que cambiaba entre piezas era
la paleta de papel. El chat era una barra de color con dos rectángulos
redondeados; la web, un rectángulo blanco con tres puntitos. Se leían como un
diagrama armado, no como algo que quien mira reconoce de su propio teléfono —
y encima todas las piezas de la cuenta salían visualmente iguales.

Acá los mockups son DATA, no layouts escritos a mano: un renderer parametrizado
por un dict de tokens (colores, wallpaper, forma de burbuja, cromo del sistema
operativo). Sumar la variante 11 es agregar un diccionario a la lista, no
copiar y pegar CSS. Mismo criterio que PALETTES en design.py.

Los mockups traen su propio <style> inline en vez de sumarse a la hoja global
de design.py: cada slide se renderiza como un documento HTML independiente, y
así el CSS de la variante viaja pegado al único slide que la usa (design._css
no necesita enterarse de qué skin se sorteó).

La variante se sortea UNA vez por pieza (igual que la paleta) y se guarda en
contenido.json, así dos slides del mismo carrusel no muestran dos teléfonos
distintos y se puede saber después qué skin generó cada pieza.
"""

import html
import random

# --- Iconos del sistema, como SVG inline -------------------------------------
# Nada de fuentes de iconos ni PNGs: son cuatro formas simples y el render es
# Chrome headless, así que el SVG inline sale nítido a cualquier tamaño y no
# agrega un solo pedido de red.
_SVG_SENAL = ('<svg viewBox="0 0 18 12" width="26" height="18" fill="{c}">'
              '<rect x="0" y="8.5" width="3" height="3.5" rx="1"/>'
              '<rect x="4.6" y="6" width="3" height="6" rx="1"/>'
              '<rect x="9.2" y="3" width="3" height="9" rx="1"/>'
              '<rect x="13.8" y="0" width="3" height="12" rx="1"/></svg>')
_SVG_WIFI = ('<svg viewBox="0 0 20 14" width="26" height="18" fill="{c}">'
             '<path d="M10 13.5 6.9 9.9a4.8 4.8 0 0 1 6.2 0z"/>'
             '<path d="M10 5.2c2.2 0 4.2.8 5.7 2.2l1.7-2A11 11 0 0 0 10 2.4 11 11 0 0 0 2.6 5.4l1.7 2A8.4 8.4 0 0 1 10 5.2z" '
             'opacity=".95"/></svg>')
_SVG_BATERIA = ('<svg viewBox="0 0 28 13" width="34" height="16">'
                '<rect x="0.6" y="0.6" width="23" height="11.8" rx="3.4" fill="none" stroke="{c}" '
                'stroke-opacity=".45" stroke-width="1.2"/>'
                '<rect x="2.4" y="2.4" width="16" height="8.2" rx="2" fill="{c}"/>'
                '<path d="M25.4 4.4v4.2a2.4 2.4 0 0 0 0-4.2z" fill="{c}" fill-opacity=".5"/></svg>')
_SVG_CHEVRON = ('<svg viewBox="0 0 12 20" width="17" height="28" fill="none" stroke="{c}" '
                'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">'
                '<path d="M10.5 1.5 2 10l8.5 8.5"/></svg>')
_SVG_CHECKS = ('<svg viewBox="0 0 22 12" width="30" height="17" fill="none" stroke="{c}" '
               'stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">'
               '<path d="M1 6.6 4.2 10 11 2.2"/><path d="M9.6 8.4 11.6 10 20 1.6"/></svg>')
_SVG_MIC = ('<svg viewBox="0 0 14 20" width="22" height="30" fill="{c}">'
            '<rect x="4.4" y="0.8" width="5.2" height="11" rx="2.6"/>'
            '<path d="M1.6 9.2a5.4 5.4 0 0 0 10.8 0" fill="none" stroke="{c}" stroke-width="1.6" '
            'stroke-linecap="round"/><rect x="6.3" y="14.6" width="1.4" height="4.2" rx=".7"/></svg>')
_SVG_ENVIAR = ('<svg viewBox="0 0 20 20" width="26" height="26" fill="{c}">'
               '<path d="M1.4 18.6 19 10 1.4 1.4l0 6.7L13 10 1.4 11.9z"/></svg>')


def _icono(svg: str, color: str) -> str:
    return svg.replace("{c}", color)


# --- Wallpapers ---------------------------------------------------------------
# Cada wallpaper es (capas, tamanos), un tamano por capa. Con un
# background-size unico se tilea tambien el gradiente de base y el fondo sale
# con bandas horizontales; y con todas las capas al mismo paso el patron se lee
# como una grilla en vez de como una textura. El fondo con textura es la mitad
# de lo que hace que un chat se vea real: un color plano detras de las burbujas
# se lee como diagrama. Son gradientes CSS, no imagenes: no pesan nada.
_WP_WHATSAPP_CLARO = (
    "radial-gradient(circle at 18% 12%, rgba(0,0,0,.032) 0 2px, transparent 3px),"
    "radial-gradient(circle at 62% 34%, rgba(0,0,0,.026) 0 3px, transparent 4px),"
    "radial-gradient(circle at 38% 72%, rgba(0,0,0,.030) 0 2px, transparent 3px),"
    "linear-gradient(#EFE6DC,#EAE0D5)",
    "190px 190px, 260px 260px, 330px 330px, 100% 100%",
)
_WP_WHATSAPP_OSCURO = (
    "radial-gradient(circle at 18% 12%, rgba(255,255,255,.034) 0 2px, transparent 3px),"
    "radial-gradient(circle at 62% 34%, rgba(255,255,255,.026) 0 3px, transparent 4px),"
    "radial-gradient(circle at 38% 72%, rgba(255,255,255,.030) 0 2px, transparent 3px),"
    "linear-gradient(#0B141A,#0B141A)",
    "190px 190px, 260px 260px, 330px 330px, 100% 100%",
)
_WP_TELEGRAM = (
    "radial-gradient(circle at 22% 18%, rgba(255,255,255,.20) 0 3px, transparent 4px),"
    "radial-gradient(circle at 70% 62%, rgba(255,255,255,.14) 0 4px, transparent 5px),"
    "linear-gradient(160deg,#8AB8D8,#B9D4E6 55%,#CFE0EC)",
    "210px 210px, 290px 290px, 100% 100%",
)
_WP_LISO_CLARO = ("linear-gradient(#FFFFFF,#F7F7F9)", "100% 100%")
_WP_LISO_OSCURO = ("linear-gradient(#000000,#0A0A0C)", "100% 100%")
_WP_MATERIAL = ("linear-gradient(#F3F1F8,#EDEAF4)", "100% 100%")


# --- Skins de chat ------------------------------------------------------------
# Diez variantes reales, no diez recoloreadas: cambian el sistema operativo
# (barra de estado de iOS con isla dinámica vs. Android), la forma de la
# burbuja, si hay tilde de entregado, el wallpaper y el orden del encabezado.
SKINS_CHAT = [
    {
        "name": "whatsapp_claro", "label": "WhatsApp (claro)", "os": "ios",
        "wallpaper": _WP_WHATSAPP_CLARO, "screen_bg": "#EFE6DC",
        "head_bg": "#F6F6F6", "head_fg": "#0B0B0B", "head_sub": "#7D8489", "head_icon": "#1A8CFF",
        "in_bg": "#FFFFFF", "in_fg": "#111B21", "out_bg": "#D9FDD3", "out_fg": "#111B21",
        "meta": "#667781", "check": "#53BDEB", "tail": True, "radius": 20,
        "bar_bg": "#F6F6F6", "bar_field": "#FFFFFF", "bar_fg": "#8E9296", "bar_icon": "#8E9296",
        "status_fg": "#0B0B0B", "sub": "en línea",
    },
    {
        "name": "whatsapp_oscuro", "label": "WhatsApp (oscuro)", "os": "ios",
        "wallpaper": _WP_WHATSAPP_OSCURO, "screen_bg": "#0B141A",
        "head_bg": "#1F2C33", "head_fg": "#E9EDEF", "head_sub": "#8696A0", "head_icon": "#53BDEB",
        "in_bg": "#202C33", "in_fg": "#E9EDEF", "out_bg": "#005C4B", "out_fg": "#E9EDEF",
        "meta": "#8696A0", "check": "#53BDEB", "tail": True, "radius": 20,
        "bar_bg": "#1F2C33", "bar_field": "#2A3942", "bar_fg": "#8696A0", "bar_icon": "#8696A0",
        "status_fg": "#E9EDEF", "sub": "en línea",
    },
    {
        "name": "whatsapp_business", "label": "WhatsApp Business", "os": "android",
        "wallpaper": _WP_WHATSAPP_CLARO, "screen_bg": "#EFE6DC",
        "head_bg": "#008069", "head_fg": "#FFFFFF", "head_sub": "#D7F0E9", "head_icon": "#FFFFFF",
        "in_bg": "#FFFFFF", "in_fg": "#111B21", "out_bg": "#D9FDD3", "out_fg": "#111B21",
        "meta": "#667781", "check": "#53BDEB", "tail": True, "radius": 20,
        "bar_bg": "#F0F2F5", "bar_field": "#FFFFFF", "bar_fg": "#8E9296", "bar_icon": "#8E9296",
        "status_fg": "#FFFFFF", "sub": "cuenta de empresa", "badge": "EMPRESA",
    },
    {
        "name": "whatsapp_android", "label": "WhatsApp (Android)", "os": "android",
        "wallpaper": _WP_WHATSAPP_CLARO, "screen_bg": "#EFE6DC",
        "head_bg": "#075E54", "head_fg": "#FFFFFF", "head_sub": "#CFE9E3", "head_icon": "#FFFFFF",
        "in_bg": "#FFFFFF", "in_fg": "#111B21", "out_bg": "#DCF8C6", "out_fg": "#111B21",
        "meta": "#667781", "check": "#4FC3F7", "tail": True, "radius": 18,
        "bar_bg": "#F0F2F5", "bar_field": "#FFFFFF", "bar_fg": "#8E9296", "bar_icon": "#8E9296",
        "status_fg": "#FFFFFF", "sub": "en línea",
    },
    {
        "name": "telegram", "label": "Telegram", "os": "ios",
        "wallpaper": _WP_TELEGRAM, "screen_bg": "#B9D4E6",
        "head_bg": "#517DA2", "head_fg": "#FFFFFF", "head_sub": "#D3E3EF", "head_icon": "#FFFFFF",
        "in_bg": "#FFFFFF", "in_fg": "#101010", "out_bg": "#EEFFDE", "out_fg": "#101010",
        "meta": "#7A9BB0", "check": "#4FAE4E", "tail": True, "radius": 22,
        "bar_bg": "#FFFFFF", "bar_field": "#FFFFFF", "bar_fg": "#9AA6AE", "bar_icon": "#9AA6AE",
        "status_fg": "#FFFFFF", "sub": "en línea",
    },
    {
        "name": "imessage", "label": "iMessage", "os": "ios",
        "wallpaper": _WP_LISO_CLARO, "screen_bg": "#FFFFFF",
        "head_bg": "rgba(249,249,249,.94)", "head_fg": "#000000", "head_sub": "#8A8A8E",
        "head_icon": "#007AFF",
        "in_bg": "#E9E9EB", "in_fg": "#000000",
        "out_bg": "linear-gradient(#1FA0FF,#007AFF)", "out_fg": "#FFFFFF",
        "meta": "#8A8A8E", "check": None, "entregado": "Entregado", "tail": True, "radius": 26,
        "bar_bg": "#F9F9F9", "bar_field": "#FFFFFF", "bar_fg": "#A9A9AE", "bar_icon": "#007AFF",
        "status_fg": "#000000", "sub": "iMessage", "head_centrado": True,
    },
    {
        "name": "instagram_dm", "label": "Instagram DM", "os": "ios",
        "wallpaper": _WP_LISO_CLARO, "screen_bg": "#FFFFFF",
        "head_bg": "#FFFFFF", "head_fg": "#0F0F0F", "head_sub": "#8E8E8E", "head_icon": "#0F0F0F",
        "in_bg": "#EFEFEF", "in_fg": "#0F0F0F",
        "out_bg": "linear-gradient(120deg,#8A3AB9,#D6249F 55%,#F46F30)", "out_fg": "#FFFFFF",
        "meta": "#8E8E8E", "check": None, "entregado": "Visto", "tail": False, "radius": 30,
        "bar_bg": "#FFFFFF", "bar_field": "#F1F1F1", "bar_fg": "#8E8E8E", "bar_icon": "#0F0F0F",
        "status_fg": "#0F0F0F", "sub": "activo ahora",
    },
    {
        "name": "instagram_oscuro", "label": "Instagram DM (oscuro)", "os": "ios",
        "wallpaper": _WP_LISO_OSCURO, "screen_bg": "#000000",
        "head_bg": "#000000", "head_fg": "#FAFAFA", "head_sub": "#A8A8A8", "head_icon": "#FAFAFA",
        "in_bg": "#262626", "in_fg": "#FAFAFA",
        "out_bg": "linear-gradient(120deg,#8A3AB9,#D6249F 55%,#F46F30)", "out_fg": "#FFFFFF",
        "meta": "#A8A8A8", "check": None, "entregado": "Visto", "tail": False, "radius": 30,
        "bar_bg": "#000000", "bar_field": "#1C1C1E", "bar_fg": "#A8A8A8", "bar_icon": "#FAFAFA",
        "status_fg": "#FAFAFA", "sub": "activo ahora",
    },
    {
        "name": "messenger", "label": "Messenger", "os": "android",
        "wallpaper": _WP_LISO_CLARO, "screen_bg": "#FFFFFF",
        "head_bg": "#FFFFFF", "head_fg": "#050505", "head_sub": "#65676B", "head_icon": "#0084FF",
        "in_bg": "#F0F0F0", "in_fg": "#050505",
        "out_bg": "linear-gradient(#0099FF,#0078FF)", "out_fg": "#FFFFFF",
        "meta": "#65676B", "check": None, "entregado": "Entregado", "tail": False, "radius": 30,
        "bar_bg": "#FFFFFF", "bar_field": "#F0F2F5", "bar_fg": "#8A8D91", "bar_icon": "#0084FF",
        "status_fg": "#050505", "sub": "activo hace 2 min",
    },
    {
        "name": "sms_android", "label": "Mensajes (Android)", "os": "android",
        "wallpaper": _WP_MATERIAL, "screen_bg": "#F3F1F8",
        "head_bg": "#F3F1F8", "head_fg": "#1B1B1F", "head_sub": "#5F6368", "head_icon": "#1B1B1F",
        "in_bg": "#E8EAED", "in_fg": "#1B1B1F", "out_bg": "#1A73E8", "out_fg": "#FFFFFF",
        "meta": "#5F6368", "check": None, "entregado": "Entregado", "tail": False, "radius": 34,
        "bar_bg": "#F3F1F8", "bar_field": "#FFFFFF", "bar_fg": "#5F6368", "bar_icon": "#1A73E8",
        "status_fg": "#1B1B1F", "sub": "SMS",
    },
]

SKINS_CHAT_POR_NOMBRE = {s["name"]: s for s in SKINS_CHAT}


def pick_skin_chat() -> str:
    """Devuelve el NOMBRE de la variante, no el dict: es lo que se guarda en
    contenido.json y lo que después permite re-renderizar la misma pieza."""
    return random.choice(SKINS_CHAT)["name"]


def _es_oscura(skin: dict) -> bool:
    """Una skin es oscura si su pantalla lo es. Se mide sobre el color en vez
    de pedir un flag en cada diccionario: un flag que hay que acordarse de
    poner es un flag que alguna variante nueva va a tener mal."""
    hexa = skin["screen_bg"].lstrip("#")
    if len(hexa) != 6:
        return False
    r, g, b = (int(hexa[i:i + 2], 16) for i in (0, 2, 4))
    return (0.299 * r + 0.587 * g + 0.114 * b) < 128


def _skin_chat(nombre: str | None) -> dict:
    """Resuelve el nombre a su dict, completando los tokens derivables. Ante un
    nombre desconocido (una pieza vieja, o una variante que se sacó de la lista)
    cae a la primera en vez de explotar: el render no puede fallar por un tema
    estético.

    Los tokens que se pueden deducir del resto no se piden en la tabla de
    skins: repetirlos diez veces es diez oportunidades de que uno quede mal."""
    base = SKINS_CHAT_POR_NOMBRE.get(nombre or "", SKINS_CHAT[0])
    k = dict(base)
    oscura = _es_oscura(k)
    k.setdefault("fecha_bg", "rgba(255,255,255,.13)" if oscura else "rgba(0,0,0,.06)")
    k.setdefault("fecha_fg", k["meta"])
    # Color macizo para la cola de la burbuja saliente: las skins con burbuja
    # en gradiente no pueden usar 'out_bg' ahi (un border-color no acepta un
    # gradiente), asi que declaran el tono equivalente.
    k.setdefault("out_solid", k["out_bg"] if "gradient" not in k["out_bg"] else None)
    return k


# --- Cromo del sistema operativo ---------------------------------------------
def _status_bar(skin: dict, hora: str) -> str:
    """La barra de estado es el detalle que más barato compra realismo: sin
    ella el mockup es una tarjeta; con la hora, la señal y la batería, el ojo
    lo lee como una captura de pantalla."""
    c = skin["status_fg"]
    iconos = _icono(_SVG_SENAL, c) + _icono(_SVG_WIFI, c) + _icono(_SVG_BATERIA, c)
    isla = '<div class="isla"></div>' if skin["os"] == "ios" else ""
    return (f'<div class="statusbar"><span class="sb-hora">{html.escape(hora)}</span>'
            f'{isla}<span class="sb-icons">{iconos}</span></div>')


def _hora_de(quien_entra: str) -> str:
    """La hora del teléfono sale del propio contenido cuando la IA la puso en
    'quien_entra' ("Cliente · 23:40"): que el reloj de arriba diga una hora y
    el mensaje otra es exactamente el tipo de detalle que rompe la ilusión."""
    _, _, meta = quien_entra.partition("·")
    meta = meta.strip()
    if any(c.isdigit() for c in meta) and ":" in meta:
        return meta.split()[-1] if " " in meta else meta
    return "23:41"


def chat_html(s: dict, p: dict, nombre_skin: str | None = None) -> str:
    """Slide 'chat' como captura de teléfono. `p` es la paleta de la pieza: se
    usa solo para el titular y el pie (que viven sobre el papel de la marca),
    no para el teléfono, que tiene los colores reales de la app que imita."""
    k = _skin_chat(nombre_skin)
    nombre, _, meta = s["quien_entra"].partition("·")
    nombre = nombre.strip() or s["quien_entra"]
    hora_msg = meta.strip() or ""
    hora_status = _hora_de(s["quien_entra"])
    inicial = html.escape((nombre[:1] or "?").upper())

    sub = k.get("sub", "en línea")
    badge = (f'<span class="badge">{html.escape(k["badge"])}</span>') if k.get("badge") else ""
    centrado = " head-centro" if k.get("head_centrado") else ""

    # El acuse del mensaje saliente: doble tilde donde la app la tiene, y el
    # texto de estado ("Entregado", "Visto") donde no.
    if k.get("check"):
        acuse = f'<span class="acuse">{_icono(_SVG_CHECKS, k["check"])}</span>'
        estado = ""
    else:
        acuse = ""
        estado = f'<div class="estado">{html.escape(k.get("entregado", "Entregado"))}</div>'

    hora_in = f'<span class="hora">{html.escape(hora_msg)}</span>' if hora_msg else ""
    tail_in = '<span class="tail tail-in"></span>' if k["tail"] else ""
    tail_out = '<span class="tail tail-out"></span>' if k["tail"] and k["out_solid"] else ""

    pie = (f'<div class="mk-pie">{html.escape(s["pie"])}</div>') if s.get("pie") else ""

    return f"""<style>
.mk-wrap {{ display:flex; flex-direction:column; align-items:center; }}
.fono {{
  width:720px; border-radius:62px; padding:13px;
  background:linear-gradient(160deg,#2B2B2F,#101012 45%,#232327);
  box-shadow:0 46px 90px rgba(20,16,12,.30), 0 0 0 1px rgba(255,255,255,.06) inset;
}}
.pantalla {{
  border-radius:50px; overflow:hidden; background:{k['screen_bg']};
  display:flex; flex-direction:column; height:1010px;
}}
.statusbar {{
  display:flex; align-items:center; justify-content:space-between;
  padding:20px 44px 12px; background:{k['head_bg']}; position:relative;
}}
.sb-hora {{ font-size:26px; font-weight:650; color:{k['status_fg']}; letter-spacing:.2px; }}
.sb-icons {{ display:flex; align-items:center; gap:9px; }}
.isla {{
  position:absolute; left:50%; transform:translateX(-50%); top:14px;
  width:172px; height:44px; border-radius:24px; background:#000;
}}
.cabecera {{
  display:flex; align-items:center; gap:20px; padding:14px 34px 20px;
  background:{k['head_bg']}; border-bottom:1px solid rgba(0,0,0,.06);
}}
.cabecera.head-centro {{ justify-content:center; text-align:center; }}
.av {{
  width:74px; height:74px; border-radius:50%; flex:none;
  background:linear-gradient(150deg,{p['accent']},{p['ink']});
  color:#fff; font-size:34px; font-weight:700;
  display:flex; align-items:center; justify-content:center;
}}
.quien {{ font-size:33px; font-weight:680; color:{k['head_fg']}; line-height:1.15; }}
.sub {{ font-size:24px; color:{k['head_sub']}; margin-top:4px; }}
.badge {{
  display:inline-block; margin-left:12px; padding:3px 12px; border-radius:8px;
  background:rgba(255,255,255,.22); color:{k['head_fg']};
  font-size:17px; font-weight:700; letter-spacing:.8px; vertical-align:middle;
}}
.cuerpo {{
  flex:1; padding:30px 30px 36px;
  background-image:{k['wallpaper'][0]}; background-size:{k['wallpaper'][1]};
  display:flex; flex-direction:column; gap:22px; justify-content:flex-end;
}}
/* margin-bottom:auto empuja la fecha arriba y deja los mensajes abajo, que es
   como se ve un chat real: el hueco queda arriba, no entre las burbujas. */
.fecha {{ margin-bottom:auto; text-align:center; }}
.fecha span {{
  display:inline-block; padding:9px 24px; border-radius:16px;
  font-size:21px; letter-spacing:.6px; color:{k['fecha_fg']};
  background:{k['fecha_bg']};
}}
.msg {{ display:flex; }}
.msg.der {{ justify-content:flex-end; }}
.burbuja {{
  position:relative; max-width:78%; padding:24px 28px 30px;
  font-size:32px; line-height:1.36; border-radius:{k['radius']}px;
  box-shadow:0 2px 3px rgba(0,0,0,.10);
}}
.b-in {{ background:{k['in_bg']}; color:{k['in_fg']}; border-top-left-radius:8px; }}
.b-out {{ background:{k['out_bg']}; color:{k['out_fg']}; border-top-right-radius:8px; }}
.tail {{ position:absolute; top:0; width:0; height:0; }}
.tail-in {{
  left:-11px; border-top:14px solid {k['in_bg']};
  border-left:12px solid transparent;
}}
.tail-out {{
  right:-11px; border-top:14px solid {k['out_solid'] or 'transparent'};
  border-right:12px solid transparent;
}}
.hora, .acuse {{
  position:absolute; right:20px; bottom:8px;
  font-size:20px; color:{k['meta']}; display:flex; align-items:center; gap:5px;
}}
.b-out .hora {{ right:56px; }}
.estado {{ font-size:21px; color:{k['meta']}; text-align:right; margin-top:-12px; padding-right:8px; }}
.barra {{
  display:flex; align-items:center; gap:18px; padding:22px 30px 30px;
  background:{k['bar_bg']};
}}
.campo {{
  flex:1; background:{k['bar_field']}; border-radius:32px; padding:20px 28px;
  font-size:28px; color:{k['bar_fg']}; box-shadow:0 1px 2px rgba(0,0,0,.08);
}}
.mk-pie {{ margin-top:44px; font-size:31px; line-height:1.5; color:{p['dim']}; }}
</style>
<div class="mk-wrap">
<h2 style="font-size:58px; align-self:flex-start; margin-bottom:44px">{html.escape(s['titular'])}</h2>
<div class="fono"><div class="pantalla">
{_status_bar(k, hora_status)}
<div class="cabecera{centrado}">
  {'' if k.get('head_centrado') else _icono(_SVG_CHEVRON, k['head_icon'])}
  <div class="av">{inicial}</div>
  <div><div class="quien">{html.escape(nombre)}{badge}</div>
  <div class="sub">{html.escape(sub)}</div></div>
</div>
<div class="cuerpo">
  <div class="fecha"><span>HOY</span></div>
  <div class="msg"><div class="burbuja b-in">{tail_in}{html.escape(s['entrada'])}{hora_in}</div></div>
  <div class="msg der"><div class="burbuja b-out">{tail_out}{html.escape(s['respuesta'])}{acuse}</div></div>
  {estado}
</div>
<div class="barra">
  <div class="campo">Escribí un mensaje</div>
  {_icono(_SVG_MIC, k['bar_icon'])}
  {_icono(_SVG_ENVIAR, k['bar_icon'])}
</div>
</div></div>
{pie}
</div>"""


# --- Skins de web -------------------------------------------------------------
# Tres ejes que se combinan, en vez de diez layouts escritos a mano:
#   cromo   -> safari / chrome / mobile (el sitio dentro de un teléfono) / limpio
#   tema    -> claro u oscuro
#   layout  -> hero (titular grande), split (texto + tarjeta) o panel (dashboard)
# El widget del agente IA flota abajo a la derecha en todas: es el punto de la
# slide; lo que cambia alrededor es el sitio donde está instalado.
SKINS_WEB = [
    {"name": "safari_hero", "label": "Safari · landing", "cromo": "safari",
     "tema": "claro", "layout": "hero"},
    {"name": "safari_split", "label": "Safari · split", "cromo": "safari",
     "tema": "claro", "layout": "split"},
    {"name": "chrome_hero", "label": "Chrome · landing", "cromo": "chrome",
     "tema": "claro", "layout": "hero"},
    {"name": "chrome_panel", "label": "Chrome · panel", "cromo": "chrome",
     "tema": "claro", "layout": "panel"},
    {"name": "chrome_oscuro_hero", "label": "Chrome oscuro · landing", "cromo": "chrome",
     "tema": "oscuro", "layout": "hero"},
    {"name": "safari_oscuro_panel", "label": "Safari oscuro · panel", "cromo": "safari",
     "tema": "oscuro", "layout": "panel"},
    {"name": "mobile_hero", "label": "Sitio en el celular", "cromo": "mobile",
     "tema": "claro", "layout": "hero"},
    {"name": "mobile_oscuro", "label": "Sitio en el celular (oscuro)", "cromo": "mobile",
     "tema": "oscuro", "layout": "hero"},
    {"name": "limpio_split", "label": "Captura limpia · split", "cromo": "limpio",
     "tema": "claro", "layout": "split"},
    {"name": "limpio_panel", "label": "Captura limpia · panel", "cromo": "limpio",
     "tema": "oscuro", "layout": "panel"},
]

SKINS_WEB_POR_NOMBRE = {s["name"]: s for s in SKINS_WEB}

# Los dos temas del sitio. El acento no vive acá: sale de la paleta de la pieza,
# para que el sitio del caso se sienta parte de ESA pieza y no de un template.
_TEMA_WEB = {
    "claro": {"bg": "#FFFFFF", "bg2": "#F6F7F9", "fg": "#0E1116", "dim": "#5B6470",
              "line": "#E6E9ED", "card": "#FFFFFF", "sombra": "rgba(16,20,26,.10)"},
    "oscuro": {"bg": "#0E1116", "bg2": "#161A21", "fg": "#F2F4F7", "dim": "#98A2B3",
               "line": "#232833", "card": "#171C24", "sombra": "rgba(0,0,0,.45)"},
}

_SVG_CANDADO = ('<svg viewBox="0 0 14 16" width="20" height="22" fill="{c}">'
                '<path d="M7 .8a3.6 3.6 0 0 0-3.6 3.6V6H3a1.4 1.4 0 0 0-1.4 1.4v6.2A1.4 1.4 0 0 0 3 15h8a1.4 '
                '1.4 0 0 0 1.4-1.4V7.4A1.4 1.4 0 0 0 11 6h-.4V4.4A3.6 3.6 0 0 0 7 .8zm0 1.8a1.8 1.8 0 0 1 '
                '1.8 1.8V6H5.2V4.4A1.8 1.8 0 0 1 7 2.6z"/></svg>')
_SVG_RECARGAR = ('<svg viewBox="0 0 16 16" width="22" height="22" fill="none" stroke="{c}" '
                 'stroke-width="1.7" stroke-linecap="round">'
                 '<path d="M13.5 8a5.5 5.5 0 1 1-1.7-4"/><path d="M12.2 1.2V4h-2.8"/></svg>')


def pick_skin_web() -> str:
    return random.choice(SKINS_WEB)["name"]


def _skin_web(nombre: str | None) -> dict:
    base = SKINS_WEB_POR_NOMBRE.get(nombre or "", SKINS_WEB[0])
    k = dict(base)
    k["t"] = _TEMA_WEB[k["tema"]]
    return k


def _cromo_web(k: dict, url: str, titulo: str) -> str:
    """La barra del navegador. Es lo que convierte un rectángulo blanco en "una
    web": sin semáforo, sin campo de URL con candado y sin pestaña, el ojo lo
    lee como una tarjeta cualquiera."""
    t = k["t"]
    if k["cromo"] == "limpio":
        return ""
    if k["cromo"] == "mobile":
        barra = _status_bar({"os": "ios", "status_fg": t["fg"], "head_bg": t["bg2"]}, "9:41")
        return (barra + f'<div class="wb-mobilebar">'
                f'<span class="wb-lock">{_icono(_SVG_CANDADO, t["dim"])}</span>'
                f'<span class="wb-url-m">{html.escape(url)}</span></div>')
    puntos = ('<span class="wb-dot" style="background:#FF5F57"></span>'
              '<span class="wb-dot" style="background:#FEBC2E"></span>'
              '<span class="wb-dot" style="background:#28C840"></span>')
    if k["cromo"] == "safari":
        return (f'<div class="wb-bar">{puntos}'
                f'<span class="wb-url"><span class="wb-lock">{_icono(_SVG_CANDADO, t["dim"])}</span>'
                f'{html.escape(url)}</span>'
                f'<span class="wb-acc">{_icono(_SVG_RECARGAR, t["dim"])}</span></div>')
    # chrome: pestaña con favicon y título arriba de la barra de direcciones
    return (f'<div class="wb-tabs">{puntos}'
            f'<span class="wb-tab"><span class="wb-fav"></span>{html.escape(titulo)}</span></div>'
            f'<div class="wb-bar wb-bar-chrome">'
            f'<span class="wb-acc">{_icono(_SVG_RECARGAR, t["dim"])}</span>'
            f'<span class="wb-url"><span class="wb-lock">{_icono(_SVG_CANDADO, t["dim"])}</span>'
            f'{html.escape(url)}</span></div>')


def _nav_web(k: dict, marca: str) -> str:
    inicial = html.escape((marca[:1] or "R").upper())
    links = "".join(f"<span>{x}</span>" for x in ("Inicio", "Servicios", "Contacto"))
    return (f'<div class="wb-nav"><span class="wb-marca"><span class="wb-logo">{inicial}</span>'
            f'{html.escape(marca)}</span><span class="wb-links">{links}</span></div>')


def _cuerpo_web(k: dict, s: dict, p: dict) -> str:
    """Los tres layouts de página. Comparten los mismos campos que ya escribe la
    IA (headline, bajada, chips, boton): lo que cambia es cómo se acomodan, no
    que haya que pedirle contenido nuevo al modelo."""
    chips = s.get("chips", []) or []
    headline = html.escape(s["headline"])
    bajada = html.escape(s["bajada"])
    boton = html.escape(s["boton"])

    if k["layout"] == "panel":
        # Dashboard: solo los chips que EMPIEZAN con un número pasan a tarjeta
        # de métrica. Partir cualquier chip por su primera palabra daba cosas
        # como un "Sin" gigante en serif arriba de "llamados": el resto va como
        # fila de estado, que es donde de verdad vive un texto así en un panel.
        # Cada chip aparece una sola vez, arriba o abajo, nunca en los dos.
        numericos = [c for c in chips if c.split() and c.split()[0][0].isdigit()]
        textuales = [c for c in chips if c not in numericos]
        tarjetas = "".join(
            f'<div class="wb-metrica"><div class="wb-metrica-n">{html.escape(c.split()[0])}</div>'
            f'<div class="wb-metrica-t">{html.escape(" ".join(c.split()[1:]) or "total")}</div></div>'
            for c in numericos[:3]
        )
        tarjetas = f'<div class="wb-metricas">{tarjetas}</div>' if tarjetas else ""
        filas = "".join(
            f'<div class="wb-fila"><span class="wb-punto"></span><span>{html.escape(c)}</span>'
            f'<span class="wb-ok">activo</span></div>' for c in textuales[:3]
        )
        filas = f'<div class="wb-lista">{filas}</div>' if filas else ""
        return (f'<div class="wb-panel"><div class="wb-side">'
                f'<span class="wb-side-i wb-side-on"></span><span class="wb-side-i"></span>'
                f'<span class="wb-side-i"></span><span class="wb-side-i"></span></div>'
                f'<div class="wb-main"><div class="wb-h2">{headline}</div>'
                f'<div class="wb-sub">{bajada}</div>{tarjetas}{filas}</div></div>')

    if k["layout"] == "split":
        filas = "".join(
            f'<div class="wb-fila"><span class="wb-punto"></span><span>{html.escape(c)}</span></div>'
            for c in chips[:3]
        )
        return (f'<div class="wb-split"><div><div class="wb-h1">{headline}</div>'
                f'<div class="wb-sub">{bajada}</div>'
                f'<div class="wb-btn">{boton}</div></div>'
                f'<div class="wb-card"><div class="wb-card-t">Disponibilidad</div>'
                f'{filas}</div></div>')

    chips_html = "".join(f'<span class="wb-chip">{html.escape(c)}</span>' for c in chips)
    return (f'<div class="wb-hero"><div class="wb-h1">{headline}</div>'
            f'<div class="wb-sub">{bajada}</div>'
            f'<div class="wb-chips">{chips_html}</div>'
            f'<div class="wb-btn">{boton}</div></div>')


def web_html(s: dict, p: dict, nombre_skin: str | None = None) -> str:
    """Slide 'web': el sitio del negocio con el agente IA instalado, dentro del
    navegador (o del teléfono) de verdad. Diez variantes, ver SKINS_WEB."""
    k = _skin_web(nombre_skin)
    t = k["t"]
    marca = (s["url"].split(".")[0] or "sitio").replace("-", " ").title()
    movil = k["cromo"] == "mobile"

    marco_ini = '<div class="fono fono-web"><div class="pantalla-web">' if movil else '<div class="wb">'
    marco_fin = "</div></div>" if movil else "</div>"
    ancho = "720px" if movil else "780px"
    h1 = "50px" if movil else "58px"
    pie = f'<div class="mk-pie">{html.escape(s["pie"])}</div>' if s.get("pie") else ""

    return f"""<style>
.mk-wrap {{ display:flex; flex-direction:column; align-items:center; }}
.wb, .fono-web {{ width:{ancho}; }}
.wb {{
  border-radius:26px; overflow:hidden; background:{t['bg']};
  box-shadow:0 40px 80px {t['sombra']}, 0 0 0 1px {t['line']};
}}
.fono-web {{
  border-radius:62px; padding:13px;
  background:linear-gradient(160deg,#2B2B2F,#101012 45%,#232327);
  box-shadow:0 46px 90px rgba(20,16,12,.30);
}}
.pantalla-web {{ border-radius:50px; overflow:hidden; background:{t['bg']}; }}
.wb-tabs {{
  display:flex; align-items:center; gap:14px; padding:16px 24px 0;
  background:{t['bg2']};
}}
.wb-tab {{
  display:flex; align-items:center; gap:10px; margin-left:10px;
  background:{t['bg']}; color:{t['dim']}; font-size:20px;
  padding:14px 26px; border-radius:12px 12px 0 0; max-width:420px;
  overflow:hidden; white-space:nowrap; text-overflow:ellipsis;
}}
.wb-fav {{ width:18px; height:18px; border-radius:4px; background:{p['accent']}; flex:none; }}
.wb-bar {{
  display:flex; align-items:center; gap:14px; padding:18px 26px;
  background:{t['bg2']}; border-bottom:1px solid {t['line']};
}}
.wb-bar-chrome {{ padding-top:12px; }}
.wb-dot {{ width:15px; height:15px; border-radius:50%; display:inline-block; }}
.wb-url {{
  flex:1; display:flex; align-items:center; gap:10px; justify-content:center;
  background:{t['bg']}; border-radius:20px; padding:13px 26px;
  font-size:23px; color:{t['dim']};
}}
.wb-lock {{ display:flex; align-items:center; }}
.wb-acc {{ display:flex; align-items:center; opacity:.75; }}
.wb-mobilebar {{
  display:flex; align-items:center; justify-content:center; gap:10px;
  padding:26px 30px 16px; background:{t['bg2']}; color:{t['dim']};
}}
.wb-url-m {{ font-size:24px; }}
.wb-nav {{
  display:flex; align-items:center; justify-content:space-between;
  padding:26px 40px; border-bottom:1px solid {t['line']}; background:{t['bg']};
}}
.wb-marca {{ display:flex; align-items:center; gap:14px; font-size:25px; font-weight:680; color:{t['fg']}; }}
.wb-logo {{
  width:40px; height:40px; border-radius:11px; background:{p['accent']}; color:#fff;
  font-size:22px; font-weight:700; display:flex; align-items:center; justify-content:center;
}}
.wb-links {{ display:flex; gap:30px; font-size:21px; color:{t['dim']}; }}
.wb-hero {{ padding:56px 48px 270px; background:{t['bg']}; }}
.wb-h1 {{
  font-family:'Display',serif; font-weight:800; font-size:{h1};
  line-height:1.1; color:{t['fg']}; letter-spacing:-.5px;
}}
.wb-h2 {{ font-size:34px; font-weight:700; color:{t['fg']}; }}
.wb-sub {{ margin-top:22px; font-size:27px; line-height:1.5; color:{t['dim']}; }}
.wb-chips {{ display:flex; flex-wrap:wrap; gap:14px; margin-top:34px; }}
.wb-chip {{
  padding:14px 26px; border-radius:999px; font-size:22px;
  color:{t['fg']}; background:{t['bg2']}; border:1px solid {t['line']};
}}
.wb-btn {{
  display:inline-block; margin-top:38px; padding:22px 44px; border-radius:14px;
  background:{p['accent']}; color:#fff; font-size:25px; font-weight:700;
  box-shadow:0 14px 26px {t['sombra']};
}}
.wb-split {{
  display:grid; grid-template-columns:1.05fr .95fr; gap:38px;
  padding:52px 48px 250px; background:{t['bg']}; align-items:start;
}}
.wb-card {{
  background:{t['card']}; border:1px solid {t['line']}; border-radius:20px;
  padding:30px 28px; box-shadow:0 18px 34px {t['sombra']};
}}
.wb-card-t {{ font-size:21px; letter-spacing:1px; text-transform:uppercase; color:{t['dim']}; margin-bottom:20px; }}
.wb-fila {{
  display:flex; align-items:center; gap:14px; padding:16px 0;
  border-top:1px solid {t['line']}; font-size:23px; color:{t['fg']};
}}
.wb-punto {{ width:11px; height:11px; border-radius:50%; background:{p['accent']}; flex:none; }}
.wb-ok {{ margin-left:auto; font-size:19px; color:#12A150; }}
.wb-panel {{ display:flex; background:{t['bg2']}; min-height:520px; }}
.wb-side {{
  width:92px; padding:34px 0; background:{t['card']}; border-right:1px solid {t['line']};
  display:flex; flex-direction:column; align-items:center; gap:26px;
}}
.wb-side-i {{ width:40px; height:40px; border-radius:12px; background:{t['line']}; }}
.wb-side-on {{ background:{p['accent']}; }}
.wb-main {{ flex:1; padding:38px 40px 260px; }}
.wb-metricas {{ display:flex; gap:18px; margin-top:30px; }}
.wb-metrica {{
  flex:1; background:{t['card']}; border:1px solid {t['line']}; border-radius:16px; padding:24px 22px;
}}
.wb-metrica-n {{ font-family:'Display',serif; font-size:44px; font-weight:800; color:{p['accent']}; }}
.wb-metrica-t {{ font-size:19px; color:{t['dim']}; margin-top:6px; }}
.wb-lista {{
  margin-top:30px; background:{t['card']}; border:1px solid {t['line']};
  border-radius:16px; padding:6px 24px 14px;
}}
.wb-lista .wb-fila:first-child {{ border-top:0; }}
/* El widget del agente: es el punto de la slide, así que va con sombra fuerte
   para que se despegue del sitio y se lea primero. */
.wb-rel {{ position:relative; }}
.wgt {{
  position:absolute; right:26px; bottom:26px; width:330px;
  border-radius:20px; overflow:hidden; background:{t['card']};
  box-shadow:0 26px 50px rgba(0,0,0,.28);
}}
.wgt-h {{
  display:flex; align-items:center; gap:12px; padding:18px 20px;
  background:{p['accent']}; color:#fff;
}}
.wgt-dot {{
  width:12px; height:12px; border-radius:50%; background:#37D67A; flex:none;
  box-shadow:0 0 0 4px rgba(55,214,122,.25);
}}
.wgt-t {{ font-size:21px; font-weight:700; }}
.wgt-s {{ font-size:16px; opacity:.9; margin-top:2px; }}
.wgt-b {{ padding:20px; font-size:19px; line-height:1.45; color:{t['dim']}; }}
.wgt-burb {{
  margin-top:14px; background:{t['bg2']}; border-radius:14px 14px 14px 4px;
  padding:16px 18px; color:{t['fg']};
}}
.mk-pie {{ margin-top:44px; font-size:31px; line-height:1.5; color:{p['dim']}; }}
</style>
<div class="mk-wrap">
<h2 style="font-size:56px; align-self:flex-start; margin-bottom:44px">{html.escape(s['titular'])}</h2>
{marco_ini}
<div class="wb-rel">
{_cromo_web(k, s['url'], marca)}
{_nav_web(k, marca)}
{_cuerpo_web(k, s, p)}
<div class="wgt">
  <div class="wgt-h"><span class="wgt-dot"></span>
    <div><div class="wgt-t">Agente IA</div><div class="wgt-s">En línea ahora</div></div></div>
  <div class="wgt-b">Hola&#128075; ¿en qué te puedo ayudar?
    <div class="wgt-burb">Escribime tu consulta y te respondo al toque.</div></div>
</div>
</div>
{marco_fin}
{pie}
</div>"""


# --- Skins de flujo -----------------------------------------------------------
# Tres familias con una idea distinta de qué es un flujo, no diez recoloreadas:
#   nodos    -> tarjetas conectadas por línea, como se ve un flujo en n8n/Zapier
#   timeline -> línea vertical con nodos numerados, más editorial
#   consola  -> el log de la ejecución, terminal
# Cada una en claro y oscuro, y con la marca (número, tilde o punto) variando:
# es lo que hace que dos piezas con el mismo ángulo no rindan la misma lámina.
SKINS_FLUJO = [
    {"name": "nodos_claro", "label": "Nodos (claro)", "familia": "nodos",
     "tema": "claro", "marca": "numero"},
    {"name": "nodos_oscuro", "label": "Nodos (oscuro)", "familia": "nodos",
     "tema": "oscuro", "marca": "numero"},
    {"name": "nodos_check", "label": "Nodos con tilde", "familia": "nodos",
     "tema": "claro", "marca": "check"},
    {"name": "timeline_claro", "label": "Timeline (claro)", "familia": "timeline",
     "tema": "claro", "marca": "numero"},
    {"name": "timeline_oscuro", "label": "Timeline (oscuro)", "familia": "timeline",
     "tema": "oscuro", "marca": "numero"},
    {"name": "timeline_check", "label": "Timeline con tilde", "familia": "timeline",
     "tema": "claro", "marca": "check"},
    {"name": "timeline_punto", "label": "Timeline al hilo", "familia": "timeline",
     "tema": "claro", "marca": "punto"},
    {"name": "consola", "label": "Consola", "familia": "consola",
     "tema": "oscuro", "marca": "check"},
    {"name": "consola_clara", "label": "Consola clara", "familia": "consola",
     "tema": "claro", "marca": "check"},
    {"name": "nodos_oscuro_check", "label": "Nodos oscuros con tilde", "familia": "nodos",
     "tema": "oscuro", "marca": "check"},
]

SKINS_FLUJO_POR_NOMBRE = {s["name"]: s for s in SKINS_FLUJO}

_TEMA_FLUJO = {
    "claro": {"bg": "#FFFFFF", "bg2": "#F5F6F8", "fg": "#111418", "dim": "#616B78",
              "line": "#E3E7EC", "sombra": "rgba(16,20,26,.10)"},
    "oscuro": {"bg": "#12161C", "bg2": "#1A2029", "fg": "#EEF1F5", "dim": "#95A0AE",
               "line": "#262E39", "sombra": "rgba(0,0,0,.42)"},
}

_SVG_TILDE = ('<svg viewBox="0 0 16 12" width="26" height="20" fill="none" stroke="{c}" '
              'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">'
              '<path d="M1.6 6.4 5.8 10.4 14.4 1.6"/></svg>')


def pick_skin_flujo() -> str:
    return random.choice(SKINS_FLUJO)["name"]


def _skin_flujo(nombre: str | None) -> dict:
    base = SKINS_FLUJO_POR_NOMBRE.get(nombre or "", SKINS_FLUJO[0])
    k = dict(base)
    k["t"] = _TEMA_FLUJO[k["tema"]]
    return k


def _marca_flujo(k: dict, i: int, color_fg: str) -> str:
    """El disco que encabeza cada paso: número, tilde o punto según la skin."""
    if k["marca"] == "check":
        return _icono(_SVG_TILDE, color_fg)
    if k["marca"] == "punto":
        return '<span class="fl-punto"></span>'
    return str(i)


def flujo_html(s: dict, p: dict, nombre_skin: str | None = None) -> str:
    """Slide 'flujo': los pasos que corre la automatización. Antes era una lista
    con filetes —correcta y absolutamente igual en todas las piezas—; ahora son
    diez variantes en tres familias (ver SKINS_FLUJO), que además leen como
    software funcionando y no como una enumeración de folleto."""
    k = _skin_flujo(nombre_skin)
    t = k["t"]
    pasos = [x for x in (s.get("pasos") or []) if x]

    if k["familia"] == "consola":
        # El prompt de la consola usa el rubro del propio flujo, no un
        # "user@host" inventado: es un detalle chico que evita que se lea a
        # plantilla.
        filas = "".join(
            f'<div class="fl-log"><span class="fl-hora">23:40:{(i - 1) * 3 + 2:02d}</span>'
            f'<span class="fl-flecha">&rsaquo;</span><span class="fl-txt">{html.escape(x)}</span>'
            f'<span class="fl-ok">OK</span></div>'
            for i, x in enumerate(pasos, 1)
        )
        cuerpo = (f'<div class="fl-consola"><div class="fl-cbar">'
                  f'<span class="fl-cdot" style="background:#FF5F57"></span>'
                  f'<span class="fl-cdot" style="background:#FEBC2E"></span>'
                  f'<span class="fl-cdot" style="background:#28C840"></span>'
                  f'<span class="fl-ctitulo">agente · ejecución</span></div>'
                  f'<div class="fl-cbody">{filas}'
                  f'<div class="fl-cursor">_</div></div></div>')
    elif k["familia"] == "nodos":
        cuerpo = "".join(
            f'<div class="fl-nodo"><span class="fl-marca">{_marca_flujo(k, i, "#fff")}</span>'
            f'<span class="fl-txt">{html.escape(x)}</span></div>'
            + ('<div class="fl-cable"></div>' if i < len(pasos) else "")
            for i, x in enumerate(pasos, 1)
        )
        cuerpo = f'<div class="fl-nodos">{cuerpo}</div>'
    else:
        cuerpo = "".join(
            f'<div class="fl-hito"><span class="fl-marca">{_marca_flujo(k, i, "#fff")}</span>'
            f'<span class="fl-txt">{html.escape(x)}</span></div>'
            for i, x in enumerate(pasos, 1)
        )
        cuerpo = f'<div class="fl-timeline">{cuerpo}</div>'

    # La consola ya trae su propio marco: envolverla ademas en .fl-caja deja
    # una caja adentro de otra. Las otras dos familias si necesitan la lamina.
    caja = "fl-caja fl-caja-plana" if k["familia"] == "consola" else "fl-caja"

    return f"""<style>
.fl-caja {{
  margin-top:56px; border-radius:26px; padding:46px 44px;
  background:{t['bg']}; box-shadow:0 34px 70px {t['sombra']}, 0 0 0 1px {t['line']};
}}
.fl-caja-plana {{ padding:0; background:transparent; box-shadow:0 34px 70px {t['sombra']}; }}
.fl-txt {{ font-size:36px; line-height:1.34; color:{t['fg']}; }}
.fl-marca {{
  width:66px; height:66px; border-radius:20px; flex:none;
  background:{p['accent']}; color:#fff;
  font-size:30px; font-weight:750;
  display:flex; align-items:center; justify-content:center;
}}
.fl-punto {{ width:16px; height:16px; border-radius:50%; background:#fff; display:block; }}
/* Nodos: tarjeta + cable, como un flujo de automatización de verdad. */
.fl-nodos {{ display:flex; flex-direction:column; align-items:stretch; }}
.fl-nodo {{
  display:flex; align-items:center; gap:26px;
  background:{t['bg2']}; border:1px solid {t['line']}; border-radius:20px;
  padding:26px 30px;
}}
.fl-cable {{
  width:4px; height:34px; margin:0 auto; border-radius:2px;
  background:linear-gradient(180deg,{p['accent']},{t['line']});
}}
/* Timeline: un solo hilo vertical que atraviesa todos los hitos. */
.fl-timeline {{ position:relative; padding-left:12px; }}
.fl-timeline::before {{
  content:""; position:absolute; left:45px; top:34px; bottom:34px;
  width:3px; background:{t['line']};
}}
.fl-hito {{
  position:relative; display:flex; align-items:center; gap:30px;
  padding:22px 0;
}}
.fl-hito .fl-marca {{ border-radius:50%; box-shadow:0 0 0 10px {t['bg']}; z-index:1; }}
/* Consola: el log de la corrida. */
.fl-consola {{
  border-radius:20px; overflow:hidden; background:{t['bg2']};
  border:1px solid {t['line']};
}}
.fl-cbar {{
  display:flex; align-items:center; gap:12px; padding:20px 24px;
  background:{t['line']};
}}
.fl-cdot {{ width:14px; height:14px; border-radius:50%; }}
.fl-ctitulo {{ margin-left:14px; font-size:21px; color:{t['dim']}; letter-spacing:.4px; }}
.fl-cbody {{ padding:28px 26px 30px; }}
.fl-log {{ display:flex; align-items:baseline; gap:16px; padding:13px 0; }}
.fl-log .fl-txt {{ font-size:30px; flex:1; }}
.fl-hora {{ font-size:24px; color:{t['dim']}; font-variant-numeric:tabular-nums; }}
.fl-flecha {{ font-size:28px; color:{p['accent']}; font-weight:700; }}
.fl-ok {{
  font-size:19px; letter-spacing:1px; color:#12A150;
  border:1px solid rgba(18,161,80,.35); border-radius:8px; padding:4px 11px;
}}
.fl-cursor {{ font-size:30px; color:{p['accent']}; margin-top:10px; }}
</style>
<div>
<h2 style="font-size:62px">{html.escape(s['titular'])}</h2>
<div class="{caja}">{cuerpo}</div>
</div>"""


def pick_skins() -> dict:
    """Las variantes de UNA pieza, una por tipo de mockup. Se sortean juntas y
    de una sola vez (generate.py las guarda en contenido.json) por dos razones:
    que las dos slides de chat de un mismo carrusel no muestren dos telefonos
    distintos, y que despues se pueda saber que combinacion genero la pieza que
    mejor rindio."""
    return {"chat": pick_skin_chat(), "web": pick_skin_web(), "flujo": pick_skin_flujo()}
