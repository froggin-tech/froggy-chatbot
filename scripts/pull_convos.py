#
# Versión 1.0
# Fecha: 31 de julio de 2025
#
# Autor: Helena Ruiz Ramírez
# Función: Llamar registros de conversaciones de la plataforma LiveConnect según ciertos parametros
#           de tiempos y etiquetas, para luego exportarlos a un archivo .csv
#
import os
import io
from pathlib import Path
from types import NoneType
from dotenv import load_dotenv
import requests
import pandas as pd
from enum_equipos import Equipos
from upload_convos import *

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

# Método general para requests a LC
def get_liveconnect(lc_endpoint, lc_payload, token):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "PageGearToken": token
    }
    response = requests.post("https://api.liveconnect.chat/prod/"+lc_endpoint, json=lc_payload, headers=headers)
    return response.json()

# Cambia los IDs por los nombres de los usuarios e indica cuales son de parte del sistema
def switch_contact_ids(dataframe, participants, token):
    for x in dataframe.index:
        user_id = int(dataframe.loc[x,'Usuario'])
        if user_id == 0:
            dataframe.loc[x,'Usuario'] = 'Sistema'
        else:
            try:
                dataframe.loc[x,'Usuario'] = participants[user_id]
            except:
                # Si detecta un usuario que LC no registró como participante, lo busca externamente
                user_payload = { "id": user_id }
                user_json_resp = get_liveconnect("users/get", user_payload, token)
                dataframe.loc[x,'Usuario'] = user_json_resp['data']['nombre']

def pull_conversations(limit_of_convos_to_pull, google_creds, first_convo=0):
    # Quita los límites de las tablas
    pd.set_option('display.max_colwidth', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_columns', None)

    # Carga el archivo .env con todos los secrets necesarios
    load_dotenv()

    # Los datos necesarios para hacer un request a LC
    all_convos_endpoint = "history/conversations"
    all_convos_payload = {
        "initFrom": first_convo,
        "limit": limit_of_convos_to_pull, # limite de 5 convos
    }
    messages_endpoint = "history/conversation" # Todos los mensajes en una conversación
    participants_endpoint = "history/participants" # Todas las ADM de una conversación

    # Crea el token único por usuario para usar las APIs cada que corre el script
    token_json_resp = get_token()
    pageGearToken = token_json_resp['PageGearToken']

    # Pasamos el contexto para jalar el historial de conversaciones
    try:
        convos_json_resp = get_liveconnect(all_convos_endpoint, all_convos_payload, pageGearToken)
    except:
        print("\n"+convos_json_resp['status_message']+"\n")
        quit()

    # Cada 'x' aquí representa cada conversación
    for x in convos_json_resp['data']:
        convo_id = 0 # ID único por conversación, no por historial del usuario
        convo_participants = {} # Todos las ADM y el usuario de la conversación
        user_messages = [] # Para almacenar todas las conversaciones ligadas a un usuario

        # Guarda en un diccionario el nombre completo del prospecto o papá
        user_full_name = x['contacto']['nombre']
        if not isinstance(x['contacto']['apellidos'], NoneType):
            user_full_name += ' '
            user_full_name += x['contacto']['apellidos']
        convo_participants[x['id_contacto']] = user_full_name

        # Primero, hay que agrupar todas las conversaciones ligadas a un usuario
        all_user_convos_payload = {
            "id_contacto": x['id_contacto']
        }
        all_user_convos_json_resp = get_liveconnect(all_convos_endpoint, all_user_convos_payload, pageGearToken)
        index = 1
        for y in all_user_convos_json_resp['data']:
            # Guarda en un diccionario los datos de las ADM que atendieron la conversacion
            convo_id = y['id']
            participants_payload = { "id_conversacion": convo_id }
            participants_json_resp = get_liveconnect(participants_endpoint, participants_payload, pageGearToken)
            for z in participants_json_resp['data']:
                convo_participants[z['id_usuario']] = z['nombre']

            # Agrupa cada mensaje individual en la conversación
            messages_payload = { "id": convo_id }
            messages_json_resp = get_liveconnect(messages_endpoint, messages_payload, pageGearToken)
            for z in messages_json_resp['data']['mensajes']:
                user_messages.append(z)

            # Checa si está revisando la conversación más reciente, osea la primera en la búsqueda
            if index == 1:
                # Extrae la unidad según el último grupo/equipo asignado a la conversación
                unidad = y['grupo']
                unidad = Equipos.from_value(unidad).name
                index -= 1

        # Guarda la lista de todos los mensajes en un dataframe normalizado
        df = pd.json_normalize(user_messages)

        # Crea una tabla donde almacenar los mensajes de manera ordenada y por fecha
        convo_table = pd.DataFrame(columns=['Usuario','Mensaje','Fecha','Interno'])
        convo_table['Usuario'] = df['id_remitente'].astype(object)
        convo_table['Mensaje'] = df['mensaje'].astype(object)
        convo_table['Fecha'] = df['fecha_add'].astype(object)
        convo_table['Interno'] = df['interno']
        convo_table = convo_table.sort_values(by='Fecha')

        # Reemplaza los IDs de LiveConnect por el nombre del cliente o agente
        switch_contact_ids(convo_table, convo_participants, pageGearToken)

        convo_table = convo_table.infer_objects(copy=False).fillna('')

        # Finalmente intenta exportar la tabla a un .csv. Si hay un error, lo imprime a la consola
        # El nombre del archivo es el tag del prospecto/papá y se guarda en la carpeta de su unidad
        csv_buffer = io.StringIO()
        file_name = f"{unidad} {user_full_name}"
        try:
            convo_table.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
        except:
            print(f"\nHubo un error al guardar la conversación con '{file_name}'")
            del df
            del convo_table
        else:
            upload_file_to_google(file_name, csv_buffer, google_creds)

        # Borra las tablas antes de moverse a la siguiente conversación
        del df
        del convo_table