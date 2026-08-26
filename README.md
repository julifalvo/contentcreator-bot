# Content Creator Bot

Pipeline automatizado para generar y publicar contenido de TikTok (carruseles de
imágenes o video) con aprobación manual por Telegram antes de cada publicación.

## Qué hace

1. **Generación** (`generate.py`): a partir de un pilar temático (`config.py`)
   y un ángulo/rubro sorteado, un LLM (Groq) escribe una historia completa y la
   parte en slides.
2. **Diseño y render** (`design.py`, `render.py`): cada slide se arma como HTML/CSS
   y se rinde a PNG (1080x1920) con Chrome headless.
3. **Video opcional** (`video_gen.py`): arma un MP4 vertical a partir de las
   imágenes y una pista de música local, usando ffmpeg.
4. **Aprobación** (`telegram_client.py`): la vista previa (imágenes + caption) se
   manda a un chat de Telegram y espera un botón de aprobar/cancelar antes de
   publicar nada.
5. **Publicación** (`publish.py`, `tiktok_client.py`): sube el contenido a TikTok
   vía la Content Posting API (carrusel de fotos o video, según el flag usado).
6. **Bot en vivo** (`bot.py`): corre todo el pipeline a demanda desde comandos de
   Telegram (`/generar`, `/publicar`, `/pilares`, `/ayuda`), sin tocar la terminal.

## Setup

```bash
git clone <este-repo>
cd contentcreator-bot
pip install -r requirements.txt
cp .env.example .env   # completá tus credenciales
```

Variables necesarias en `.env`:

- `GROQ_API_KEY` (generación de contenido, free tier sin tarjeta en
  [console.groq.com](https://console.groq.com)).
- `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID` (creá un bot con @BotFather).
- `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`, `TIKTOK_REDIRECT_URI` (app en
  [TikTok for Developers](https://developers.tiktok.com/apps) con el producto
  Content Posting API).

Antes de publicar carruseles de fotos hace falta un dominio propio verificado
ante TikTok que sirva las imágenes por URL pública (la API de fotos no acepta
archivos subidos directo); con `--video` se sube un `.mp4` en su lugar y no
hace falta ese paso.

Corré `python tiktok_auth.py` una vez para autorizar tu cuenta de TikTok
(genera `tiktok_tokens.json`, que **no** se commitea).

## Uso

```bash
python generate.py --pillar automatizacion    # genera un carrusel puntual
python generate.py --pillar random --count 3  # varias piezas al azar
python bot.py                                 # deja el bot escuchando Telegram
```

Desde Telegram, con el bot corriendo:

```
/generar [pilar]   genera un carrusel y lo manda a aprobar
/publicar           manda a aprobar la última pieza generada (sin regenerar)
/pilares             lista los pilares de contenido disponibles
/ayuda               este mensaje
```

## Costo

Todo el pipeline corre con free tiers: Groq (sin tarjeta), render local con
Chrome headless, y ffmpeg estático vía `imageio-ffmpeg`. Sin servicios de pago.

## Licencia

MIT — ver [LICENSE](LICENSE).
