#
# Versión 0.4
# Fecha: 15 de agosto de 2025
#
# Autores: Helena Ruiz Ramírez, Pablo Andrés Ruiz Ramírez
# Función: Crear spreadsheets a partir de un .csv y colocarlos en un designado folder de Google Drive
#           El archivo se crea con OAuth. Es necesario dar permisos de aplicación cada vez que se corre este script
#
import os
import pandas as pd
from dotenv import load_dotenv
from format_convos import apply_formatting
from enum_unidades import Unidades


def upload_file_to_google(ssheet_name, csv_buffer, google_creds, system_message_rows, format_option, google_file_ids):
    # Guarda los datos del csv buffer en una tabla para un spreadsheet
    try:
        csv_buffer.seek(0)
        df = pd.read_csv(csv_buffer, na_filter=False)
    except Exception as e:
        print(f"Hubo un error al subir la conversación de '{ssheet_name}' a Google Sheets")
        print(f"{e}")
        os.system("pause")
        return
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
            ssheet = google_creds.open(ssheet_name)
        except:
            ssheet = google_creds.create(ssheet_name, ssheet_folder_id)
            worksheet = ssheet.add_worksheet(title="00 Conversación", rows=df.shape[0], cols=df.shape[1])
            ssheet.del_worksheet(ssheet.sheet1)
        worksheet = ssheet.worksheet("00 Conversación")
    else:
        # guardar data en una pestaña del archivo de la unidad ya existente
        ssheet_id = google_file_ids[csv_unidad]
        try:
            ssheet = google_creds.open_by_key(ssheet_id)
        except:
            print(f"No se encontró el ID del spreadsheet para '{csv_unidad}'")
            print(f"{e}")
            os.system("pause")
        else:
            worksheet = ssheet.add_worksheet(title=ssheet_name, rows=df.shape[0], cols=df.shape[1])
    worksheet.clear()
    worksheet.update(values)
    apply_formatting(worksheet, system_message_rows)
    print(f"Se subió la conversación de '{ssheet_name}' a Google Sheets")
    return True