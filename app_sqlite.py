"""
Aplicación Flask con SQLite para anotación colaborativa
"""
from flask import Flask, render_template, send_from_directory, session
import os
from config import Config
from routes.sqlite_api_routes import sqlite_api_bp
from models.database import DatabaseManager

def create_sqlite_app():
    """Factory para crear la aplicación Flask con SQLite"""
    app = Flask(__name__)
    
    # Cargar configuración
    config = Config.from_env()
    
    # Configuración de sesiones
    app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Inicializar base de datos
    db_manager = DatabaseManager()
    db_manager.create_tables()
    db_manager.init_admin_user()
    
    # Registrar blueprints
    app.register_blueprint(sqlite_api_bp)
    
    # Rutas principales
    @app.route('/')
    def index():
        """Página principal"""
        if 'user_id' in session:
            return render_template('sqlite_index.html')
        else:
            return render_template('sqlite_login.html')
    
    @app.route('/login')
    def login_page():
        """Página de login"""
        return render_template('sqlite_login.html')
    
    @app.route('/admin')
    def admin_page():
        """Página de administración"""
        if 'user_id' not in session:
            return render_template('sqlite_login.html')
        
        # Verificar que sea admin
        from services.database_service import DatabaseService
        db_service = DatabaseService()
        user = db_service.get_user_by_id(session['user_id'])
        
        if not user or user.role != 'admin':
            return "Access denied", 403
        
        return render_template('sqlite_admin.html')
    
    @app.route('/images/<filename>')
    def serve_image(filename):
        """Servir imágenes"""
        return send_from_directory(config.IMAGES_FOLDER, filename)
    
    # Información de inicio
    print(f"=== Aplicación SQLite iniciada ===")
    print(f"Servidor: http://localhost:{config.PORT}")
    print(f"Imágenes: {config.IMAGES_FOLDER}")
    print(f"Base de datos: labeling_app.db")
    print(f"Credenciales por defecto:")
    print(f"  Admin: admin / admin123")
    print(f"=====================================")
    
    return app, config

if __name__ == '__main__':
    try:
        app, config = create_sqlite_app()
        app.run(
            debug=config.DEBUG, 
            host=config.HOST, 
            port=config.PORT
        )
    except Exception as e:
        print(f"Error iniciando la aplicación: {e}")
        import traceback
        traceback.print_exc()
