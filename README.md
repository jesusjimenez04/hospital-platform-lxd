# Práctica Gestión Hospitalaria - Servidor Web Replicado

## Descripción funcional

Este proyecto implementa una aplicación de gestión hospitalaria que permite administrar pacientes a través de una interfaz web accesible desde diferentes dispositivos. La aplicación está replicada en varios servidores para asegurar tolerancia a fallos y escalabilidad.

El sistema incluye:

- Varios servidores Node.js que proporcionan el servicio web.
- Un balanceador de carga que distribuye las peticiones de forma transparente entre los servidores disponibles.
- Un servidor de base de datos MongoDB para almacenar la información persistente de los pacientes.
- Despliegue y configuración de los componentes en contenedores LXD, incluyendo la base de datos que puede estar alojada en un contenedor remoto para mayor flexibilidad.

Además, la aplicación permite:

- La gestión dinámica de servidores para adaptar la capacidad del sistema a la demanda.
- Acceso remoto a la base de datos mediante configuración específica del contenedor y proxy.

## Explicación técnica

El proyecto está desarrollado en Python con un script principal `pfinal2.py` que automatiza la creación, configuración y gestión de los contenedores necesarios (servidores web, base de datos y balanceador).

Se ha configurado un balanceador de carga que distribuye las peticiones HTTP entrantes entre los servidores Node.js usando un algoritmo de reparto de carga, garantizando la transparencia al usuario.

La base de datos MongoDB se ejecuta en un contenedor LXD, que puede estar en el mismo equipo o en una máquina remota. Para el despliegue remoto, se ha configurado el acceso seguro a través de LXD con certificados y un proxy para redirigir las conexiones.

Los servidores web interactúan con la base de datos para gestionar la información de pacientes, asegurando la persistencia y consistencia de los datos.

Se ha seguido la estructura modular recomendada para facilitar el mantenimiento y extensión del código.
