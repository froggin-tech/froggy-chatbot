#
# Versión 1.1
# Fecha: 20 de septiembre de 2025
#
# Autor: Helena Ruiz Ramírez
# Función: Módulo para centralizar las funciones de la API de LiveConnect
#
import os
import pandas as pd
import requests


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
    response_json = {}
    try:
        response = requests.post("https://api.liveconnect.chat/prod/account/token", json=payload, headers=headers, timeout=10)
    except Exception as e:
        print("HUBO UN ERROR AL GENERAR EL TOKEN")
        print(f"{e}")
        os.system("pause")
        return response_json
    else:
        print("¡TOKEN DE API OBTENIDO!")
        response_json = response.json()
        return response_json


# Función para hacer un API request a LiveConnect. Varía según el endpoint y payload
def get_liveconnect(endpoint, payload, pageGearToken):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "PageGearToken": pageGearToken
    }
    response_json = {}
    try:
        response = requests.post("https://api.liveconnect.chat/prod/"+endpoint, json=payload, headers=headers, timeout=10)
    except Exception as e:
        print("HUBO UN ERROR AL CONECTARSE CON LIVECONNECT")
        print(f"{e}")
        os.system("pause")
    else:
        response_json = response.json()
        if 'data' not in response_json:
            print("NO SE ENCONTRARON LOS DATOS EN LIVECONNECT")
            if 'message' in response_json:
                print(f"{response_json['message']}")
            response_json = {}
            os.system("pause")
    return response_json


# Edita los datos del contacto especificados dentro del payload
def edit_contact(payload, pageGearToken):
    endpoint = "contacts/edt"
    edit_contact_json_resp = get_liveconnect(endpoint, payload, pageGearToken)
    if 'status' in edit_contact_json_resp and edit_contact_json_resp['status'] < 0:
        print(edit_contact_json_resp['status_message'])
    else:
        print("Se editó el usuario")


# Cambia los IDs por los nombres de los usuarios e indica cuales son de parte del sistema
def switch_contact_ids(dataframe, participants, pageGearToken):
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
                user_json_resp = get_liveconnect("users/get", user_payload, pageGearToken)
                if user_json_resp:
                    try:
                        dataframe.loc[x, 'Usuario'] = user_json_resp['data']['nombre']
                    except:
                        dataframe.loc[x, 'Usuario'] = "Usuario No Encontrado"


# Agrupa todas las conversaciones asociadas a un contacto y las ordena en un dataframe por usuario, mensaje, fecha y visibilidad
# get_canal: Si se quiere obtener el canal a partir de la conversación más reciente
# include_internal_msgs: Si se quieren incluir los mensajes 'internos' en la agrupación
# message_limit: Si se quiere limitar el número de mensajes a incluir en la agrupación
def group_convo(pageGearToken, contact_ID, contact_name, get_canal=False, include_internal_msgs=False, message_limit=None):
    convo_participants = {} # Todos las ADM y el usuario de la conversación
    convo_participants[contact_ID] = contact_name # Agrega como 1er participante al contacto

    all_convos_endpoint = "history/conversations"
    all_user_convos_payload = { "id_contacto": contact_ID }
    all_user_convos_json_resp = get_liveconnect(all_convos_endpoint, all_user_convos_payload, pageGearToken)

    participants_endpoint = "history/participants"
    convo_endpoint = "history/conversation"
    messages_data = [] # Para después almacenar todas las conversaciones ligadas a un usuario
    system_message_rows = [] # Para después almacenar el número de cada fila con mensajes del 'Sistema'
    convo_table = [] # Para después almacenar la conversación en formato de tabla
    canal = '' # Para después guardar el canal asociado con el contacto y escribirlo en el título del archivo
    if 'data' in all_user_convos_json_resp:
        index = 1
        for x in all_user_convos_json_resp['data']:
            temp_ID = x['id']

            # Guarda en un diccionario los datos de las ADM que atendieron la conversacion
            participants_payload = {"id_conversacion": temp_ID}
            participants_json_resp = get_liveconnect(participants_endpoint, participants_payload, pageGearToken)
            if 'data' in participants_json_resp:
                for y in participants_json_resp['data']:
                    convo_participants[y['id_usuario']] = y['nombre']
            else:
                print("HUBO UN ERROR AL OBTENER LOS PARTICIPANTES DE LA CONVERSACIÓN")

            # Agrupa cada mensaje individual en la conversación
            messages_payload = {"id": temp_ID}
            messages_json_resp = get_liveconnect(convo_endpoint, messages_payload, pageGearToken)
            if 'data' in messages_json_resp and 'mensajes' in messages_json_resp['data']:
                for y in messages_json_resp['data']['mensajes']:
                    if include_internal_msgs or (y['id_remitente'] != 0 and y['interno'] == 0):
                        # Se salta los mensajes irrelevantes (msjs del sistema o internos) de ser necesario
                        messages_data.append(y)
            else:
                print("HUBO UN ERROR AL OBTENER LOS MENSAJES DE LA CONVERSACIÓN")
            
            # Checa si está revisando la conversación más reciente, osea la primera en la búsqueda
            if index == 1:
                canal = x['id_canal']
                index -=1

        # Para que solo analice los mensajes más recientes según el máximo establecido
        if message_limit and len(messages_data) > message_limit:
            messages_data = messages_data[-message_limit:]

        # Guarda la lista de todos los mensajes en un dataframe normalizado
        df = pd.json_normalize(messages_data)

        # Crea una tabla donde almacenar los mensajes de manera ordenada y por fecha
        columns = ['Usuario', 'Mensaje', 'Fecha']
        if include_internal_msgs:
            # Solo incluye la columna de 'interno' si es necesario
            columns.append('Interno')
        convo_table = pd.DataFrame(columns=columns)
        if not df.empty:
            # Indicamos cuál valor del json/dataframe corresponde a las columnas de la tabla
            convo_table['Usuario'] = df['id_remitente'].astype(object)
            convo_table['Mensaje'] = df['mensaje'].astype(object)
            convo_table['Fecha'] = df['fecha_add'].astype(object)
            if include_internal_msgs:
                convo_table['Interno'] = df['interno']

            # Ordena las filas por el timestamp de cada mensaje
            # Luego, vuelve a generar el índice de las filas del dataframe
            convo_table['Fecha'] = pd.to_datetime(convo_table['Fecha'], format='%Y-%m-%d %H:%M:%S')
            convo_table = convo_table.sort_values(by='Fecha')
            convo_table = convo_table.reset_index(drop=True)

            # Reemplaza los IDs de LiveConnect por el nombre del cliente o agente
            switch_contact_ids(convo_table, convo_participants, pageGearToken)

            # Encuentra los índices de las filas que son mensajes del sistema para darles formato
            if include_internal_msgs:
                system_message_index = convo_table.index[convo_table['Usuario'] == 'Sistema'].tolist()
                system_message_rows = [i+2 for i in system_message_index]

            # Reemplaza los espacios sin datos por un espacio vacio para evitar problemas al subir los datos
            convo_table = convo_table.infer_objects(copy=False).fillna('')
    else:
        print("HUBO UN ERROR AL OBTENER LAS CONVERSACIONES DEL USUARIO")

    if get_canal:
        return convo_table, canal, system_message_rows
    else:
        return convo_table