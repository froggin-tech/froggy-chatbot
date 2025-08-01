#
# Versión 0.1
# Fecha: 31 de julio de 2025
#
# Autor: Helena Ruiz Ramírez
# Función: Archivo principal para mandar a llamar las funciones de Froggy
#
from google_auth import *
from pull_convos import *

# Primero, obtiene las credenciales para usar las APIs de Google Spreadsheets y Drive
google_creds = create_google_credentials()

# Luego, hace el proceso de jalar y subir conversaciones en LiveConnect según la cantidad indicada
limit_of_convos_to_pull = 1
pull_conversations(limit_of_convos_to_pull, google_creds)