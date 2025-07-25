"""
Configuración de la aplicación
"""
import os
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
    PORT: int = 5000
    
    @classmethod
    def from_env(cls):
        """Crear configuración desde variables de entorno"""
        return cls(
            IMAGES_FOLDER=os.getenv('IMAGES_FOLDER', cls.IMAGES_FOLDER),
            JSON_PATH=os.getenv('JSON_PATH', cls.JSON_PATH),
            AUTOSAVE_INTERVAL=int(os.getenv('AUTOSAVE_INTERVAL', cls.AUTOSAVE_INTERVAL)),
            DEBUG=os.getenv('DEBUG', 'True').lower() == 'true',
            HOST=os.getenv('HOST', cls.HOST),
            PORT=int(os.getenv('PORT', cls.PORT))
        )
