#
# Versión 1.2
# Fecha: 08 de octubre de 2025
#
# Autor: Helena Ruiz Ramírez
# Función: Interfaz del usuario para una web app con streamlit que
#           exporta conversaciones de LiveConnect a Google Sheets.
#
import streamlit as st
from google_auth import create_google_credentials
from pull_convos import pull_conversations
from utils.enum_liveconnect import Unidades

# --- Page Config ---
st.set_page_config(page_title="Froggy App", page_icon="🐸")

st.title("🐸 Exportador de Conversaciones")

if 'step' not in st.session_state:
    st.session_state.step = 0

convos_option = 0
starting_user_index = 0
starting_page_index = 0
total_convos_to_fetch = 0
ending_user_index = 0
ending_page_index = 0
format_option = 0
google_file_ids = {}

# --- Autenticación de Google ---
google_creds = create_google_credentials()
if google_creds:
    st.success("¡Conexión a Google Cloud obtenida!")
    tab1, tab2, tab3 = st.tabs(["Paso 1", "Paso 2", "Paso 3"])
    with tab1:
        # Menú para seleccionar el tipo de exportación a realizar
        st.subheader("1. Definir Conversaciones a Exportar")
        convos_option_str = st.radio(
            "¿Qué conversaciones desea exportar?",
            ("Una conversación específica", "Una cantidad específica de conversaciones (una sola página)", "Exportar por mes (varias páginas)")
        )
        if convos_option_str.startswith("Una conversación"):
            convos_option = 1
        elif convos_option_str.startswith("Una cantidad"):
            convos_option = 2
        else:
            convos_option = 3
        
        st.divider()
        if convos_option == 1:
            starting_user_index = st.text_input("ID de la conversación a exportar (Ej: 12345678, sin puntos):")
            total_convos_to_fetch = 1
            st.write("El ID de una conversación finalizada se encuentra en la página 'Historial' o en la ficha del contacto.")
        elif convos_option == 2:
            st.write("Indique a partir de dónde se deben exportar las conversaciones según su posición en 'Historial'.")
            starting_page_index = st.number_input("Número de la página donde están las conversaciones (mín. 1):", min_value=1)
            starting_user_index = st.number_input("Número de la fila donde está la primera conversación (1-100):", min_value=1, max_value=100)
            total_convos_to_fetch = st.number_input("Número de conversaciones a jalar:", min_value=1)
            starting_user_index = (int(starting_user_index) - 1) + ((int(starting_page_index) - 1) * 100)
        elif convos_option == 3:
            st.write("Indique dónde se ubica la primera y última conversación a exportar, para calcular el total de filas.")
            starting_page_index = st.number_input("Número de la página donde están las conversaciones (mín. 1):", min_value=1)
            starting_user_index = st.number_input("Número de la fila donde está la primera conversación (1-100):", min_value=1, max_value=100)
            ending_page_index = st.number_input("Número de la página donde está la última conversación (mín. 1):", min_value=1)
            ending_user_index = st.number_input("Número de la fila donde está la última conversación (1-100):", min_value=1, max_value=100)
            starting_user_index = (int(starting_user_index) - 1) + ((int(starting_page_index) - 1) * 100)
            ending_user_index = int(ending_user_index) + ((int(ending_page_index) - 1) * 100)
            total_convos_to_fetch = ending_user_index - starting_user_index
    with tab2:
        # Menú para seleccionar el formato de almacenamiento
        st.subheader("2. Escoger Método de Almacenamiento")
        format_option_str = st.radio(
            "¿Cómo desea almacenar las conversaciones?",
            ("Un archivo por conversación en la carpeta de la unidad", "Una pestaña por conversación en el archivo de la unidad")
        )
        format_option = 1 if format_option_str.startswith("Un archivo") else 2

        st.divider()
        if format_option == 1:
            st.write("Los ID's de las carpetas ya se encuentran en el sistema. Puede continuar.")
        elif format_option == 2:
            # Itera cada una de las unidades registradas en el archivo enum_equipos.py
            # ¡Es importante mantener este y enum_equipos actualizados si hay cambios en las sucursales!
            st.write("Por favor, escriba el ID del archivo de cada unidad. Fíjese en el URL y escriba el código sin las diagonales.")
            st.write("Ejemplo: 'https:// docs.google.com/spreadsheets/d/12345/edit?...', el ID es '12345'")
            for item in Unidades:
                google_file_ids[item.name] = st.text_input(f"ID para {item.name}:")
    with tab3:
        # Botón para iniciar la exportación
        st.subheader("3. Exportar a Google Sheets")
        st.write("Por favor de click al botón cuando haya configurado los pasos anteriores.")
        if st.button("Iniciar Exportación", type="primary"):
            if convos_option > 0:
                pull_conversations(
                    total_convos_to_fetch=total_convos_to_fetch,
                    google_creds=google_creds,
                    first_convo=starting_user_index,
                    convos_option=convos_option,
                    format_option=format_option,
                    google_file_ids=google_file_ids
                )
            else:
                st.error("Por favor, seleccione una opción de exportación válida (Paso #2 y #3).")
else:
    st.warning("Por favor, autorize la aplicación con su cuenta de Google para continuar.")