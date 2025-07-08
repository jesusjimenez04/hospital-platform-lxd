#Fichero para logging y validaciones
#Jesús Jiménez Serrano
#Yago Gil Iglesias
import logging

logging.basicConfig(
	filename = 'logs/eventos.log',
	level = logging.DEBUG
	)

#Funciones de logging
def log_debug(mensaje):
	logging.debug(mensaje)

def log_info(mensaje):
	logging.info(mensaje)

def log_warning(mensaje):
	logging.warning(mensaje)

def log_error(mensaje):
	logging.error(mensaje)

def log_critical(mensaje):
	logging.critical(mensaje)

#Función de validación numérica
def validar_numero_servidores(n):
	if 1 <= n <= 5:
		return True
	else:
		log_error(f"Número de servidores invalido: {n}")
		return False	