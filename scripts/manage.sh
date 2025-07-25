#!/bin/bash

# Scripts de desarrollo y deployment

# Instalar dependencias
install-deps() {
    echo "🔧 Instalando dependencias..."
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
}

# Ejecutar tests
run-tests() {
    echo "🧪 Ejecutando tests..."
    python -m pytest tests/ -v --cov=services --cov=routes --cov-report=html --cov-report=term
}

# Linter y formateo
lint() {
    echo "🔍 Ejecutando linter..."
    flake8 services/ routes/ app_refactored.py config.py
    black services/ routes/ app_refactored.py config.py --check
}

# Formatear código
format() {
    echo "✨ Formateando código..."
    black services/ routes/ app_refactored.py config.py
    isort services/ routes/ app_refactored.py config.py
}

# Ejecutar aplicación en desarrollo
dev() {
    echo "🚀 Iniciando servidor de desarrollo..."
    export FLASK_ENV=development
    python app_refactored.py
}

# Ejecutar aplicación en producción
prod() {
    echo "🌐 Iniciando servidor de producción..."
    export FLASK_ENV=production
    gunicorn -w 4 -b 0.0.0.0:5000 app_refactored:create_app
}

# Crear backup de datos
backup() {
    echo "💾 Creando backup..."
    timestamp=$(date +%Y%m%d_%H%M%S)
    mkdir -p backups
    cp -r data/ backups/data_backup_$timestamp/
    echo "Backup creado en: backups/data_backup_$timestamp/"
}

# Deploy con Docker
docker-build() {
    echo "🐳 Construyendo imagen Docker..."
    docker build -t ocr-corrector .
}

docker-run() {
    echo "🐳 Ejecutando contenedor Docker..."
    docker run -p 5000:5000 -v $(pwd)/data:/app/data ocr-corrector
}

# Función principal
case "$1" in
    install)
        install-deps
        ;;
    test)
        run-tests
        ;;
    lint)
        lint
        ;;
    format)
        format
        ;;
    dev)
        dev
        ;;
    prod)
        prod
        ;;
    backup)
        backup
        ;;
    docker-build)
        docker-build
        ;;
    docker-run)
        docker-run
        ;;
    *)
        echo "Uso: $0 {install|test|lint|format|dev|prod|backup|docker-build|docker-run}"
        echo ""
        echo "Comandos disponibles:"
        echo "  install      - Instalar dependencias"
        echo "  test         - Ejecutar tests"
        echo "  lint         - Verificar código"
        echo "  format       - Formatear código"
        echo "  dev          - Servidor desarrollo"
        echo "  prod         - Servidor producción"
        echo "  backup       - Crear backup"
        echo "  docker-build - Construir imagen Docker"
        echo "  docker-run   - Ejecutar contenedor"
        exit 1
        ;;
esac
