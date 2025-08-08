#!/bin/bash

# Script para ejecutar la aplicación de anotación colaborativa con WSGI
set -e  # Salir si hay errores

echo "=== Iniciando aplicación de anotación colaborativa ==="

# Navegar al directorio de la aplicación  

# Configurar variables de entorno para producción
export FLASK_ENV=production
export HOST=0.0.0.0
export PORT=8080

# Verificar que Gunicorn está instalado
if ! command -v gunicorn &> /dev/null; then
    echo "Instalando Gunicorn..."
    pip install gunicorn
fi

echo "Configuración:"
echo "  Host: $HOST"
echo "  Puerto: $PORT" 
echo "  Log Level: $LOG_LEVEL"
echo "  Entorno: $FLASK_ENV"

# Ejecutar con Gunicorn usando archivo de configuración
echo "Iniciando servidor WSGI con Gunicorn..."
exec gunicorn --config gunicorn.conf.py wsgi:app

