"""
Servicios para manejo de datos
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class ImageData:
    """Datos de una imagen"""
    key: str
    filename: str
    transcription: str
    exists: bool
    index: int
    total: int

@dataclass
class Stats:
    """Estadísticas del progreso"""
    total_original: int
    reviewed: int
    remaining: int
    correct: int
    edited: int
    discarded: int
    error_rate: float
    edit_rate: float
    discard_rate: float

class DataManager:
    """Maneja los datos de transcripciones y progreso"""
    
    def __init__(self, json_path: str, images_folder: str):
        self.json_path = json_path
        self.images_folder = images_folder
        self.original_data = {}
        self.current_data = {}
        self.review_status = {}
        self.current_index = 0
        self.image_keys = []
        self.corrected_json_path = ""
        
    def load_data(self) -> None:
        """Cargar datos del JSON y buscar progreso previo"""
        self._validate_paths()
        self._load_original_data()
        self._setup_corrected_path()
        self._load_or_create_progress()
        self._setup_image_keys()
        
    def _validate_paths(self) -> None:
        """Validar que existan los archivos necesarios"""
        if not os.path.exists(self.json_path):
            raise FileNotFoundError(f"No se encontró el archivo JSON: {self.json_path}")
        
        if not os.path.exists(self.images_folder):
            raise FileNotFoundError(f"No se encontró la carpeta de imágenes: {self.images_folder}")
    
    def _load_original_data(self) -> None:
        """Cargar el JSON original"""
        with open(self.json_path, 'r', encoding='utf-8') as f:
            self.original_data = json.load(f)
    
    def _setup_corrected_path(self) -> None:
        """Configurar la ruta del archivo corregido"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_dir = os.path.dirname(self.json_path)
        json_name = os.path.splitext(os.path.basename(self.json_path))[0]
        self.corrected_json_path = os.path.join(json_dir, f"{json_name}_corrected_{timestamp}.json")
    
    def _load_or_create_progress(self) -> None:
        """Cargar progreso existente o crear uno nuevo"""
        progress_files = self._find_progress_files()
        
        if progress_files:
            self._load_latest_progress(progress_files)
        else:
            self._create_new_progress()
    
    def _find_progress_files(self) -> List[str]:
        """Buscar archivos de progreso existentes"""
        json_dir = os.path.dirname(self.json_path)
        json_name = os.path.splitext(os.path.basename(self.json_path))[0]
        
        progress_files = []
        for file in os.listdir(json_dir):
            if file.startswith(f"{json_name}_corrected_") and file.endswith('.json'):
                progress_files.append(os.path.join(json_dir, file))
        
        return progress_files
    
    def _load_latest_progress(self, progress_files: List[str]) -> None:
        """Cargar el progreso más reciente"""
        latest_progress = max(progress_files, key=os.path.getmtime)
        
        try:
            with open(latest_progress, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
            
            if isinstance(progress_data, dict) and 'data' in progress_data:
                # Formato nuevo
                self.current_data = progress_data['data']
                self.current_index = progress_data.get('current_index', 0)
                self.review_status = progress_data.get('review_status', {})
                self.corrected_json_path = latest_progress
                print(f"Reanudando progreso desde: {latest_progress}")
            else:
                # Formato antiguo
                self.current_data = progress_data
                self.current_index = 0
                self.review_status = {}
                self.corrected_json_path = latest_progress
                print(f"Archivo de progreso encontrado (formato antiguo): {latest_progress}")
                
        except Exception as e:
            print(f"Error al cargar progreso anterior: {e}")
            self._create_new_progress()
    
    def _create_new_progress(self) -> None:
        """Crear progreso nuevo"""
        self.current_data = self.original_data.copy()
        self.current_index = 0
        self.review_status = {}
    
    def _setup_image_keys(self) -> None:
        """Configurar las claves de imágenes"""
        self.image_keys = list(self.original_data.keys())
        print(f"Datos cargados: {len(self.image_keys)} imágenes totales")
        print(f"Progreso actual: imagen {self.current_index + 1} de {len(self.image_keys)}")
        print(f"Imágenes revisadas: {len(self.review_status)}")
    
    def get_current_image(self) -> Optional[ImageData]:
        """Obtener datos de la imagen actual"""
        if self.current_index >= len(self.image_keys):
            return None
        
        image_key = self.image_keys[self.current_index]
        image_filename = self._get_image_filename(image_key)
        transcription = self.current_data.get(image_key, "")
        
        image_path = os.path.join(self.images_folder, image_filename)
        image_exists = os.path.exists(image_path)
        
        return ImageData(
            key=image_key,
            filename=image_filename,
            transcription=transcription,
            exists=image_exists,
            index=self.current_index,
            total=len(self.image_keys)
        )
    
    def _get_image_filename(self, image_key: str) -> str:
        """Extraer nombre del archivo desde la clave"""
        return os.path.basename(image_key)
    
    def submit_correction(self, action: str, image_key: str, new_transcription: str = "") -> bool:
        """Procesar una corrección"""
        if action == 'correct':
            self.review_status[image_key] = 'correct'
        elif action == 'edit':
            if new_transcription.strip():
                self.current_data[image_key] = new_transcription.strip()
                self.review_status[image_key] = 'edited'
            else:
                return False
        elif action == 'discard':
            if image_key in self.current_data:
                del self.current_data[image_key]
            self.review_status[image_key] = 'discarded'
        
        self.current_index += 1
        return True
    
    def go_to_index(self, index: int) -> bool:
        """Ir a un índice específico"""
        if 0 <= index < len(self.image_keys):
            self.current_index = index
            return True
        return False
    
    def get_stats(self) -> Stats:
        """Obtener estadísticas del progreso"""
        total_original = len(self.original_data)
        reviewed_count = len(self.review_status)
        correct_count = sum(1 for status in self.review_status.values() if status == 'correct')
        edited_count = sum(1 for status in self.review_status.values() if status == 'edited')
        discarded_count = sum(1 for status in self.review_status.values() if status == 'discarded')
        remaining = len(self.image_keys) - self.current_index
        
        # Calcular porcentajes
        error_rate = 0
        edit_rate = 0
        discard_rate = 0
        
        if reviewed_count > 0:
            error_rate = round(((edited_count + discarded_count) / reviewed_count) * 100, 1)
            edit_rate = round((edited_count / reviewed_count) * 100, 1)
            discard_rate = round((discarded_count / reviewed_count) * 100, 1)
        
        return Stats(
            total_original=total_original,
            reviewed=reviewed_count,
            remaining=remaining,
            correct=correct_count,
            edited=edited_count,
            discarded=discarded_count,
            error_rate=error_rate,
            edit_rate=edit_rate,
            discard_rate=discard_rate
        )
    
    def save_progress(self) -> None:
        """Guardar progreso actual"""
        progress_data = {
            'data': self.current_data,
            'current_index': self.current_index,
            'review_status': self.review_status,
            'original_count': len(self.original_data),
            'timestamp': datetime.now().isoformat()
        }
        
        with open(self.corrected_json_path, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
    
    def should_autosave(self, autosave_interval: int) -> bool:
        """Determinar si debe guardar automáticamente"""
        return (self.current_index % autosave_interval == 0 or 
                self.current_index >= len(self.image_keys))
    
    def is_finished(self) -> bool:
        """Verificar si se han revisado todas las imágenes"""
        return self.current_index >= len(self.image_keys)
    
    def get_progress_percentage(self) -> float:
        """Obtener porcentaje de progreso"""
        if not self.image_keys:
            return 0.0
        return round((self.current_index / len(self.image_keys)) * 100, 1)
