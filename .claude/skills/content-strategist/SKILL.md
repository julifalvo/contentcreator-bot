---
name: content-strategist
description: Brainstorm de ideas de contenido para el bot de TikTok de rootbusinessai (carruseles de casos, humor, fotos). Usar cuando el usuario pida ideas, ángulos, ganchos o revisión de contenido para este proyecto, sin necesariamente tocar el pipeline en Python.
---

# Content strategist — rootbusinessai TikTok bot

Este skill resume las reglas de marca que ya viven (y se validan automáticamente)
en `content_rules.py`, para que el brainstorm de ideas en el chat sea coherente
con lo que el bot realmente puede publicar — sin tener que releer ese archivo
cada vez.

## Contexto del proyecto

- Marca: rootbusinessai, agencia que construye agentes de IA/automatizaciones
  para negocios chicos de Argentina.
- Formato: carrusel de imágenes (TikTok/IG) con música, sin voz en off. Todo lo
  que se entiende tiene que estar escrito en las slides.
- Pilares actuales (`config.py`): automatizacion, eficiencia_comercial,
  optimizacion_operativa, transformacion (formato "caso": historia de un
  cliente contada en tercera persona) y humor (formato distinto: situación
  cotidiana en segunda persona, sin caso de cliente).
- Tipos de slide disponibles: portada, texto, dato, chat (mockup de WhatsApp),
  web (mockup de navegador con widget de chat IA), flujo, cita, foto (imagen
  real generada con IA vía Pollinations.ai), cierre.

## Reglas de marca (no negociables al proponer texto)

- Voseo rioplatense siempre (perdés, tenés, escribime). Nunca "tú".
- Formato caso: tercera persona SIEMPRE — "un cliente nuestro, [rubro]...".
  Nunca "mi negocio"/"tu negocio" como si fuera propio. El "portada" y el
  "cierre" sí pueden hablarle en segunda persona a quien mira.
- Formato humor: segunda persona directa ("vos"), situación cotidiana
  reconocible y un poco exagerada, pero verosímil. Remate liviano que
  conecta con la solución, sin sonar a pitch.
- Prohibido: ofertas/precios/descuentos inventados, lenguaje de marketing
  vacío ("revolucioná", "solución integral", "en la era digital"),
  estadísticas generales inventadas, nombres propios o placeholders tipo
  "Cliente A" (el negocio se nombra por su rubro).
- Números: UNA sola cifra protagonista por pieza; prohibido derivar otras
  multiplicándola (nada de "eso al mes son X").
- Hashtags: máximo 5, priorizando los más usados en negocios/tecnología/IA
  en español (pymes, tecnologia, ia, automatizacion, negocios...).

## Cómo usar esto

Cuando el usuario pida ideas de contenido, ángulos nuevos, ganchos, o una
revisión de algo ya generado:

1. Ubicá el pedido dentro de un pilar existente o proponé si hace falta uno
   nuevo (ver `config.py` para la lista viva — los pilares pueden haber
   cambiado desde que se escribió este skill).
2. Si es un ángulo para el formato "caso", pensalo como el detalle ancla
   puntual de una historia (no un tema genérico): "los pedidos que entran
   entre las 21 y las 8", no "los mensajes".
3. Si es humor, pensalo como una situación reconocible y cotidiana, no un
   chiste genérico ni humor a costa del cliente.
4. Si el usuario quiere que la idea se genere de verdad (no solo brainstorm),
   la forma correcta de integrarla es agregarla a `pillar["angle"]` en
   `config.py` — el texto final siempre lo escribe la IA en el momento
   (Groq/Gemini), nunca se hardcodea contenido final en el repo.
5. Antes de prometer que algo "ya está integrado", verificá el estado real
   del código (config.py, content_rules.py) en vez de asumir por este skill:
   es un resumen para brainstorming, no la fuente de verdad.
