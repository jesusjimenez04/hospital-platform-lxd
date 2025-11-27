#Segunda parte del esquema: configuración de componentes, conectarlos
#Configuración de redes y bridges virtuales
import logging
from modulos.logger_config import log_info, log_error 
import subprocess

#Configuración bridges
def crear_bridges():
    log_info("Creando y configurando el bridge br0")
    subprocess.run(["lxc", "network", "create", "lxdbr0"])

    # Necesito separar la creación y configuración, sino LXD no toma como válida la IP 134.3.0.1/24
    subprocess.run(["lxc", "network", "set", "lxdbr0", "ipv4.address", "134.3.0.1/24"], check=True)
    subprocess.run(["lxc", "network", "set", "lxdbr0", "ipv4.nat", "true"], check=True)
    subprocess.run(["lxc", "network", "set", "lxdbr0", "ipv6.address", "none"], check=True)
    subprocess.run(["lxc", "network", "set", "lxdbr0", "ipv6.nat", "false"], check=True)

    log_info("Creando y configurando el bridge br1")
    subprocess.run(["lxc", "network", "create", "lxdbr1"])

    # Necesito separar la creación y configuración, sino LXD no toma como válida la IP 134.3.1.1/24
    subprocess.run(["lxc", "network", "set", "lxdbr1", "ipv4.address", "134.3.1.1/24"], check=True)
    subprocess.run(["lxc", "network", "set", "lxdbr1", "ipv4.nat", "true"], check=True)
    subprocess.run(["lxc", "network", "set", "lxdbr1", "ipv6.address", "none"], check=True)
    subprocess.run(["lxc", "network", "set", "lxdbr1", "ipv6.nat", "false"], check=True)

#Eliminar bridges
def eliminar_bridges():
	try:
		log_info("Eliminando bridge br0")
		subprocess.run(["lxc", "network", "delete", "lxdbr0"], check=True)
		log_info("Bridge lxdbr0 eliminado correctamente")
	except subprocess.CalledProcessError as e:
		log_error(f"Error eliminando bridge lxdbr0: {e}")

	try:
		log_info("Eliminando bridge br1")
		subprocess.run(["lxc", "network", "delete", "lxdbr1"], check=True)
		log_info("Bridge lxdbr1 eliminado correctamente")
	except subprocess.CalledProcessError as e:
		log_error(f"Error eliminando bridge lxdbr1: {e}")	
