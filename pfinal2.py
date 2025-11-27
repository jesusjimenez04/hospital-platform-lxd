#Fichero principal que hace llamadas a todos los anteriores
import logging
from modulos import gestion_lxc, gestion_balanceador, gestion_red, gestion_imagen, gestion_individual, gestion_bbdd
from modulos.logger_config import log_info, log_error, validar_numero_servidores
import subprocess, sys

#Creación del método principal
def main():
    #Si no se introduce un número adecuado de parámetros:
    if len(sys.argv) < 2:
        log_error("No estás introduciendo los parámetros correctamente.")
        sys.exit(1) #el 1 indica que el programa cerró por un error

    orden = sys.argv[1]	
 
    #Una vez tenemos en una variable el valor del argumento, ejecutamos cada caso

    if orden == "create":
        num_servidores = int(sys.argv[2])
        
        if not validar_numero_servidores(num_servidores):
            sys.exit(1)

        #Guardamos en config.txt el nº de servidores pasado como parámetro
        #Ya que cada ejecución es separada y la variable se elimina cuando termina
        #Por ello, lo guardamos en un .txt externo para poder usarlo en otras órdenes 

        gestion_imagen.importar_imagen_ubuntu_base()
        gestion_imagen.importar_imagen_profesor()
        gestion_lxc.escribir_config(num_servidores)
        #gestion_imagen.crear_contenedor_base("navegador")
        #gestion_imagen.realizar_configuraciones_servidor("navegador")	
        #gestion_imagen.crear_imagen_personalizada("navegador", "imagenpers")
        #(ya no son necesarias estas funciones con la imagen dada por Óscar)
        gestion_red.crear_bridges()
        gestion_lxc.crear_servidores(num_servidores)
        gestion_balanceador.crear_balanceador()
        gestion_lxc.crear_cliente()
        gestion_balanceador.instalar_haproxy()
        gestion_balanceador.configurar_haproxy(num_servidores)

    elif orden == "configure":
        
        gestion_imagen.crear_contenedor_base("mdbase")
        gestion_bbdd.realizar_configuraciones_bbdd("mdbase", ip="134.3.0.20")
        gestion_bbdd.crear_imagen_bbdd("mdbase", "imagenmdb")
        ip_local = gestion_bbdd.obtener_ip_local()  # Dirección del host local
        ip_remota = gestion_bbdd.obtener_ip_remota()  # Dirección del host remoto
        gestion_bbdd.desplegar_bbdd_remota(ip_local, ip_remota)
        gestion_lxc.desplegar_aplicacion_web_masiva(gestion_lxc.leer_config())

    elif orden == "start":
        #Primero comprobamos si se ha llamado a create previamente
        #Para ello, debemos ver si el fichero config.txt ha sido creado
        num_servidores = gestion_lxc.leer_config()

        log_info("Ejecutando orden 'start'")
        gestion_lxc.arrancar_contenedores(num_servidores)	

    elif orden == "list":
        gestion_lxc.listar_contenedores()

    elif orden == "delete":
        #Primero comprobamos si se ha llamado a create previamente
        #Para ello, debemos ver si el fichero config.txt ha sido creado
        #Además, debemos coger el número de servidores que se haya creado
        num_servidores = gestion_lxc.leer_config()

        log_info(f"Ejecutando orden 'delete' con {num_servidores} servidores.")
        gestion_lxc.borrar_contenedores(num_servidores)
        gestion_red.eliminar_bridges()
        gestion_imagen.borrar_imagen_personalizada()
        gestion_bbdd.borrar_imagen_bbdd()
        gestion_bbdd.borrar_remoto()

    elif orden == "parar" or orden == "arrancar":
        if len(sys.argv) < 3:
            log_error("Debes indicar el nombre del servidor.")
            sys.exit(1)
        nombre_servidor = sys.argv[2]
        accion = sys.argv[1]
        gestion_individual.gestionar_servidor_individual(accion, nombre_servidor)

    elif orden == "crearuno":
        if len(sys.argv) < 3:
            log_error("Debes indicar el nombre del nuevo servidor.")
            sys.exit(1)
        nombre_servidor = sys.argv[2]

        #Comprobamos si se ha utilizado la imagen personalizada ya
        #Esto es, si se ha utilizado la orden "create" previamente
        num_servidores = gestion_lxc.leer_config()
        gestion_individual.crear_servidor_individual(nombre_servidor)

        #Añado el servidor al config.txt para que luego se borre con "delete"
        num_servidores += 1

        # Escribir el nuevo número en el archivo
        gestion_lxc.escribir_config(num_servidores)

    elif orden == "borraruno":
        if len(sys.argv) < 3:
            log_error("Debes indicar el nombre del servidor a borrar.")
            sys.exit(1)
        nombre_servidor = sys.argv[2]

        #Comprobamos si se ha creado algún servidor previamente
        #Para esto, debe existir el fichero cofnig.txt
        num_servidores = gestion_lxc.leer_config()
        gestion_individual.eliminar_servidor_individual(nombre_servidor)

        #Elimino el servidor al config.txt para que luego se borre con "delete"
        num_servidores -= 1

        # Escribir el nuevo número en el archivo
        gestion_lxc.escribir_config(num_servidores)

    elif orden == "enlarge":
        gestion_individual.enlarge()

    else:			
        log_error(f"Orden desconocida: {orden}")
        sys.exit(1)

if __name__ == "__main__":
    main()


