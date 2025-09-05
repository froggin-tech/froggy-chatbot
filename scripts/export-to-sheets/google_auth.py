#
# Versión 1.2
# Fecha: 07 de agosto de 2025
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
    with open(os.environ.get('G_OAUTH', None)) as f:
        creds = json.load(f)

    # En este paso, se abrirá una pestaña pidiendo permiso para accesar a tu cuenta con la aplicación
    print("... PIDIENDO PERMISOS A SU CUENTA DE GOOGLE ...")
    try:
        google_creds, authorized_user = gspread.oauth_from_dict(creds)
    except Exception as e:
        print("HUBO UN ERROR AL CONECTAR SU CUENTA")
        print(f"{e}")
        os.system("pause")
        return
    print("¡CONEXIÓN A GOOGLE CLOUD OBTENIDA!")
    return google_creds