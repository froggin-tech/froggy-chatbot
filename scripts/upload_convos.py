#
# Versión 0.1
# Fecha: 25 de julio de 2025
#
# Autores: Helena Ruiz Ramírez, Pablo Andrés Ruiz Ramírez
# Función: Crear spreadsheets a partir de un .csv y colocarlos en un designado folder de Google Drive
#           El archivo se crea con OAuth. Es necesario dar permisos de aplicación cada vez que se corre este script
#
import os
import json
import pandas as pd
from dotenv import load_dotenv
import gspread
from enum_unidades import Unidades

# Carga el archivo .env con los secretos
load_dotenv()

# Busca el archivo .csv a subir segun su nombre
ssheet_name = os.environ.get('G_FILE_NAME', None)

# Si el nombre del archivo, o etiqueta, tiene doble tag (AZL, VRD< AMA, etc), las elimina
# Elimina caracteres hasta que solo exista un espacio, que es el que esta entre el tag y el ID numérico
csv_unidad = ssheet_name
while csv_unidad.count(' ') > 1:
    csv_unidad = csv_unidad[1:]

# Se extrae el caracter del tag que representa la unidad, para después obtener el nombre completo
# Con el nombre compoleto, se jala del .env el ID de la carpeta en GDrive de esa unidad
temp = -1
for chr in csv_unidad:
    # Se detiene al encontrar el primer dígito
    if chr.isdigit():
        temp = csv_unidad.index(chr)
        csv_unidad = csv_unidad[temp-2] # Extrae el caracter dos espacios antes del 1er dígito
        break

# Si el tag venía mal escrito, el archivo se sube a la carpeta de respaldo
# Si por alguna razón la carpeta indicada no existe, se sube a la de respaldo
if temp == -1: csv_unidad = 'L'
if not str(csv_unidad).isalpha(): csv_unidad = 'L'
csv_unidad = Unidades(csv_unidad).name
folder_name = "G_FOLDER_ID_"+ csv_unidad
try:
    ssheet_folder_id = os.environ.get(folder_name, None)
except:
    csv_unidad = Unidades('L').name
    folder_name = "G_FOLDER_ID_"+ csv_unidad
    ssheet_folder_id = os.environ.get(folder_name, None)
    print(f"\nLa carpeta {csv_unidad} no existe. Se va a subir a la carpeta 'Sin Organizar'.\n")

# Intenta obtener el archivo .csv a subir según la dirección que se armo
# Si lo encuentra, guarda el contenido en un dataframe
csv_path = "../data/convos/"+csv_unidad+"/"+ssheet_name+".csv"
print(f"\nBuscando el archivo... {csv_path}")
try:
    df = pd.read_csv(csv_path)
except:
    print(f"\nHubo un error al obtener el archivo a subir.\n")
    quit()
print(f"\n¡Se encontró el archivo a subir!\n")
values = [df.columns.tolist()] + df.values.tolist()

# Carga las credenciales de Google Cloud
# En este paso, se abrirá una pestaña pidiendo permiso para modificar tu GDrive
with open(os.environ.get('G_OAUTH', None)) as f:
    creds = json.load(f)
google_creds, authorized_user = gspread.oauth_from_dict(creds)

# Si se proporcionó un spreadsheet ID, lo busca en el GDrive y actualiza la pestaña con la Conversación
# Si no había ID, se asume que el archivo nunca se ha subido y crea uno nuevo
ssheet_id = os.environ.get('G_SPREADSHEET_ID', None)
if ssheet_id == '':
    ssheet = google_creds.create(ssheet_name, ssheet_folder_id)
    worksheet = ssheet.add_worksheet(title="00 Conversación", rows=df.shape[0], cols=df.shape[1])
    ssheet_id = ssheet.id
    ssheet.del_worksheet(ssheet.sheet1)
    print("\nSpreadsheet creado.\n")
else:
    try:
        ssheet = google_creds.open_by_key(ssheet_id)
    except gspread.SpreadsheetNotFound:
        print("\nNo se encontró un spreadsheet con ese ID.\n")
        quit()
    except:
        print("\nHubo un error al obtener el spreadsheet.\n")
        quit()
    print("\nSpreadsheet encontrado.\n")
    worksheet = ssheet.worksheet("00 Conversación")
    worksheet.clear()
worksheet.update(values)
print("\n¡Se subieron los datos con éxito!\n")