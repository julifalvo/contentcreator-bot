"""Configuración central: pilares de contenido, marca visual y textos fijos."""

# Plantillas de orden narrativo. Cada una es una lista de bloques que se arman
# con el MISMO contenido generado (mismos 4 slides, demo, 2 mockups, cta) pero
# en distinto orden/selección, para que la estructura del video no sea
# siempre "problema -> costo -> solución -> resultado -> demo -> mockups -> cta".
#
# Tokens válidos: "portada", "slide:0".."slide:3", "demo", "mockup:0"/"mockup:1",
# "foto" (slide 100% foto, sin texto ni título — solo respiro visual), "cta".
NARRATIVE_TEMPLATES = [
    # Clásico: como era antes, todo en orden.
    ["portada", "slide:0", "slide:1", "slide:2", "slide:3", "demo", "mockup:0", "mockup:1", "cta"],
    # Gancho de resultado: muestra el resultado primero, después explica cómo se llegó.
    ["portada", "slide:3", "demo", "slide:0", "slide:1", "slide:2", "mockup:0", "cta"],
    # El demo primero, antes de dar contexto.
    ["portada", "demo", "slide:0", "slide:1", "slide:2", "slide:3", "mockup:0", "mockup:1", "cta"],
    # Arranca mostrando la solución visual, versión más corta y directa.
    ["portada", "mockup:0", "slide:1", "slide:3", "demo", "mockup:1", "cta"],
    # Pregunta directa: problema -> demo -> solución -> resultado, se salta el costo.
    ["portada", "slide:0", "demo", "slide:2", "slide:3", "mockup:1", "cta"],
    # Con una foto de respiro después de plantear el problema.
    ["portada", "slide:0", "slide:1", "foto", "slide:2", "slide:3", "demo", "mockup:0", "cta"],
    # Foto de apertura como ambientación, antes de arrancar con el problema.
    ["portada", "foto", "slide:0", "slide:1", "demo", "slide:3", "mockup:1", "cta"],
]

# Pilares temáticos del perfil (negocios en automático / agentes AI / chatbots)
PILLARS = {
    "automatizacion": {
        "label": "Automatización",
        "emoji": "⚙️",
        "angle": (
            "Cómo un negocio puede dejar de hacer tareas repetitivas a mano "
            "gracias a la automatización con IA y flujos automáticos."
        ),
    },
    "eficiencia_comercial": {
        "label": "Eficiencia Comercial",
        "emoji": "📈",
        "angle": (
            "Cómo un chatbot o agente de IA ayuda a vender más rápido, "
            "responder leads al instante y cerrar más ventas."
        ),
    },
    "optimizacion_operativa": {
        "label": "Optimización Operativa",
        "emoji": "🛠️",
        "angle": (
            "Cómo optimizar procesos internos (soporte, agenda, cobros, "
            "inventario) usando agentes de IA para ahorrar tiempo y errores."
        ),
    },
    "transformacion": {
        "label": "Transformación Digital",
        "emoji": "🚀",
        "angle": (
            "Cómo un negocio tradicional se transforma al adoptar IA y "
            "automatización, y por qué quedarse atrás es un riesgo real."
        ),
    },
}

# Paletas de marca — todas estilo tech/oscuro, alto contraste, aptas para TikTok.
# Cada pieza generada sortea una al azar (ver generate.py) para que el look
# visual también varíe, no solo el texto. La primera es la paleta original.
PALETTES = [
    {  # Cian / Violeta
        "bg_top": (10, 14, 26),
        "bg_bottom": (24, 20, 60),
        "accent": (0, 224, 255),
        "accent_2": (255, 184, 0),
        "text": (245, 246, 250),
        "text_dim": (170, 176, 195),
        "badge_bg": (255, 255, 255),
    },
    {  # Verde Neón
        "bg_top": (8, 20, 18),
        "bg_bottom": (14, 42, 36),
        "accent": (60, 240, 150),
        "accent_2": (255, 214, 64),
        "text": (240, 250, 246),
        "text_dim": (170, 196, 188),
        "badge_bg": (255, 255, 255),
    },
    {  # Rosa Neón
        "bg_top": (20, 10, 24),
        "bg_bottom": (48, 16, 56),
        "accent": (255, 90, 190),
        "accent_2": (255, 196, 60),
        "text": (250, 245, 250),
        "text_dim": (200, 176, 202),
        "badge_bg": (255, 255, 255),
    },
    {  # Azul Eléctrico
        "bg_top": (8, 14, 28),
        "bg_bottom": (18, 30, 62),
        "accent": (70, 150, 255),
        "accent_2": (255, 200, 90),
        "text": (244, 248, 255),
        "text_dim": (170, 186, 214),
        "badge_bg": (255, 255, 255),
    },
    {  # Coral / Carbón
        "bg_top": (22, 10, 12),
        "bg_bottom": (48, 18, 20),
        "accent": (255, 99, 90),
        "accent_2": (255, 204, 70),
        "text": (250, 244, 244),
        "text_dim": (208, 178, 176),
        "badge_bg": (255, 255, 255),
    },
]

BRAND = dict(PALETTES[0])

# Tamaño de lienzo formato TikTok (9:16)
CANVAS_SIZE = (1080, 1920)

# Combinaciones tipográficas — cada pieza sortea una (ver generate.py), para que
# la letra también cambie y no todo se vea con la misma fuente siempre.
# En Windows usa las fuentes del sistema; en Linux (ej. un server Ubuntu sin
# fuentes de Microsoft) usa equivalentes libres de Google Fonts / Ubuntu que
# se instalan con apt, sin licencias raras ni descargas manuales:
#   sudo apt install fonts-liberation fonts-noto-core fonts-dejavu-core \
#                     fonts-crosextra-carlito fonts-freefont-ttf
import platform

if platform.system() == "Windows":
    _FONTS_DIR = r"C:\Windows\Fonts"
    FONT_SETS = [
        {  # Arial — clásico corporativo, muy legible
            "black": f"{_FONTS_DIR}\\ariblk.ttf",
            "bold": f"{_FONTS_DIR}\\arialbd.ttf",
            "regular": f"{_FONTS_DIR}\\arial.ttf",
        },
        {  # Segoe UI — moderno, el original del proyecto
            "black": f"{_FONTS_DIR}\\seguibl.ttf",
            "bold": f"{_FONTS_DIR}\\segoeuib.ttf",
            "regular": f"{_FONTS_DIR}\\segoeui.ttf",
        },
        {  # Franklin Gothic Heavy — impacto tipo revista/editorial de negocios
            "black": f"{_FONTS_DIR}\\FRAHV.TTF",
            "bold": f"{_FONTS_DIR}\\FRAHV.TTF",
            "regular": f"{_FONTS_DIR}\\framd.ttf",
        },
        {  # Eras — geométrica, premium, look de marca tech/consultora
            "black": f"{_FONTS_DIR}\\ERASBD.TTF",
            "bold": f"{_FONTS_DIR}\\ERASDEMI.TTF",
            "regular": f"{_FONTS_DIR}\\ERASMD.TTF",
        },
        {  # Berlin Sans FB — redondeada, llamativa pero prolija, look de branding moderno
            "black": f"{_FONTS_DIR}\\BRLNSB.TTF",
            "bold": f"{_FONTS_DIR}\\BRLNSDB.TTF",
            "regular": f"{_FONTS_DIR}\\BRLNSR.TTF",
        },
        {  # Bahnschrift/Corbel — tech-corporativo, estilo dashboard SaaS
            "black": f"{_FONTS_DIR}\\bahnschrift.ttf",
            "bold": f"{_FONTS_DIR}\\corbelb.ttf",
            "regular": f"{_FONTS_DIR}\\corbel.ttf",
        },
    ]
else:
    FONT_SETS = [
        {  # Liberation Sans — clon métrico de Arial, clásico corporativo
            "black": "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "bold": "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "regular": "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        },
        {  # Noto Sans — moderno, neutro, gran cobertura de acentos
            "black": "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
            "bold": "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
            "regular": "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        },
        {  # DejaVu Sans Bold — impacto tipo revista/editorial
            "black": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "bold": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "regular": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        },
        {  # Carlito — clon métrico de Calibri, geométrica y prolija
            "black": "/usr/share/fonts/truetype/crosextra-carlito/Carlito-Bold.ttf",
            "bold": "/usr/share/fonts/truetype/crosextra-carlito/Carlito-Bold.ttf",
            "regular": "/usr/share/fonts/truetype/crosextra-carlito/Carlito-Regular.ttf",
        },
        {  # FreeSans — geométrica, look distinto para variedad
            "black": "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
            "bold": "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
            "regular": "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        },
    ]
FONTS = dict(FONT_SETS[1])

# Estilos de forma/layout — badge, indicador de progreso, acento decorativo de
# la portada, radio de esquina de tarjetas y patrón de fondo. Cada pieza
# sortea uno también.
STYLES = [
    {"name": "pill-dots", "corner_radius": 40, "badge_style": "pill", "accent_shape": "bar", "progress_style": "dots", "bg_pattern": "dots"},
    {"name": "sharp-tag", "corner_radius": 10, "badge_style": "tag", "accent_shape": "triangle", "progress_style": "bars", "bg_pattern": "grid"},
    {"name": "medium-frame", "corner_radius": 24, "badge_style": "tag", "accent_shape": "frame", "progress_style": "dots", "bg_pattern": "diagonal"},
    {"name": "round-cluster", "corner_radius": 36, "badge_style": "pill", "accent_shape": "dots-cluster", "progress_style": "bars", "bg_pattern": "blobs"},
    {"name": "clean-plain", "corner_radius": 24, "badge_style": "pill", "accent_shape": "bar", "progress_style": "dots", "bg_pattern": "plain"},
]
STYLE = dict(STYLES[0])

HANDLE = "@rootbusinessai"

HASHTAGS_BASE = [
    "automatizacion", "iaparanegocios", "chatbots", "agentesia",
    "emprendimiento", "negociosdigitales", "productividad", "tiktokbusiness",
]

CTAS = [
    "Seguime para más tips de automatización 🤖",
    "Comentá 'AUTO' y te cuento cómo empezar",
    "Guardá este video para no perdértelo",
    "¿Querés esto en tu negocio? Escribime",
    "Seguime si querés vender mientras dormís",
]
