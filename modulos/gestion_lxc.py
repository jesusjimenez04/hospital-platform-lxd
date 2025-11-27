# Primera parte del esquema: creación de componentes
# Fichero para hacer operaciones sobre los contenedores: crear, borrar, listar...
import logging
from modulos.logger_config import log_info, log_error
from modulos import gestion_bbdd
import subprocess
import time

# Alias adaptado para usar la imagen de Óscar sin cambiar todo el código
imagenpers = "imagenprof"


# Creación de los servidores
def crear_servidores(num_servidores=2):
    for i in range(1, num_servidores + 1):
        nombre = f"s{i}"
        ip = f"134.3.0.{10 + i}" # IPs: 134.3.0.11, .12, .13...
        try:
            # Crear contenedor sin arrancar
            subprocess.run(["lxc", "init", imagenpers, nombre], check=True)

            # Conectar a red y configurar IP antes de arrancar
            subprocess.run(["lxc", "network", "attach", "lxdbr0", nombre, "eth0"], check=True)
            subprocess.run([
                "lxc", "config", "device", "set",
                nombre, "eth0", "ipv4.address", ip
            ], check=True)

            log_info(f"Servidor {nombre} creado con IP {ip}")
        except subprocess.CalledProcessError as e:
            log_error(f"Error al crear {nombre}: {e}")

def configurar_netplan_cliente():
    # Desactivar cloud-init
    subprocess.run("lxc exec cl -- bash -c 'echo \"network: {config: disabled}\" > /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg'", shell=True, check=True)

    # Realizamos una copia de seguridad del archivo original
    subprocess.run("lxc exec cl -- cp /etc/netplan/50-cloud-init.yaml /etc/netplan/50-cloud-init.bak", shell=True, check=True)

    # Configuración de la interfaz eth1
    netplan_config = """\
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
"""
    # Escribimos la nueva configuración en el archivo
    subprocess.run(f"echo \"{netplan_config}\" | lxc exec cl -- tee /etc/netplan/50-cloud-init.yaml", shell=True, check=True)

    # Reiniciamos el contenedor para asegurar que la configuración sea aplicada
    subprocess.run("lxc restart cl", shell=True, check=True)

    log_info("Configuración de red aplicada en el contenedor cl.")

# Configuración del cliente: contenedor que se conecta a la subred del bridge1
# Como no se especifica la ip, podemos elegir la que queramos (siempre que esté dentro de la ipv4)
def crear_cliente():
    try:
        # Crear contenedor sin arrancar
        subprocess.run(["lxc", "init", "ubuntu2004", "cl"], check=True)

        # Conectar a red y configurar IP antes de arrancar
        subprocess.run(["lxc", "network", "attach", "lxdbr1", "cl", "eth0"], check=True)
        subprocess.run([
            "lxc", "config", "device", "set",
            "cl", "eth0", "ipv4.address", "134.3.1.11"
        ], check=True)

        #Arrancar el contenedor para poder aplicar el netplan
        subprocess.run(["lxc", "start", "cl"], check=True)
        
        #Aplicamos el método auxiliar
        configurar_netplan_cliente()

        #Lo paramos para que no se inicialice "starteado"
        subprocess.run(["lxc", "stop", "cl"], check=True)

        log_info("Cliente 'cl' creado y configurado correctamente en eth1 con IP 134.3.1.11")

    except subprocess.CalledProcessError as e:
        log_error(f"Error al crear el cliente 'cl': {e}")


# Método para simular peticiones del cliente
def realizar_peticiones():
    pass

#Método para leer/escribir sobre el fichero config.txt, para legibilidad
def leer_config():
    try:
        with open("config.txt", "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0  # Si no existe o es inválido, asumimos 0

def escribir_config(num):
    with open("config.txt", "w") as f:
        f.write(str(num))


# Método llamado cuando se ejecuta la orden "list"
def listar_contenedores():
    try:
        log_info("Listando contenedores con 'lxc init'")
        subprocess.run(["lxc", "list"], check=True)
    except subprocess.CalledProcessError as e:
        log_error(f"Error al listar los contenedores: {e}")

# Método para eliminar todos los contenedores del escenario
def borrar_contenedores(num_servidores):
    try:
        # Borrar servidores replicados
        for i in range(1, num_servidores + 1):
            nombre = f"s{i}"
            subprocess.run(["lxc", "delete", nombre, "--force"], check=True)
            log_info(f"Contenedor {nombre} eliminado")

        # Borrar cliente y balanceador
        for nombre in ["cl", "lb"]:
            subprocess.run(["lxc", "delete", nombre, "--force"], check=True)
            log_info(f"Contenedor {nombre} eliminado")

        #La db tiene su propio método de borrar

    except subprocess.CalledProcessError as e:
        log_error(f"Error al borrar contenedores: {e}")

def arrancar_contenedores(num_servidores):
#Primero vamos a comprobar si tenemos algun contenedor arrancado
#En tal caso, primero lo paramos, ya que sino da error 
  
    try:
        for i in range(1, num_servidores + 1):
            nombre = f"s{i}"
            estado = subprocess.run(
                ["lxc", "list", nombre, "--format", "csv", "-c", "s"],
                capture_output=True, text=True
            ).stdout.strip()
            if estado == "RUNNING":
                log_info(f"{nombre} está arrancado. Deteniéndolo...")
                subprocess.run(["lxc", "stop", nombre], check=True)
                time.sleep(2)
    except subprocess.CalledProcessError as e:
        log_error(f"Error al arrancar contenedores: {e}")

#Una vez ya hemos hecho la comprobación, ya arrancamos los contenedores

    try:
        # Arrancar servidores replicados
        for i in range(1, num_servidores + 1):
            nombre = f"s{i}"
            subprocess.run(["lxc", "start", nombre], check=True)
            time.sleep(5)
            log_info(f"Contenedor {nombre} arrancado")

        # Arrancar cliente y balanceador
        for nombre in ["cl", "lb"]:
            subprocess.run(["lxc", "start", nombre], check=True)
            time.sleep(5)
            log_info(f"Contenedor {nombre} arrancado")

        # Mostramos las consolas
        for i in range(1, num_servidores + 1):
            subprocess.Popen(["xterm", "-e", f"lxc exec s{i} bash"])
        subprocess.Popen(["xterm", "-e", "lxc exec lb bash"])
        subprocess.Popen(["xterm", "-e", "lxc exec cl bash"])

    except subprocess.CalledProcessError as e:
        log_error(f"Error al arrancar contenedores: {e}")

#Métodos para subir la app a los servidores:
def desplegar_aplicacion_web(nombre_contenedor="s1", ip_mongo = None):
    try:
        log_info(f"Desplegando app web en contenedor {nombre_contenedor}...")

        # Reparar DNS antes de cualquier instalación por si acaso
        subprocess.run(
            f"lxc exec {nombre_contenedor} -- bash -c \"rm -f /etc/resolv.conf && echo 'nameserver 8.8.8.8' > /etc/resolv.conf\"",
            shell=True, check=True
        )

        time.sleep(5)

        # Subir y descomprimir app (por si no se usa imagen personalizada)
        subprocess.run([
            "lxc", "file", "push", "-r", "app.tar.gz", f"{nombre_contenedor}/root/"
        ], check=True)

        subprocess.run([
            "lxc", "exec", nombre_contenedor, "--",
            "tar", "-xvzf", "/root/app.tar.gz", "-C", "/root"
        ], check=True)

        if ip_mongo:
            patch_app_mongo_url(nombre_contenedor, ip_mongo)

        # Instalar dependencias y lanzar forever
        subprocess.run([
            "lxc", "exec", nombre_contenedor, "--", "bash", "-c",
            "cd /root/app && npm install"
        ], check=True)

        #Instalar forever
        subprocess.run([
            "lxc", "exec", nombre_contenedor, "--", "npm", "install", "-g", "forever"
        ], check=True)


        subprocess.run([
            "lxc", "exec", nombre_contenedor, "--", "bash", "-c",
            "cd /root/app && forever start rest_server.js"
        ], check=True)

        log_info(f"Aplicación web desplegada correctamente en {nombre_contenedor}.")

    except subprocess.CalledProcessError as e:
        log_error(f"Error desplegando la aplicación web en {nombre_contenedor}: {e}")


def desplegar_aplicacion_web_masiva(num_servidores):
    ip_mongo = gestion_bbdd.obtener_ip_remota()
    log_info(f"Desplegando aplicación en {num_servidores} servidores...")
    for i in range(1, num_servidores + 1):
        nombre = f"s{i}"
        desplegar_aplicacion_web(nombre_contenedor=nombre, ip_mongo=ip_mongo)

def patch_app_mongo_url(nombre_cont, ip_mongo):
    files = ["/root/app/rest_server.js",
             "/root/app/md-seed-config.js"]
    for f in files:
        # forma sin puerto
        subprocess.run(
            ["lxc", "exec", nombre_cont, "--", "sed", "-i",
             f"s@mongodb://[^\"']*/bio_bbdd@mongodb://{ip_mongo}/bio_bbdd@g", f],
            check=True)

        # forma con :27017
        subprocess.run(
            ["lxc", "exec", nombre_cont, "--", "sed", "-i",
             f"s@mongodb://[^\"']*:27017/bio_bbdd@mongodb://{ip_mongo}:27017/bio_bbdd@g", f],
            check=True)





