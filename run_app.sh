#!/bin/bash

# Script para ejecutar la aplicación de anotación colaborativa con WSGI
set -e  # Salir si hay errores

echo "=== Iniciando aplicación de anotación colaborativa ==="

# Navegar al directorio de la aplicación  
cd /home/cristobal/Labeling_app

# Activar el entorno conda
source /home/cristobal/miniconda3/etc/profile.d/conda.sh
conda activate labeling_app

# Configurar variables de entorno para producción
export FLASK_ENV=production
export LOG_LEVEL=INFO
export JWT_SECRET_KEY=$(openssl rand -hex 32)  # Generar clave JWT segura
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

