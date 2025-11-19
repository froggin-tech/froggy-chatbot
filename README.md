# Franny Chatbot y Froggy Análisis

Código necesario para la funcionalidad "callback" de Franny Chatbot y "export" de Froggy Análisis. También incluye los archivos y configuraciones necesarias para correr las aplicaciones de manera local y en la web. La configuración web utiliza los dockerfiles y los cloudbuilds para desplegar las aplicaciones en Google Cloud.

## Tabla de Contenidos

1.  [Descripción General](#descripción-general)
2.  [Dockerfiles](#dockerfiles)
3.  [Cloud Build](#cloud-build)
4.  [Variables de Entorno](#variables-de-entorno)
5.  [Estructura del Repositorio](#estructura-del-repositorio)

## Descripción General

Este repositorio contiene dos aplicaciones principales:

*   **Callback:** Esta aplicación maneja los "callbacks" que recibe del webhook en LC (Franny Transfer) usando APIs.
*   **Export:** Esta aplicación tipo streamlit exporta conversaciones de LC a Google Sheets.

Estas aplicaciones tienen sus directorios respectivos (`scripts/callbacks`, `scripts/export-to-sheets`), pero también comparten funciones del directorio `scripts/utils`. Estas herramientas sirven para definir módulos de las APIs de LC y Google Drive.

Aparte, contiene archivos para desplegar las aplicaciones en Google Cloud usando contenedores Docker. El despliegue se mantiene actualizado utilizando los archivos Cloud Build, que sincronizan los cambios subidos al repositorio con el servidor Google.

## Dockerfiles

El directorio `scripts/docker` contiene los Dockerfiles para cada aplicación:

*   `scripts/docker/dockerfile_callback`: Este Dockerfile se utiliza para construir una imagen de Docker para la aplicación Callback.
*   `scripts/docker/dockerfile_export`: Este Dockerfile se utiliza para construir una imagen de Docker para la aplicación Export.

Estos Dockerfiles definen el entorno y las dependencias necesarias para ejecutar cada aplicación. Aseguran que las aplicaciones se puedan construir y ejecutar de manera consistente en diferentes entornos.

Este directorio también incluye los archivos `requirements`, o requisitos, para que los contenedores sepan que dependencias instalar. Por dependencias nos referimos a librerías o paquetes.

## Cloud Build

Los archivos `cloudbuild.export.yaml` y `cloudbuild.callback.yaml` definen configuraciones de Cloud Build para construir y desplegar automáticamente las aplicaciones Export y Callback, respectivamente, a Google Cloud Run cuando se envían cambios a la rama principal.

## Variables de Entorno

Este proyecto utiliza variables de entorno para almacenar información sensible y configuraciones (secrets, configs, API keys, IDs).

Para crear tu propio archivo `.env`:

1.  Haz una copia del archivo `.env.example` en el directorio raíz.
2.  Renombra la copia a `.env`.
3.  Edita el archivo `.env` y reemplaza los valores de marcador de posición con tus valores reales.

**Importante:** No subas el archivo `.env` a tu repositorio, ya que contiene información sensible. Ya está incluido en `.gitignore`.

## Estructura del Repositorio

```
.gitattributes
.gitignore
cloudbuild.callback.yaml
cloudbuild.export.yaml
README.md
docs/
  contents.txt
scripts/
  .dockerignore
  README.md
  callbacks/
    __init__.py
    check_history.py
  docker/
    dockerfile_callback
    dockerfile_export
    requirements_callback.txt
    requirements_export.txt
  export-to-sheets/
    __init__.py
    format_convos.py
    google_auth.py
    pull_convos.py
    streamlit_app.py
    upload_convos.py
    .streamlit/
  utils/
    __init__.py
    enum_liveconnect.py
    google_api.py
    liveconnect_api.py
secrets/
  .gitkeep
