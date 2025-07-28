#
# Versión 0.2
# Fecha: 25 de julio de 2025
#
# Autor: Helena Ruiz Ramírez
# Función: Llamar registros de conversaciones de la plataforma LiveConnect según ciertos parametros
#           de tiempos y etiquetas, para luego exportarlos a un archivo .csv
#
import os
import json
from pathlib import Path
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
convoID = os.environ.get('LC_CONVERSATION_ID', None)

# Los datos necesarios para hacer un request a LC de una conversación en específico
base_url = "https://api.liveconnect.chat/prod/"
convo_endpoint = "history/conversation"
convo_payload = { "id": convoID }
convo_participants = {}

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
        if dataframe.loc[x,'Interno'] == 1:
            dataframe.drop(x, inplace=True)
        else:
            user_id = int(dataframe.loc[x,'Usuario'])
            if user_id == 0:
                dataframe.loc[x,'Usuario'] = 'Sistema'
            else:
                dataframe.loc[x,'Usuario'] = convo_participants[user_id]
    dataframe.drop(['Interno'], axis=1, inplace=True)

# Crea el token único por usuario para usar las APIs cada que corre el script
json_resp = get_token()
pageGearToken = json_resp['PageGearToken']
print("\n"+json_resp['status_message']+"\n")

# Pasamos el contexto para jalar el historial de una conversacion
json_resp = get_liveconnect(convo_endpoint, convo_payload, pageGearToken)
print("\n"+json_resp['status_message']+"\n")

# Guarda en un diccionario el nombre completo del prospecto o papá
convo_participants[json_resp['data']['conversacion']['id_contacto']]=json_resp['data']['conversacion']['contacto']['nombre']
convo_participants[json_resp['data']['conversacion']['id_contacto']]+=' '
convo_participants[json_resp['data']['conversacion']['id_contacto']]+=json_resp['data']['conversacion']['contacto']['apellidos']

# Guarda en un diccionario los datos de las ADM que le respondieron
for x in json_resp['data']['participantes']:
    convo_participants[x['id_usuario']] = x['nombre']

# Acomoda los participantes y sus mensajes en una tabla que se exporta como .csv
# El nombre del archivo es el tag del prospecto/papá y se guarda en la carpeta de su unidad
# Finalmente intenta exportar la tabla a un .csv. Si hay un error, lo imprime a la consola
if json_resp['status'] > 0:
    df = pd.json_normalize(json_resp['data']['mensajes'])
    convo_table = pd.DataFrame(columns=['Usuario','Mensaje','Fecha','Interno'])
    convo_table['Usuario'] = df['id_remitente'].astype(object)
    convo_table['Mensaje'] = df['mensaje'].astype(object)
    convo_table['Fecha'] = df['fecha_add'].astype(object)
    convo_table['Interno'] = df['interno']

    switch_contact_ids(convo_table)

    canal = json_resp['data']['conversacion']['canalnombre']
    canal = Canales.from_value(canal).name
    path_name = '../data/convos/'+canal+'/'
    os.makedirs(path_name, exist_ok=True)

    try:
        convo_table.to_csv(path_name+json_resp['data']['conversacion']['contacto']['nombre']+'.csv', encoding='utf-8-sig')
    except IOError as e:
        print("\nHubo un error al crear el archivo: ", e)
        if e.args[0] == 13: print("Por favor cierre el archivo y vuélvalo a intentar.\n")
    else:
        print("\nEl archivo se creó con éxito\n")