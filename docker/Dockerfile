# Usar una imagen oficial de Python como imagen base
FROM python:3.9-slim

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# Copiar el archivo de requerimientos, osea las librerias que utilisa el programa
COPY docker/requirements.txt .

# Instalar las paqueterías necesarias
RUN pip install --no-cache-dir -r requirements.txt

# Crear los directorios necesarios para la aplicación
RUN mkdir -p callbacks utils

# Copiar los archivos específicos de la aplicación a sus respectivos directorios
COPY scripts/callbacks/check_history.py callbacks/
COPY scripts/callbacks/enum_canales.py callbacks/
COPY scripts/utils/liveconnect_api.py utils/

# Hacer que el puerto 8080 esté disponible
EXPOSE 8080

# Definir la variable de entorno para el puerto
ENV PORT 8080

# Ejecutar la aplicación cuando el contenedor se inicie
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "callbacks.check_history:app"]