#
# Versión 0.2
# Fecha: 06 de agosto de 2025
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
starting_user_index = 0
pull_conversations(limit_of_convos_to_pull, google_creds, starting_user_index)
