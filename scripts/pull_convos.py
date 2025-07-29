#
# Versión 0.3
# Fecha: 29 de julio de 2025
#
# Autor: Helena Ruiz Ramírez
# Función: Llamar registros de conversaciones de la plataforma LiveConnect según ciertos parametros
#           de tiempos y etiquetas, para luego exportarlos a un archivo .csv
#
import os
import json
from pathlib import Path
from types import NoneType
from dotenv import load_dotenv
import requests
import pandas as pd
from enum_canales import Canales

# Quita los límites de las tablas
pd.set_option('display.max_colwidth', None)
pd.set_option('display.width', None)
pd.set_option('display.max_columns', None)

# Carga el archivo .env con todos los secrets necesarios
load_dotenv()
ckey = os.environ.get('LC_C_KEY', None)
privateKey = os.environ.get('LC_PRIVATE_KEY', None)
#convoID = os.environ.get('LC_CONVERSATION_ID', None)

# Los datos necesarios para hacer un request a LC
base_url = "https://api.liveconnect.chat/prod/"

limit_of_convos_to_pull = 5
all_convos_endpoint = "history/conversations"
all_convos_payload = {
    "initFrom": 0,
    "limit": limit_of_convos_to_pull, # limite de 5 convos
}

messages_endpoint = "history/conversation" # Todos los mensajes en una conversación
participants_endpoint = "history/participants" # Todas las ADM de una conversación
user_endpoint = "users/get" # Los datos del usuario de una ADM

convo_participants = {} # Todos las ADM y el usuario de la conversación
convo_id = " " # ID único por conversación, no por historial del usuario


# Regresa el token de autorización para LC
def get_token():
    endpoint = "account/token"
    payload = {
        "cKey": ckey,
        "privateKey": privateKey
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, application/xml"
    }
    response = requests.post(base_url+endpoint, json=payload, headers=headers)
    return response.json()

# Método general para requests a LC
def get_liveconnect(lc_endpoint, lc_payload, token):
    endpoint = lc_endpoint
    payload = lc_payload
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "PageGearToken": token
    }
    response = requests.post(base_url+endpoint, json=payload, headers=headers)
    return response.json()

# Cambia los IDs por los nombres de los usuarios e indica cuales son de parte del sistema
def switch_contact_ids(dataframe):
    for x in dataframe.index:
        if dataframe.loc[x,'Interno'] == 0:
            user_id = int(dataframe.loc[x,'Usuario'])
            if user_id == 0:
                dataframe.loc[x,'Usuario'] = 'Sistema'
            else:
                try:
                    dataframe.loc[x,'Usuario'] = convo_participants[user_id]
                except:
                    # Si detecta un usuario que LC no registró como participante, lo busca externamente
                    user_payload = { "id": user_id }
                    user_json_resp = get_liveconnect(user_endpoint, user_payload, pageGearToken)
                    dataframe.loc[x,'Usuario'] = user_json_resp['data']['nombre']
    #dataframe.drop(['Interno'], axis=1, inplace=True)

# Crea el token único por usuario para usar las APIs cada que corre el script
token_json_resp = get_token()
pageGearToken = token_json_resp['PageGearToken']
print("\n"+token_json_resp['status_message']+"\n")

# Pasamos el contexto para jalar el historial de conversaciones
try:
    convos_json_resp = get_liveconnect(all_convos_endpoint, all_convos_payload, pageGearToken)
    print("\n"+convos_json_resp['status_message']+"\n")
except:
    quit()

# Cada 'x' aquí representa cada conversación
for x in convos_json_resp['data']:
    # Guarda en un diccionario el nombre completo del prospecto o papá
    user_full_name = x['contacto']['nombre']
    if not isinstance(x['contacto']['apellidos'], NoneType):
        user_full_name += ' '
        user_full_name += x['contacto']['apellidos']
    convo_participants[x['id_contacto']] = user_full_name

    # Guarda en un diccionario los datos de las ADM que le respondieron
    convo_id = x['id']
    participants_payload = { "id_conversacion": convo_id }
    participants_json_resp = get_liveconnect(participants_endpoint, participants_payload, pageGearToken)
    for y in participants_json_resp['data']:
        convo_participants[y['id_usuario']] = y['nombre']

    # Acomoda los participantes y sus mensajes en una tabla que se exporta como .csv
    # El nombre del archivo es el tag del prospecto/papá y se guarda en la carpeta de su unidad
    # Finalmente intenta exportar la tabla a un .csv. Si hay un error, lo imprime a la consola
    messages_payload = { "id": convo_id }
    messages_json_resp = get_liveconnect(messages_endpoint, messages_payload, pageGearToken)
    df = pd.json_normalize(messages_json_resp['data']['mensajes'])
    convo_table = pd.DataFrame(columns=['Usuario','Mensaje','Fecha','Interno'])
    convo_table['Usuario'] = df['id_remitente'].astype(object)
    convo_table['Mensaje'] = df['mensaje'].astype(object)
    convo_table['Fecha'] = df['fecha_add'].astype(object)
    convo_table['Interno'] = df['interno']

    switch_contact_ids(convo_table)

    # Extrae la unidad según el canal de la conversación
    canal = x['canalnombre']
    canal = Canales.from_value(canal).name
    path_name = '../data/convos/'+canal+'/'
    os.makedirs(path_name, exist_ok=True)

    # Convierte la tabla con todos los mensajes a un archivo .csv
    try:
        convo_table.to_csv(f"{path_name}[{canal[0:3]}] {user_full_name}.csv", encoding='utf-8-sig')
    except IOError as e:
        print(f"\nHubo un error al crear el archivo '{user_full_name}': {e}")
        if e.args[0] == 13: print("Por favor cierre el archivo y vuélvalo a intentar.\n")
    else:
        print(f"\nEl archivo '{user_full_name}' se creó con éxito\n")

    convo_participants.clear()
    del df
    del convo_table