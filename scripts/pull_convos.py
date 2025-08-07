#
# Versión 1.1
# Fecha: 06 de agosto de 2025
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
        user_id = int(dataframe.loc[x, 'Usuario'])
        if user_id == 0:
            dataframe.loc[x, 'Usuario'] = 'Sistema'
        else:
            try:
                dataframe.loc[x, 'Usuario'] = participants[user_id]
            except:
                # Si detecta un usuario que LC no registró como participante, lo busca externamente
                user_payload = {"id": user_id}
                user_json_resp = get_liveconnect("users/get", user_payload, token)
                dataframe.loc[x, 'Usuario'] = user_json_resp['data']['nombre']


def pull_conversations(total_convos_to_fetch, google_creds, first_convo, format_option, google_file_ids):
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
        "limit": total_convos_to_fetch,  # limite de 5 convos
    }
    # Todos los mensajes en una conversación
    messages_endpoint = "history/conversation"
    # Todas las ADM de una conversación
    participants_endpoint = "history/participants"

    # Crea el token único por usuario para usar las APIs cada que corre el script
    try:
        token_json_resp = get_token()
    except Exception as e:
        print("HUBO UN ERROR AL GENERAR EL TOKEN")
        print(f"{e}")
        os.system("pause")
        return
    else:
        pageGearToken = token_json_resp['PageGearToken']
        print("¡TOKEN DE API OBTENIDO!")

    # Pasamos el contexto para jalar el historial de conversaciones
    print("\n... PASO 2/3: BUSCANDO CONVERSACIONES EN LOS SERVIDORES DE LIVECONNECT ...")
    try:
        convos_json_resp = get_liveconnect(all_convos_endpoint, all_convos_payload, pageGearToken)
    except Exception as e:
        print("HUBO UN ERROR AL CONECTARSE CON LIVECONNECT")
        print(f"{e}")
        os.system("pause")
        return
    if 'data' not in convos_json_resp:
        print("HUBO UN ERROR AL CONECTARSE CON LIVECONNECT")
        if 'message' in convos_json_resp:
            print(f"{convos_json_resp['message']}")
        os.system("pause")
        return
    print("¡CONVERSACIONES OBTENIDAS!")

    # Cada 'x' aquí representa cada conversación
    print("\n... PASO 3/3: SUBIENDO CONVERSACIONES A GOOGLE SHEETS ...")
    convo_index = 1
    for x in convos_json_resp['data']:
        print(f"\nCONVERSACIÓN #{convo_index}")
        convo_id = 0  # ID único por conversación, no por historial del usuario
        convo_participants = {}  # Todos las ADM y el usuario de la conversación
        user_messages = []  # Para almacenar todas las conversaciones ligadas a un usuario

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
            participants_payload = {"id_conversacion": convo_id}
            participants_json_resp = get_liveconnect(participants_endpoint, participants_payload, pageGearToken)
            for z in participants_json_resp['data']:
                convo_participants[z['id_usuario']] = z['nombre']

            # Agrupa cada mensaje individual en la conversación
            messages_payload = {"id": convo_id}
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
        convo_table = pd.DataFrame(columns=['Usuario', 'Mensaje', 'Fecha', 'Interno'])
        convo_table['Usuario'] = df['id_remitente'].astype(object)
        convo_table['Mensaje'] = df['mensaje'].astype(object)
        convo_table['Fecha'] = df['fecha_add'].astype(object)
        convo_table['Interno'] = df['interno']

        # Ordena las filas por el timestamp de cada mensaje
        # Luego, vuelve a generar el índice de las filas del dataframe
        convo_table['Fecha'] = pd.to_datetime(convo_table['Fecha'], format='%Y-%m-%d %H:%M:%S')
        convo_table = convo_table.sort_values(by='Fecha')
        convo_table = convo_table.reset_index(drop=True)

        # Reemplaza los IDs de LiveConnect por el nombre del cliente o agente
        switch_contact_ids(convo_table, convo_participants, pageGearToken)

        # Reemplaza los espacios sin datos por un espacio vacio para evitar problemas al subir los datos
        convo_table = convo_table.infer_objects(copy=False).fillna('')

        # Encuentra los índices de las filas que son mensajes del sistema para darles formato
        system_message_index = convo_table.index[convo_table['Usuario'] == 'Sistema'].tolist()
        system_message_rows = [i+2 for i in system_message_index]

        # Finalmente intenta exportar la tabla a un .csv. Si hay un error, lo imprime a la consola
        # El nombre del archivo es el tag del prospecto/papá y se guarda en la carpeta de su unidad
        csv_buffer = io.StringIO()
        file_name = f"{unidad} {user_full_name}"
        try:
            convo_table.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
        except Exception as e:
            print(f"Hubo un error al guardar la conversación con '{file_name}' en csv")
            print(f"{e}")
            os.system("pause")
            return
        else:
            print(f"Se guardó la conversación de '{user_full_name}' en formato csv")
            if not upload_file_to_google(file_name, csv_buffer, google_creds, system_message_rows, format_option, google_file_ids):
                continue

        convo_index += 1

    print("\n¡TODAS LAS CONVERSACIONES FUERON GUARDADAS EXITOSAMENTE!")
    os.system("pause")
