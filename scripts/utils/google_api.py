#
# Versión 1.0
# Fecha: 08 de octubre de 2025
#
# Autores: Helena Ruiz Ramírez
# Función: Función decoradora para checar si el API request fue exitoso o si se necesita hacer un conteo (backoff)
import random
import time
from gspread.exceptions import APIError


def exponential_backoff(func):
    def wrapper(*args, **kwargs):
        max_retries = 5 # El máximo número de intentos que va a hacer antes de cancelar el run
        base_delay = 5  # en segundos
        for attempt in range(max_retries):
            # Por cada intento, checa si el request se completó sin errores
            # Si regresa un error 429, significa que topo el límite
            # Entonces, agrega más segundos al delay con cada intento antes de volver a intentar
            try:
                return func(*args, **kwargs)
            except APIError as e:
                if e.response.status_code == 429 and attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    print(f"Error de API 429. Reintentando en {delay:.2f} segundos...")
                    time.sleep(delay)
                else:
                    raise
    return wrapper


# Ejecuta una función con exponential backoff
@exponential_backoff
def execute_api_operation(func, *args, **kwargs):
    return func(*args, **kwargs)