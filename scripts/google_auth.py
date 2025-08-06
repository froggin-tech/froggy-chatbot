#
# Versión 1.1
# Fecha: 06 de agosto de 2025
#
# Autor: Helena Ruiz Ramírez
# Función: Autenticar credenciales de Google Cloud
#
import os
import json
import gspread
from dotenv import load_dotenv


def create_google_credentials():
    # Carga el archivo .env con los secretos
    load_dotenv()

    # En este paso, se abrirá una pestaña pidiendo permiso para accesar a tu cuenta con la aplicación
    with open(os.environ.get('G_OAUTH', None)) as f:
        creds = json.load(f)
    google_creds, authorized_user = gspread.oauth_from_dict(creds)
    print("\nSe autorizó la conexión a Google\n")
    return google_creds
