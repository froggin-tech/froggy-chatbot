#
# Versión 0.1
# Fecha: 26 de agosto de 2025
#
# Autor: Helena Ruiz Ramírez
# Función: Determina el callback response al recibir un webhook de un chatbot. Por ahora, determina si el mensaje
#           entrante es de un contacto nuevo o ya existente según su historial de conversaciones.
#
from flask import Flask, request, jsonify
import requests
import os
from enum_canales import Canales, Sucursales


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
    response = requests.post("https://api.liveconnect.chat/prod/account/token", json=payload, headers=headers)
    return response.json()


# Función para consultar historial de un contacto
def get_liveconnect(endpoint, payload, pageGearToken):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "PageGearToken": pageGearToken
    }
    response = requests.post("https://api.liveconnect.chat/prod"+endpoint, json=payload, headers=headers)
    return response.json()


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
        
        sucursal = data.get('chat', {}).get('dinamicos', {}).get('dinamicovmoXo1', '').strip()
        if not sucursal:
            valor_canal = data.get('chat', {}).get('id_canal', '')
            if valor_canal:
                tag_sucursal = Canales.from_value(valor_canal).name
                print(tag_sucursal)
                sucursal = Sucursales.from_value(tag_sucursal).value
                print(sucursal)
            else:
                print("Error al solicitar la sucursal / nombre del canal")

        # Ahora, extrae el id del contacto del mensaje entrante para revisar si tiene historial > 0
        historial = False
        id_chatbot = 0
        nombre_chatbot = ""
        contact_id = data.get('inputs', {}).get('id_contacto')
        if contact_id:
            # Pasamos el ID del contacto del cual queremos consultar el historial
            # Este se obtiene del webhook lanzado al transferir la convo al equipo de chatbots
            history_endpoint = "/history/conversations"
            history_payload = { "id_contacto": contact_id }
            contact_history_json_resp = get_liveconnect(history_endpoint, history_payload, pageGearToken)
            if 'status' in contact_history_json_resp and contact_history_json_resp['status'] > 0:
                historial = True
                id_chatbot = 53958
                nombre_chatbot = "Franny Chatbot (Existentes)"
                print("Historial encontrado - Contacto existente")
            else:
                historial = False
                id_chatbot = 53415
                nombre_chatbot = "Franny Chatbot (Nuevos)"
                print("Historial no encontrado - Contacto nuevo")

        if historial:
            texto_respuesta = "¡Hola de nuevo! Le atiende Franny, una asistente virtual para la sucursal "+sucursal+" de *Froggin English for Kids* ⭐🐸📚\n"
            texto_respuesta += "\nEstoy aquí para contestar cualquier duda, ya sea por mensaje de texto o de voz, sobre nuestras divertidas clases de inglés para niños de *3 a 12 años* 🏫💚\n"
            
            valor_contexto = data.get('chat', {}).get('contacto', {}).get('dinamicos', {}).get('dinamicoQBTVa1', '').strip()
            if valor_contexto:
                if valor_contexto == "":
                    print("Contexto vacio")
                else:
                    print("Contexto encontrado: "+valor_contexto)
                    contexto = valor_contexto

                    texto_respuesta+= "\nPermítame confirmar los siguientes datos:\n"
                    texto_respuesta+=contexto+"\n"
            else:
                print("Error al obtener contexto del contacto")
        else:
            texto_respuesta = "¡Bienvenido! Le atiende Franny, una asistente virtual para la sucursal "+sucursal+" de *Froggin English for Kids* ⭐🐸📚\n"
            texto_respuesta += "\nEstoy aquí para contestar cualquier duda, ya sea por mensaje de texto o de voz, sobre nuestras divertidas clases de inglés para niños de *3 a 12 años* 🏫💚\n"
            
            contexto = ""
        
        chat_id = data.get('chat', {}).get('id').strip()
        edit_endpoint = "/contacts/edt"
        edit_payload = {
            "id": contact_id,
            "dinamicos": {
                "dinamicovmoXo1": sucursal,
                "dinamicoQBTVa1": contexto
            },
            "id_chat": chat_id
        }
        edit_contact_json_resp = get_liveconnect(edit_endpoint, edit_payload, pageGearToken)
        if 'status' in edit_contact_json_resp and edit_contact_json_resp['status'] < 0:
            print(edit_contact_json_resp['status_message'])
        else:
            print("Se editó el usuario")

        # Esta es la respuesta que se regresa a LC. La variable 'respuesta' varia.
        response = {
            "status": 1,
            "status_message": "Ok",
            "data": {
                "actions": [
                {
                    "type": "sendText",
                    "text": texto_respuesta
                },
                {
                    "type": "userDelegate",
                    "id_user": id_chatbot,
                    "name": nombre_chatbot
                }
                ]
            }
        }

        return jsonify(response)
    except Exception as e:
        print(e)
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(port=5000, debug=True)