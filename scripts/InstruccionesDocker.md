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
    *   Abra la terminal o el command prompt.
    *   Navegue al directorio del proyecto (donde se encuentra este archivo README.md).
    *   Ejecute el siguiente comando:
        ```bash
        docker build -t your-image-name -f docker/dockerfile_export .
        ```
        Reemplace `your-image-name` con el nombre que desee para su imagen. Por ejemplo, `franny-export`.

        **Note for Windows users:** These commands should work in PowerShell or in the Docker Desktop's terminal.

4.  **Correr la Imagen:**
    *   Abra la terminal o el command prompt.
    *   Ejecute el siguiente comando:
        ```bash
        docker run -p 8000:8000 your-image-name
        ```
        Reemplace `your-image-name` con el nombre que le dio a su imagen en el paso anterior.

5.  **Monitorear el estado de "build" en Docker Desktop (opcional)**
    *   Abra Docker Desktop.
    *   Vaya a la sección de "Containers/Apps".
    *   Aquí puede ver el estado de su "build" y los logs.

6.  **Revise la Aplicación:** Abra su navegador de preferencia y vaya a la liga `http://localhost:8000`. Debería de ver la aplicación corriendo ya sea con un mensaje o con una interfaz.

## Variables de Entorno

La aplicación requiere variables de entorno para funcionar correctamente. Estas variables se encuentran en el archivo `.env` en el directorio raíz del proyecto. Para configurar estas variables:

1.  Cree un archivo `.env` en el directorio raíz del proyecto copiando el contenido de `.env.example` y reemplazando los valores de marcador de posición con sus valores reales.
2.  Cuando corra la imagen (paso 4), puede especificar las variables de entorno usando la bandera `-e` en el comando `docker run`. Por ejemplo:
    ```bash
    docker run -p 8000:8000 -e LC_C_KEY=your_lc_c_key -e LC_PRIVATE_KEY=your_lc_private_key your-image-name
    ```
    Reemplace `your_lc_c_key` y `your_lc_private_key` con los valores reales de sus variables de entorno.