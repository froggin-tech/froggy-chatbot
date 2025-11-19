# Instrucciones para Copiar el Proyecto

Para replicar las herramientas de "callback" y "export" elaboradas en estos scripts, es necesario armar la "imagen" usando la tecnología de Docker. Esto permite que cada versión construida de estas aplicaciones se haga exactamente de la misma manera y con un solo comando.

Esta la opción de usar la terminal, pero es recomendable instalar Docker Desktop. Esta hecho con una interfaz amigable para usuarios y es más fácil de manejar.

## Requisitos

1. **Instalar Docker Desktop:** Si no lo tiene instalado aún, hay que descargar e instalarlo [de esta liga](https://www.docker.com/products/docker-desktop/). Siga las instrucciones de su sistema operativo.
2. **Abrir Docker Desktop:** Una vez que se instale, abra la aplicación. Va a correr en el fondo y proveer una interfaz visual para poder administrar los contenedores tipo Docker.

**Nota:** Se necesita hacer login con una cuenta Docker. La info para Froggin está en 1Password.

## Armando y Corriendo el Proyecto

1. **Abrir Docker Desktop:** Asegurese de que la aplicación está corriendo.
2. **Navegar al Project Directory:** Abra el explorador de archivos y vaya al folder donde se encuentra este README.md. Este es el directorio del proyecto.
3.  **Armar la Imagen:**
    *   De click en la pestaña de "Images".
    *   De click en el botón de "Build".
    *   En el campo de "Path", escriba "." (sin las comillas). Esto le dice a Docker que debe utilizar el directorio actual (paso 2).
    *   En el campo de "Dockerfile", escriba "docker/dockerfile\_export" o "docker/dockerfile\_callback" (sin las comillas). Esto especifica cual proyecto quiere construir a partir de un dockerfile.
    *   En el campo de "Tags", escriba un nombre para su imagen. Puede ser "proyecto-export" o "proyecto-callback" (sin las comillas).
    *   De click al botón "Build". Docker Desktop ahora va a armar la imagen. Puede revisar el progreso en la pestaña de "Build".
4.  **Correr la Imagen:**
    *   Cuando la imagen se haya construido, vaya a la pestaña de "Images".
    *   Busque la imagen que acaba de construir ("proyecto-export", "proyecto-callback").
    *   De click al botón "Run" a un lado de la imagen.
    *   En la sección de "Optional settings", de click a "port mapping".
    *   En el campo de "Host port", escriba "8000".
    *   En el campo de "Container port", escriba "8000".
    *   De click al botón de "Run". Docker Desktop ahora va a correr el contenedor.
5.  **Revise la Aplicación:** Abra su navegador de preferencia y vaya a la liga `http://localhost:8000`. Debería de ver la aplicación corriendo ya sea con un mensaje o con una interfaz.

## Variables de Entorno

La aplicación requiere variables de entorno para funcionar correctamente. Estas variables se encuentran en el archivo `.env` en el directorio raíz del proyecto. Para configurar estas variables en Docker Desktop:

1.  Cuando corra la imagen (paso 4), expanda la sección "Optional settings".
2.  De click en "Environment variables".
3.  Agregue cada variable de entorno y su valor correspondiente. Por ejemplo:
    *   `LC_C_KEY`: (valor de su archivo `.env`)
    *   `LC_PRIVATE_KEY`: (valor de su archivo `.env`)
    *   `GPT_KEY`: (valor de su archivo `.env`)
    *   etc.
4.  De click al botón de "Run" para correr el contenedor con las variables de entorno configuradas.