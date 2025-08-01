#!/bin/bash

# Script maestro para controlar la aplicación de anotación colaborativa
set -e

APP_DIR="/home/cvasquez/Labeling_app"
cd "$APP_DIR"

show_help() {
    echo "Uso: $0 {start|stop|restart|dev|status|logs}"
    echo ""
    echo "Comandos:"
    echo "  start   - Iniciar aplicación en producción con WSGI/Gunicorn"
    echo "  stop    - Detener aplicación" 
    echo "  restart - Reiniciar aplicación"
    echo "  dev     - Iniciar en modo desarrollo con Flask"
    echo "  status  - Mostrar estado de la aplicación"
    echo "  logs    - Mostrar logs de la aplicación"
    echo ""
    echo "Variables de entorno opcionales:"
    echo "  LOG_LEVEL=DEBUG|INFO|WARNING|ERROR"
    echo "  HOST=127.0.0.1|0.0.0.0"
    echo "  PORT=8080"
    echo "  WORKERS=4"
    exit 1
}

show_status() {
    echo "=== Estado de la aplicación ==="
    
    # Verificar procesos de Gunicorn
    GUNICORN_PIDS=$(pgrep -f "gunicorn.*wsgi:app" || true)
    if [ ! -z "$GUNICORN_PIDS" ]; then
        echo "✓ Gunicorn ejecutándose (PIDs: $GUNICORN_PIDS)"
        echo "  Puerto: $(netstat -tlnp 2>/dev/null | grep gunicorn | awk '{print $4}' | cut -d':' -f2 || echo 'desconocido')"
    else
        echo "✗ Gunicorn no está ejecutándose"
    fi
    
    # Verificar procesos de Flask
    FLASK_PIDS=$(pgrep -f "python.*app_sqlite.py" || true)
    if [ ! -z "$FLASK_PIDS" ]; then
        echo "✓ Flask desarrollo ejecutándose (PIDs: $FLASK_PIDS)"
    else
        echo "✗ Flask desarrollo no está ejecutándose"
    fi
    
    # Verificar base de datos
    if [ -f "labeling_app.db" ]; then
        echo "✓ Base de datos SQLite existe"
        DB_SIZE=$(du -h labeling_app.db | cut -f1)
        echo "  Tamaño: $DB_SIZE"
    else
        echo "✗ Base de datos SQLite no encontrada"
    fi
    
    # Verificar logs
    if [ -f "app.log" ]; then
        echo "✓ Archivo de log existe"
        LOG_SIZE=$(du -h app.log | cut -f1)
        echo "  Tamaño: $LOG_SIZE"
    else
        echo "ⓘ No hay archivo de log"
    fi
}

show_logs() {
    echo "=== Últimas 50 líneas del log ==="
    if [ -f "app.log" ]; then
        tail -n 50 app.log
    else
        echo "No se encontró archivo de log (app.log)"
    fi
}

case "${1:-}" in
    start)
        echo "Iniciando aplicación en modo producción..."
        ./scripts/run_app.sh
        ;;
    stop)
        ./scripts/stop_app.sh
        ;;
    restart)
        echo "Reiniciando aplicación..."
        ./scripts/stop_app.sh
        sleep 2
        ./scripts/run_app.sh
        ;;
    dev)
        echo "Iniciando aplicación en modo desarrollo..."
        ./scripts/run_dev.sh
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    *)
        show_help
        ;;
esac
