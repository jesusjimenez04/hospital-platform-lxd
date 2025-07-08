#Jesús Jiménez Serrano
#Yago Gil Iglesias
#Código para generar la imagen sobre la que se inicializarán los servidores
#La idea es:
#  1) Crear un contenedor base a partir de la imagen ubuntu2004
#  2) Personalizar este contenedor (al que llamaremos navegador)
#  3) Exportarlo a una imagen para tener una imagen propia personalizada
#  4) Crear los contenedores de la pŝractica inicializando esta imagen propia

import logging
from modulos.logger_config import log_info, log_error, log_warning 
import subprocess
import time
import os


# Ruta común a los .tar.gz pesados (no entran en la carpeta de la práctica)
RUTA_DESCARGAS = os.path.expanduser("~/Descargas")


#Paso 1:
def crear_contenedor_base(nombre_base="navegador"):
	log_info(f"Creando contenedor base '{nombre_base}'")
	subprocess.run(["lxc", "image", "import", 
		"/mnt/vnx/repo/arso/ubuntu2004.tar.gz",
		"--alias", "ubuntu2004"])
	subprocess.run(["lxc", "init", "ubuntu2004", nombre_base])
	subprocess.run(["lxc", "start", nombre_base])

#Paso 2:
def realizar_configuraciones_servidor(nombre_base="navegador"):
    try:
        # Node.js + app + forever
        log_info("Instalando NodeJS y preparando app en contenedor servidor...")

        # Añadir manualmente DNS para evitar problemas de resolución
        subprocess.run(
            f"lxc exec {nombre_base} -- bash -c \"rm -f /etc/resolv.conf && echo 'nameserver 8.8.8.8' > /etc/resolv.conf\"",
            shell=True, check=True
        )

        time.sleep(3)

        # 1. Actualizar e instalar NodeJS y npm
        subprocess.run(f"lxc exec {nombre_base} -- apt update", shell=True, check=True)
        subprocess.run(f"lxc exec {nombre_base} -- apt install -y nodejs npm", shell=True, check=True)

        # 1.1. Crear symlink de nodejs a node si no existe node (muy importante en Ubuntu 20.04)
        subprocess.run(
            f"lxc exec {nombre_base} -- bash -c 'command -v node || ln -s /usr/bin/nodejs /usr/bin/node'",
            shell=True, check=True
        )

        # 2. Instalar forever globalmente
        subprocess.run(f"lxc exec {nombre_base} -- npm install -g forever", shell=True, check=True)

        # 3. Subir y descomprimir la app
        subprocess.run(f"lxc file push app.tar.gz {nombre_base}/root/app.tar.gz", shell=True, check=True)
        subprocess.run(f"lxc exec {nombre_base} -- tar -xvf /root/app.tar.gz -C /root/", shell=True, check=True)

        # 4. Instalar dependencias de la app
        subprocess.run(f"lxc exec {nombre_base} -- bash -c 'cd /root/app && npm install'", shell=True, check=True)

        # 5. Lanzar la app con forever (CORREGIDO)
        subprocess.run(f"lxc exec {nombre_base} -- bash -c 'cd /root/app && forever start rest_server.js'", shell=True, check=True)

        log_info("Contenedor base servidor personalizado correctamente y app lanzada con forever.")

    except subprocess.CalledProcessError as e:
        log_error(f"Error configurando contenedor servidor: {e}")


#Paso 3:
def crear_imagen_personalizada(nombre_base="navegador", alias="imagenpers"):
	log_info(f"Creando imagen personalizada '{alias}' desde '{nombre_base}'")
	subprocess.run(["lxc", "stop", nombre_base])
	subprocess.run(["lxc", "publish", nombre_base, "--alias", alias])

def borrar_imagen_personalizada():
    log_info("Borrando contenedor con el que se inicializa la imagen ubuntu2004")
    subprocess.run(["lxc", "image", "delete", "imagenprof"], check=False)
    subprocess.run(["lxc", "image", "delete", "ubuntu2004"], check=False)

#Nuevo paso: Importar imagen profesor
def importar_imagen_profesor(ruta_imagen=os.path.join(RUTA_DESCARGAS, "arso25-p2.tar.gz"), alias="imagenprof"):
    """
    Importa automáticamente la imagen del profesor, si no existe aún en LXD.
    Debe ejecutarse desde la raíz del proyecto, donde esté el archivo .tar.gz.
    """
    try:
        # Verificar si ya existe una imagen con ese alias
        resultado = subprocess.run(["lxc", "image", "list", alias],
                                   capture_output=True, text=True)
        if alias in resultado.stdout:
            log_info(f"La imagen '{alias}' ya está importada.")
            return

        if not os.path.exists(ruta_imagen):
            log_error(f"No se encontró el archivo de imagen en: {ruta_imagen}")
            return

        log_info(f"Importando imagen del profesor desde '{ruta_imagen}' con alias '{alias}'...")
        subprocess.run(["lxc", "image", "import", ruta_imagen, "--alias", alias], check=True)
        log_info(f"Imagen del profesor importada con éxito con alias '{alias}'.")

    except subprocess.CalledProcessError as e:
        log_error(f"Error importando la imagen del profesor: {e}")

def importar_imagen_ubuntu_base(ruta=os.path.join(RUTA_DESCARGAS, "ubuntu2004.tar.gz"), alias="ubuntu2004"):
    """
    Importa automáticamente la imagen base de Ubuntu si no está presente.
    Requiere que el archivo .tar.gz esté accesible localmente.
    """
    try:
        resultado = subprocess.run(["lxc", "image", "list", alias],
                                   capture_output=True, text=True)
        if alias in resultado.stdout:
            log_info(f"La imagen base '{alias}' ya está importada.")
            return

        if not os.path.exists(ruta):
            log_error(f"No se encontró el archivo de imagen base en: {ruta}")
            return

        log_info(f"Importando imagen base de Ubuntu desde '{ruta}' con alias '{alias}'...")
        subprocess.run(["lxc", "image", "import", ruta, "--alias", alias], check=True)
        log_info(f"Imagen base '{alias}' importada correctamente.")

    except subprocess.CalledProcessError as e:
        log_error(f"Error al importar la imagen base de Ubuntu: {e}")
