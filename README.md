# Content Creator Bot

Pipeline automatizado para generar y publicar contenido de TikTok (carruseles de
imágenes o video) con aprobación manual por Telegram antes de cada publicación.

## Qué hace

Cinco formatos de contenido, elegibles desde el wizard de `/generar`:

- **Carrusel de imágenes** (default): un LLM (`ai_providers.py`, alterna entre
  Groq y Gemini) escribe una historia completa y la parte en slides;
  `design.py`/`render.py` las renderizan a PNG (1080x1920) con Chrome headless.
  Opcionalmente una slide puede ser una foto real generada con Pollinations.ai.
- **Humor**: mismo mecanismo, pilar con tono distinto (situación cotidiana en
  segunda persona en vez de un caso de cliente).
- **Video narrado**: guion generado por IA (`video_rules.py`) narrado con voz
  real (`elevenlabs_client.py`, ElevenLabs free tier) sobre b-roll de video
  real (`pexels_client.py`, Pexels), armado con ffmpeg (`video_narrado.py`).
- **Chisme Tech Argento** (`chisme_rules.py`): puro fun content, sin caso de
  cliente ni pitch — rankings y listas graciosas que mezclan herramientas de
  IA con costumbres argentinas, con un ícono pixel art generado por IA por
  cada ítem de la lista.
- **El Error de los 30 Minutos** (`impacto_rules.py`): confesión en primera
  persona sobre un error de negocio, seguida de una lista de acciones
  concretas con IA (automatizar, generar impacto, atraer clientes). Cada
  slide lleva una foto de fondo a página completa generada por IA, pensada
  para ser vistosa y que el texto se recorte fuerte encima — es el único
  formato que no usa el papel editorial del resto de la marca.

Pipeline común:

1. **Generación** (`generate.py`): a partir de un pilar temático (`config.py`)
   y un ángulo/rubro (elegido en el wizard o al azar), se pide el contenido a
   `ai_providers.py`, que reintenta con el otro proveedor de texto si uno se
   queda sin cuota. Los ángulos no están hardcodeados: salen del pool en
   `angulos_pool.json` (`angulos.py`), que se amplía corriendo
   `refrescar_angulos.py`.

   Antes de pedir el texto, la pieza recibe su **contexto estratégico**
   (`audiencia.py`): una **intención** sorteada entre las que soporta el pilar
   — educativo, emocional, de conexión o de venta (`config.INTENCIONES`) — y
   una **tensión** puntual de la audiencia (un problema, un deseo, un miedo,
   una pregunta y una objeción reales de un dueño de negocio chico). El ángulo
   define de qué habla la pieza; la intención, para qué está hecha; la tensión,
   contra qué se escribe. Por eso el mismo ángulo no rinde siempre la misma
   pieza. Las reglas del **gancho** (los primeros 2 segundos: abrir curiosidad
   sin prometer de más) viven en `content_rules.GANCHO` y las comparten los
   cinco formatos; las promesas exageradas se rechazan en la validación, igual
   que el tono de vendedor o el español neutro.
2. **Aprobación** (`telegram_client.py`): la vista previa (imágenes o video +
   caption) se manda a un chat de Telegram y espera un botón de
   aprobar/cancelar antes de publicar nada.
3. **Publicación** (`tiktok_client.py`): sube el contenido a TikTok vía la
   Content Posting API (carrusel de fotos o video, según el formato).
4. **Bot en vivo** (`bot.py`): corre todo el pipeline a demanda desde
   Telegram (`/generar` abre un wizard con botones; `/publicar`, `/pilares`,
   `/metricas`, `/ayuda`), sin tocar la terminal.
5. **Realimentación** (`tiktok_metrics.py` + `rendimiento.py`): se traen las
   vistas reales de lo ya publicado (Display API de TikTok) y se cruzan con
   el pilar, el ángulo y la intención que generaron cada pieza — el caption guardado en
   `output/*/contenido.json` es el que se subió, así que emparejarlo con la
   descripción del video devuelve la atribución. Con eso, los ángulos nuevos
   que inventa `refrescar_angulos.py` salen empujados hacia lo que de verdad
   funcionó en la cuenta, y `/metricas` muestra qué pilar y qué intención rinden
mejor.

Aparte, `scrapecreators_client.py` es una herramienta de investigación de
competencia (perfiles/posts de TikTok) para inspirar ángulos nuevos — no es
parte del flujo de `/generar`, se corre suelta.

## Setup

```bash
git clone <este-repo>
cd contentcreator-bot
pip install -r requirements.txt
cp .env.example .env   # completá tus credenciales
```

Variables necesarias en `.env` (ver `.env.example` para el detalle de cada una):

- `GROQ_API_KEY` y/o `GEMINI_API_KEY` — generación de texto (carrusel/humor/video),
  ambos free tier sin tarjeta. Con las dos cargadas se alterna y hay respaldo
  si una se queda sin cuota; con una sola alcanza.
- `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID` (creá un bot con @BotFather).
- `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`, `TIKTOK_REDIRECT_URI` (app en
  [TikTok for Developers](https://developers.tiktok.com/apps) con el producto
  Content Posting API).
- Opcionales, solo para el formato **video narrado**: `PEXELS_API_KEY` (b-roll,
  gratis) y `ELEVENLABS_API_KEY` (locución, free tier). Sin estas dos, el bot
  funciona igual pero ese formato no está disponible.
- Opcional, solo para investigación de competencia: `SCRAPECREATORS_API_KEY`
  (de pago, no tiene free tier — no hace falta para `/generar`).

Antes de publicar carruseles de fotos hace falta un dominio propio verificado
ante TikTok que sirva las imágenes por URL pública (la API de fotos no acepta
archivos subidos directo); con `--video` se sube un `.mp4` en su lugar y no
hace falta ese paso.

Corré `python tiktok_auth.py` una vez para autorizar tu cuenta de TikTok
(genera `tiktok_tokens.json`, que **no** se commitea). Para que además
funcionen las métricas hay que habilitar los scopes `user.info.stats` y
`video.list` en la app de TikTok antes de autorizar (ver el encabezado de
`tiktok_metrics.py`); sin ellos el resto del pipeline anda igual.

## Uso

```bash
python generate.py --pillar automatizacion    # genera un carrusel puntual
python generate.py --pillar random --count 3  # varias piezas al azar
python generate.py --pillar automatizacion --foto  # permite la slide de foto real
python bot.py                                 # deja el bot escuchando Telegram
python refrescar_angulos.py                   # suma ángulos nuevos al pool
python refrescar_angulos.py humor --n 25      # solo ese pilar, pidiendo más
```

`refrescar_angulos.py` es la forma de sumar ideas: en vez de editar
`config.py`, la IA inventa ángulos nuevos evitando repetir los que ya están,
guiándose por las métricas reales de la cuenta (con `--sin-metricas` no
consulta TikTok) y por el perfil de audiencia de `audiencia.py`, para que cada
ángulo nazca de un problema, un miedo o una objeción concretos y el lote quede
repartido entre las intenciones que soporta el pilar.

Desde Telegram, con el bot corriendo:

```
/generar            abre un wizard: formato -> pilar -> ángulo -> ¿foto IA?
/generar [pilar]     atajo rápido: carrusel con ese pilar, ángulo y rubro al azar
/publicar           manda a aprobar la última pieza generada (sin regenerar)
/pilares             lista los pilares y con qué intención se cuenta cada uno
/metricas           seguidores, top 5 por vistas y rendimiento por pilar e intención
/ayuda               este mensaje
```

## Costo

El carrusel (con o sin humor, con o sin foto) es 100% gratis: Groq/Gemini,
Pollinations y el render local no piden tarjeta. El video narrado también es
gratis dentro de los free tiers de Pexels y ElevenLabs (ElevenLabs: ~10.000
caracteres/mes). La investigación de competencia (`scrapecreators_client.py`)
es la única pieza de pago del proyecto — no hace falta para `/generar`.

## Licencia

MIT — ver [LICENSE](LICENSE).
