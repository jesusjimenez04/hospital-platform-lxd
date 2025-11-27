# Operaciones sobre contenedores individuales
import logging
from modulos.logger_config import log_info, log_error
from modulos import gestion_lxc
import subprocess

# Alias adaptado para usar la imagen de Óscar sin cambiar todo el código
imagenpers = "imagenprof"

#Método para arrancar o parar un contenedor individualmente
def gestionar_servidor_individual(accion, nombre_servidor):
    if accion not in ['parar', 'arrancar']:
        log_info("Acción no válida. Usa 'parar' o 'arrancar'.")
        return
    try:
        if accion == 'parar':
            subprocess.run(["lxc", "stop", nombre_servidor], check=True)
            log_info(f"Servidor {nombre_servidor} parado correctamente.")
        if accion == "arrancar":
            subprocess.run(["lxc", "start", nombre_servidor], check=True)
            log_info(f"Servidor {nombre_servidor} arrancado correctamente.")
    except subprocess.CalledProcessError:
        log_info(f"Error al intentar {accion} el servidor {nombre_servidor}.")

#Método para crear un contenedor individualmente
def crear_servidor_individual(nombre_servidor, imagen="imagenpers"):
    try:
        subprocess.run(["lxc", "init", imagen, nombre_servidor], check=True)
        log_info(f"Servidor {nombre_servidor} creado y arrancado correctamente.")
    except subprocess.CalledProcessError:
        log_info(f"Error al crear el servidor {nombre_servidor}.")

#Método para eliminar un contenedor individualmente
def eliminar_servidor_individual(nombre_servidor):
    try:
        subprocess.run(["lxc", "delete", nombre_servidor], check=True)
        log_info(f"Servidor {nombre_servidor} eliminado correctamente.")
    except subprocess.CalledProcessError:
        log_info(f"Error al eliminar el servidor {nombre_servidor}.")

#Método adicional para aumentar la capacidad requerida
def enlarge():
    #Primero obtenemos el número de servidores que tenemos hasta ahora
    num_actual = gestion_lxc.leer_config()
    
    #Ahora, para asignar nombre e ip, seguimos los mismos pasos que crear_servidores()
    siguiente = num_actual + 1
    nombre = f"s{siguiente}"
    ip = f"134.3.0.{10 + siguiente}"

    #Con los datos anteriores, ya inicializo y arranco
    try:
        subprocess.run(["lxc", "init", imagenpers, nombre], check=True)
        subprocess.run(["lxc", "network", "attach", "lxdbr0", nombre, "eth0"], check=True)
        subprocess.run([
            "lxc", "config", "device", "set",
            nombre, "eth0", "ipv4.address", ip
        ], check=True)

        #Arrancar el contenedor
        subprocess.run(["lxc", "start", nombre], check=True)

        log_info(f"Servidor {nombre} creado, arrancado y conectado a eth0 con IP {ip}")

        #Escribimos en el fichero config.txt el número actual de servidores
        gestion_lxc.escribir_config(siguiente)

    except subprocess.CalledProcessError as e:
        log_error(f"Error al crear/arrancar {nombre}: {e}")
