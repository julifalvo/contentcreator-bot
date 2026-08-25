"""Configuración central: pilares de contenido, marca visual y textos fijos."""

# Plantillas de orden narrativo. Cada una es una lista de bloques que se arman
# con el MISMO contenido generado (mismos 4 slides, demo, 2 mockups, cta) pero
# en distinto orden/selección, para que la estructura del video no sea
# siempre "problema -> costo -> solución -> resultado -> demo -> mockups -> cta".
#
# Tokens válidos: "portada", "slide:0".."slide:3", "demo", "mockup:0"/"mockup:1",
# "foto" (slide 100% foto, sin texto ni título — solo respiro visual), "cta".
NARRATIVE_TEMPLATES = [
    # Clásico: todo en orden, con las dos soluciones visuales al final.
    ["portada", "slide:0", "slide:1", "slide:2", "slide:3", "demo", "mockup:0", "mockup:1", "cta"],
    # Gancho de resultado: muestra el resultado primero, después explica cómo se llegó.
    ["portada", "slide:3", "demo", "slide:0", "slide:1", "slide:2", "mockup:0", "cta"],
    # El demo primero, antes de dar contexto. Un solo mockup, separado del final.
    ["portada", "demo", "slide:0", "slide:1", "mockup:0", "slide:2", "slide:3", "cta"],
    # Arranca mostrando la solución visual, versión más corta y directa.
    ["portada", "mockup:0", "slide:1", "slide:3", "demo", "cta"],
    # Pregunta directa: problema -> demo -> solución -> resultado, se salta el costo.
    ["portada", "slide:0", "demo", "slide:2", "slide:3", "mockup:0", "cta"],
    # Con una foto de respiro después de plantear el problema. Sin mockups.
    ["portada", "slide:0", "slide:1", "foto", "slide:2", "slide:3", "demo", "cta"],
    # Foto de apertura como ambientación, antes de arrancar con el problema.
    ["portada", "foto", "slide:0", "slide:1", "demo", "slide:3", "mockup:0", "cta"],
    # Solo texto + demo: pieza corta y directa, sin ninguna solución visual.
    ["portada", "slide:0", "slide:1", "demo", "slide:3", "cta"],
    # Mockup intercalado entre el problema y el resultado, con foto de cierre.
    ["portada", "slide:0", "mockup:0", "demo", "slide:3", "foto", "cta"],
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

# Paletas de marca. Cada pieza sortea una al azar (ver generate.py) para que el
# look visual varíe, no solo el texto. El criterio es "smooth": degradés de poco
# recorrido (los dos tonos cercanos entre sí, sin saltos bruscos), acentos
# desaturados en vez de neón puro, y fondos claros mezclados con los oscuros.
PALETTES = [
    {  # Medianoche / Cian suave
        "bg_top": (16, 22, 38),
        "bg_bottom": (28, 36, 62),
        "accent": (96, 208, 224),
        "accent_2": (240, 196, 132),
        "text": (240, 244, 250),
        "text_dim": (168, 180, 200),
        "badge_bg": (255, 255, 255),
    },
    {  # Salvia / Verde apagado
        "bg_top": (20, 32, 30),
        "bg_bottom": (34, 52, 46),
        "accent": (134, 214, 174),
        "accent_2": (238, 206, 138),
        "text": (238, 246, 242),
        "text_dim": (168, 192, 182),
        "badge_bg": (255, 255, 255),
    },
    {  # Lavanda / Ciruela
        "bg_top": (30, 24, 42),
        "bg_bottom": (48, 38, 66),
        "accent": (188, 164, 236),
        "accent_2": (240, 186, 168),
        "text": (244, 240, 250),
        "text_dim": (190, 180, 208),
        "badge_bg": (255, 255, 255),
    },
    {  # Azul pizarra / Durazno
        "bg_top": (22, 30, 44),
        "bg_bottom": (36, 48, 68),
        "accent": (128, 176, 232),
        "accent_2": (242, 176, 148),
        "text": (240, 245, 252),
        "text_dim": (172, 188, 210),
        "badge_bg": (255, 255, 255),
    },
    {  # Arena clara (fondo claro, texto oscuro)
        "bg_top": (246, 242, 236),
        "bg_bottom": (232, 226, 218),
        "accent": (198, 122, 90),
        "accent_2": (122, 142, 128),
        "text": (42, 38, 34),
        "text_dim": (110, 102, 94),
        "badge_bg": (42, 38, 34),
    },
    {  # Niebla fría (fondo claro, texto oscuro)
        "bg_top": (240, 244, 248),
        "bg_bottom": (222, 230, 238),
        "accent": (68, 122, 156),
        "accent_2": (196, 138, 106),
        "text": (30, 40, 50),
        "text_dim": (100, 116, 132),
        "badge_bg": (30, 40, 50),
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
    "Escribime y te digo cuánto estás perdiendo",
    "Comentá 'AUTO' y te armo el primer flujo",
    "Guardalo antes de perder otro cliente",
    "¿Cuánto más vas a seguir haciéndolo a mano?",
    "Seguime si no querés seguir perdiendo mensajes",
    "Contame tu caso y te digo por dónde empezar",
    "Esto ya lo tiene tu competencia. ¿Y vos?",
]
