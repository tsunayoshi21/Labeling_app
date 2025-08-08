"""
Configuración de la aplicación
"""
import os
import logging
from dataclasses import dataclass

@dataclass
class Config:
    # Rutas de archivos
    IMAGES_FOLDER: str = "data/words_cropped_raw"
    JSON_PATH: str = "data/words_raw_dict.json"
    
    # Configuración de guardado
    AUTOSAVE_INTERVAL: int = 10  # Guardar cada N imágenes
    
    # Configuración del servidor
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    
    # Configuración de seguridad JWT
    JWT_SECRET_KEY: str = None
    JWT_ACCESS_TOKEN_EXPIRES: int = 60  # minutos (1 hora)
    JWT_REFRESH_TOKEN_EXPIRES: int = 30  # días
    
    # Flask session secret
    FLASK_ENV: str = "development"  # development, production
    SECRET_KEY: str = None
    # Configuración de logging
    LOG_PATH: str = "logs/"
    LOG_LEVEL: str = "DEBUG"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FORMAT: str = "%(asctime)s - %(levelname)s - %(message)s"
    LOG_FILE: str = os.path.join(LOG_PATH, "app.log")
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5

    # DB Configuración
    DATABASE_URL: str = "sqlite:///labeling_app.db"

    @classmethod
    def from_env(cls):
        """Crear configuración desde variables de entorno"""
        return cls(
            IMAGES_FOLDER=os.getenv('IMAGES_FOLDER', cls.IMAGES_FOLDER),
            JSON_PATH=os.getenv('JSON_PATH', cls.JSON_PATH),
            AUTOSAVE_INTERVAL=int(os.getenv('AUTOSAVE_INTERVAL', cls.AUTOSAVE_INTERVAL)),
            DEBUG=os.getenv('DEBUG', 'True').lower() == 'true',
            HOST=os.getenv('HOST', cls.HOST),
            PORT=int(os.getenv('PORT', cls.PORT)),
            JWT_SECRET_KEY=os.getenv('JWT_SECRET_KEY'),
            JWT_ACCESS_TOKEN_EXPIRES=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', cls.JWT_ACCESS_TOKEN_EXPIRES)),
            JWT_REFRESH_TOKEN_EXPIRES=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', cls.JWT_REFRESH_TOKEN_EXPIRES)),
            SECRET_KEY=os.getenv('SECRET_KEY', cls.SECRET_KEY),
            FLASK_ENV=os.getenv('FLASK_ENV', 'development'),
            LOG_LEVEL=os.getenv('LOG_LEVEL', cls.LOG_LEVEL).upper(),
            LOG_FORMAT=os.getenv('LOG_FORMAT', cls.LOG_FORMAT),
            LOG_FILE=os.getenv('LOG_FILE', cls.LOG_FILE),
            LOG_MAX_BYTES=int(os.getenv('LOG_MAX_BYTES', cls.LOG_MAX_BYTES)),
            LOG_BACKUP_COUNT=int(os.getenv('LOG_BACKUP_COUNT', cls.LOG_BACKUP_COUNT)),
            DATABASE_URL=os.getenv('DATABASE_URL', cls.DATABASE_URL)
        )
    
    def setup_logging(self):
        """Configura el sistema de logging"""
        from logging.handlers import RotatingFileHandler
        
        # Obtener el nivel de logging
        level = getattr(logging, self.LOG_LEVEL, logging.DEBUG)
        
        # Crear formateador
        formatter = logging.Formatter(self.LOG_FORMAT)
        
        # Configurar logger raíz
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        
        # Limpiar handlers existentes
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # Handler para archivo con rotación
        try:
            file_handler = RotatingFileHandler(
                self.LOG_FILE,
                maxBytes=self.LOG_MAX_BYTES,
                backupCount=self.LOG_BACKUP_COUNT
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            logging.warning(f"No se pudo configurar el logging a archivo: {e}")
        
        # Configurar loggers específicos
        # Reducir verbosidad de loggers externos
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        
        logging.info(f"Sistema de logging configurado - Nivel: {self.LOG_LEVEL}")
        return root_logger

    def is_production(self):
        return self.FLASK_ENV == 'production'
    
    def validate_production_config(self):
        """Valida configuración crítica para producción"""
        if self.is_production():
            if not self.JWT_SECRET_KEY:
                raise ValueError("JWT_SECRET_KEY es obligatorio en producción")
            if not self.SECRET_KEY:
                raise ValueError("SECRET_KEY es obligatorio en producción")
            if len(self.JWT_SECRET_KEY) < 32:
                raise ValueError("JWT_SECRET_KEY debe tener al menos 32 caracteres")