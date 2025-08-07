#
# Versión 0.3
# Fecha: 07 de agosto de 2025
#
# Autor: Helena Ruiz Ramírez
# Función: Archivo principal para mandar a llamar las funciones de Froggy
#
from google_auth import *
from pull_convos import *
from enum_unidades import Unidades


# Función para determinar si la opción escrita está dentro de un rango válido
def check_input_range(lower_limit, upper_limit, user_input):
    try:
        user_input = int(user_input)
        return lower_limit <= user_input <= upper_limit
    except (ValueError, TypeError):
        return False


# Función para determinar si la opción escrita es del tipo de variable correcto
def check_input_type(user_input):
    try:
        user_input = int(user_input)
    except (ValueError, TypeError):
        return False
    else:
        return True


# Primero, limpia la terminal y obtiene los permisos para el Google Cloud API
os.system('cls||clear')
print("\n-------------------------------------\n")
google_creds = create_google_credentials()

# Luego, entra al menú principal. Las opciones se escogen escribiendo el número de la acción a realizar
while True:
    menu_option = 0
    print("\n-------------------------------------\n")
    print("= MENÚ DEL SISTEMA DE FROGGY =")
    print("1. Jalar conversaciones de LiveConnect")
    print("2. Salir")
    while not check_input_range(1,2,menu_option):
        menu_option = input("Escoge una opción: ").strip()

    menu_option = int(menu_option)
    if menu_option == 2:
        break
    elif menu_option == 1:
        while True:
            convos_option = 0
            os.system('cls||clear')
            print("\n-------------------------------------\n")
            print("= CONVERSACIONES DE LIVECONNECT =")
            print("1. Exportar una cantidad específica")
            print("2. Exportar por mes (varias páginas)")
            print("3. Regresar al menú principal")
            while not check_input_range(1,3,convos_option):
                convos_option = input("Escoge una opción: ").strip()

            convos_option = int(convos_option)
            starting_user_index = '' # Contando desde 1, es la fila de la primera conversación a traer
            total_convos_to_fetch = '' # limit_of_convos_to_fetch: Total de conversaciones a traer.
            ending_user_index = '' # ending_user_index: Contando desde 1, es la fila de la última conversación a traer
            full_pages = '' # full_pages: Número de páginas de conversaciones completas entre la primera y la última

            if convos_option == 3:
                break
            elif convos_option == 1:
                while not check_input_type(starting_user_index):
                    starting_user_index = input("\nFila de la primera conversación en LC: ").strip()
                while not check_input_type(total_convos_to_fetch):
                    total_convos_to_fetch = input("Total de conversaciones a jalar: ").strip()
                starting_user_index = int(starting_user_index)
                total_convos_to_fetch = int(total_convos_to_fetch)
            elif convos_option == 2:
                while not check_input_type(starting_user_index):
                    starting_user_index = input("\nFila de la primera conversación en LC: ").strip()
                while not check_input_type(ending_user_index):
                    ending_user_index = input("Fila de la última conversación en LC: ").strip()
                while not check_input_type(full_pages):
                    full_pages = input("Páginas completas entre ambas conversaciones: ").strip()
                starting_user_index = int(starting_user_index)
                ending_user_index = int(ending_user_index)
                full_pages = int(full_pages)
                total_convos_to_fetch = (100 - starting_user_index) + (full_pages * 100) + ending_user_index
            else:
                print("Opción inválida.\n")
                break

            format_option = 0
            google_file_ids = {}
            print("\n-------------------\n")
            print("¿CÓMO DESEA ALMACENAR LAS CONVERSACIONES?")
            print("1. Un archivo por conversación en la carpeta de la unidad")
            print("2. Crear pestañas en el archivo de la unidad")
            print("3. Regresar al menú principal")
            while not check_input_range(1,3,format_option):
                format_option = input("Escoge una opción: ").strip()

            format_option = int(format_option)
            if format_option == 3:
                break
            elif format_option == 2:
                option = "NO"
                while option == "NO":
                    print("\nPOR FAVOR ESCRIBA EL ID DEL ARCHIVO DE CADA UNIDAD.")
                    print("FIJESE EN EL URL Y ESCRIBA EL CÓDIGO DESPUÉS DE LA DIAGONAL.")
                    print("EJEMPLO: 'https://docs.google.com/spreadsheets/d/12345...', EL ID ES '12345...'\n")
                    # Itera cada una de las unidades registradas en el archivo enum_equipos.py
                    # ¡Es muy importante mantener este y enum_equipos actualizados si hay cambios en las sucursales/etiquetas!
                    for x in Unidades:
                        google_file_ids[x.name] = input(f"{x.name}: ")
                    print("\nASI SE GUARDARON SUS DATOS:")
                    for x, y in google_file_ids.items():
                        print(f"\n{x}: {y}")
                    option = input("LOS DATOS SON CORRECTOS? (SI/NO): ")
                    if not option == "SI" and not option == "NO":
                        option == "NO"
                    if option == "NO":
                        ids_option = 0
                        print("\n1. Ingresar IDs de nuevo")
                        print("2. Regresar al menú principal")
                        while not check_input_range(1,2,ids_option):
                            ids_option = input("Escoge una opción: ").strip()
                            if ids_option == 2:
                                break
                            elif not ids_option == 1:
                                print("Opción inválida.\n")
                                break
            elif not format_option == 1:
                print("Opción inválida.\n")
                break
            
            os.system('cls||clear')
            print("\n-------------------\n")
            print("... PASO 1/3: GENERANDO TOKEN PARA AUTORIZAR LA CONEXIÓN A LIVECONNECT ...")
            pull_conversations(total_convos_to_fetch, google_creds, starting_user_index - 1, format_option, google_file_ids)
    else:
        print("Opción inválida.")

    os.system('cls||clear')
