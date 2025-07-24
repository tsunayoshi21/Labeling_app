import os
import json
import shutil
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from pathlib import Path

app = Flask(__name__)

# PARÁMETROS PARA CONFIGURAR - MODIFICA ESTAS RUTAS
IMAGES_FOLDER = "data/words_cropped_raw"  # Ruta a la carpeta de imágenes
JSON_PATH = "data/words_raw_dict.json"    # Ruta al JSON original

# Variables globales
current_data = {}
original_data = {}
current_index = 0
image_keys = []
corrected_json_path = ""

def load_data():
    """Cargar datos del JSON y crear una copia de trabajo"""
    global current_data, original_data, image_keys, corrected_json_path, current_index
    
    # Verificar que existan los archivos
    if not os.path.exists(JSON_PATH):
        raise FileNotFoundError(f"No se encontró el archivo JSON: {JSON_PATH}")
    
    if not os.path.exists(IMAGES_FOLDER):
        raise FileNotFoundError(f"No se encontró la carpeta de imágenes: {IMAGES_FOLDER}")
    
    # Cargar JSON original
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        original_data = json.load(f)
    
    # Crear nombre para el JSON corregido
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_dir = os.path.dirname(JSON_PATH)
    json_name = os.path.splitext(os.path.basename(JSON_PATH))[0]
    corrected_json_path = os.path.join(json_dir, f"{json_name}_corrected_{timestamp}.json")
    
    # Buscar archivo de progreso existente
    progress_files = []
    for file in os.listdir(json_dir):
        if file.startswith(f"{json_name}_corrected_") and file.endswith('.json'):
            progress_files.append(os.path.join(json_dir, file))
    
    # Si hay archivos de progreso, usar el más reciente
    if progress_files:
        latest_progress = max(progress_files, key=os.path.getmtime)
        try:
            with open(latest_progress, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
            
            # Verificar si el archivo tiene el formato nuevo (con metadatos)
            if isinstance(progress_data, dict) and 'data' in progress_data:
                current_data = progress_data['data']
                current_index = progress_data.get('current_index', 0)
                corrected_json_path = latest_progress
                print(f"Reanudando progreso desde: {latest_progress}")
                print(f"Continuando desde la imagen {current_index + 1}")
            else:
                # Formato antiguo, solo los datos
                current_data = progress_data
                current_index = 0
                corrected_json_path = latest_progress
                print(f"Archivo de progreso encontrado (formato antiguo): {latest_progress}")
        except Exception as e:
            print(f"Error al cargar progreso anterior: {e}")
            current_data = original_data.copy()
            current_index = 0
    else:
        # No hay progreso previo, empezar desde cero
        current_data = original_data.copy()
        current_index = 0
    
    # Obtener lista de claves (nombres de imágenes) del archivo original
    # para mantener el orden original
    image_keys = list(original_data.keys())
    
    print(f"Datos cargados: {len(image_keys)} imágenes totales")
    print(f"Progreso actual: imagen {current_index + 1} de {len(image_keys)}")
    print(f"Las correcciones se guardarán en: {corrected_json_path}")

def save_progress():
    """Guardar progreso actual en el JSON de correcciones"""
    progress_data = {
        'data': current_data,
        'current_index': current_index,
        'original_count': len(original_data),
        'timestamp': datetime.now().isoformat()
    }
    with open(corrected_json_path, 'w', encoding='utf-8') as f:
        json.dump(progress_data, f, ensure_ascii=False, indent=2)

def get_image_filename(image_key):
    """Extraer el nombre del archivo de imagen desde la clave del JSON"""
    # La clave puede tener formato como "resultados/words_cropped_raw/img_00000000000.jpg"
    return os.path.basename(image_key)

@app.route('/')
def index():
    """Página principal"""
    #return render_template('index_simple.html')
    return render_template('index.html')

@app.route('/test')
def test():
    """Página de test"""
    return render_template('test.html')

@app.route('/api/current_image')
def get_current_image():
    """Obtener información de la imagen actual"""
    global current_index
    
    if current_index >= len(image_keys):
        return jsonify({
            'finished': True,
            'message': 'Has revisado todas las imágenes',
            'total': len(image_keys),
            'corrected_file': corrected_json_path
        })
    
    image_key = image_keys[current_index]
    image_filename = get_image_filename(image_key)
    transcription = current_data[image_key]
    
    # Verificar si la imagen existe
    image_path = os.path.join(IMAGES_FOLDER, image_filename)
    image_exists = os.path.exists(image_path)
    
    return jsonify({
        'finished': False,
        'image_key': image_key,
        'image_filename': image_filename,
        'transcription': transcription,
        'image_exists': image_exists,
        'current_index': current_index,
        'total': len(image_keys),
        'progress': round((current_index / len(image_keys)) * 100, 1)
    })

@app.route('/api/submit_correction', methods=['POST'])
def submit_correction():
    """Procesar corrección del usuario"""
    global current_index
    
    data = request.json
    action = data.get('action')
    image_key = data.get('image_key')
    
    if current_index >= len(image_keys):
        return jsonify({'error': 'No hay más imágenes para revisar'})
    
    if action == 'correct':
        # La transcripción es correcta, no hacer nada
        pass
    elif action == 'edit':
        # Actualizar con la transcripción corregida
        new_transcription = data.get('new_transcription', '').strip()
        if new_transcription:
            current_data[image_key] = new_transcription
    elif action == 'discard':
        # Eliminar la entrada del diccionario
        if image_key in current_data:
            del current_data[image_key]
    
    # Avanzar al siguiente
    current_index += 1
    
    # Guardar progreso cada 10 imágenes o al finalizar
    if current_index % 10 == 0 or current_index >= len(image_keys):
        save_progress()
    
    return jsonify({'success': True, 'next_index': current_index})

@app.route('/api/go_to_index', methods=['POST'])
def go_to_index():
    """Ir a un índice específico"""
    global current_index
    
    data = request.json
    new_index = data.get('index', 0)
    
    if 0 <= new_index < len(image_keys):
        current_index = new_index
        return jsonify({'success': True, 'current_index': current_index})
    else:
        return jsonify({'error': 'Índice fuera de rango'})

@app.route('/images/<filename>')
def serve_image(filename):
    """Servir imágenes"""
    return send_from_directory(IMAGES_FOLDER, filename)

@app.route('/api/stats')
def get_stats():
    """Obtener estadísticas del progreso"""
    total_original = len(original_data)
    total_current = len(current_data)
    discarded = total_original - total_current
    reviewed = current_index
    remaining = len(image_keys) - current_index
    
    # Calcular métricas de error
    edited_count = 0
    for i in range(min(current_index, len(image_keys))):
        image_key = image_keys[i]
        if image_key in current_data and image_key in original_data:
            if current_data[image_key] != original_data[image_key]:
                edited_count += 1
    
    # Calcular porcentajes
    error_rate = 0
    if reviewed > 0:
        error_rate = round(((edited_count + discarded) / reviewed) * 100, 1)
    
    edit_rate = 0
    if reviewed > 0:
        edit_rate = round((edited_count / reviewed) * 100, 1)
    
    discard_rate = 0
    if reviewed > 0:
        discard_rate = round((discarded / reviewed) * 100, 1)
    
    return jsonify({
        'total_original': total_original,
        'total_current': total_current,
        'discarded': discarded,
        'reviewed': reviewed,
        'remaining': remaining,
        'edited': edited_count,
        'correct': reviewed - edited_count - discarded,
        'progress_percent': round((reviewed / len(image_keys)) * 100, 1) if image_keys else 0,
        'error_rate': error_rate,
        'edit_rate': edit_rate,
        'discard_rate': discard_rate
    })

@app.route('/api/save_progress', methods=['POST'])
def manual_save_progress():
    """Guardar progreso manualmente"""
    try:
        save_progress()
        return jsonify({
            'success': True, 
            'message': 'Progreso guardado exitosamente',
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'file': corrected_json_path
        })
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': f'Error al guardar: {str(e)}'
        })

if __name__ == '__main__':
    try:
        load_data()
        print(f"Servidor iniciado. Abre http://localhost:5000 en tu navegador")
        print(f"Imágenes desde: {IMAGES_FOLDER}")
        print(f"JSON original: {JSON_PATH}")
        print(f"Correcciones se guardarán en: {corrected_json_path}")
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"Error al iniciar la aplicación: {e}")