#
# Versión 0.1
# Fecha: 26 de agosto de 2025
#
# Autor: Helena Ruiz Ramírez
# Función: Determina el callback response al recibir un webhook de un chatbot. Por ahora, determina si el mensaje
#           entrante es de un contacto nuevo o ya existente según su historial de conversaciones.
#
from xml.sax.handler import all_features
from flask import Flask, request, jsonify
import requests
import os


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
def get_contact_history(contact_id):
    # Crea el token único por usuario para usar las APIs cada que corre el script
    try:
        token_json_resp = get_token()
    except Exception as e:
        print("HUBO UN ERROR AL GENERAR EL TOKEN")
        print(f"{e}")
        os.system("pause")
    else:
        pageGearToken = token_json_resp['PageGearToken']
        print("¡TOKEN DE API OBTENIDO!")

    # Pasamos el ID del contacto del cual queremos consultar el historial
    # Este se obtiene del webhook lanzado al transferir la convo al equipo de chatbots
    payload = {
        "id_contacto": contact_id
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "PageGearToken": pageGearToken
    }

    response = requests.post("https://api.liveconnect.chat/prod/history/conversations", json=payload, headers=headers)
    return response.json()


@app.route("/", methods=["POST"])
def identify_contact():
    # Protege al servidor de requests no deseados al verificar el secret key
    incoming_secret = request.headers.get("secret")
    my_secret = os.environ.get('LC_WEBHOOK_SECRET', None)
    if incoming_secret != my_secret:
        print(f"[WARNING] Secret inválido recibido: {incoming_secret}")
        return jsonify({"error": "Unauthorized"}), 401
    
    # Primero revisa si los datos recibidos continen la estructura correcta
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No se proporcionaron datos"}), 400
        print("Callback recibido:", data)
        
        # Ahora, extrae el id del contacto del mensaje entrante para revisar si tiene historial > 0
        contact_id = data.get('chat', {}).get('contacto', {}).get('id_contacto')
        respuesta = "texto respuesta"
        if contact_id:
            contact_history_json_resp = get_contact_history(contact_id)
            if 'data' in contact_history_json_resp and len(contact_history_json_resp['data']) > 0:
                respuesta = "Historial encontrado - Contacto existente"
            else:
                respuesta = "Historial no encontrado - Contacto nuevo"
        print("Texto respuesta:", respuesta)

        # Esta es la respuesta que se regresa a LC. La variable 'respuesta' varia.
        response = {
            "status": 1,
            "status_message": "Ok",
            "data": {
                "actions": [
                    {
                        "type": "sendText",
                        "text": respuesta
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