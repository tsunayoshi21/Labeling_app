#!/bin/bash

# Script para detener la aplicación de anotación colaborativa
echo "=== Deteniendo aplicación de anotación colaborativa ==="

# Buscar procesos de Gunicorn
PIDS=$(pgrep -f "gunicorn.*wsgi:app" || true)

if [ -z "$PIDS" ]; then
    echo "No se encontraron procesos de Gunicorn ejecutándose"
else
    echo "Deteniendo procesos de Gunicorn: $PIDS"
    kill $PIDS
    
    # Esperar un poco y verificar
    sleep 2
    
    # Forzar terminación si es necesario
    REMAINING=$(pgrep -f "gunicorn.*wsgi:app" || true)
    if [ ! -z "$REMAINING" ]; then
        echo "Forzando terminación de procesos restantes: $REMAINING"
        kill -9 $REMAINING
    fi
    
    echo "Aplicación detenida exitosamente"
fi

# También buscar procesos de Flask en desarrollo
FLASK_PIDS=$(pgrep -f "python.*app_sqlite.py" || true)
if [ ! -z "$FLASK_PIDS" ]; then
    echo "Deteniendo procesos de Flask: $FLASK_PIDS"
    kill $FLASK_PIDS
fi

echo "Limpieza completada"
