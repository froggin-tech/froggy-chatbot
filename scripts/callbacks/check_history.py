#
# Versión 0.2
# Fecha: 03 de septiembre de 2025
#
# Autor: Helena Ruiz Ramírez
# Función: Determina el callback response al recibir un webhook de un chatbot. Por ahora, determina si el mensaje
#           entrante es de un contacto nuevo o ya existente según su historial de conversaciones.
#
from flask import Flask, request, jsonify
from openai import OpenAI
import pandas as pd
import requests
import os
from enum_canales import Canales, Sucursales, equipos_IDs


app = Flask(__name__)


# Regresa el token de autorización para LC
def get_token():
    ckey = os.environ.get('LC_C_KEY', None)
    privateKey = os.environ.get('LC_PRIVATE_KEY', None)
    payload = {
        "cKey": ckey,
        "privateKey": privateKey
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, application/xml"
    }
    response = requests.post("https://api.liveconnect.chat/prod/account/token", json=payload, headers=headers, timeout=10)
    return response.json()


# Función para consultar historial de un contacto
def get_liveconnect(endpoint, payload, pageGearToken):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "PageGearToken": pageGearToken
    }
    response = requests.post("https://api.liveconnect.chat/prod"+endpoint, json=payload, headers=headers, timeout=10)
    return response.json()


def edit_contact(payload, pageGearToken):
    endpoint = "/contacts/edt"
    edit_contact_json_resp = get_liveconnect(endpoint, payload, pageGearToken)
    if 'status' in edit_contact_json_resp and edit_contact_json_resp['status'] < 0:
        print(edit_contact_json_resp['status_message'])
    else:
        print("Se editó el usuario")


# Cambia los IDs por los nombres de los usuarios e indica cuales son de parte del sistema
def switch_contact_ids(dataframe, participants, token):
    for x in dataframe.index:
        user_id = int(dataframe.loc[x, 'Usuario'])
        try:
            dataframe.loc[x, 'Usuario'] = participants[user_id]
        except:
            # Si detecta un usuario que LC no registró como participante, lo busca externamente
            user_payload = {"id": user_id}
            user_json_resp = get_liveconnect("users/get", user_payload, token)
            try:
                dataframe.loc[x, 'Usuario'] = user_json_resp['data']['nombre']
            except:
                dataframe.loc[x, 'Usuario'] = "Usuario No Encontrado"


def group_convo(pageGearToken, contact_ID, contact_name):
    convo_participants = {}
    convo_participants[contact_ID] = contact_name

    all_convos_endpoint = "/history/conversations"
    all_user_convos_payload = { "id_contacto": contact_ID }
    all_user_convos_json_resp = get_liveconnect(all_convos_endpoint, all_user_convos_payload, pageGearToken)

    participants_endpoint = "/history/participants"
    convo_endpoint = "/history/conversation"
    messages_data = []
    for x in all_user_convos_json_resp['data']:
        # Guarda en un diccionario los datos de las ADM que atendieron la conversacion
        temp_ID = x['id']
        participants_payload = {"id_conversacion": temp_ID}
        participants_json_resp = get_liveconnect(participants_endpoint, participants_payload, pageGearToken)
        for y in participants_json_resp['data']:
            convo_participants[y['id_usuario']] = y['nombre']

        # Agrupa cada mensaje individual en la conversación
        messages_payload = {"id": temp_ID}
        messages_json_resp = get_liveconnect(convo_endpoint, messages_payload, pageGearToken)
        for y in messages_json_resp['data']['mensajes']: # Se salta los mensajes irrelevantes (msjs del sistema o internos)
            if (y['id_remitente'] != 0) and (y['interno'] == 0):
                messages_data.append(y)

    messages_index = 0
    if len(messages_data) > 25: # Para que solo analice máximo los 25 mensajes más recientes
        messages_index = len(messages_data) - 25
    most_recent_messages = []
    for x in messages_data[messages_index:]:
        most_recent_messages.append(x)

    # Guarda la lista de todos los mensajes en un dataframe normalizado
    df = pd.json_normalize(most_recent_messages)

    # Crea una tabla donde almacenar los mensajes de manera ordenada y por fecha
    convo_table = pd.DataFrame(columns=['Usuario', 'Mensaje', 'Fecha'])
    convo_table['Usuario'] = df['id_remitente'].astype(object)
    convo_table['Mensaje'] = df['mensaje'].astype(object)
    convo_table['Fecha'] = df['fecha_add'].astype(object)

    # Ordena las filas por el timestamp de cada mensaje
    # Luego, vuelve a generar el índice de las filas del dataframe
    convo_table['Fecha'] = pd.to_datetime(convo_table['Fecha'], format='%Y-%m-%d %H:%M:%S')
    convo_table = convo_table.sort_values(by='Fecha')
    convo_table = convo_table.reset_index(drop=True)

    # Reemplaza los IDs de LiveConnect por el nombre del cliente o agente
    switch_contact_ids(convo_table, convo_participants, pageGearToken)

    # Reemplaza los espacios sin datos por un espacio vacio para evitar problemas al subir los datos
    convo_table = convo_table.infer_objects(copy=False).fillna('')
    return convo_table


def summarize_convo(convo_table, contact_name):
    # Valida el API key para llamar al cliente de operaciones OpenAI
    client = OpenAI(api_key = os.environ.get('GPT_KEY', None))
    
    # Formatea la tabla de conversación a un string legible
    convo_string = ""
    for index, row in convo_table.iterrows():
        convo_string += f"{row['Usuario']}: {row['Mensaje']}\n"

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


@app.route("/", methods=["POST"])
def identify_contact():
    # Protege al servidor de requests no deseados al verificar el secret key
    incoming_secret = request.headers.get("secret")
    my_secret = os.environ.get('LC_WEBHOOK_SECRET', None)
    if incoming_secret != my_secret:
        print(f"[WARNING] Secret inválido recibido: {incoming_secret}")
        return jsonify({"error": "Unauthorized"}), 401
    
    # Crea el token único por usuario para usar las APIs cada que corre el script
    pageGearToken = ""
    try:
        token_json_resp = get_token()
    except Exception as e:
        print("HUBO UN ERROR AL GENERAR EL TOKEN")
        print(f"{e}")
        os.system("pause")
    else:
        pageGearToken = token_json_resp['PageGearToken']
        print("¡TOKEN DE API OBTENIDO!")
    
    # Primero revisa si los datos recibidos contienen la estructura correcta
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No se proporcionaron datos"}), 400
        print("Callback recibido:", data)
        
        contexto = "contexto de ejemplo"
        sucursal = "sucursal de ejemplo"
        texto_respuesta = "respuesta de ejemplo"
        acciones = []
        
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
        edit_payload = {}
        contact_ID = data.get('inputs', {}).get('id_contacto')
        if contact_ID:
            # Pasamos el ID del contacto del cual queremos consultar el historial
            # Este se obtiene del webhook lanzado al transferir la convo al equipo de chatbots
            history_endpoint = "/history/conversations"
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
            if "74937" in tag_list.values():
                texto_respuesta = "¡Hola de nuevo! Le atiende Franny, una asistente virtual para la sucursal "+sucursal+" de *Froggin English for Kids* ⭐🐸📚\n"
                texto_respuesta += "\nEstoy aquí para contestar cualquier duda, ya sea por mensaje de texto o de voz, sobre nuestras divertidas clases de inglés para niños de *3 a 12 años* 🏫💚\n"

                contact_name = data.get('inputs', {}).get('nombre')
                convo_table = group_convo(pageGearToken, contact_ID, contact_name)
                contexto = summarize_convo(convo_table, contact_name)
                print("Contexto generado: "+contexto)

                texto_respuesta+= "\nPermítame confirmar los siguientes datos que nos compartió previamente:\n"
                texto_respuesta+=contexto+"\n"
                acciones.append({
                    "type": "sendText",
                    "text": texto_respuesta
                })

                delegate_user_id = 53958 # Franny Chatbot (Existentes)
                acciones.append({
                    "type": "userDelegate",
                    "id_user": delegate_user_id
                })

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
                valor_canal = data.get('chat', {}).get('id_canal')
                delegate_team_id = equipos_IDs.get(valor_canal, 1959) # Si no existe, se asigna a Atención Virtual (ID 1959)
                print(delegate_team_id)
                acciones.append({
                    "type": "teamDelegate",
                    "id_team": delegate_team_id
                })
        else:
            texto_respuesta = "¡Bienvenido! Le atiende Franny, una asistente virtual para la sucursal "+sucursal+" de *Froggin English for Kids* ⭐🐸📚\n"
            texto_respuesta += "\nEstoy aquí para contestar cualquier duda, ya sea por mensaje de texto o de voz, sobre nuestras divertidas clases de inglés para niños de *3 a 12 años* 🏫💚\n"
            acciones.append({
                "type": "sendText",
                "text": texto_respuesta
            })

            acciones.append({
                "type": "addTag",
                "id_tag": 74937
            })

            delegate_user_id = 53415 # Franny Chatbot (Nuevos)
            acciones.append({
                "type": "userDelegate",
                "id_user": delegate_user_id
            })

            chat_ID = data.get('chat', {}).get('id').strip()
            edit_payload = {
                "id": contact_ID,
                "dinamicos": {
                    "dinamicovmoXo1": sucursal
                },
                "id_chat": chat_ID
            }
            edit_contact(edit_payload, pageGearToken)
        
        # Esta es la respuesta que se regresa a LC con las acciones a realizar (mandar msj, delegar a chatbot/equipo)
        response = {
            "status": 1,
            "status_message": "Ok",
            "data": {
                "actions": acciones
            }
        }

        return jsonify(response)
    except Exception as e:
        print(e)
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(port=5000, debug=True)