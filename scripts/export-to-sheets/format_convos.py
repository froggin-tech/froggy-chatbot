#
# Versión 1.0
# Fecha: 06 de agosto de 2025
#
# Autores: Helena Ruiz Ramírez
# Función: Aplicar formato a las celdas al subir las conversaciones a Google Sheets
#
from gspread_formatting import *


def apply_formatting(worksheet, system_message_rows):
    # Toda la pestaña
    cellFormat1 = CellFormat(
        verticalAlignment='MIDDLE',
        wrapStrategy='WRAP',
        backgroundColor=Color(1, 1, 1),
        textFormat=TextFormat(
            italic=False, foregroundColor=Color(0, 0, 0))  # negro
    )

    # Títulos de columnas
    cellFormat2 = CellFormat(
        backgroundColor=Color(67/255, 67/255, 67/255),  # gris oscuro
        textFormat=TextFormat(
            bold=True, foregroundColor=Color(1, 1, 1))  # blanco
    )

    # Mensajes del sistema
    cellFormat3 = CellFormat(
        backgroundColor=Color(217/255, 217/255, 217/255),  # gris claro
        textFormat=TextFormat(italic=True)
    )

    # Junta todos los formatos especificados en un diccionario
    # Luego aplica los formatos del diccionario en una solo batch request, para mantenernos bajo el limite del API
    formatting_requests = [
        ('A:D', cellFormat1),
        ('A1:D1', cellFormat2)
    ]
    for x in system_message_rows:
        a1_notation = f"A{x}:D{x}"
        formatting_requests.append((a1_notation, cellFormat3))
    format_cell_ranges(worksheet, formatting_requests)

    # Ajusta el grosor de cada columna: Usuario, Mensaje, Fecha, Interno?
    set_column_widths(worksheet, [('A', 235), ('B', 500), ('C', 135), ('D', 60)])
