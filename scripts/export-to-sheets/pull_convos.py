#
# Versión 1.3
# Fecha: 04 de septiembre de 2025
#
# Autor: Helena Ruiz Ramírez
# Función: Llamar registros de conversaciones de la plataforma LiveConnect según ciertos parametros
#           de tiempos y etiquetas, para luego exportarlos a un archivo .csv
#
import os
import io
from types import NoneType
from dotenv import load_dotenv
import pandas as pd
from upload_convos import *
from enum_equipos import Equipos
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.liveconnect_api import get_token, get_liveconnect, group_convo


def export_to_csv(unidad, user_full_name, convo_table, google_creds, system_message_rows, format_option, google_file_ids):
    # Intenta exportar la tabla a un .csv. Si hay un error, lo imprime a la consola
    # El nombre del archivo es el tag del prospecto/papá y se guarda en la carpeta de su unidad
    csv_buffer = io.StringIO()
    unidad = Equipos.from_value(unidad).name
    file_name = f"{unidad} {user_full_name}"
    try:
        convo_table.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
    except Exception as e:
        print(f"Hubo un error al guardar la conversación con '{file_name}' en csv")
        print(f"{e}")
        os.system("pause")
        return 1
    else:
        print(f"Se guardó la conversación de '{user_full_name}' en formato csv")
        if not upload_file_to_google(file_name, csv_buffer, google_creds, system_message_rows, format_option, google_file_ids):
            print(f"Hubo un error al subir la conversación '{file_name}' a Google Drive")
            os.system("pause")
            return 2
        else:
            return 0


def pull_conversations(total_convos_to_fetch, google_creds, first_convo, convos_option, format_option, google_file_ids):
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

    # Crea el token único por usuario para usar las APIs cada que corre el script
    token_json_resp = get_token()
    if 'PageGearToken' in token_json_resp:
        pageGearToken = token_json_resp['PageGearToken']
    else:
        return

    # Pasamos el contexto para jalar el historial de conversaciones
    print("\n... PASO 2/3: BUSCANDO CONVERSACIONES EN LOS SERVIDORES DE LIVECONNECT ...")
    messages_endpoint = "history/conversation" # Para obtener una conversación completa
    if convos_option == 1: # Una sola conversación
        messages_payload = {"id": first_convo}
        messages_json_resp = get_liveconnect(messages_endpoint, messages_payload, pageGearToken)
        if not messages_json_resp:
            return
    else: # Varias conversaciones
        convos_json_resp = get_liveconnect(all_convos_endpoint, all_convos_payload, pageGearToken)
        if not convos_json_resp:
            return
    print("¡CONVERSACIONES OBTENIDAS!")

    print("\n... PASO 3/3: SUBIENDO CONVERSACIONES A GOOGLE SHEETS ...")
    convo_index = 1
    if convos_option == 1: # Una sola conversación
        # Guarda en un diccionario el nombre completo del prospecto o papá
        messages_data = messages_json_resp['data']
        contacto = messages_data['conversacion']['contacto']
        user_full_name = contacto['nombre']
        if not isinstance(contacto['apellidos'], NoneType):
            user_full_name += ' '
            user_full_name += contacto['apellidos']
        id_contacto = messages_data['conversacion']['id_contacto']
        
        # Manda a llamar la función para agrupar todo el historial de conversaciones del usuario
        convo_table, unidad, system_message_rows = group_convo(pageGearToken, id_contacto, user_full_name, get_unidad=True, include_internal_msgs=True)

        result = export_to_csv(unidad, user_full_name, convo_table, google_creds, system_message_rows, format_option, google_file_ids) 
        if result != 0:
            os.system("pause")
            return
    else: # Varias conversaciones
        for x in convos_json_resp['data']:
            # Cada 'x' aquí representa cada conversación
            print(f"\nCONVERSACIÓN #{convo_index}")
            user_full_name = x['contacto']['nombre']
            if not isinstance(x['contacto']['apellidos'], NoneType):
                user_full_name += ' '
                user_full_name += x['contacto']['apellidos']
            id_contacto = x['id_contacto']

            # Manda a llamar la función para agrupar todo el historial de conversaciones del usuario
            convo_table, unidad, system_message_rows = group_convo(pageGearToken, id_contacto, user_full_name, get_unidad=True, include_internal_msgs=True)
            
            result = export_to_csv(unidad, user_full_name, convo_table, google_creds, system_message_rows, format_option, google_file_ids) 
            if result != 0:
                os.system("pause")
                return

            convo_index += 1

    print("\n¡TODAS LAS CONVERSACIONES FUERON GUARDADAS EXITOSAMENTE!")
    os.system("pause")