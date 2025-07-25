"""
Rutas API refactorizadas
"""
from flask import Blueprint, jsonify, request, send_from_directory
from datetime import datetime
from services.data_service import DataManager
from config import Config

# Crear blueprint para las APIs
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Instancia global del manejador de datos (se inicializará en app.py)
data_manager: DataManager = None

def init_api(dm: DataManager):
    """Inicializar el blueprint con el data manager"""
    global data_manager
    data_manager = dm

@api_bp.route('/current_image')
def get_current_image():
    """Obtener información de la imagen actual"""
    if data_manager.is_finished():
        return jsonify({
            'finished': True,
            'message': 'Has revisado todas las imágenes',
            'total': len(data_manager.image_keys),
            'corrected_file': data_manager.corrected_json_path
        })
    
    image_data = data_manager.get_current_image()
    if not image_data:
        return jsonify({'error': 'No se pudo cargar la imagen'}), 500
    
    return jsonify({
        'finished': False,
        'image_key': image_data.key,
        'image_filename': image_data.filename,
        'transcription': image_data.transcription,
        'image_exists': image_data.exists,
        'current_index': image_data.index,
        'total': image_data.total,
        'progress': data_manager.get_progress_percentage()
    })

@api_bp.route('/submit_correction', methods=['POST'])
def submit_correction():
    """Procesar corrección del usuario"""
    data = request.json
    action = data.get('action')
    image_key = data.get('image_key')
    new_transcription = data.get('new_transcription', '')
    
    if data_manager.is_finished():
        return jsonify({'error': 'No hay más imágenes para revisar'}), 400
    
    success = data_manager.submit_correction(action, image_key, new_transcription)
    
    if not success:
        return jsonify({'error': 'Error al procesar la corrección'}), 400
    
    # Guardar progreso si es necesario
    config = Config()
    if data_manager.should_autosave(config.AUTOSAVE_INTERVAL):
        data_manager.save_progress()
    
    return jsonify({
        'success': True, 
        'next_index': data_manager.current_index
    })

@api_bp.route('/go_to_index', methods=['POST'])
def go_to_index():
    """Ir a un índice específico"""
    data = request.json
    new_index = data.get('index', 0)
    
    success = data_manager.go_to_index(new_index)
    
    if success:
        # Guardar progreso al cambiar de índice
        data_manager.save_progress()
        return jsonify({
            'success': True, 
            'current_index': data_manager.current_index
        })
    else:
        return jsonify({'error': 'Índice fuera de rango'}), 400

@api_bp.route('/stats')
def get_stats():
    """Obtener estadísticas del progreso"""
    stats = data_manager.get_stats()
    
    return jsonify({
        'total_original': stats.total_original,
        'total_current': len(data_manager.current_data),
        'reviewed': stats.reviewed,
        'remaining': stats.remaining,
        'correct': stats.correct,
        'edited': stats.edited,
        'discarded': stats.discarded,
        'progress_percent': data_manager.get_progress_percentage(),
        'error_rate': stats.error_rate,
        'edit_rate': stats.edit_rate,
        'discard_rate': stats.discard_rate
    })

@api_bp.route('/save_progress', methods=['POST'])
def manual_save_progress():
    """Guardar progreso manualmente"""
    try:
        data_manager.save_progress()
        return jsonify({
            'success': True,
            'message': 'Progreso guardado exitosamente',
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'file': data_manager.corrected_json_path
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error al guardar: {str(e)}'
        }), 500
