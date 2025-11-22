# Hospital Management Practice - Replicated Web Server

## Functional Description

This project implements a hospital management application that allows for patient administration through a web interface accessible from different devices. The application is replicated across several servers to ensure fault tolerance and scalability.

The system includes:

- Several Node.js servers that provide the web service.
- A load balancer that transparently distributes requests among the available servers.
- A MongoDB database server to store persistent patient information.
- Deployment and configuration of the components in LXD containers, including the database, which can be hosted in a remote container for greater flexibility.

Additionally, the application allows for:

- Dynamic server management to adapt the system's capacity to demand.
- Remote access to the database using specific container configuration and proxy.

## Technical Explanation

The project is developed in Python with a main script `pfinal2.py` that automates the creation, configuration, and management of the necessary containers (web servers, database, and load balancer).

A load balancer has been configured to distribute incoming HTTP requests among the Node.js servers using a load-sharing algorithm, guaranteeing transparency to the user.

The MongoDB database runs in an LXD container, which can be on the same equipment or a remote machine. For remote deployment, secure access has been configured through LXD with certificates and a proxy to redirect connections.

The web servers interact with the database to manage patient information, ensuring data persistence and consistency.

The recommended modular structure has been followed to facilitate code maintenance and extension.
