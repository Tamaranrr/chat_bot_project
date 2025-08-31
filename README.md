# 🤖 Chatbot IA – Proyecto con FastAPI

Este es un chatbot inteligente construido con Python, FastAPI y SQLAlchemy. El objetivo principal del proyecto es mantener conversaciones con los usuarios, clasificarlas en categorías como ventas, soporte o general, y responder de forma dinámica teniendo en cuenta el contexto. También cuenta con una API funcional y una interfaz de usuario básica para pruebas.

---------------------------------------------------------------------------------------------

# ✅ Funcionalidades implementadas

- Creación y gestión de conversaciones
- Persistencia en base de datos (PostgreSQL para pruebas)
- Clasificación automática del mensaje en categorías (ventas, soporte, general)
- Flujo conversacional con contexto (mantiene el estado)
- Derivación a agente humano si se requiere
- Sistema de métricas globales
- Respuestas adaptadas al contexto y la categoría
- Interfaz web simple para pruebas
- Logging de eventos y errores
- Manejo de excepciones global
- Soporte para tokens y recuperación semántica (con corpus embebido)

---------------------------------------------------------------------------------------------

## 🧠 Tecnologías utilizadas

Tecnología	                    Uso	                                            Justificación

Python 3.x	                    Lenguaje base	                                Versátil y con excelente ecosistema para IA y web APIs
FastAPI	                        API RESTful	                                    Rápido, moderno, tipado y con documentación Swagger automática
SQLAlchemy	                    ORM	                                            Manejo robusto y flexible de bases de datos relacionales
Pydantic	                    Validación de datos con tipado	                Facilita validación estricta de entradas/salidas
PostgreSQL / SQLite	            Base de datos relacional	                    Persistencia de conversaciones y métricas
Uvicorn	                        Servidor ASGI	                                Soporte para apps asincrónicas
pytest	                        Pruebas unitarias	                            Mantenimiento del código mediante testing
dotenv	                        Variables de entorno desde archivo	            Configuración desacoplada del entorno de ejecución
logging	                        Registro de eventos del sistema	                Ayuda al monitoreo y debugging

---------------------------------------------------------------------------------------------
## ✅ Prerrequisitos

-Python 3.10 o superior
-Rust
-PostgreSQL instalado (opcional si usas SQLite)
-Git
-Visual Studio 

---------------------------------------------------------------------------------------------
## 📁 Estructura del proyecto

chat_bot_project/
│
├── app/
│ ├── main_api.py                       # API principal y endpoints
│ ├── bot.py                            # Lógica del chatbot
│ ├── db.py                             # Configuración de la base de datos
│ ├── models.py                         # Modelos ORM de SQLAlchemy
│ ├── repository.py                     # Funciones que interactúan con la base de datos
│ ├── conversation.py                   # Manejo de estado y flujo de conversación
│ ├── retrieval.py                      # Normalización y recuperación semántica
│ ├── semantic_service.py               # Búsqueda semántica de respuestas
│ ├── utils/
│ │ └── logger.py                       # Configuración de logs
│ └── static/                           # Página web estática de prueba
│
├── scripts/
│ └── init_db.py                        # Script para inicializar la base de datos
│
├── test/                               # Tests automáticos con pytest
│ └── test_api.py
|
├── .env                                # Variables de entorno
├── requirements.txt                    # Dependencias
└── README.md                           # Documentación del proyecto

---------------------------------------------------------------------------------------------

## ⚙️ Instalación paso a paso

1. Clona el repositorio
    -git clone https://github.com/tu_usuario/chat_bot_project.git
    -cd chat_bot_project

2. Crea un entorno virtual

    -python -m venv .venv

3. Activa el entorno

    a. En Windows:          .venv\Scripts\activate
    b. En Linux / macOS:    source .venv/bin/activate

4. Instala los paquetes requeridos

    - pip install -r requirements.txt

5. Crea un archivo .env con la URL de conexión a la base de datos:

    Ejemplo para PostgreSQL:

    - DATABASE_URL=postgresql+psycopg2://usuario:contraseña@localhost:5432/chatbot_ia

6. Inicializa la base de datos

    - python scripts/init_db.py

---------------------------------------------------------------------------------------------

## ⚙️ Cómo ejecutar el proyecto
Con el entorno virtual activado insertar en la terminal:

    - uvicorn app.main_api:app --reload

Esto levantará el servidor en:

    -API interactiva: http://localhost:8000/docs
    -Interfaz web simple (opcional): http://localhost:8000/

---------------------------------------------------------------------------------------------

## 📡 Endpoints principales
Método	      |      Ruta	                        |   Descripción
GET     	  |      /	                            |   Verifica que el servidor esté activo
POST	      |      /conversations	                |   Crea una nueva conversación
GET	          |      /conversations	                |   Lista todas las conversaciones
GET	          |      /conversations/{id}	        |   Obtiene una conversación por ID
GET	          |      /conversations/{id}/messages	|   Lista los mensajes de una conversación
DELETE	      |      /conversations/{id}/messages	|   Reinicia una conversación
POST	      |      /chat	                        |   Envía un mensaje al bot
GET	          |      /metrics	                    |   Devuelve métricas generales
POST	      |      /conversations/{id}/close	    |   Marca la conversación como cerrada

---------------------------------------------------------------------------------------------

## 🧪 Pruebas automáticas
El proyecto incluye varios tests automáticos con pytest para asegurar el funcionamiento del bot.

Para ejecutarlos insertar en la terminal:

    -pytest

---------------------------------------------------------------------------------------------

## 🧠 Procesamiento de lenguaje natural

    -Las frases del usuario son analizadas y clasificadas.
    -Se realiza recuperación semántica en un corpus definido.
    -Las respuestas se generan basadas en la categoría detectada y el contexto previo.
    -Se consideran parámetros como plan, país, usuarios, etc. para ventas.

---------------------------------------------------------------------------------------------

## 🧩 Gestión del contexto y flujo

    -Cada conversación guarda su historial de mensajes.
    -El bot mantiene el contexto entre mensajes usando ConversationState.
    -Es posible reiniciar una conversación y empezar desde cero.
    -Se derivan mensajes confusos o mal clasificados a un agente humano si es necesario.

---------------------------------------------------------------------------------------------

## 🌐 Interfaz de usuario

    -Se incluye una interfaz HTML/CSS básica dentro del directorio app/static/.
    -Se sirve automáticamente al acceder a http://localhost:8000/.

---------------------------------------------------------------------------------------------

## 📦 Notas adicionales

    -El código está modularizado y organizado por responsabilidad.
    -El logger centralizado permite rastrear errores y actividad.
    -El sistema de excepciones global mejora la resiliencia.
    -Puedes cambiar fácilmente entre SQLite y PostgreSQL según el entorno.

---------------------------------------------------------------------------------------------

## Dificultades encontradas y soluciones

                Dificultad	                                                                                Solución implementada

    1. Mantener el contexto de conversación                                         Se implementó una clase ConversationState para rehidratar el historial y  
                entre intercambios	                                                                    reconstruir el estado conversacional

    2. Clasificar intenciones (ventas, soporte, general)                                    Se usaron reglas simples con expresiones regulares 
                sin modelos pesados	                                                                para simular clasificación contextual

    3. Separar configuración según entorno (dev, prod)	                                        Se introdujo uso de archivo .env y os.getenv() 
                                                                                                    para lectura de configuración externa

    4. Manejo de errores en FastAPI	                                                        Se agregaron handlers globales para errores de validación, 
                                                                                                        SQLAlchemy y excepciones generales

    5. Medición de métricas de uso del chatbot	                                        Se añadieron contadores en base de datos (por estado, categoría, 
                                                                                                        mensajes) para endpoints /metrics
---------------------------------------------------------------------------------------------


## ✅ Estado del proyecto

    -API REST con FastAPI
    -Persistencia en base de datos
    -Múltiples endpoints (conversaciones, mensajes, métricas)
    -Manejo de contexto entre intercambios
    -Interfaz web embebida (HTML estático)
    -Manejo de excepciones y logging
    -Soporte para SQLite y PostgreSQL
    -Pruebas unitarias con pytest
    -Configuración externa por .env

---------------------------------------------------------------------------------------------

## 📄 Licencia
    -Este proyecto se distribuye bajo la Licencia MIT. Puedes usarlo, modificarlo y distribuirlo libremente.

---------------------------------------------------------------------------------------------

## ✍️ Autor
    -Desarrollado por Nicoll Rengifo
    -Se desarrollo en base a una prueba tecnica

---------------------------------------------------------------------------------------------
