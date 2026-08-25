"""Banco de casos reales escritos a mano, listos para usar sin gastar créditos de la API.

Pensado para video sin voz en off (solo música de fondo): todo lo que importa
tiene que estar en el texto de las imágenes, por eso cada caso se cuenta a
través de las slides y el demo visual, sin depender de un guion hablado.

Cada caso tiene la misma forma que lo que devuelve ai_client.generate_content(),
para que generate.py pueda usar cualquiera de los dos motores sin cambios.
"""

CASES = [
    # ---------------------------------------------------------------- automatizacion
    {
        "pillar": "automatizacion",
        "negocio_ejemplo": "un vivero",
        "demo": {
            "canal": "WhatsApp",
            "mensaje_cliente": "Necesito 3 potus grandes y 2 bolsas de tierra, ¿me las llevan mañana?",
            "respuesta_bot": "Anotado: 3 potus grandes y 2 bolsas de tierra para mañana. ¿A qué dirección las llevamos?",
            "tiempo_respuesta": "cargado en la planilla al instante",
        },
        "portada_text": "Ese cuaderno te está costando pedidos",
        "slides": [
            {"title": "El problema", "text": "20 pedidos por WhatsApp, todos anotados en un cuaderno"},
            {"title": "Lo que pasaba", "text": "Se mezclaban direcciones y perdía pedidos"},
            {"title": "La solución", "text": "Un agente carga cada pedido sin que nadie escriba nada"},
            {"title": "El resultado", "text": "De 40 minutos por noche a cero minutos cargando pedidos"},
        ],
        "cta_slide_text": "Contame qué anotás a mano vos",
        "caption": (
            "Si todavía anotás pedidos en un cuaderno o en las notas del celular, ese es el primer "
            "proceso que hay que sacarte de encima. ¿Qué tarea repetitiva te come más tiempo en tu negocio?"
        ),
        "hashtags": ["automatizacion", "iaparanegocios", "emprendimiento", "pymes", "chatbots", "negociosdigitales", "productividad", "whatsappbusiness"],
    },
    {
        "pillar": "automatizacion",
        "negocio_ejemplo": "una despensa de barrio",
        "demo": {
            "canal": "WhatsApp",
            "mensaje_cliente": "Me quedan pocas gaseosas de litro y se terminó el aceite de girasol",
            "respuesta_bot": "Anotado: gaseosas 1L y aceite de girasol. ¿Algo más para el pedido del lunes?",
            "tiempo_respuesta": "agregado a la lista en el momento",
        },
        "portada_text": "Cada lunes regalás una hora de tu vida",
        "slides": [
            {"title": "El problema", "text": "Anotaba el pedido a mano cada lunes a la noche"},
            {"title": "Se le pasaban cosas", "text": "A veces se quedaba sin stock a mitad de semana"},
            {"title": "La solución", "text": "Un bot arma la lista desde un audio de WhatsApp"},
            {"title": "El resultado", "text": "De 1 hora armando la lista a 3 audios de un minuto"},
        ],
        "cta_slide_text": "¿Qué armás a mano cada semana vos?",
        "caption": (
            "Una hora todos los lunes revisando góndolas y anotando en papel, solo para armar un pedido. "
            "Ahora son 3 audios. ¿Cuánto tiempo te lleva a vos armar tu pedido semanal?"
        ),
        "hashtags": ["automatizacion", "negociosdigitales", "iaparanegocios", "pymes", "emprendedores", "productividad", "chatbots", "comerciodebarrio"],
    },
    {
        "pillar": "automatizacion",
        "negocio_ejemplo": "un consultorio de kinesiología",
        "demo": {
            "canal": "WhatsApp",
            "mensaje_cliente": "Hola, no voy a poder ir a mi turno de mañana a las 10",
            "respuesta_bot": "Sin problema. Tengo lugar mañana 16hs o el jueves 11hs. ¿Cuál te queda mejor?",
            "tiempo_respuesta": "reprogramado en el momento, sin mirar la agenda",
        },
        "portada_text": "Cada noche regalás 40 minutos gratis",
        "slides": [
            {"title": "El problema", "text": "12 a 15 mensajes de recordatorio, todas las noches"},
            {"title": "El costo", "text": "40 minutos por noche solo copiando y pegando"},
            {"title": "La solución", "text": "El agente manda el recordatorio y reprograma solo"},
            {"title": "El resultado", "text": "De 4 faltazos por semana a 1"},
        ],
        "cta_slide_text": "¿Cuántos recordatorios mandás vos a mano?",
        "caption": (
            "40 minutos por noche mandando el mismo mensaje con distinto horario, todas las noches. "
            "Eso es lo primero que automatizaría en cualquier consultorio. ¿Vos todavía confirmás turnos a mano?"
        ),
        "hashtags": ["automatizacion", "agentesdeia", "consultorios", "saludydigital", "pymes", "productividad", "iaparanegocios", "whatsappbusiness"],
    },

    {
        "pillar": "automatizacion",
        "negocio_ejemplo": "una carnicería",
        "demo": {
            "canal": "WhatsApp",
            "mensaje_cliente": "Necesito 2 kilos de asado y una docena de chorizos para el domingo",
            "respuesta_bot": "Anotado: 2kg de asado y 12 chorizos para el domingo. ¿Retirás en el local o llevamos a domicilio?",
            "tiempo_respuesta": "cargado en el pedido del día al instante",
        },
        "portada_text": "El sábado alguien se queda sin su pedido",
        "slides": [
            {"title": "El problema", "text": "Los sábados se amontonaban 15 pedidos por WhatsApp"},
            {"title": "Lo que pasaba", "text": "Se mezclaban cantidades y faltaba mercadería"},
            {"title": "La solución", "text": "Un agente arma la lista de pedidos sin que nadie tipee nada"},
            {"title": "El resultado", "text": "De errores de cantidad todas las semanas a cero"},
        ],
        "cta_slide_text": "¿Cuántos pedidos anotás vos a mano el finde?",
        "caption": (
            "Los sábados se te llenan de pedidos por WhatsApp y al final alguien se queda sin su corte. "
            "Eso se resuelve solo. ¿Cuántos pedidos anotás vos a mano un sábado?"
        ),
        "hashtags": ["automatizacion", "carniceria", "pymes", "iaparanegocios", "chatbots", "negociosdigitales", "emprendedores", "comerciodebarrio"],
    },
    {
        "pillar": "automatizacion",
        "negocio_ejemplo": "una lavandería",
        "demo": {
            "canal": "WhatsApp",
            "mensaje_cliente": "Hola, ¿ya está lista mi ropa? La dejé el martes",
            "respuesta_bot": "Sí, tu pedido #482 está listo desde ayer a las 18hs. Podés retirarlo hasta las 20hs.",
            "tiempo_respuesta": "respondido sin revisar el cuaderno de pedidos",
        },
        "portada_text": "20 veces por día te cortan el trabajo",
        "slides": [
            {"title": "El problema", "text": "20 llamados por día preguntando por el estado del pedido"},
            {"title": "Lo que pasaba", "text": "Interrumpía el trabajo en el mostrador todo el día"},
            {"title": "La solución", "text": "El agente responde el estado del pedido al instante"},
            {"title": "El resultado", "text": "De 20 llamados diarios a 3"},
        ],
        "cta_slide_text": "¿Cuántas veces te interrumpen a vos preguntando lo mismo?",
        "caption": (
            "Contestar 'todavía no está lista' 20 veces por día no suma nada. Ahora lo responde solo. "
            "¿Qué pregunta repetida te interrumpe más a vos?"
        ),
        "hashtags": ["automatizacion", "lavanderia", "pymes", "iaparanegocios", "chatbots", "negociosdigitales", "emprendedores", "atencionalcliente"],
    },
    {
        "pillar": "automatizacion",
        "negocio_ejemplo": "un local de comida rápida",
        "demo": {
            "canal": "WhatsApp",
            "mensaje_cliente": "Quiero 2 hamburguesas completas y una papas grandes, para retirar",
            "respuesta_bot": "Anotado: 2 hamburguesas completas + papas grandes. Listo en 15 minutos, para retirar.",
            "tiempo_respuesta": "pedido cargado en cocina al instante",
        },
        "portada_text": "En la hora pico se te pierden pedidos",
        "slides": [
            {"title": "El problema", "text": "El mostrador anotaba el pedido y lo volvía a escribir para cocina"},
            {"title": "Lo que pasaba", "text": "Se perdían pedidos en la hora pico"},
            {"title": "La solución", "text": "El agente manda el pedido directo a cocina"},
            {"title": "El resultado", "text": "0 pedidos perdidos en la hora pico del viernes"},
        ],
        "cta_slide_text": "¿Se te pierde algún pedido en la hora pico?",
        "caption": (
            "Anotar el pedido dos veces (mostrador y cocina) es donde se pierden los pedidos en la hora pico. "
            "Sacar ese paso cambia todo. ¿Se te complica la hora pico a vos también?"
        ),
        "hashtags": ["automatizacion", "gastronomia", "pymes", "iaparanegocios", "chatbots", "negociosdigitales", "emprendedores", "comidarapida"],
    },

    # ---------------------------------------------------------------- eficiencia_comercial
    {
        "pillar": "eficiencia_comercial",
        "negocio_ejemplo": "una inmobiliaria",
        "demo": {
            "canal": "DM de Instagram",
            "mensaje_cliente": "Hola, el depto de 2 ambientes en Palermo tiene cochera? Cuánto sale?",
            "respuesta_bot": "Sí, tiene cochera. Alquiler $450.000 + expensas. Puedo mostrártelo hoy 17hs o mañana 10hs, ¿cuál te sirve?",
            "tiempo_respuesta": "en 8 segundos, sin que nadie mirara el celular",
        },
        "portada_text": "Tardaste 6 horas. Ya reservaron en otro lado",
        "slides": [
            {"title": "El problema", "text": "Contestaban los mensajes recién a la tarde"},
            {"title": "Lo que perdían", "text": "La mitad ya había agendado visita en otro lado"},
            {"title": "La solución", "text": "El agente responde precio y ofrece horario al instante"},
            {"title": "El resultado", "text": "De 2 visitas agendadas por semana a 7"},
        ],
        "cta_slide_text": "¿Cuánto tardás vos en contestar un interesado?",
        "caption": (
            "6 horas de espera contra 8 segundos. Esa diferencia es la que decide si te agendan una visita "
            "a vos o al que contestó primero. ¿Cuánto tardás en responder un lead nuevo?"
        ),
        "hashtags": ["eficienciacomercial", "inmobiliaria", "ventas", "agentesdeia", "leads", "negociosdigitales", "iaparanegocios", "chatbots"],
    },
    {
        "pillar": "eficiencia_comercial",
        "negocio_ejemplo": "un estudio de tatuajes",
        "demo": {
            "canal": "WhatsApp",
            "mensaje_cliente": "Quiero un tatuaje chico en el antebrazo, más o menos cuánto sale?",
            "respuesta_bot": "Para ese tamaño arranca en $25.000. Tengo lugar el jueves 15hs o el sábado 12hs. ¿Te reservo alguno?",
            "tiempo_respuesta": "al instante, aunque el tatuador esté trabajando",
        },
        "portada_text": "3 turnos por semana se van a otro estudio",
        "slides": [
            {"title": "El problema", "text": "Contestaba recién cuando terminaba de tatuar"},
            {"title": "Lo que perdía", "text": "3 turnos por semana reservados en otro estudio"},
            {"title": "La solución", "text": "El agente cotiza y ofrece horario al instante"},
            {"title": "El resultado", "text": "De 3 turnos perdidos por semana a 0"},
        ],
        "cta_slide_text": "¿Cuántos turnos perdés vos por responder tarde?",
        "caption": (
            "El que contesta primero se queda con el turno. No es que trabaje peor, es que responde después. "
            "¿Cuántos clientes se te van a la competencia por tardar en contestar?"
        ),
        "hashtags": ["eficienciacomercial", "tatuajes", "agentesdeia", "ventas", "emprendedores", "chatbots", "negociosdigitales", "iaparanegocios"],
    },
    {
        "pillar": "eficiencia_comercial",
        "negocio_ejemplo": "una veterinaria",
        "demo": {
            "canal": "WhatsApp",
            "mensaje_cliente": "Mi perro no comió nada en todo el día y está muy decaído",
            "respuesta_bot": "Entendido. ¿Tomó agua hoy? Con esos síntomas conviene traerlo ya, tengo lugar en 20 minutos.",
            "tiempo_respuesta": "en menos de 1 minuto, aunque la veterinaria esté en consultorio",
        },
        "portada_text": "Te escriben angustiados y contestás 2 horas después",
        "slides": [
            {"title": "El problema", "text": "Urgencias contestadas 2 horas después"},
            {"title": "Lo que pasaba", "text": "La gente se iba a otra clínica más rápida"},
            {"title": "La solución", "text": "El agente distingue urgencia real en 3 preguntas"},
            {"title": "El resultado", "text": "Ningún mensaje sin respuesta más de 1 minuto"},
        ],
        "cta_slide_text": "¿Cuánto tardás vos en responder una urgencia?",
        "caption": (
            "Cuando alguien te escribe angustiado por su mascota, 2 horas de espera es toda la diferencia. "
            "¿Tenés forma de responder eso cuando estás con las manos ocupadas?"
        ),
        "hashtags": ["eficienciacomercial", "veterinaria", "agentesdeia", "chatbots", "ventas", "negociosdigitales", "iaparanegocios", "atencionalcliente"],
    },

    {
        "pillar": "eficiencia_comercial",
        "negocio_ejemplo": "una agencia de turismo",
        "demo": {
            "canal": "WhatsApp",
            "mensaje_cliente": "Hola, ¿cuánto sale un paquete a Bariloche para 2 personas en enero?",
            "respuesta_bot": "Para 2 personas en enero, desde $850.000 con hotel y traslados. ¿Querés que te arme la cotización completa?",
            "tiempo_respuesta": "en 12 segundos, sin que nadie mire el celular",
        },
        "portada_text": "Mientras cotizás, ya compraron en otra agencia",
        "slides": [
            {"title": "El problema", "text": "Las cotizaciones tardaban hasta un día en responderse"},
            {"title": "Lo que perdían", "text": "La mitad ya había cotizado en otra agencia"},
            {"title": "La solución", "text": "El agente cotiza al instante con precios actualizados"},
            {"title": "El resultado", "text": "De 3 paquetes vendidos por semana a 9"},
        ],
        "cta_slide_text": "¿Cuánto tardás vos en mandar una cotización?",
        "caption": (
            "Un día de espera por una cotización es un día para que el cliente compare en otro lado. "
            "Eso se resuelve con una respuesta al instante. ¿Cuánto tardás vos en cotizar un viaje?"
        ),
        "hashtags": ["eficienciacomercial", "turismo", "agentesdeia", "ventas", "pymes", "negociosdigitales", "iaparanegocios", "chatbots"],
    },
    {
        "pillar": "eficiencia_comercial",
        "negocio_ejemplo": "un local de indumentaria",
        "demo": {
            "canal": "DM de Instagram",
            "mensaje_cliente": "Hola, ¿tienen el pantalón negro talle 42 que vi en Instagram?",
            "respuesta_bot": "Sí, queda 1 en talle 42. Te lo reservo 24hs, ¿pasás a buscarlo o lo enviamos?",
            "tiempo_respuesta": "en 6 segundos, aunque el local esté cerrado",
        },
        "portada_text": "Ese talle único ya se vendió mientras dormías",
        "slides": [
            {"title": "El problema", "text": "Contestaban los DMs recién al otro día"},
            {"title": "Lo que perdían", "text": "El talle único ya se había vendido en el local"},
            {"title": "La solución", "text": "El agente confirma stock y reserva al instante, 24/7"},
            {"title": "El resultado", "text": "De 2 ventas por Instagram a la semana a 11"},
        ],
        "cta_slide_text": "¿Cuántas ventas perdés vos por contestar tarde un DM?",
        "caption": (
            "El talle único no espera a que abras el local al otro día. Reservarlo al toque es la diferencia "
            "entre vender o no. ¿Cuánto tardás vos en contestar un DM?"
        ),
        "hashtags": ["eficienciacomercial", "indumentaria", "agentesdeia", "ventas", "pymes", "negociosdigitales", "iaparanegocios", "chatbots"],
    },
    {
        "pillar": "eficiencia_comercial",
        "negocio_ejemplo": "un taller mecánico",
        "demo": {
            "canal": "WhatsApp",
            "mensaje_cliente": "Se me prendió la luz de motor, ¿me pueden ver el auto hoy?",
            "respuesta_bot": "Tengo lugar hoy a las 16hs para diagnóstico. Dura 30 minutos, ¿te sirve ese horario?",
            "tiempo_respuesta": "en 40 segundos, aunque estén con las manos en un motor",
        },
        "portada_text": "3 autos por semana se van a otro taller",
        "slides": [
            {"title": "El problema", "text": "Los mensajes se contestaban recién al cerrar el taller"},
            {"title": "Lo que perdían", "text": "3 autos por semana se iban a otro taller"},
            {"title": "La solución", "text": "El agente agenda el diagnóstico sin interrumpir el trabajo"},
            {"title": "El resultado", "text": "De 3 turnos perdidos por semana a 0"},
        ],
        "cta_slide_text": "¿Cuánto tardás vos en contestar con las manos ocupadas?",
        "caption": (
            "Es difícil soltar la llave para contestar el celular. Por eso el agente contesta primero y agenda. "
            "¿Cuántos turnos se te escapan a vos por no soltar el trabajo?"
        ),
        "hashtags": ["eficienciacomercial", "tallermecanico", "agentesdeia", "ventas", "pymes", "negociosdigitales", "iaparanegocios", "chatbots"],
    },

    # ---------------------------------------------------------------- optimizacion_operativa
    {
        "pillar": "optimizacion_operativa",
        "negocio_ejemplo": "un gimnasio",
        "demo": {
            "canal": "WhatsApp",
            "mensaje_cliente": "Uy me olvidé de pagar la cuota, ¿cuánto era?",
            "respuesta_bot": "Tranquilo, son $18.000. Te paso el link de pago: pago.tugimnasio.com",
            "tiempo_respuesta": "recordatorio automático enviado el día 1 de cada mes",
        },
        "portada_text": "Pasás 2 días al mes persiguiendo plata tuya",
        "slides": [
            {"title": "El problema", "text": "2 días juntando pagos, mensaje por mensaje"},
            {"title": "Lo que se perdía", "text": "5 o 6 socios se olvidaban directamente"},
            {"title": "La solución", "text": "El agente cobra y reclama solo, sin que nadie se acuerde"},
            {"title": "El resultado", "text": "80% de los pagos entran el primer día"},
        ],
        "cta_slide_text": "¿Cuánto tiempo perdés vos cobrando cuotas?",
        "caption": (
            "Cobrar no debería ser un trabajo aparte. Un mensaje con el link y el monto exacto, mandado solo "
            "el día que corresponde, cambia todo. ¿Cuánto tardás vos en juntar los pagos del mes?"
        ),
        "hashtags": ["optimizacion", "gimnasios", "agentesdeia", "cobranzas", "pymes", "negociosdigitales", "iaparanegocios", "chatbots"],
    },
    {
        "pillar": "optimizacion_operativa",
        "negocio_ejemplo": "un consultorio odontológico",
        "demo": {
            "canal": "WhatsApp",
            "mensaje_cliente": "No voy a poder ir mañana a las 9, perdón",
            "respuesta_bot": "No hay problema, gracias por avisar. Le ofrezco el lugar a alguien de la lista de espera. ¿Querés reprogramar?",
            "tiempo_respuesta": "el hueco se cubre en minutos, no en días",
        },
        "portada_text": "Cada sillón vacío es plata que no vuelve",
        "slides": [
            {"title": "El problema", "text": "Una hora de sillón vacía por cada faltazo"},
            {"title": "Lo que pasaba", "text": "Las cancelaciones llegaban tarde para reaccionar"},
            {"title": "La solución", "text": "El agente confirma y cubre el hueco solo"},
            {"title": "El resultado", "text": "De 3 turnos vacíos por semana a 1"},
        ],
        "cta_slide_text": "¿Cuántos turnos vacíos tenés vos por semana?",
        "caption": (
            "Un sillón vacío no se recupera ese día. La diferencia entre enterarte de una cancelación a "
            "tiempo o tarde es plata real. ¿Cuánto te cuesta a vos un faltazo?"
        ),
        "hashtags": ["optimizacion", "odontologia", "agentesdeia", "consultorios", "pymes", "negociosdigitales", "iaparanegocios", "chatbots"],
    },
    {
        "pillar": "optimizacion_operativa",
        "negocio_ejemplo": "un restaurante",
        "demo": {
            "canal": "WhatsApp",
            "mensaje_cliente": "¿Cómo estamos de papa para el finde?",
            "respuesta_bot": "Quedan 4 kilos, por debajo del mínimo de 10. Ya avisé al proveedor para reponer mañana a la mañana.",
            "tiempo_respuesta": "control automático, sin revisar la heladera",
        },
        "portada_text": "Viernes 9 de la noche y te falta un ingrediente",
        "slides": [
            {"title": "El problema", "text": "Controlaban el stock a ojo, revisando la heladera"},
            {"title": "Lo que pasaba", "text": "Sacaban platos del menú a mitad de servicio"},
            {"title": "La solución", "text": "El agente avisa antes de que falte, no cuando ya faltó"},
            {"title": "El resultado", "text": "2 meses sin sacar un plato del menú por stock"},
        ],
        "cta_slide_text": "¿Controlás el stock a ojo vos también?",
        "caption": (
            "Enterarte que te falta un ingrediente a las 9 de la noche con el salón lleno es lo peor. "
            "El aviso tiene que llegar a la mañana. ¿Cómo controlás el stock en tu negocio?"
        ),
        "hashtags": ["optimizacion", "gastronomia", "agentesdeia", "inventario", "pymes", "negociosdigitales", "iaparanegocios", "chatbots"],
    },

    {
        "pillar": "optimizacion_operativa",
        "negocio_ejemplo": "una farmacia de barrio",
        "demo": {
            "canal": "WhatsApp",
            "mensaje_cliente": "¿Tienen ibuprofeno de 600mg?",
            "respuesta_bot": "Sí, quedan 8 unidades. ¿Te lo reservo para retirar hoy?",
            "tiempo_respuesta": "consulta de stock respondida sin ir hasta la góndola",
        },
        "portada_text": "Perdés horas caminando para decir 'sí, tenemos'",
        "slides": [
            {"title": "El problema", "text": "Cada consulta de stock implicaba ir a revisar físicamente"},
            {"title": "Lo que pasaba", "text": "10 minutos perdidos por consulta, todo el día"},
            {"title": "La solución", "text": "El agente contesta el stock desde el sistema, al instante"},
            {"title": "El resultado", "text": "De 10 minutos por consulta a 5 segundos"},
        ],
        "cta_slide_text": "¿Cuánto tiempo perdés vos yendo a revisar stock?",
        "caption": (
            "Ir y volver de la góndola para contestar 'sí, tenemos' suma horas perdidas en el día. Ahora lo "
            "contesta el sistema solo. ¿Cuánto tiempo te consume a vos revisar stock?"
        ),
        "hashtags": ["optimizacion", "farmacia", "agentesdeia", "pymes", "negociosdigitales", "iaparanegocios", "chatbots", "inventario"],
    },
    {
        "pillar": "optimizacion_operativa",
        "negocio_ejemplo": "una óptica",
        "demo": {
            "canal": "WhatsApp",
            "mensaje_cliente": "Hola, ¿ya están listos mis anteojos?",
            "respuesta_bot": "Sí, tu pedido está listo desde el martes. Podés retirarlo hasta las 19hs cualquier día.",
            "tiempo_respuesta": "estado del pedido respondido sin revisar la planilla",
        },
        "portada_text": "Una hora por día buscando en la planilla",
        "slides": [
            {"title": "El problema", "text": "Cada consulta de estado implicaba buscar en la planilla de pedidos"},
            {"title": "Lo que pasaba", "text": "5 minutos por consulta, con 15 consultas por día"},
            {"title": "La solución", "text": "El agente contesta el estado del pedido automáticamente"},
            {"title": "El resultado", "text": "De más de una hora por día a cero"},
        ],
        "cta_slide_text": "¿Cuánto tiempo te lleva a vos revisar el estado de un pedido?",
        "caption": (
            "Buscar en la planilla si el pedido está listo es tiempo que no vuelve. El agente ya lo sabe y "
            "contesta solo. ¿Cuánto tiempo te consume esa consulta a vos?"
        ),
        "hashtags": ["optimizacion", "optica", "agentesdeia", "pymes", "negociosdigitales", "iaparanegocios", "chatbots", "atencionalcliente"],
    },
    {
        "pillar": "optimizacion_operativa",
        "negocio_ejemplo": "un lavadero de autos",
        "demo": {
            "canal": "WhatsApp",
            "mensaje_cliente": "¿Tienen lugar para un lavado completo hoy a la tarde?",
            "respuesta_bot": "Sí, tengo 15hs y 17hs libres para lavado completo. ¿Cuál preferís?",
            "tiempo_respuesta": "turno confirmado sin interrumpir el lavado en curso",
        },
        "portada_text": "Entre auto y auto se te escapan 4 turnos",
        "slides": [
            {"title": "El problema", "text": "Contestaban los mensajes recién entre auto y auto"},
            {"title": "Lo que pasaba", "text": "Perdían turnos por la demora en responder"},
            {"title": "La solución", "text": "El agente agenda mientras el equipo sigue lavando"},
            {"title": "El resultado", "text": "De 4 turnos perdidos por semana a 1"},
        ],
        "cta_slide_text": "¿Cuántos turnos perdés vos por no soltar la manguera?",
        "caption": (
            "Entre auto y auto no hay tiempo de mirar el celular, y ahí se pierden turnos. El agente lo agenda "
            "solo mientras el equipo sigue trabajando. ¿Cuántos turnos se te escapan a vos?"
        ),
        "hashtags": ["optimizacion", "lavadero", "agentesdeia", "pymes", "negociosdigitales", "iaparanegocios", "chatbots", "ventas"],
    },

    # ---------------------------------------------------------------- transformacion
    {
        "pillar": "transformacion",
        "negocio_ejemplo": "una ferretería de barrio",
        "demo": {
            "canal": "WhatsApp",
            "mensaje_cliente": "Tenés tornillos autoperforantes de 1 pulgada?",
            "respuesta_bot": "Sí, tenemos. La caja de 100 sale $6.500. ¿Te la reservo para retirar hoy?",
            "tiempo_respuesta": "respondido sin que nadie deje el mostrador",
        },
        "portada_text": "Tu competencia abrió a 3 cuadras con catálogo online",
        "slides": [
            {"title": "30 años igual", "text": "El negocio funcionó siempre solo con el mostrador"},
            {"title": "Lo que cambió", "text": "Abrió competencia grande a 3 cuadras, con catálogo online"},
            {"title": "La solución", "text": "Un agente vende por WhatsApp sin tocar el mostrador"},
            {"title": "El resultado", "text": "1 de cada 4 ventas ya viene por mensaje"},
        ],
        "cta_slide_text": "¿Tu negocio todavía depende solo del mostrador?",
        "caption": (
            "No hizo falta cambiar el local ni el mostrador de 30 años. Alcanzó con sumar un canal más. "
            "¿Cuánto de lo que vendés hoy depende de que alguien entre caminando?"
        ),
        "hashtags": ["transformaciondigital", "pymes", "comerciodebarrio", "agentesdeia", "iaparanegocios", "emprendedores", "chatbots", "negociosdigitales"],
    },
    {
        "pillar": "transformacion",
        "negocio_ejemplo": "un estudio contable",
        "demo": {
            "canal": "WhatsApp",
            "mensaje_cliente": "Hola, soy cliente nuevo, ¿qué datos necesitan?",
            "respuesta_bot": "Bienvenido. Pasame tu CUIT y el rubro de tu actividad para arrancar el legajo.",
            "tiempo_respuesta": "carga automática, sin que el contador escriba nada",
        },
        "portada_text": "25 minutos por cliente que no cobrás",
        "slides": [
            {"title": "El problema", "text": "Cada legajo se armaba a mano, dato por dato"},
            {"title": "El riesgo", "text": "Con 40 clientes activos, algo siempre se pasaba"},
            {"title": "La solución", "text": "Un formulario conversacional carga todo solo"},
            {"title": "El resultado", "text": "De 25 minutos por cliente a carga automática"},
        ],
        "cta_slide_text": "¿Cuánto tardás vos en dar de alta un cliente?",
        "caption": (
            "Un estudio contable no necesita un sistema carísimo para dejar de armar legajos a mano. "
            "Necesita que alguien le pregunte bien y cargue solo. ¿Cómo das de alta a un cliente nuevo vos?"
        ),
        "hashtags": ["transformaciondigital", "contadores", "agentesdeia", "pymes", "iaparanegocios", "emprendedores", "chatbots", "negociosdigitales"],
    },
    {
        "pillar": "transformacion",
        "negocio_ejemplo": "una peluquería",
        "demo": {
            "canal": "WhatsApp",
            "mensaje_cliente": "Hay lugar para corte y color mañana a la tarde?",
            "respuesta_bot": "Sí, tengo 15hs o 17:30hs libres para corte y color. ¿Cuál preferís?",
            "tiempo_respuesta": "agendado al instante, sin interrumpir a nadie",
        },
        "portada_text": "Cada llamada que no atendés es un turno perdido",
        "slides": [
            {"title": "El problema", "text": "La agenda vivía en un cuaderno de tapa dura"},
            {"title": "Lo que se perdía", "text": "Turnos perdidos por no atender el teléfono"},
            {"title": "La solución", "text": "El agente muestra horarios y agenda por WhatsApp"},
            {"title": "El resultado", "text": "Cero turnos perdidos por teléfono en el primer mes"},
        ],
        "cta_slide_text": "¿Tu agenda todavía vive en un cuaderno?",
        "caption": (
            "El cuaderno no desapareció, solo dejó de ser la única forma de sacar turno. "
            "¿Cuántos turnos se te escapan a vos por no atender el teléfono a tiempo?"
        ),
        "hashtags": ["transformaciondigital", "peluquerias", "agentesdeia", "pymes", "iaparanegocios", "emprendedores", "chatbots", "negociosdigitales"],
    },
    {
        "pillar": "transformacion",
        "negocio_ejemplo": "una librería de barrio",
        "demo": {
            "canal": "WhatsApp",
            "mensaje_cliente": "Hola, ¿tienen el libro nuevo de Piñeiro?",
            "respuesta_bot": "Sí, tenemos 3 unidades. ¿Te lo reservo para retirar o lo enviamos?",
            "tiempo_respuesta": "respondido sin que nadie deje la caja",
        },
        "portada_text": "Solo vendés si alguien entra caminando",
        "slides": [
            {"title": "40 años igual", "text": "El local siempre vendió solo a quien entraba caminando"},
            {"title": "Lo que cambió", "text": "Empezaron a preguntar por WhatsApp si había tal libro"},
            {"title": "La solución", "text": "Un agente contesta stock y reserva sin tocar la caja"},
            {"title": "El resultado", "text": "1 de cada 5 ventas ya arranca por mensaje"},
        ],
        "cta_slide_text": "¿Tu local también depende solo de que entren caminando?",
        "caption": (
            "No hizo falta cambiar nada del local de toda la vida. Alcanzó con responder los mensajes que ya "
            "estaban llegando. ¿Cuánto de lo que vendés depende de que alguien entre caminando?"
        ),
        "hashtags": ["transformaciondigital", "libreria", "pymes", "comerciodebarrio", "agentesdeia", "iaparanegocios", "emprendedores", "chatbots"],
    },
    {
        "pillar": "transformacion",
        "negocio_ejemplo": "una florería",
        "demo": {
            "canal": "WhatsApp",
            "mensaje_cliente": "Necesito un ramo para hoy a la tarde, ¿hacen envío?",
            "respuesta_bot": "Sí, hacemos envío hoy hasta las 19hs. ¿Para qué ocasión es, para armarte una propuesta?",
            "tiempo_respuesta": "cotizado y coordinado en el momento",
        },
        "portada_text": "Un pedido urgente mal anotado y perdés al cliente",
        "slides": [
            {"title": "El problema", "text": "Los pedidos de último momento se anotaban en un cuaderno"},
            {"title": "Lo que pasaba", "text": "Se mezclaban horarios de entrega y direcciones"},
            {"title": "La solución", "text": "El agente cotiza, coordina el envío y confirma solo"},
            {"title": "El resultado", "text": "Cero errores de entrega en el primer mes"},
        ],
        "cta_slide_text": "¿Tu agenda de pedidos todavía vive en un cuaderno?",
        "caption": (
            "Los pedidos de último momento son los que más se complican a mano. Ahora los ordena el agente. "
            "¿Cómo manejás vos los pedidos urgentes?"
        ),
        "hashtags": ["transformaciondigital", "floreria", "pymes", "agentesdeia", "iaparanegocios", "emprendedores", "chatbots", "negociosdigitales"],
    },
    {
        "pillar": "transformacion",
        "negocio_ejemplo": "un estudio de arquitectura",
        "demo": {
            "canal": "WhatsApp",
            "mensaje_cliente": "Hola, quiero consultar por un proyecto de ampliación",
            "respuesta_bot": "Perfecto. Contame la superficie aproximada y la zona, así te paso un rango de presupuesto inicial.",
            "tiempo_respuesta": "primer contacto respondido sin agendar una llamada",
        },
        "portada_text": "El interesado se enfría mientras coordinás la llamada",
        "slides": [
            {"title": "El problema", "text": "Cada consulta nueva esperaba a coordinar una llamada"},
            {"title": "Lo que pasaba", "text": "Muchos interesados se enfriaban en la espera"},
            {"title": "La solución", "text": "El agente arranca la conversación y junta los datos clave"},
            {"title": "El resultado", "text": "De 2 consultas avanzadas por mes a 7"},
        ],
        "cta_slide_text": "¿Cuánto tarda en arrancar una consulta nueva en tu estudio?",
        "caption": (
            "Esperar a coordinar una llamada para la primera consulta enfría al interesado. Arrancar la "
            "conversación al toque cambia eso. ¿Cómo arranca hoy una consulta nueva en tu estudio?"
        ),
        "hashtags": ["transformaciondigital", "arquitectura", "agentesdeia", "iaparanegocios", "emprendedores", "chatbots", "negociosdigitales", "pymes"],
    },
]
