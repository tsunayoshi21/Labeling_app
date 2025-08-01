#!/bin/bash

# Script para ejecutar la aplicación en modo desarrollo
set -e  # Salir si hay errores

echo "=== Iniciando aplicación en modo DESARROLLO ==="

# Navegar al directorio de la aplicación  
cd /home/cvasquez/Labeling_app

# Activar el entorno conda
source /home/cvasquez/miniconda3/etc/profile.d/conda.sh
conda activate labeling_app

# Configurar variables de entorno para desarrollo
export FLASK_ENV=development
export LOG_LEVEL=DEBUG
export DEBUG=true
export HOST=0.0.0.0
export PORT=8080

echo "Configuración de desarrollo:"
echo "  Host: $HOST"
echo "  Puerto: $PORT" 
echo "  Log Level: $LOG_LEVEL"
echo "  Debug: $DEBUG"
echo "  Entorno: $FLASK_ENV"

# Ejecutar directamente con Flask
echo "Iniciando servidor Flask en modo desarrollo..."
python app_sqlite.py
