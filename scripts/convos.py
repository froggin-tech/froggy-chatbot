#
# Versión 0.1
# Fecha: 21 de julio de 2025
#
# Autor: Helena Ruiz Ramírez
# Función: Llamar registros de conversaciones de la plataforma LiveConnect según ciertos parametros
#           de tiempos y etiquetas, para luego exportarlos en un archivo.
#
import os
import json
from pathlib import Path
from dotenv import load_dotenv
import requests
import pandas as pd

load_dotenv()

pd.set_option('display.max_colwidth', None)
pd.set_option('display.width', None)
pd.set_option('display.max_columns', None)

ckey = os.environ.get('LC_C_KEY', None)
privateKey = os.environ.get('LC_PRIVATE_KEY', None)
convoID = os.environ.get('LC_CONVERSATION_ID', None)

base_url = "https://api.liveconnect.chat/prod/"

convo_endpoint = "history/conversation"
convo_payload = { "id": convoID }

def get_token():
  endpoint = "account/token"
  payload = {
    "cKey": ckey,
    "privateKey": privateKey
  }
  headers = {
    "Content-Type": "application/json",
    "Accept": "application/json, application/xml"
  }
  response = requests.post(base_url+endpoint, json=payload, headers=headers)
  return response.json()

def get_liveconnect(lc_endpoint, lc_payload, token):
  endpoint = lc_endpoint
  payload = lc_payload
  headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "PageGearToken": token
  }
  response = requests.post(base_url+endpoint, json=payload, headers=headers)
  return response.json()

json_resp = get_token()
os.environ['LC_PAGE_GEAR_TOKEN'] = json_resp['PageGearToken']
pageGearToken = os.environ.get('LC_PAGE_GEAR_TOKEN', None)
print("\n"+json_resp['status_message']+"\n")

json_resp = get_liveconnect(convo_endpoint, convo_payload, pageGearToken)
print("\n"+json_resp['status_message']+"\n")
if json_resp['status'] > 0:
  print('ID: '+str(json_resp['data']['conversacion']['contacto']['id']))
  print('Contacto: '+json_resp['data']['conversacion']['contacto']['nombre']+' '+json_resp['data']['conversacion']['contacto']['apellidos'])
  print('Primer Mensaje: '+json_resp['data']['mensajes'][0]['mensaje'])
  print('\n')

if json_resp['status'] > 0:
  df = pd.json_normalize(json_resp['data']['mensajes'])
  msg_data = df[['id_remitente', 'mensaje']]
  path_name = '../data/convos/'+json_resp['data']['conversacion']['canalnombre']+'/'
  os.makedirs(path_name, exist_ok=True)
  msg_data.to_csv(path_name+json_resp['data']['conversacion']['contacto']['nombre']+'.csv', encoding='utf-8-sig')