"""
Aplicación Flask con SQLite para anotación colaborativa con JWT Auth
"""
from flask import Flask, render_template, send_from_directory, session, redirect, request
import os
import logging
from config import Config
from routes.sqlite_api_routes_jwt import api_bp  # Cambiado a JWT
from models.database import DatabaseManager

# Configurar logger para este módulo
logger = logging.getLogger(__name__)

def create_app():
    """Factory para crear la aplicación Flask con SQLite y JWT"""
    app = Flask(__name__)
    
    # Cargar configuración
    config = Config.from_env()

    # Validar configuración en producción
    if config.is_production():
        config.validate_production_config()
    
    # Configuración JWT mejorada
    if config.JWT_SECRET_KEY:
        app.config['JWT_SECRET_KEY'] = config.JWT_SECRET_KEY
    else:
        if config.is_production():
            raise ValueError("JWT_SECRET_KEY es obligatorio en producción")
        else:
            # Solo para desarrollo - generar clave temporal
            app.config['JWT_SECRET_KEY'] = os.urandom(32).hex()
            logger.warning("⚠️  Usando JWT_SECRET_KEY temporal para desarrollo")
    
    # Flask session secret
    if config.SECRET_KEY:
        app.secret_key = config.SECRET_KEY
    else:
        if config.is_production():
            raise ValueError("SECRET_KEY es obligatorio en producción")
        else:
            app.secret_key = 'dev-secret-key-change-in-production'
            logger.warning("⚠️  Usando SECRET_KEY temporal para desarrollo")

    # Configurar logging
    config.setup_logging()
    logger.info("Iniciando aplicación Flask con JWT Auth")
    
    # Configuración JWT
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = config.JWT_ACCESS_TOKEN_EXPIRES
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = config.JWT_REFRESH_TOKEN_EXPIRES
    logger.debug(f"JWT configurado - Access token: {config.JWT_ACCESS_TOKEN_EXPIRES}min, Refresh: {config.JWT_REFRESH_TOKEN_EXPIRES}días")
    
    app.config["DATABASE_URL"] = config.DATABASE_URL  
    # Inicializar base de datos
    logger.info("Inicializando base de datos")
    db_manager = DatabaseManager(config.DATABASE_URL)
    db_manager.create_tables()
    db_manager.init_admin_user()
    logger.info("Base de datos inicializada correctamente")
    
    # Registrar blueprints
    app.register_blueprint(api_bp)
    logger.debug("Blueprint de API registrado")
    
    # Importar decoradores de autenticación
    from services.jwt_service import optional_auth, require_admin, require_auth
    
    # Rutas principales
    @app.route('/')
    @require_auth
    def index():
        """Página principal - autenticación opcional"""
        logger.debug("Acceso a página principal")
        
        if hasattr(request, 'current_user') and request.current_user:
            logger.debug(f"Usuario autenticado accediendo a index: {request.current_user.get('username')}")
        else:
            logger.debug("Acceso a index sin autenticación")
        
        return render_template('sqlite_index.html')
    
    @app.route('/login')
    @optional_auth
    def login_page():
        """Página de login - redirige si ya está autenticado"""
        logger.debug("Acceso a página de login")
        
        # Si ya está autenticado, redirigir según rol
        if hasattr(request, 'current_user') and request.current_user:
            user = request.current_user
            logger.debug(f"Usuario {user.get('username')} ya autenticado, redirigiendo")
            if user.get('role') == 'admin':
                return redirect('/admin')
            else:
                return redirect('/')
        
        return render_template('sqlite_login.html')
    
    @app.route('/admin')
    @require_admin
    def admin_page():
        """Página de administración - REQUIERE AUTENTICACIÓN DE ADMIN"""
        logger.debug("Acceso a página de administración")
        
        user = request.current_user
        logger.info(f"Acceso concedido a panel admin para usuario {user.get('username')}")
        return render_template('sqlite_admin.html')
    
    @app.route('/images/<filename>')
    def serve_image(filename):
        """Servir imágenes"""
        logger.debug(f"Sirviendo imagen: {filename}")
        try:
            return send_from_directory(config.IMAGES_FOLDER, filename)
        except Exception as e:
            logger.error(f"Error sirviendo imagen {filename}: {e}")
            return "Image not found", 404
    
    # Información de inicio
    logger.info("=== Aplicación SQLite con JWT iniciada ===")
    logger.info(f"Servidor: http://localhost:{config.PORT}")
    logger.info(f"Imágenes: {config.IMAGES_FOLDER}")
    logger.info(f"Base de datos: labeling_app.db")
    logger.info(f"Autenticación: JWT (tokens)")
    logger.info(f"Log Level: {config.LOG_LEVEL}")
    logger.info("Credenciales por defecto: Admin: admin / admin123")
    logger.info("===========================================")
    
    return app, config

if __name__ == '__main__':
    try:
        logger.info("Iniciando aplicación desde main")
        app, config = create_app()
        logger.info(f"Ejecutando servidor en {config.HOST}:{config.PORT} (debug={config.DEBUG})")
        app.run(
            debug=config.DEBUG, 
            host=config.HOST, 
            port=config.PORT
        )
    except Exception as e:
        logger.critical(f"Error crítico iniciando la aplicación: {e}")
        import traceback
        logger.error(traceback.format_exc())
