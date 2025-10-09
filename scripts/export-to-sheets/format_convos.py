#
# Versión 1.1
# Fecha: 08 de octubre de 2025
#
# Autores: Helena Ruiz Ramírez
# Función: Aplicar formato a las celdas al subir las conversaciones a Google Sheets
#
from gspread_formatting import *
from utils.google_api import execute_api_operation


def apply_formatting(worksheet, system_message_rows):
    # Junta todos los formatos especificados en una lista.
    # gspread-formatting se encargará de mandarlos en un solo batch request.
    formatting_requests = []

    # Formato para toda la pestaña
    formatting_requests.append(('A:D', CellFormat(
        verticalAlignment='MIDDLE',
        wrapStrategy='WRAP',
        backgroundColor=Color(1, 1, 1),  # blanco
        textFormat=TextFormat(italic=False, foregroundColor=Color(0, 0, 0))  # negro
    )))

    # Formato para los títulos de las columnas
    formatting_requests.append(('A1:D1', CellFormat(
        backgroundColor=Color(67/255, 67/255, 67/255),  # gris oscuro
        textFormat=TextFormat(bold=True, foregroundColor=Color(1, 1, 1))  # blanco
    )))

    # Formato para los mensajes del sistema
    for x in system_message_rows:
        a1_notation = f"A{x}:D{x}"
        formatting_requests.append((a1_notation, CellFormat(
            backgroundColor=Color(217/255, 217/255, 217/255),  # gris claro
            textFormat=TextFormat(italic=True)
        )))

    # Ejecuta las llamadas a la API, protegidas por el decorador de backoff
    if formatting_requests:
        execute_api_operation(format_cell_ranges, worksheet, formatting_requests)
    
    execute_api_operation(set_column_widths, worksheet, [('A', 235), ('B', 500), ('C', 135), ('D', 60)])
