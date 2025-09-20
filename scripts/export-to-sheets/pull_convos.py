#
# Versión 2.1
# Fecha: 20 de septiembre de 2025
#
# Autor: Helena Ruiz Ramírez
# Función: Llamar registros de conversaciones de la plataforma LiveConnect según ciertos parametros
#           de tiempos y etiquetas, para luego exportarlos a un archivo .csv
#
import io
import streamlit as st
from types import NoneType
import pandas as pd
from upload_convos import *
from utils.liveconnect_api import get_token, get_liveconnect, group_convo
from utils.enum_liveconnect import Canales


def export_to_csv(canal, user_full_name, convo_table, google_creds, system_message_rows, format_option, google_file_ids, logs, log_container):
    # Intenta exportar la tabla a un .csv. Si hay un error, lo imprime a la consola
    # El nombre del archivo es el tag del prospecto/papá y se guarda en la carpeta de su unidad
    csv_buffer = io.StringIO()
    unidad = Canales.from_value(canal).name
    file_name = f"{unidad} {user_full_name}"
    try:
        convo_table.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
    except Exception as e:
        update_logs(logs, log_container, f"Hubo un error al guardar la conversación con '{file_name}' en csv: {e}")
        return False
    else:
        update_logs(logs, log_container, f"Se guardó la conversación de '{user_full_name}' en formato csv")
        if not upload_file_to_google(file_name, csv_buffer, google_creds, system_message_rows, format_option, google_file_ids, logs, log_container):
            update_logs(logs, log_container, f"Hubo un error al subir la conversación '{file_name}' a Google Drive")
            return False
        else:
            return True


def pull_conversations(total_convos_to_fetch, google_creds, first_convo, convos_option, format_option, google_file_ids):
    # Quita los límites de las tablas
    pd.set_option('display.max_colwidth', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_columns', None)

    # Los datos necesarios para hacer un request a LC
    all_convos_endpoint = "history/conversations"
    all_convos_payload = {
        "initFrom": first_convo,
        "limit": total_convos_to_fetch,  # limite de 5 convos
    }

    with st.spinner("... PASO 1/3: GENERANDO TOKEN PARA AUTORIZAR LA CONEXIÓN A LIVECONNECT ..."):
        # Crea el token único por usuario para usar las APIs cada que corre el script
        token_json_resp = get_token()
        if 'PageGearToken' in token_json_resp:
            pageGearToken = token_json_resp['PageGearToken']
        else:
            st.error("No se pudo obtener el token de LiveConnect.")
            return
    st.success("¡Token de API de LiveConnect obtenido!")

    # Pasamos el contexto para jalar el historial de conversaciones
    with st.spinner("... PASO 2/3: BUSCANDO CONVERSACIONES EN LOS SERVIDORES DE LIVECONNECT ..."):
        messages_endpoint = "history/conversation" # Para obtener una conversación completa
        if convos_option == 1: # Una sola conversación
            messages_payload = {"id": first_convo}
            messages_json_resp = get_liveconnect(messages_endpoint, messages_payload, pageGearToken)
            if not messages_json_resp:
                st.error("No se pudo obtener la conversación de LiveConnect.")
                return
        else: # Varias conversaciones
            convos_json_resp = get_liveconnect(all_convos_endpoint, all_convos_payload, pageGearToken)
            if not convos_json_resp:
                st.error("No se pudieron obtener las conversaciones de LiveConnect.")
                return
    st.success("¡Conversaciones obtenidas!")

    with st.spinner("... PASO 3/3: SUBIENDO CONVERSACIONES A GOOGLE SHEETS ..."):
        progress_bar = st.progress(0)
        convos_progress = 1 if convos_option == 1 else len(convos_json_resp['data'])
        
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
            convo_table, canal, system_message_rows = group_convo(pageGearToken, id_contacto, user_full_name, get_canal=True, include_internal_msgs=True)

            result = export_to_csv(canal, user_full_name, convo_table, google_creds, system_message_rows, format_option, google_file_ids)
            if not result:
                return
            progress_bar.progress(1.0)
        else: # Varias conversaciones
            log_container = st.empty()
            logs = []
            for i, x in enumerate(convos_json_resp['data']):
                new_log = f"Agrupando la conversación #{i+1}..."
                update_logs(logs, log_container, new_log)

                # Cada 'x' aquí representa cada conversación
                user_full_name = x['contacto']['nombre']
                if not isinstance(x['contacto']['apellidos'], NoneType):
                    user_full_name += ' '
                    user_full_name += x['contacto']['apellidos']
                id_contacto = x['id_contacto']

                # Manda a llamar la función para agrupar todo el historial de conversaciones del usuario
                convo_table, canal, system_message_rows = group_convo(pageGearToken, id_contacto, user_full_name, get_canal=True, include_internal_msgs=True)
                
                result = export_to_csv(canal, user_full_name, convo_table, google_creds, system_message_rows, format_option, google_file_ids, logs, log_container)
                if not result:
                    st.error(f"Se detuvo el proceso en la conversación #{i+1}.")
                    return

                progress_bar.progress((i + 1) / convos_progress)
    st.success("¡Todas las conversaciones fueron guardadas exitosamente!")