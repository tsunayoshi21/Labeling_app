"""
Aplicación principal refactorizada
"""
from flask import Flask, render_template, send_from_directory
from config import Config
from services.data_service import DataManager
from routes.api_routes import api_bp, init_api

def create_app():
    """Factory para crear la aplicación Flask"""
    app = Flask(__name__)
    
    # Cargar configuración
    config = Config.from_env()
    
    # Inicializar el manejador de datos
    data_manager = DataManager(config.JSON_PATH, config.IMAGES_FOLDER)
    data_manager.load_data()
    
    # Inicializar rutas API
    init_api(data_manager)
    app.register_blueprint(api_bp)
    
    # Rutas principales
    @app.route('/')
    def index():
        """Página principal"""
        return render_template('index_refactored.html')
    
    @app.route('/images/<filename>')
    def serve_image(filename):
        """Servir imágenes"""
        return send_from_directory(config.IMAGES_FOLDER, filename)
    
    # Información de inicio
    print(f"Servidor iniciado. Abre http://localhost:{config.PORT} en tu navegador")
    print(f"Imágenes desde: {config.IMAGES_FOLDER}")
    print(f"JSON original: {config.JSON_PATH}")
    print(f"Correcciones se guardarán en: {data_manager.corrected_json_path}")
    
    return app, config

if __name__ == '__main__':
    try:
        app, config = create_app()
        app.run(
            debug=config.DEBUG, 
            host=config.HOST, 
            port=config.PORT
        )
    except Exception as e:
        print(f"Error al iniciar la aplicación: {e}")
