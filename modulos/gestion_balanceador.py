# Primera parte del esquema: creación de componentes
# Fichero para hacer operaciones sobre los contenedores: crear, borrar, listar...
#Jesús Jiménez Serrano
#Yago Gil Iglesias
import logging
from modulos.logger_config import log_info, log_error, log_warning
import subprocess
import time

def configurar_netplan_balanceador():
    # Desactivar cloud-init
    subprocess.run("lxc exec lb -- bash -c 'echo \"network: {config: disabled}\" > /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg'", shell=True, check=True)

    # Realizamos una copia de seguridad del archivo original
    subprocess.run("lxc exec lb -- cp /etc/netplan/50-cloud-init.yaml /etc/netplan/50-cloud-init.bak", shell=True, check=True)

    # Configuración de la interfaz eth1
    netplan_config = """\
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
    eth1:
      dhcp4: true
"""
    # Escribimos la nueva configuración en el archivo
    subprocess.run(f"echo \"{netplan_config}\" | lxc exec lb -- tee /etc/netplan/50-cloud-init.yaml", shell=True, check=True)

    # Reiniciamos el contenedor para asegurar que la configuración sea aplicada
    subprocess.run("lxc restart lb", shell=True, check=True)

    time.sleep(5)

    log_info("Configuración de red aplicada en el contenedor lb.")

# Creación del balanceador de carga
def crear_balanceador():
    try:
        log_info("Creando el balanceador 'lb'")
        subprocess.run(["lxc", "init", "ubuntu2004", "lb"], check=True)

        # Conectar interfaces correctamente
        subprocess.run(["lxc", "network", "attach", "lxdbr0", "lb", "eth0"], check=True)
        subprocess.run([
            "lxc", "config", "device", "set",
            "lb", "eth0", "ipv4.address", "134.3.0.10"
        ], check=True)

        subprocess.run(["lxc", "network", "attach", "lxdbr1", "lb", "eth1"], check=True)
        subprocess.run([
            "lxc", "config", "device", "set",
            "lb", "eth1", "ipv4.address", "134.3.1.10"
        ], check=True)

        #Arrancar el contenedor para poder aplicar el netplan
        subprocess.run(["lxc", "start", "lb"], check=True)

        time.sleep(5)
        
        #Aplicamos el método auxiliar
        configurar_netplan_balanceador()

        #Lo paramos para que no se inicialice "starteado"
        subprocess.run(["lxc", "stop", "lb"], check=True)

        time.sleep(5)

        log_info("Balanceador 'lb' creado correctamente (pendiente arrancar)")

    except subprocess.CalledProcessError as e:
        log_error(f"Error al crear balanceador 'lb': {e}")
    
# Configuración del software HAProxy para el balanceo de carga
def instalar_haproxy():
    try:
        log_info("Arrancando contenedor 'lb' para instalar HAProxy...")
        subprocess.run(["lxc", "start", "lb"], check=True)
        
        time.sleep(5)

        log_info("Reparando DNS en 'lb'...")
        # Reparar DNS
        subprocess.run([
            "lxc", "exec", "lb", "--", "bash", "-c",
            "echo 'nameserver 8.8.8.8' > /etc/resolv.conf"
        ], check=True)

        time.sleep(3)

        log_info("Instalando HAProxy en el balanceador 'lb'...")
        subprocess.run(["lxc", "exec", "lb", "--", "apt", "update"], check=True)
        subprocess.run(["lxc", "exec", "lb", "--", "apt", "install", "-y", "haproxy"], check=True)

        log_info("HAProxy instalado correctamente en 'lb'.")

    except subprocess.CalledProcessError as e:
        log_error(f"Error instalando HAProxy en lb: {e}")


 #Método para configurar el haproxy 
def configurar_haproxy(num_servidores):
    try:
        #Arrancar el contenedor 'lb'
        subprocess.run(["lxc", "start", "lb"], check=False)
        time.sleep(5)

        #Arrancar servidores para asegurar que están activos
        for i in range(1, num_servidores + 1):
            nombre = f"s{i}"
            subprocess.run(["lxc", "start", nombre], check=False)
            time.sleep(5)

        #Verificación de conectividad con Mongo (opcional)
        mongo_ok = subprocess.run(
            ["lxc", "exec", "lb", "--", "bash", "-c", "nc -zvw2 134.3.0.20 27017"],
            capture_output=True
        ).returncode == 0

        if mongo_ok:
            log_info("MongoDB está accesible desde lb.")
        else:
            log_warning("MongoDB no está accesible desde lb. La app puede fallar al lanzarse.")

        #Construir backend_servers sin comprobaciones condicionales
        backend_servers = ""
        for i in range(1, num_servidores + 1):
            backend_servers += f"    server webserver{i} 134.3.0.{10+i}:8001\n"
            log_info(f"Servidor webserver{i} añadido al backend HAProxy.")

        #Configuración completa del haproxy.cfg
        haproxy_cfg = f"""
global
    log /dev/log local0
    log /dev/log local1 notice
    chroot /var/lib/haproxy
    stats socket /run/haproxy/admin.sock mode 660 level admin
    stats timeout 30s
    user haproxy
    group haproxy
    daemon

    ca-base /etc/ssl/certs
    crt-base /etc/ssl/private
    ssl-default-bind-ciphers ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:ECDH+AES128:DH+AES:ECDH+3DES:DH+3DES:RSA+AESGCM:RSA+AES:RSA+3DES:!aNULL:!MD5:!DSS
    ssl-default-bind-options no-sslv3

defaults
    log global
    mode http
    option httplog
    option dontlognull
    timeout connect 5000
    timeout client 50000
    timeout server 50000
    errorfile 400 /etc/haproxy/errors/400.http
    errorfile 403 /etc/haproxy/errors/403.http
    errorfile 408 /etc/haproxy/errors/408.http
    errorfile 500 /etc/haproxy/errors/500.http
    errorfile 502 /etc/haproxy/errors/502.http
    errorfile 503 /etc/haproxy/errors/503.http
    errorfile 504 /etc/haproxy/errors/504.http

frontend firstbalance
    bind *:80
    option forwardfor
    default_backend webservers

backend webservers
    balance roundrobin
{backend_servers}
"""

        #Guardar y subir el fichero
        with open("haproxy.cfg", "w") as f:
            f.write(haproxy_cfg)

        subprocess.run(["lxc", "exec", "lb", "--", "mkdir", "-p", "/etc/haproxy"], check=True)
        subprocess.run(["lxc", "file", "push", "haproxy.cfg", "lb/etc/haproxy/"], check=True)
        log_info("Fichero haproxy.cfg subido correctamente al contenedor lb")

        #Validar y reiniciar HAProxy
        subprocess.run(["lxc", "exec", "lb", "--", "haproxy", "-f", "/etc/haproxy/haproxy.cfg", "-c"], check=True)
        subprocess.run(["lxc", "exec", "lb", "--", "service", "haproxy", "restart"], check=True)
        time.sleep(5)
        log_info("HAProxy instalado y configurado correctamente.")

    except subprocess.CalledProcessError as e:
        log_error(f"Error en configuración de HAProxy: {e}")

    finally:
        #Parar servidores
        for i in range(1, num_servidores + 1):
            try:
                subprocess.run(["lxc", "stop", f"s{i}", "--force"], check=True)
                time.sleep(5)
                log_info(f"Servidor s{i} parado correctamente.")
            except subprocess.CalledProcessError:
                log_warning(f"No se pudo parar s{i}, puede que ya esté detenido o no exista.")

        #Parar balanceador
        try:
            subprocess.run(["lxc", "stop", "lb", "--force"], check=True)
            time.sleep(5)
            log_info("Contenedor 'lb' parado correctamente.")
        except subprocess.CalledProcessError:
            log_warning("No se pudo parar 'lb', puede que ya esté detenido o no exista.")
