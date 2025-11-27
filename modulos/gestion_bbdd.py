#Código para generar la imagen sobre la que se inicializará la BBDD
#La idea es:
#  1) Crear un contenedor base a partir de la imagen ubuntu2004
#  2) Personalizar este contenedor (al que llamaremos navegador)
#  3) Exportarlo a una imagen para tener una imagen propia personalizada
#  4) Crear los contenedores de la pŕactica inicializando esta imagen propia
#También se realizarán aquí todos los métodos relacionados con el despliegue de la BBDD

import subprocess
from modulos.logger_config import log_info, log_error, log_warning
import socket
import time

def realizar_configuraciones_bbdd(nombre_base: str = "mdbase",
                                  ip: str = "134.3.0.20") -> None:
    """
    Instala y configura MongoDB dentro del contenedor `nombre_base`.

    1. Arregla el DNS (añade 8.8.8.8).
    2. Instala MongoDB de forma no interactiva.
    3. Hace que escuche en todas las interfaces (`bind_ip = 0.0.0.0`).
    4. Reinicia el servicio para aplicar los cambios.
    """
    try:
        log_info("Instalando MongoDB en contenedor de base de datos…")

        # 1 ▪ Reparar DNS para evitar fallos de resolución
        subprocess.run(
            f"lxc exec {nombre_base} -- bash -c "
            "\"rm -f /etc/resolv.conf && echo 'nameserver 8.8.8.8' "
            "> /etc/resolv.conf\"",
            shell=True,
            check=True,
        )

        time.sleep(3)

        # 2 ▪ Install MongoDB de forma robusta
        subprocess.run(f"lxc exec {nombre_base} -- apt update",
                       shell=True, check=True)
        subprocess.run(
            "lxc exec {0} -- bash -c "
            "'DEBIAN_FRONTEND=noninteractive apt install -y mongodb "
            "|| echo \"MongoDB no disponible\"'".format(nombre_base),
            shell=True,
            check=True,
        )

        # 3 ▪ Asegurar que MongoDB escuche en todas las interfaces
        subprocess.run(
            f"lxc exec {nombre_base} -- "
            "sed -i 's/^bind_ip.*/bind_ip = 0.0.0.0/' /etc/mongodb.conf",
            shell=True,
            check=True,
        )

        # 4 ▪ Reiniciar MongoDB para aplicar los cambios
        subprocess.run(
            ["lxc", "exec", nombre_base, "--",
             "service", "mongodb", "restart"],
            check=True,
        )

        log_info(f"MongoDB instalado y configurado en {nombre_base}")

    except subprocess.CalledProcessError as e:
        log_error(f"Error configurando MongoDB: {e}")

def crear_imagen_bbdd(nombre_base="mdbase", alias="imagenmdb"):
	log_info(f"Creando imagen de MongoDB '{alias}' desde '{nombre_base}'")
	subprocess.run(["lxc", "stop", nombre_base])
	subprocess.run(["lxc", "publish", nombre_base, "--alias", alias])

def borrar_imagen_bbdd():
	log_info("Borrando contenedor con el que se inicializa la imagen mdbase")
	subprocess.run(["lxc", "delete", "mdbase"])

def desplegar_bbdd_remota(ip_local, ip_remota, password='mypassword'):
    try:
        log_info("Configurando acceso remoto a LXD en ambos equipos")

        # 1. Configurar LXD en ambos extremos
        subprocess.run(["lxc", "config", "set", "core.https_address", f"{ip_local}:8443"], check=True)
        subprocess.run(["ssh", f"{ip_remota}", f"lxc config set core.https_address {ip_remota}:8443"], check=True)
        subprocess.run(["ssh", f"{ip_remota}", f"lxc config set core.trust_password {password}"], check=True)

        # 2. Añadir remoto (eliminar primero si existe)
        subprocess.run(["lxc", "remote", "remove", "remoto"], check=False)
        subprocess.run([
            "lxc", "remote", "add", "remoto", f"{ip_remota}:8443",
            "--password", password, "--accept-certificate"
        ], check=True)

        # 3. Configurar red remota
        log_info("Configurando bridge remoto")
        subprocess.run(["lxc", "network", "set", "remoto:lxdbr0", "ipv4.address", "134.3.0.1/24"], check=True)
        subprocess.run(["lxc", "network", "set", "remoto:lxdbr0", "ipv4.nat", "true"], check=True)

        # 4. Crear contenedor remoto y darle IP fija
        log_info("Creando contenedor remoto con MongoDB")
        subprocess.run(["lxc", "init", "ubuntu2004", "remoto:db"], check=True)
        subprocess.run([
            "lxc", "config", "device", "override", "remoto:db", "eth0",
            "ipv4.address=134.3.0.20"
        ], check=True)
        subprocess.run(["lxc", "start", "remoto:db"], check=True)

        # 5. Arreglar DNS en remoto:db
        subprocess.run(
            "lxc exec remoto:db -- bash -c \"rm -f /etc/resolv.conf && echo 'nameserver 8.8.8.8' > /etc/resolv.conf\"",
            shell=True, check=True
        )

        time.sleep(5)

        # 6. Instalar MongoDB
        subprocess.run([
            "lxc", "exec", "remoto:db", "--", "bash", "-c",
            "DEBIAN_FRONTEND=noninteractive apt update && apt install -y mongodb || echo 'MongoDB no disponible'"
        ], check=True)

        # 7. Configurar proxy correctamente
        log_info("Configurando proxy para acceso a MongoDB")
        subprocess.run([
            "lxc", "config", "device", "remove", "remoto:db", "miproxy"
        ], check=False)  # por si ya existía

        subprocess.run(
            [
                "lxc", "config", "device", "add", "remoto:db",
                "miproxy", "proxy",
                f"listen=tcp:{ip_remota}:27017",
                "connect=tcp:134.3.0.20:27017"
            ],
            check=True
        )


        # 8. Reiniciar MongoDB
        subprocess.run(["lxc", "exec", "remoto:db", "--", "service", "mongodb", "restart"], check=True)

        log_info("Base de datos remota desplegada correctamente")

    except subprocess.CalledProcessError as e:
        log_error(f"Error durante el despliegue de la BBDD remota: {e}")


def obtener_ip_remota():
    try:
        nombre_remoto = input("Introduce el nombre corto del ordenador remoto (ej: l018): ").strip()
        nombre_completo = f"{nombre_remoto}.lab.dit.upm.es"
        ip = socket.gethostbyname(nombre_completo)
        log_info(f"Nombre remoto detectado: {nombre_completo} → IP: {ip}")
        return ip
    except Exception as e:
        log_error(f"No se pudo obtener la IP remota: {e}")
        return None


def obtener_ip_local():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	try:
		s.connect(("8.8.8.8", 80))
		ip = s.getsockname()[0]
	finally:
		s.close()
	return ip

def borrar_remoto(nombre_remoto="remoto", nombre_contenedor="db"):
    try:
        # Verificar si el contenedor remoto existe
        result = subprocess.run(
            ["lxc", "list", f"{nombre_remoto}:{nombre_contenedor}", "--format", "csv"],
            capture_output=True, text=True
        )
        if result.stdout.strip() == "":
            log_info(f"El contenedor {nombre_contenedor} no existe en remoto:{nombre_remoto}")
            return

        subprocess.run(["lxc", "delete", f"{nombre_remoto}:{nombre_contenedor}", "--force"], check=True)
        log_info(f"Contenedor remoto {nombre_contenedor} eliminado correctamente de {nombre_remoto}")
    except subprocess.CalledProcessError as e:
        log_error(f"Error al eliminar el contenedor remoto {nombre_contenedor}: {e}")

