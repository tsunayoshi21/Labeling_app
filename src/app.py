"""
Aplicación Flask con SQLite para anotación colaborativa con JWT Auth
"""
from flask import Flask, render_template, send_from_directory, session
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
    
    # Configurar logging
    config.setup_logging()
    logger.info("Iniciando aplicación Flask con JWT Auth")
    
    # Configuración JWT
    app.config['JWT_SECRET_KEY'] = config.JWT_SECRET_KEY or os.urandom(32).hex()
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = config.JWT_ACCESS_TOKEN_EXPIRES
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = config.JWT_REFRESH_TOKEN_EXPIRES
    logger.debug(f"JWT configurado - Access token: {config.JWT_ACCESS_TOKEN_EXPIRES}min, Refresh: {config.JWT_REFRESH_TOKEN_EXPIRES}días")
    
    # Configuración de sesiones (mantenemos para compatibilidad temporal)
    app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Inicializar base de datos
    logger.info("Inicializando base de datos")
    db_manager = DatabaseManager(config.DATABASE_URL)
    db_manager.create_tables()
    db_manager.init_admin_user()
    logger.info("Base de datos inicializada correctamente")
    
    # Registrar blueprints
    app.register_blueprint(api_bp)
    logger.debug("Blueprint de API registrado")
    
    # Rutas principales
    @app.route('/')
    def index():
        """Página principal"""
        logger.debug("Acceso a página principal")
        if 'user_id' in session:
            logger.debug(f"Usuario logueado en sesión: {session.get('user_id')}")
            return render_template('sqlite_index.html')
        else:
            logger.debug("Usuario no logueado, redirigiendo a login")
            return render_template('sqlite_login.html')
    
    @app.route('/login')
    def login_page():
        """Página de login"""
        logger.debug("Acceso a página de login")
        return render_template('sqlite_login.html')
    
    @app.route('/admin')
    def admin_page():
        """Página de administración"""
        logger.debug("Acceso a página de administración")
        if 'user_id' not in session:
            logger.warning("Intento de acceso a admin sin sesión")
            return render_template('sqlite_login.html')
        
        # Verificar que sea admin
        from services.database_service import DatabaseService
        db_service = DatabaseService()
        user = db_service.get_user_by_id(session['user_id'])
        
        if not user or user.role != 'admin':
            logger.warning(f"Acceso denegado a admin para usuario {session.get('user_id')} con rol {user.role if user else 'None'}")
            return "Access denied", 403
        
        logger.info(f"Acceso concedido a panel admin para usuario {user.username}")
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
