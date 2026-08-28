#
# Versión 1.0
# Fecha: 20 de septiembre de 2025
#
# Autor: Helena Ruiz Ramírez
# Función: Determina el mensaje de bienvenida y las etiquetas de una conversación entrante. También redirige a un chatbot
#           o equipo según el historial del usuario y la hora del día, y genera un resumen de las conversaciones previas.
#
from flask import Flask, request, jsonify
from openai import OpenAI
from datetime import datetime, timezone
import pytz
import os
from utils.enum_liveconnect import Canales, Sucursales, equipos_IDs, EtiquetaAtender, tag_IDs, user_IDs
from utils.liveconnect_api import get_token, get_liveconnect, edit_contact, group_convo


app = Flask(__name__)


# Determina si el callback llego dentro del horario para atender los chatbots
def is_within_schedule():
    return True  # Franny 24/7 — activado 27-ago-2026
    # Define la zona horaria de México
    mexico_tz = pytz.timezone('America/Monterrey')
    
    # Obtiene el tiempo en UTC (Tiempo Universal Coordinado) y lo convierte
    now_utc = datetime.now(timezone.utc)
    now_mexico = now_utc.astimezone(mexico_tz)
    
    # Obtiene el día actual de la semana (Lunes=0, Domingo=6) y la hora
    current_day = now_mexico.weekday()
    current_hour = now_mexico.hour
    current_min = now_mexico.minute

    # 00:00 - 13:29
    # 15:10 - 15:44
    # 19:00 - 23:59
    
    # Checa si el resultado cae dentro del horario establecido
    if 0 <= current_day <= 4: # De lunes a viernes
        if 00 <= current_hour < 14: # 00:00 AM y 01:59 PM
            if current_hour == 13 and current_min >= 30: # No incluye después de la 01:29 PM
                return False
            else:
                return True
        elif 15 == current_hour: # 03 PM
            if 10 <= current_min < 45: #Entre 03:10 PM y 03:44 PM
                return True
        elif 19 <= current_hour: # De las 07:00 PM en adelante
            return True;
    # Cualquier otra hora no es válida
    return False


# Genera el contexto de la conversación para referencia de las ADM
def summarize_convo(convo_table, contact_name):
    # Valida el API key para llamar al cliente de operaciones OpenAI
    client = OpenAI(api_key = os.environ.get('GPT_KEY', None))
    
    # Formatea la tabla de conversación a un string legible
    convo_string = ""
    for index, row in convo_table.iterrows():
        convo_string += f"{row['Usuario']}: {row['Mensaje']}\n"

    # Prompt para el agente GPT con las instrucciones a seguir al generar el resumen
    prompt = f"""
    Eres un asistente que resume conversaciones con prospectos interesados en clases de inglés para niños de 3 a 12 años.
    Resume brevemente la siguiente conversación en formato lista no ordenada con exactamente 4 puntos.
    
    Reglas:
    - Cada punto debe tener máximo 8 palabras.
    - Categorías que debes cubrir en orden:
    1. Datos del hijo(a) o hijo(a)s del prospecto: nombre, edad y grado escolar
    2. Manejo de inglés del hijo(a)(s): bajo/medio/alto
    3. Objetivos de aprendizaje con las clases: dominar el idioma, quitar la pena al hablar, mejorar calificaciones, etc.
    4. Intención principal: sobre qué pidió informes, si quiere Clase Muestra, si ya quiere inscribirse, etc.
    - Si no hay información suficiente, omite ese punto y no lo incluyas en la lista final
    
    Conversación con el prospecto {contact_name}:
    {convo_string}
    """

    # Método para generar una respuesta tipo "chat completion". La temperatura es más estricta mientras más se acerque a 0
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Eres un asistente de CRM especializado en el sistema de ventas Sandler con un enfoque educativo."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=150
    )
    return resp.choices[0].message.content.strip()


# Transferir al equipo de la sucursal en horario offline o cuando el contacto ya pasó la fase de CLMU
def team_delegate(data, acciones):
    # Especifica el id del equipo a transferir la conversación, en este caso es el de la sucursal
    valor_canal = data.get('chat', {}).get('id_canal')
    acciones.append({
        "type": "teamDelegate",
        "id_team": int(equipos_IDs.get(str(valor_canal), "1959")) # Si no existe, se asigna a Atención Virtual (ID 1959)
    })
    print("Team delegate")

    # Como va directo a la sucursal, se le asigna la etiqueta para poder atenderlo después
    tag_sucursal = Canales.from_value(valor_canal).name
    acciones.append({
        "type": "addTag",
        "id_tag": int(EtiquetaAtender.from_value(tag_sucursal).value)
    })
    print(EtiquetaAtender.from_value(tag_sucursal).value)


@app.route("/", methods=["GET", "POST"])
def identify_contact():
    if request.method == 'GET':
        return '''
            <!doctype html>
            <title>Franny TRANSFER Status</title>
            <h1>¡El servidor está corriendo!</h1>
        ''', 200

    # Protege al servidor de requests no deseados al verificar el secret key
    # Primero checa en los headers, y si no, en los argumentos del URL
    incoming_secret = request.headers.get("secret") or request.args.get("secret")
    my_secret = os.environ.get('LC_WEBHOOK_SECRET', None)
    if incoming_secret != my_secret:
        print(f"[WARNING] Secret inválido recibido: {incoming_secret}")
        return jsonify({"error": "Unauthorized"}), 401
    
    # Crea el token único por usuario para usar las APIs cada que corre el script
    token_json_resp = get_token()
    if 'PageGearToken' in token_json_resp:
        pageGearToken = token_json_resp['PageGearToken']
    else:
        return jsonify({"error": f"Error interno del servidor: No se pudo obtener el API token de LiveConnect"}), 503
    
    try:
        # Primero revisa si los datos recibidos contienen la estructura correcta
        data = request.json
        if not data:
            return jsonify({"error": "No se proporcionaron datos"}), 400
        print("Callback recibido:", data)
        
        contexto = "contexto de ejemplo" # Para después guardar el resumen de la conversación
        sucursal = "sucursal de ejemplo" # Para después guardar la sucursal del contacto
        texto_respuesta = "respuesta de ejemplo" # Para después guardar el texto de bienvenida a generar
        acciones = [] # Para después agregar las acciones a realizar en LC

        # Si el callback contiene el mensaje entrante, checa si viene de una campaña para asignar la etiqueta
        mensaje = data.get("inputs", {}).get("mensaje_inicial")
        if mensaje:  # si existe y no es None
            mensaje_lower = mensaje.lower()
            if "fb.me" in mensaje_lower:
                acciones.append({
                    "type": "addTag",
                    "id_tag": int(tag_IDs["facebook"])
                })
                print("Campaña facebook")
            elif "instagram.com" in mensaje_lower:
                acciones.append({
                    "type": "addTag",
                    "id_tag": int(tag_IDs["instagram"])
                })
                print("Campaña instagram")

        # Revisa si la conversacion entrante esta dentro del horario de atencion
        if is_within_schedule():
            # --- LOGICA ONLINE: Delegar a Chatbot ---
            print("Horario ONLINE, ejecutando lógica de historial")

            # Checa si se ha definido la sucursal. Si no, la genera según el canal del mensaje entrante
            sucursal = data.get('chat', {}).get('contacto', {}).get('dinamicos', {}).get('dinamicovmoXo1', '').strip()
            if sucursal is None or sucursal == '':
                valor_canal = data.get('chat', {}).get('id_canal')
                if valor_canal:
                    tag_sucursal = Canales.from_value(valor_canal).name
                    print(tag_sucursal)
                    sucursal = Sucursales.from_value(tag_sucursal).value
                    print(sucursal)
                else:
                    print("Error al solicitar la sucursal / nombre del canal")

            # Ahora, extrae el id del contacto del mensaje entrante para revisar si tiene historial > 0
            historial = False
            contact_ID = data.get('inputs', {}).get('id_contacto')
            if contact_ID:
                # Pasamos el ID del contacto del cual queremos consultar el historial
                # Este se obtiene del webhook lanzado al transferir la convo al chatbot Franny Transfer en LC (Equipo Froggy)
                history_endpoint = "history/conversations"
                history_payload = { "id_contacto": contact_ID }
                contact_history_json_resp = get_liveconnect(history_endpoint, history_payload, pageGearToken)
                if 'status' in contact_history_json_resp and contact_history_json_resp['status'] > 0:
                    historial = True
                    print("Historial encontrado - Contacto existente")
                else:
                    historial = False
                    print("Historial no encontrado - Contacto nuevo")

            if historial:
                tag_list = data.get('chat', {}).get('etiquetas', {})
                if int(tag_IDs["fase chatbot"]) in tag_list.values():
                    # Si tiene historial y también tiene la etiqueta de 'Fase Chatbot', se redirige al chatbot Existentes
                    texto_respuesta = "¡Hola de nuevo! Le atiende Franny, una asistente virtual para la sucursal *"+sucursal+"* de *Froggin English for Kids* ⭐🐸📚\n"
                    texto_respuesta += "\nEstoy aquí para contestar cualquier duda, ya sea por mensaje de texto o de voz, sobre nuestras divertidas clases de inglés para niños de *3 a 12 años* 🏫💚\n"

                    # Manda a generar un resumen de hasta los últimos 25 mensajes con el contacto
                    # Este contexto se manda como mensaje, y más adelante se guarda en el campo dinámico 'Contexto'
                    contact_name = data.get('inputs', {}).get('nombre')
                    convo_table = group_convo(pageGearToken, contact_ID, contact_name, message_limit=25)
                    contexto = summarize_convo(convo_table, contact_name)
                    print("Contexto generado: "+contexto)

                    # Termina el mensaje de bienvenida y lo adjunta a la acción 'sendText'
                    texto_respuesta += "\n🤖 _Actualmente me encuentro bajo entrenamiento. Le agradezco su paciencia si me llego a equivocar_ 🙏"
                    acciones.append({
                        "type": "sendText",
                        "text": texto_respuesta
                    })

                    # Especifica el id del usuario a transferir la conversación, en este caso es un chatbot
                    acciones.append({
                        "type": "userDelegate",
                        "id_user": int(user_IDs["existentes"]['id']),
                        "name": user_IDs["existentes"]['name']
                    })

                    # Como lo va a atender el bot, le asigna la etiqueta '!! EN VIVO'
                    acciones.append({
                        "type": "addTag",
                        "id_tag": int(tag_IDs["live"])
                    })

                    # Actualiza los campos dinámicos de Sucursal y Contexto del contacto con un método API
                    chat_ID = data.get('chat', {}).get('id').strip()
                    edit_payload = {
                        "id": contact_ID,
                        "dinamicos": {
                            "dinamicovmoXo1": sucursal,
                            "dinamicoQBTVa1": contexto
                        },
                        "id_chat": chat_ID
                    }
                    edit_contact(edit_payload, pageGearToken)
                else:
                    # Si tiene historial pero no tiene la etiqueta de 'Fase Chatbot', se redirige al equipo de la sucursal correspondiente
                    team_delegate(data, acciones)
            else:
                # Si no tiene historial, significa que es nuevo y se le da la bienvenida por primera vez
                texto_respuesta = "¡Bienvenido! Le atiende Franny, una asistente virtual para la sucursal *"+sucursal+"* de *Froggin English for Kids* ⭐🐸📚\n"
                texto_respuesta += "\nEstoy aquí para contestar cualquier duda, ya sea por mensaje de texto o de voz, sobre nuestras divertidas clases de inglés para niños de *3 a 12 años* 🏫💚\n"
                texto_respuesta += "\n🤖 _Actualmente me encuentro bajo entrenamiento. Le agradezco su paciencia si me llego a equivocar_ 🙏"
                acciones.append({
                    "type": "sendText",
                    "text": texto_respuesta
                })

                # Como es nuevo, le asigna la etiqueta de 'Fase Chatbot' (el ID está en el dict "tag_IDs" definido en enum_liveconnect.py)
                acciones.append({
                    "type": "addTag",
                    "id_tag": int(tag_IDs["fase chatbot"])
                })

                # Como lo va a atender el bot, le asigna la etiqueta '!! EN VIVO'
                acciones.append({
                    "type": "addTag",
                    "id_tag": int(tag_IDs["live"])
                })

                # Especifica el id del usuario a transferir la conversación, en este caso es un chatbot
                acciones.append({
                    "type": "userDelegate",
                    "id_user": int(user_IDs["nuevos"]['id']),
                    "name": user_IDs["nuevos"]['name']
                })

                # Actualiza el campo dinámico de Sucursal del contacto con un método API
                chat_ID = data.get('chat', {}).get('id').strip()
                edit_payload = {
                    "id": contact_ID,
                    "dinamicos": {
                        "dinamicovmoXo1": sucursal
                    },
                    "id_chat": chat_ID
                }
                edit_contact(edit_payload, pageGearToken)
        else:
            # --- LOGICA OFFLINE: Delegar a Equipo Humano ---
            print("Horario OFFLINE, delegando a la sucursal")
            team_delegate(data, acciones)

        # Esta es la respuesta que se regresa a LC con las acciones a realizar (mandar msj, agregar etiqueta, delegar a chatbot/equipo)
        response = {
            "status": 1,
            "status_message": "Ok",
            "data": {
                "actions": acciones
            }
        }
        return jsonify(response)
    except Exception as e:
        # Cuando el servidor falla, se manda esta respuesta
        print(e)
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500


if __name__ == "__main__":
    # Instrucciones para desplegar la app en un servidor WSGI usando Gunicorn
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 8080)), debug=True)
