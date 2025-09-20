#
# Versión 2.0
# Fecha: 18 de septiembre de 2025
#
# Autor: Helena Ruiz Ramírez
# Función: Autenticar credenciales de Google Cloud para una aplicación Streamlit
#
import streamlit as st
import gspread
import os
import json
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow


def create_google_credentials():
    # Carga las credenciales en formato json para la cuenta de servicio OAuth
    try:
        load_dotenv()
        g_oauth_json = os.environ.get("G_OAUTH_JSON")
        if not g_oauth_json:
            st.error("La variable de entorno 'G_OAUTH_JSON' no está configurada.")
            return None
        client_config = json.loads(g_oauth_json)
    except json.JSONDecodeError:
        st.error("Error al decodificar el JSON de la variable de entorno 'G_OAUTH_JSON'.")
        return None
    
    # Define los scopes con los permisos necesarios para crear y editar sheets
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    # Inicializa el flujo de autenticación
    flow = Flow.from_client_config(
        client_config=client_config,
        scopes=scopes,
        redirect_uri=client_config["web"]["redirect_uris"][0] # Usa el primer redirect URI en la lista
    )

    # Revisa si ya hay algún código de autorización del usuario guardado
    # Esto para que el usuario no tenga que volver a generarlo tan seguido
    code = 0
    if 'code' in st.query_params:
        code = st.query_params['code']

    # Lógica para manejar el callback de autenticación de Google Cloud
    if "credentials" not in st.session_state:
        if code:
            # Ya tiene un código guardado, pero no se han generado las credenciales
            try:
                # Canjea el código de autorización por un token de acceso
                flow.fetch_token(code=code)
                creds = flow.credentials
                # Guarda las credenciales en el estado de la sesión para no tener que re-autenticar
                st.session_state.credentials = {
                    "token": creds.token,
                    "refresh_token": creds.refresh_token,
                    "token_uri": creds.token_uri,
                    "client_id": creds.client_id,
                    "client_secret": creds.client_secret,
                    "scopes": creds.scopes
                }
                # El script continuará y usará las credenciales recién guardadas
            except Exception as e:
                st.error(f"Error al obtener el token: {e}")
                return None
        else:
            # Si no hay código, genera la URL de autorización y pide al usuario que haga clic
            auth_url, _ = flow.authorization_url(prompt="consent")
            st.markdown(f'Por favor, [autoriza la aplicación]({auth_url}) para continuar.')
            st.stop() # Pone "pausa" a la ejecución de la app hasta que el usuario autorice
    
    # Si ya tenemos las credenciales en el estado de la sesión, las usamos para autorizar el uso de gspread API
    try:
        creds = Credentials(**st.session_state.credentials)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Hubo un error al conectar con tu cuenta de Google: {e}")
        # Si hay un error, es posible que las credenciales hayan expirado. Las borramos para re-autenticar.
        if "credentials" in st.session_state:
            del st.session_state.credentials
        return None