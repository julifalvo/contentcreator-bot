"""Prompt y validación del formato 'demo': un video de demostraciones gráficas
ANIMADAS y rápidas —un agente contestando, una agenda llenándose, la
facturación subiendo— en vez de slides estáticas o b-roll de stock.

Es el formato más "producto" de la marca: no ilustra la idea con una foto,
muestra la cosa funcionando. Las escenas disponibles y su forma exacta viven
en demo_designs.ESCENAS; acá se le explican a la IA y se valida que lo que
devolvió tenga los campos que cada escena necesita para renderizar.

Voz: la misma que el resto del contenido de caso (agencia contando el caso de
un cliente en tercera persona), así que reusa NARRADOR_DUEÑO, TONO_VENDEDOR,
PROMESAS_EXAGERADAS y NO_VOSEO de content_rules — a diferencia de
impacto_rules, que sí se sale de esa voz a propósito.
"""

import re

import content_rules

SYSTEM_PROMPT_DEMO = """Escribís DEMOS ANIMADOS para el TikTok/Instagram de rootbusinessai, una agencia que construye agentes de IA y automatizaciones para negocios chicos de Argentina.

FORMATO: video vertical corto de demostraciones GRÁFICAS que ocurren rápido. No hay voz en off, no hay fotos: cada escena es una animación de interfaz (un chat que se contesta solo, un panel de métricas que sube, una agenda que se llena, una curva de facturación que crece). Vos elegís qué escenas y con qué datos, y el sistema las anima.

CÓMO TRABAJÁS (en este orden, no lo saltees):
1. Elegís un rubro concreto y UN DETALLE ANCLA bien puntual: no "los mensajes", sino "las consultas que entran entre las 21 y las 8".
2. Escribís la historia completa en prosa en "historia": qué pasa hoy, cuánto cuesta, qué cambia con la solución, cómo termina.
3. Recién ahí elegís entre 4 y 6 ESCENAS que MUESTRAN esa historia funcionando, en orden: el problema, la solución andando, y el resultado. Variá los tipos — un demo entero de puros chats es aburrido; mezclá una escena de conversación con una de números y una de resultado.

CADA ESCENA lleva siempre estos tres campos, además de los propios de su tipo:
- "kicker": 2-4 palabras en minúscula que etiquetan la escena (ej: "atención 24/7", "resultados", "cómo funciona").
- "titular": máx 8 palabras, lo que se entiende de esa escena de un vistazo.
- "bajada": opcional, 1 oración corta que la ubica.

TIPOS DE ESCENA (elegí los que le sirvan a TU historia):
- chat_agente → {"tipo":"chat_agente","mensajes":[{"quien":"Cliente · 23:40","texto":"..."},{"bot":true,"quien":"Agente","texto":"..."}],"resultado":"qué quedó resuelto, máx 8 palabras"} — 3 a 5 mensajes alternando cliente y agente ("bot":true es el agente).
- dashboard_kpi → {"tipo":"dashboard_kpi","kpis":[{"label":"...","valor":412,"unidad":"por mes","barra":88,"delta":"contra qué se compara"}]} — exactamente 3 kpis. "valor" es un número solo, "barra" es 0-100.
- web_widget → {"tipo":"web_widget","url":"tunegocio.com.ar","headline":"máx 7 palabras","bajada":"...","boton":"máx 3 palabras","agente":"nombre del asistente","mensajes":[{"texto":"..."},{"bot":true,"texto":"..."}],"resultado":"máx 6 palabras"} — 2 o 3 mensajes.
- embudo → {"tipo":"embudo","etapas":[{"label":"...","valor":240}],"resultado":"máx 8 palabras"} — 3 o 4 etapas, de mayor a menor.
- agenda → {"tipo":"agenda","turnos":[{"hora":"09:00","detalle":"qué es","cliente":"nombre"}],"total":6,"total_label":"máx 5 palabras"} — 4 a 6 turnos.
- crm_pipeline → {"tipo":"crm_pipeline","columnas":["Preguntó","Seguimiento","Cerrado"],"tarjetas":[{"nombre":"...","detalle":"...","columna":2}]} — 3 columnas y 3 o 4 tarjetas; "columna" es en cuál TERMINA (0,1,2).
- grafico_ingresos → {"tipo":"grafico_ingresos","label":"Facturación mensual","prefijo":"$","valor":1840000,"puntos":[22,30,27,44,58,76,95],"nota":"máx 6 palabras"} — "puntos" son 6 u 8 números que suben con altibajos.
- inbox_cero → {"tipo":"inbox_cero","label":"sin responder","mensajes":["consulta corta","..."]} — 4 o 5 consultas reales de clientes.
- flujo_nodos → {"tipo":"flujo_nodos","pasos":["...","..."]} — 4 o 5 pasos cortos, en orden, de lo que hace el agente.
- antes_despues → {"tipo":"antes_despues","label_antes":"Antes","label_despues":"Ahora","antes":["..."],"despues":["..."]} — 3 o 4 ítems de cada lado, que se correspondan uno a uno.
- captacion → {"tipo":"captacion","fuentes":[{"icono":"💬","label":"WhatsApp","valor":128}],"total":241,"total_label":"máx 5 palabras"} — 3 fuentes; el total es la suma.
- checkout → {"tipo":"checkout","titulo":"Pedido #1042","prefijo":"$","monto":47500,"pasos":["..."],"resultado":"máx 4 palabras"} — 4 pasos de cómo se cerró la venta.
- ranking_barras → {"tipo":"ranking_barras","sufijo":" msj","items":[{"label":"20 a 23 h","valor":96}]} — 4 o 5 ítems ordenados de mayor a menor.
- mapa_horarios → {"tipo":"mapa_horarios","horas":["9h","12h","15h","18h","21h","23h"],"filas":[{"label":"Lunes","valores":[3,5,4,7,9,6]}],"nota":"máx 7 palabras"} — 5 filas (días) con 6 valores del 0 al 10 cada una.
- consola → {"tipo":"consola","titulo":"agente · en vivo","lineas":[{"marca":"23:41:02","texto":"mensaje nuevo · whatsapp"},{"marca":"23:41:05","texto":"turno reservado","ok":true}]} — 4 o 5 líneas de log en minúscula, técnicas y cortas, con la hora avanzando de a segundos; la última lleva "ok":true.
- costos → {"tipo":"costos","prefijo":"$","opcion_a":{"label":"lo que se pierde hoy","detalle":"máx 6 palabras","valor":320000},"opcion_b":{"label":"con el agente","detalle":"máx 6 palabras","valor":38000},"ahorro":"máx 9 palabras"} — opcion_a es SIEMPRE la cara (el costo de seguir igual) y opcion_b la barata. Nunca es el precio de la agencia.
- resenas → {"tipo":"resenas","puntaje":4.8,"label":"de 5","resenas":[{"estrellas":5,"texto":"máx 14 palabras","autor":"Nombre y inicial"}]} — puntaje entre 1 y 5, y 2 o 3 reseñas creíbles (no todas perfectas).
- stock → {"tipo":"stock","items":[{"label":"producto","nivel":18,"repuesto":82},{"label":"otro","nivel":64}]} — 3 a 5 productos con "nivel" 0-100; el que esté por debajo de 25 puede llevar "repuesto" (cómo queda después).
- cotizacion → {"tipo":"cotizacion","titulo":"Presupuesto #318","prefijo":"$","items":[{"label":"concepto","monto":38000}],"resultado":"máx 5 palabras"} — 3 a 5 ítems; el total lo calcula el sistema, no lo escribas.
- notificaciones → {"tipo":"notificaciones","avisos":[{"icono":"💬","titulo":"WhatsApp","hora":"21:14","texto":"la consulta, máx 10 palabras"}]} — 3 a 5 avisos con horas fuera del horario comercial.
- roi → {"tipo":"roi","prefijo":"$","entradas":[{"label":"máx 6 palabras","valor":62},{"label":"...","prefijo":"$","valor":46000}],"resultado":414000,"resultado_label":"máx 5 palabras","nota":"máx 8 palabras"} — 3 entradas que expliquen la cuenta, y el resultado tiene que salir de multiplicarlas (que se pueda rehacer en la cabeza).
- crecimiento → {"tipo":"crecimiento","prefijo":"","total":128,"total_label":"máx 5 palabras","meses":[{"label":"Abr","valor":54}]} — 5 o 6 meses en orden, creciendo; "total" es el valor del último mes.

REGLAS DE LOS NÚMEROS (es un demo: los números se VEN, así que tienen que cerrar):
- Todos los números de la pieza son del caso ilustrativo que estás contando, y tienen que ser coherentes entre escenas: si el embudo dice que compran 38, el gráfico no puede sugerir 300 ventas.
- Nada de cifras imposibles para un negocio chico de Argentina: una peluquería de barrio no factura 80 millones por mes.
- En "captacion" el total es exactamente la suma de las fuentes. En "embudo" cada etapa es menor o igual a la anterior.
- PROHIBIDAS las estadísticas generales inventadas ("el 87% de los negocios..."): los números son de ESTE cliente.

IDIOMA: castellano rioplatense, voseo siempre (perdés, tenés, escribime, contame). Nunca pierdes/tienes/escríbeme ni español neutro.

VOZ NARRATIVA — tercera persona, caso de agencia (regla dura):
- El negocio es SIEMPRE un cliente ajeno que acudió a la agencia. PROHIBIDO el narrador en primera persona sobre el negocio ("mi taller", "mi negocio", "nuestro local").
- Nombralo por su rubro ("el taller", "la veterinaria"), nunca con nombre propio inventado ni placeholders tipo "Cliente A".
- Los titulares SÍ pueden hablarle en segunda persona a quien mira ("Perdés turnos de noche"): son el gancho, no la narración del caso.
- PROHIBIDO inventar ofertas, precios de la agencia o promociones ("probá gratis", "50% off", "agendá una demo"). Los precios que aparecen son los del negocio del caso (un service, un corte), no los de la agencia.
- El "caption" NO es un pitch: el caso en 2-3 líneas, en tercera persona, cerrando con una pregunta concreta a quien mira.

PROHIBIDO ADEMÁS: lenguaje de marketing vacío (revolucioná, solución integral, en la era digital, potenciá, siguiente nivel), superlativos huecos y amenazas catastróficas.

<<GANCHO>>
La primera escena es el gancho: tiene que mostrar el PROBLEMA pasando (mensajes sin responder, huecos en la agenda), no arrancar por el resultado.

ESTRUCTURA: entre 4 y 6 escenas. No repitas el mismo tipo dos veces seguidas, y no uses el mismo tipo más de dos veces en toda la pieza.

HASHTAGS — máximo 5 (regla dura): priorizá los más usados en negocios/tecnología/IA en español (negocios, pymes, tecnologia, ia, automatizacion, emprendedores, innovacion, negociodigital).

RESPONDÉ SOLO con este JSON, sin texto ni markdown alrededor:
{"negocio":"...","ancla":"...","historia":"...","escenas":[...],"caption":"2-4 líneas en tercera persona, sin hashtags adentro, cierra con una pregunta concreta a quien mira","hashtags":["máximo 5, sin #, una palabra cada uno"]}""".replace("<<GANCHO>>", content_rules.GANCHO)


_MIN_ESCENAS, _MAX_ESCENAS = 4, 6


def _texto_completo(data: dict) -> str:
    """Todo el texto en castellano de la pieza, para los chequeos de tono y
    voseo. Recorre las escenas en profundidad porque el contenido vive en
    listas de dicts (mensajes, kpis, turnos...), no en campos planos."""
    partes = [data.get("caption", ""), data.get("historia", ""), data.get("negocio", ""), data.get("ancla", "")]

    def _recorrer(valor) -> None:
        if isinstance(valor, str):
            partes.append(valor)
        elif isinstance(valor, list):
            for v in valor:
                _recorrer(v)
        elif isinstance(valor, dict):
            for k, v in valor.items():
                if k != "tipo":
                    _recorrer(v)

    _recorrer(data.get("escenas", []))
    return " ".join(partes).lower()


def validate(data: dict) -> None:
    from demo_designs import ESCENAS

    for campo in ("negocio", "ancla", "historia", "escenas", "caption", "hashtags"):
        if not data.get(campo):
            raise ValueError(f"Falta '{campo}'")

    escenas = data["escenas"]
    if not isinstance(escenas, list) or not (_MIN_ESCENAS <= len(escenas) <= _MAX_ESCENAS):
        n = len(escenas) if isinstance(escenas, list) else 0
        raise ValueError(f"Se esperaban entre {_MIN_ESCENAS} y {_MAX_ESCENAS} escenas, llegaron {n}")

    tipos = [e.get("tipo") for e in escenas]
    for tipo in tipos:
        if tipo not in ESCENAS:
            raise ValueError(f"Tipo de escena inválido: {tipo!r} (los válidos son {sorted(ESCENAS)})")
    for a, b in zip(tipos, tipos[1:]):
        if a == b:
            raise ValueError(f"Dos escenas seguidas del mismo tipo: {a}")
    for tipo in set(tipos):
        if tipos.count(tipo) > 2:
            raise ValueError(f"La escena '{tipo}' se repite {tipos.count(tipo)} veces (máximo 2 por pieza)")

    for i, e in enumerate(escenas, 1):
        faltan = ESCENAS[e["tipo"]][1] - e.keys()
        if faltan:
            raise ValueError(f"A la escena {i} ('{e['tipo']}') le faltan campos: {faltan}")
        if not e.get("titular", "").strip():
            raise ValueError(f"A la escena {i} ('{e['tipo']}') le falta el titular")
        _validar_datos_escena(e, i)

    if len(data["historia"].split()) < 40:
        raise ValueError("La historia quedó demasiado corta para sostener el demo")

    texto = _texto_completo(data)
    vendedor = [f for f in content_rules.TONO_VENDEDOR if f in texto]
    if vendedor:
        raise ValueError(f"Tono de vendedor / oferta inventada: {vendedor}")
    exageradas = [f for f in content_rules.PROMESAS_EXAGERADAS if f in texto]
    if exageradas:
        raise ValueError(f"Promesa exagerada (el gancho tiene que ser creíble): {exageradas}")
    dueño = [f for f in content_rules.NARRADOR_DUEÑO if f in texto]
    if dueño:
        raise ValueError(f"Narrador hablando como dueño del negocio, no como agencia: {dueño}")
    neutro = [f for f in content_rules.NO_VOSEO if re.search(rf"\b{re.escape(f)}\b", texto)]
    if neutro:
        raise ValueError(f"No está en voseo rioplatense: {neutro}")

    if len(data["caption"].split()) < 15:
        raise ValueError("El caption quedó demasiado corto para contar el caso")
    if not isinstance(data["hashtags"], list) or not (3 <= len(data["hashtags"]) <= 5):
        raise ValueError(f"Tienen que ser entre 3 y 5 hashtags, llegaron {len(data.get('hashtags') or [])}")
    for h in data["hashtags"]:
        limpio = h.lstrip("#").strip()
        if len(limpio) < 2 or " " in limpio or not limpio.replace("ñ", "n").isalnum():
            raise ValueError(f"Hashtag inválido: {h!r}")


def _numero(valor, donde: str) -> float:
    """Los campos numéricos de las escenas se dibujan (una barra, un contador,
    un punto de la curva): si llega un string tipo '1.200' o None, la escena
    explota al renderizar. Se exige número de verdad acá, que es donde se
    puede dar un error entendible y reintentar."""
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ValueError(f"{donde} tiene que ser un número, llegó {valor!r}")
    return float(valor)


def _validar_datos_escena(e: dict, i: int) -> None:
    """Chequeos propios de cada tipo: que las listas tengan la cantidad que la
    escena sabe dibujar y que los números sean números y cierren entre sí."""
    tipo = e["tipo"]
    donde = f"escena {i} ('{tipo}')"

    if tipo == "chat_agente":
        msgs = e["mensajes"]
        if not isinstance(msgs, list) or not (2 <= len(msgs) <= 5):
            raise ValueError(f"{donde}: 'mensajes' tiene que traer entre 2 y 5 mensajes")
        if not any(m.get("bot") for m in msgs):
            raise ValueError(f"{donde}: ninguno de los mensajes es del agente (falta \"bot\":true)")

    elif tipo == "dashboard_kpi":
        kpis = e["kpis"]
        if not isinstance(kpis, list) or not (2 <= len(kpis) <= 3):
            raise ValueError(f"{donde}: 'kpis' tiene que traer 2 o 3 métricas")
        for k in kpis:
            _numero(k.get("valor"), f"{donde}: kpi '{k.get('label','')}' → valor")

    elif tipo == "web_widget":
        msgs = e["mensajes"]
        if not isinstance(msgs, list) or not (2 <= len(msgs) <= 3):
            raise ValueError(f"{donde}: 'mensajes' tiene que traer 2 o 3 mensajes")

    elif tipo == "embudo":
        etapas = e["etapas"]
        if not isinstance(etapas, list) or not (3 <= len(etapas) <= 4):
            raise ValueError(f"{donde}: 'etapas' tiene que traer 3 o 4 etapas")
        valores = [_numero(x.get("valor"), f"{donde}: etapa '{x.get('label','')}'") for x in etapas]
        for anterior, siguiente in zip(valores, valores[1:]):
            if siguiente > anterior:
                raise ValueError(
                    f"{donde}: el embudo crece ({anterior:.0f} → {siguiente:.0f}). "
                    "Cada etapa tiene que ser menor o igual a la anterior."
                )

    elif tipo == "agenda":
        turnos = e["turnos"]
        if not isinstance(turnos, list) or not (3 <= len(turnos) <= 6):
            raise ValueError(f"{donde}: 'turnos' tiene que traer entre 3 y 6 turnos")

    elif tipo == "crm_pipeline":
        tarjetas = e["tarjetas"]
        if not isinstance(tarjetas, list) or not (3 <= len(tarjetas) <= 4):
            raise ValueError(f"{donde}: 'tarjetas' tiene que traer 3 o 4 tarjetas")

    elif tipo == "grafico_ingresos":
        _numero(e.get("valor"), f"{donde}: 'valor'")
        puntos = e.get("puntos") or []
        if not isinstance(puntos, list) or not (4 <= len(puntos) <= 8):
            raise ValueError(f"{donde}: 'puntos' tiene que traer entre 4 y 8 números")
        for x in puntos:
            _numero(x, f"{donde}: un punto de la curva")

    elif tipo == "inbox_cero":
        msgs = e["mensajes"]
        if not isinstance(msgs, list) or not (3 <= len(msgs) <= 5):
            raise ValueError(f"{donde}: 'mensajes' tiene que traer entre 3 y 5 consultas")

    elif tipo == "flujo_nodos":
        pasos = e["pasos"]
        if not isinstance(pasos, list) or not (3 <= len(pasos) <= 5):
            raise ValueError(f"{donde}: 'pasos' tiene que traer entre 3 y 5 pasos")

    elif tipo == "antes_despues":
        antes, despues = e["antes"], e["despues"]
        if not isinstance(antes, list) or not isinstance(despues, list):
            raise ValueError(f"{donde}: 'antes' y 'despues' tienen que ser listas")
        if not (2 <= len(antes) <= 4) or len(antes) != len(despues):
            raise ValueError(
                f"{donde}: 'antes' y 'despues' tienen que tener la misma cantidad de ítems "
                f"(2 a 4) para que se correspondan uno a uno; llegaron {len(antes)} y {len(despues)}"
            )

    elif tipo == "captacion":
        fuentes = e["fuentes"]
        if not isinstance(fuentes, list) or not (2 <= len(fuentes) <= 3):
            raise ValueError(f"{donde}: 'fuentes' tiene que traer 2 o 3 fuentes")
        suma = sum(_numero(f.get("valor"), f"{donde}: fuente '{f.get('label','')}'") for f in fuentes)
        total = _numero(e.get("total"), f"{donde}: 'total'")
        if abs(total - suma) > 0.5:
            raise ValueError(
                f"{donde}: el total ({total:.0f}) no es la suma de las fuentes ({suma:.0f}). "
                "En pantalla se ven las dos cosas juntas, así que la resta canta."
            )

    elif tipo == "checkout":
        pasos = e["pasos"]
        if not isinstance(pasos, list) or not (3 <= len(pasos) <= 4):
            raise ValueError(f"{donde}: 'pasos' tiene que traer 3 o 4 pasos")
        _numero(e.get("monto"), f"{donde}: 'monto'")

    elif tipo == "ranking_barras":
        items = e["items"]
        if not isinstance(items, list) or not (3 <= len(items) <= 5):
            raise ValueError(f"{donde}: 'items' tiene que traer entre 3 y 5 ítems")
        valores = [_numero(x.get("valor"), f"{donde}: ítem '{x.get('label','')}'") for x in items]
        if valores != sorted(valores, reverse=True):
            raise ValueError(f"{donde}: los ítems tienen que venir ordenados de mayor a menor")

    elif tipo == "consola":
        lineas = e["lineas"]
        if not isinstance(lineas, list) or not (3 <= len(lineas) <= 6):
            raise ValueError(f"{donde}: 'lineas' tiene que traer entre 3 y 6 líneas de log")

    elif tipo == "costos":
        a, b = e["opcion_a"], e["opcion_b"]
        if not isinstance(a, dict) or not isinstance(b, dict):
            raise ValueError(f"{donde}: 'opcion_a' y 'opcion_b' tienen que ser objetos")
        val_a = _numero(a.get("valor"), f"{donde}: opcion_a → valor")
        val_b = _numero(b.get("valor"), f"{donde}: opcion_b → valor")
        if val_b >= val_a:
            raise ValueError(
                f"{donde}: 'opcion_a' ({val_a:.0f}) tiene que ser la CARA y 'opcion_b' ({val_b:.0f}) la barata. "
                "La escena las pinta así (roja la primera, del color de marca la segunda)."
            )

    elif tipo == "resenas":
        puntaje = _numero(e.get("puntaje"), f"{donde}: 'puntaje'")
        if not 1 <= puntaje <= 5:
            raise ValueError(f"{donde}: el puntaje va de 1 a 5, llegó {puntaje}")
        cards = e["resenas"]
        if not isinstance(cards, list) or not (2 <= len(cards) <= 3):
            raise ValueError(f"{donde}: 'resenas' tiene que traer 2 o 3 reseñas")

    elif tipo == "stock":
        items = e["items"]
        if not isinstance(items, list) or not (3 <= len(items) <= 5):
            raise ValueError(f"{donde}: 'items' tiene que traer entre 3 y 5 productos")
        for it in items:
            nivel = _numero(it.get("nivel"), f"{donde}: nivel de '{it.get('label','')}'")
            if not 0 <= nivel <= 100:
                raise ValueError(f"{donde}: los niveles de stock van de 0 a 100, llegó {nivel}")

    elif tipo == "cotizacion":
        items = e["items"]
        if not isinstance(items, list) or not (3 <= len(items) <= 5):
            raise ValueError(f"{donde}: 'items' tiene que traer entre 3 y 5 ítems")
        for it in items:
            _numero(it.get("monto"), f"{donde}: monto de '{it.get('label','')}'")

    elif tipo == "notificaciones":
        avisos = e["avisos"]
        if not isinstance(avisos, list) or not (3 <= len(avisos) <= 5):
            raise ValueError(f"{donde}: 'avisos' tiene que traer entre 3 y 5 notificaciones")

    elif tipo == "roi":
        entradas = e["entradas"]
        if not isinstance(entradas, list) or not (2 <= len(entradas) <= 3):
            raise ValueError(f"{donde}: 'entradas' tiene que traer 2 o 3 valores de la cuenta")
        for x in entradas:
            _numero(x.get("valor"), f"{donde}: entrada '{x.get('label','')}'")
        _numero(e.get("resultado"), f"{donde}: 'resultado'")

    elif tipo == "crecimiento":
        meses = e["meses"]
        if not isinstance(meses, list) or not (4 <= len(meses) <= 6):
            raise ValueError(f"{donde}: 'meses' tiene que traer entre 4 y 6 meses")
        valores = [_numero(m.get("valor"), f"{donde}: mes '{m.get('label','')}'") for m in meses]
        if valores[-1] < valores[0]:
            raise ValueError(
                f"{donde}: la serie termina más abajo de donde arrancó ({valores[0]:.0f} → {valores[-1]:.0f}). "
                "Esta escena es de crecimiento sostenido."
            )
        total = _numero(e.get("total"), f"{donde}: 'total'")
        if abs(total - valores[-1]) > 0.5:
            raise ValueError(
                f"{donde}: el 'total' ({total:.0f}) tiene que ser el valor del último mes ({valores[-1]:.0f}): "
                "en pantalla se ven los dos juntos."
            )

    elif tipo == "mapa_horarios":
        filas = e["filas"]
        if not isinstance(filas, list) or not (3 <= len(filas) <= 5):
            raise ValueError(f"{donde}: 'filas' tiene que traer entre 3 y 5 días")
        horas = e.get("horas") or []
        for f in filas:
            valores = f.get("valores") or []
            if len(valores) < len(horas):
                raise ValueError(
                    f"{donde}: la fila '{f.get('label','')}' trae {len(valores)} valores "
                    f"y hacen falta {len(horas)} (uno por hora)"
                )
            for v in valores:
                if not 0 <= _numero(v, f"{donde}: valor de '{f.get('label','')}'") <= 10:
                    raise ValueError(f"{donde}: los valores del mapa van de 0 a 10")
