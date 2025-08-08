"""
Archivo WSGI para ejecutar la aplicación Flask en producción
"""
import os
import sys
import logging

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(__file__))

# Importar la aplicación
from app import create_app

# Crear la aplicación Flask
app, config = create_app()

# Configurar logging para WSGI/Gunicorn
if __name__ != "__main__":
    # Solo configurar si estamos corriendo bajo WSGI (no en desarrollo directo)
    gunicorn_logger = logging.getLogger('gunicorn.error')
    if gunicorn_logger.handlers:
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)
        logging.info("Configuración de logging sincronizada con Gunicorn")

# Para desarrollo directo (cuando se ejecuta python wsgi.py)
if __name__ == "__main__":
    print("Ejecutando en modo desarrollo directo desde wsgi.py")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
