#
# Versión 1.1
# Fecha: 20 de septiembre de 2025
#
# Autores: Helena Ruiz Ramírez, Pablo Andrés Ruiz Ramírez
# Función: Crear spreadsheets a partir de un .csv y colocarlos en un designado folder de Google Drive
#           El archivo se crea con OAuth. Es necesario dar permisos de aplicación cada vez que se corre este script
#
import gspread
import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from format_convos import apply_formatting
from utils.enum_liveconnect import Unidades
from utils.google_api import execute_api_operation


# Usa HTML para crear un contenedor que automáticamente scrollea hacia abajo
# Agrupa los logs (texto debug) que van saliendo en un solo string, con un breakline entre cada uno
# Luego, usa JavaScript para asignar que el "tope" del scroll sea la altura, osea hasta el final
# Por último, traduce el string a formato Markdown para visualizar en el app de streamlit
def update_logs(logs, log_container, new_log):
    logs.insert(0, new_log)
    log_html = f"""
    <div id="log-container" style="height: 180px; overflow-y: scroll; border: 1px solid #ccc; padding: 10px; border-radius: 5px; margin-bottom: 1em;">
        {'<br>'.join(logs)}
    </div>
    """
    log_container.markdown(log_html, unsafe_allow_html=True)


# Determina si hay que crear archivos/spreadsheets o crear pestañas/hojas según la solicitud del usuario
def upload_file_to_google(ssheet_name, csv_buffer, google_creds, system_message_rows, format_option, logs, log_container):
    # Guarda los datos del csv buffer en una tabla para un spreadsheet
    try:
        csv_buffer.seek(0)
        df = pd.read_csv(csv_buffer, na_filter=False)
    except Exception as e:
        update_logs(logs, log_container, f"Hubo un error al convertir la conversación de '{ssheet_name}' a csv: {e}")
        return False
    values = [df.columns.tolist()] + df.values.tolist()

    # Separa el buffer en el tag de la unidad y el nombre completo del contacto
    # Los primeros tres caracteres siempre van a ser la unidad. Esto se asigna en las líneas 129 y 149 de pull_convos.py
    csv_unidad = ssheet_name[0:3]
    ssheet_name = ssheet_name[4:]
    csv_unidad = Unidades(csv_unidad).name

    if format_option == 1:
        # Carga el archivo .env con todos los secrets necesarios para obtener la carpeta en GDrive
        load_dotenv()
        folder_name = "G_FOLDER_ID_" + csv_unidad
        try:
            ssheet_folder_id = os.environ.get(folder_name, None)
        except:
            # Si por alguna razón la carpeta indicada no existe, se sube a la de respaldo
            csv_unidad = Unidades("DEF").name
            folder_name = "G_FOLDER_ID_" + csv_unidad
            ssheet_folder_id = os.environ.get(folder_name, None)

        # Si el contacto ya tenía un archivo, se actualiza
        # Si no lo encuentra, entonces crea un nuevo sheet
        try:
            ssheet = execute_api_operation(google_creds.open, ssheet_name)
        except gspread.exceptions.SpreadsheetNotFound:
            ssheet = execute_api_operation(google_creds.create, ssheet_name, ssheet_folder_id)
            worksheet = execute_api_operation(ssheet.add_worksheet, title="00 Conversación", rows=df.shape[0], cols=df.shape[1])
            execute_api_operation(ssheet.del_worksheet, ssheet.sheet1)
        worksheet = execute_api_operation(ssheet.worksheet, "00 Conversación")
    else:
        # Carga el archivo .env con todos los secrets necesarios para obtener el archivo BASE en GDrive
        load_dotenv()
        file_name = "G_FILE_ID_" + csv_unidad
        try:
            ssheet_id = os.environ.get(file_name, None)
        except:
            # Si por alguna razón el archivo indicado no existe, se sube al de respaldo
            csv_unidad = Unidades("DEF").name
            file_name = "G_FILE_ID_" + csv_unidad
            ssheet_id = os.environ.get(file_name, None)
        
        # Guardar data en una pestaña del archivo de la unidad ya existente
        try:
            ssheet = execute_api_operation(google_creds.open_by_key, ssheet_id)
        except Exception as e:
            st.error(f"No se encontró el ID del spreadsheet para '{csv_unidad}': {e}")
            return False
        else:
            try:
                worksheet = execute_api_operation(ssheet.worksheet, ssheet_name)
            except gspread.WorksheetNotFound:
                worksheet = execute_api_operation(ssheet.add_worksheet, title=ssheet_name, rows=df.shape[0], cols=df.shape[1])
    execute_api_operation(worksheet.clear)
    execute_api_operation(worksheet.update, values)
    apply_formatting(worksheet, system_message_rows)
    update_logs(logs, log_container, f"Se subió la conversación de '{ssheet_name}' a Google Sheets en {csv_unidad}")
    return True