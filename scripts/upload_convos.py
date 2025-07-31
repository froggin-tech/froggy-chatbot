#
# Versión 0.2
# Fecha: 31 de julio de 2025
#
# Autores: Helena Ruiz Ramírez, Pablo Andrés Ruiz Ramírez
# Función: Crear spreadsheets a partir de un .csv y colocarlos en un designado folder de Google Drive
#           El archivo se crea con OAuth. Es necesario dar permisos de aplicación cada vez que se corre este script
#
import os
import pandas as pd
from dotenv import load_dotenv
from enum_unidades import Unidades

def upload_file_to_google(ssheet_name, csv_buffer, google_creds):
    # Carga el archivo .env con todos los secrets necesarios
    load_dotenv()

    # Separa el buffer en el tag de la unidad y el nombre completo del contacto
    # Los primeros tres caracteres siempre van a ser la unidad. Esto se asigna en las líneas 129 y 149 de pull_convos.py
    csv_unidad = ssheet_name[0:3]
    ssheet_name = ssheet_name[4:]

    # Si por alguna razón la carpeta indicada no existe, se sube a la de respaldo
    csv_unidad = Unidades(csv_unidad).name
    folder_name = "G_FOLDER_ID_"+ csv_unidad
    try:
        ssheet_folder_id = os.environ.get(folder_name, None)
    except:
        csv_unidad = Unidades("DEF").name
        folder_name = "G_FOLDER_ID_"+ csv_unidad
        ssheet_folder_id = os.environ.get(folder_name, None)

    # Guarda los datos del csv buffer en una tabla para un spreadsheet
    try:
        csv_buffer.seek(0)
        df = pd.read_csv(csv_buffer, na_filter=False)
    except:
        print(f"\nHubo un error al obtener los datos de '{ssheet_name}'")
    values = [df.columns.tolist()] + df.values.tolist()

    # Si el contacto ya tenía un archivo, se actualiza
    # Si no lo encuentra, entonces crea un nuevo sheet
    try:
        ssheet = google_creds.open(ssheet_name)
    except:
        ssheet = google_creds.create(ssheet_name, ssheet_folder_id)
        worksheet = ssheet.add_worksheet(title="00 Conversación", rows=df.shape[0], cols=df.shape[1])
        ssheet.del_worksheet(ssheet.sheet1)
    worksheet = ssheet.worksheet("00 Conversación")
    worksheet.clear()
    worksheet.update(values)