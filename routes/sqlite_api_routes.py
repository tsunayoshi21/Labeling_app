"""
Rutas API para la aplicación de anotación colaborativa con SQLite
"""
from flask import Blueprint, request, jsonify, session
from functools import wraps
from services.database_service import DatabaseService

# Blueprint para las rutas de la aplicación SQLite
sqlite_api_bp = Blueprint('sqlite_api', __name__, url_prefix='/api/v2')

# Instancia del servicio de base de datos
db_service = DatabaseService()

def login_required(f):
    """Decorador para requerir autenticación"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorador para requerir permisos de administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        user = db_service.get_user_by_id(session['user_id'])
        if not user or user.role != 'admin':
            return jsonify({'error': 'Admin privileges required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

# Rutas de autenticación
@sqlite_api_bp.route('/login', methods=['POST'])
def login():
    """Autenticación de usuario"""
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Username and password required'}), 400
    
    user = db_service.authenticate_user(data['username'], data['password'])
    
    if user:
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        return jsonify({
            'success': True,
            'user': user.to_dict()
        })
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@sqlite_api_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Cerrar sesión"""
    session.clear()
    return jsonify({'success': True})

@sqlite_api_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Obtiene información del usuario actual"""
    user = db_service.get_user_by_id(session['user_id'])
    if user:
        stats = db_service.get_user_stats(user.id)
        return jsonify({
            'user': user.to_dict(),
            'stats': stats
        })
    return jsonify({'error': 'User not found'}), 404

# Rutas para tareas (anotaciones)
@sqlite_api_bp.route('/task/next', methods=['GET'])
@login_required
def get_next_task():
    """Obtiene la siguiente tarea pendiente para el usuario actual"""
    user_id = session['user_id']
    
    task_data = db_service.get_next_pending_task(user_id)
    
    if task_data:
        annotation, image = task_data
        return jsonify({
            'annotation_id': annotation.id,
            'image_id': image.id,
            'image_path': image.image_path,
            'initial_ocr_text': image.initial_ocr_text,
            'status': annotation.status
        })
    else:
        return jsonify({'message': 'No pending tasks available'}), 204

@sqlite_api_bp.route('/task/history', methods=['GET'])
@login_required
def get_task_history():
    """Obtiene el historial de tareas completadas del usuario (últimas 10)"""
    user_id = session['user_id']
    limit = int(request.args.get('limit', 10))
    
    history = db_service.get_user_task_history(user_id, limit)
    
    return jsonify({
        'history': [{
            'annotation_id': annotation.id,
            'image_id': image.id,
            'image_path': image.image_path,
            'initial_ocr_text': image.initial_ocr_text,
            'status': annotation.status,
            'corrected_text': annotation.corrected_text,
            'updated_at': annotation.updated_at.isoformat() if annotation.updated_at else None
        } for annotation, image in history]
    })

@sqlite_api_bp.route('/task/pending-preview', methods=['GET'])
@login_required
def get_pending_preview():
    """Obtiene una vista previa de las próximas tareas pendientes (máximo 10)"""
    user_id = session['user_id']
    limit = int(request.args.get('limit', 10))
    
    pending_tasks = db_service.get_pending_tasks_preview(user_id, limit)
    
    return jsonify({
        'pending': [{
            'annotation_id': annotation.id,
            'image_id': image.id
        } for annotation, image in pending_tasks]
    })

@sqlite_api_bp.route('/task/load/<int:annotation_id>', methods=['GET'])
@login_required
def load_specific_task(annotation_id):
    """Carga una tarea específica por annotation_id"""
    user_id = session['user_id']
    
    task_data = db_service.get_specific_task(annotation_id, user_id)
    
    if task_data:
        annotation, image = task_data
        return jsonify({
            'annotation_id': annotation.id,
            'image_id': image.id,
            'image_path': image.image_path,
            'initial_ocr_text': image.initial_ocr_text,
            'status': annotation.status,
            'corrected_text': annotation.corrected_text
        })
    else:
        return jsonify({'error': 'Task not found or access denied'}), 404

@sqlite_api_bp.route('/annotations/<int:annotation_id>', methods=['PUT'])
@login_required
def update_annotation(annotation_id):
    """Actualiza una anotación"""
    data = request.get_json()
    user_id = session['user_id']
    
    if not data or 'status' not in data:
        return jsonify({'error': 'Status is required'}), 400
    
    status = data['status']
    corrected_text = data.get('corrected_text')
    
    # Validar estado
    valid_statuses = ['pending', 'corrected', 'approved', 'discarded']
    if status not in valid_statuses:
        return jsonify({'error': f'Invalid status. Must be one of: {valid_statuses}'}), 400
    
    # Para mantener compatibilidad, mapear 'approved' al comportamiento correcto
    if status == 'approved' and not corrected_text:
        # Si se aprueba sin texto corregido, obtener el texto original
        # Esto se maneja ahora en el servicio de base de datos
        pass
    
    # Actualizar anotación
    success = db_service.update_annotation(annotation_id, user_id, status, corrected_text)
    
    if success:
        return jsonify({'success': True, 'message': 'Annotation updated successfully'})
    else:
        return jsonify({'error': 'Annotation not found or permission denied'}), 404

@sqlite_api_bp.route('/annotations/<int:annotation_id>', methods=['GET'])
@login_required
def get_annotation(annotation_id):
    """Obtiene una anotación específica"""
    user_id = session['user_id']
    user = db_service.get_user_by_id(user_id)
    
    # Los admins pueden ver cualquier anotación, los usuarios solo las suyas
    if user.role == 'admin':
        annotation = db_service.get_annotation_by_id(annotation_id)
    else:
        annotation = db_service.get_annotation_by_id(annotation_id, user_id)
    
    if annotation:
        return jsonify(annotation.to_dict())
    else:
        return jsonify({'error': 'Annotation not found'}), 404

# Rutas de administración
@sqlite_api_bp.route('/admin/assignments', methods=['POST'])
@admin_required
def create_assignments():
    """Asigna tareas a usuarios (solo admins)"""
    data = request.get_json()
    
    if not data or 'user_ids' not in data or 'image_ids' not in data:
        return jsonify({'error': 'user_ids and image_ids are required'}), 400
    
    user_ids = data['user_ids']
    image_ids = data['image_ids']
    
    if not isinstance(user_ids, list) or not isinstance(image_ids, list):
        return jsonify({'error': 'user_ids and image_ids must be arrays'}), 400
    
    assignments_created = db_service.assign_tasks(user_ids, image_ids)
    
    return jsonify({
        'success': True,
        'assignments_created': assignments_created
    })

@sqlite_api_bp.route('/admin/assignments/auto', methods=['POST'])
@admin_required
def create_auto_assignments():
    """Asigna automáticamente N imágenes random a un usuario"""
    data = request.get_json()
    
    if not data or 'user_id' not in data or 'count' not in data:
        return jsonify({'error': 'user_id and count are required'}), 400
    
    user_id = data['user_id']
    count = data['count']
    priority_unannotated = data.get('priority_unannotated', True)
    
    if not isinstance(count, int) or count <= 0:
        return jsonify({'error': 'count must be a positive integer'}), 400
    
    try:
        assignments_created = db_service.assign_random_tasks(user_id, count, priority_unannotated)
        
        return jsonify({
            'success': True,
            'assignments_created': assignments_created,
            'message': f'Se asignaron {assignments_created} tareas al usuario'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sqlite_api_bp.route('/admin/images/<int:image_id>/annotations', methods=['GET'])
@admin_required
def get_image_annotations(image_id):
    """Obtiene todas las anotaciones de una imagen (solo admins)"""
    annotations = db_service.get_image_annotations(image_id)
    
    return jsonify({
        'image_id': image_id,
        'annotations': [annotation.to_dict() for annotation in annotations]
    })

@sqlite_api_bp.route('/admin/images', methods=['GET'])
@admin_required
def get_all_images():
    """Obtiene todas las imágenes (solo admins)"""
    images = db_service.get_all_images()
    
    return jsonify({
        'images': [image.to_dict() for image in images]
    })

@sqlite_api_bp.route('/admin/users', methods=['GET'])
@admin_required
def get_all_users():
    """Obtiene todos los usuarios (solo admins)"""
    users = db_service.get_all_users()
    
    return jsonify({
        'users': [user.to_dict() for user in users]
    })

@sqlite_api_bp.route('/admin/users', methods=['POST'])
@admin_required
def create_user():
    """Crea un nuevo usuario (solo admins)"""
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'username and password are required'}), 400
    
    username = data['username']
    password = data['password']
    role = data.get('role', 'annotator')
    
    user = db_service.create_user(username, password, role)
    
    if user:
        return jsonify({
            'success': True,
            'user': user.to_dict()
        }), 201
    else:
        return jsonify({'error': 'Username already exists'}), 409

@sqlite_api_bp.route('/admin/images', methods=['POST'])
@admin_required
def create_image():
    """Crea una nueva imagen (solo admins)"""
    data = request.get_json()
    
    if not data or 'image_path' not in data or 'initial_ocr_text' not in data:
        return jsonify({'error': 'image_path and initial_ocr_text are required'}), 400
    
    image_path = data['image_path']
    initial_ocr_text = data['initial_ocr_text']
    
    image = db_service.create_image(image_path, initial_ocr_text)
    
    if image:
        return jsonify({
            'success': True,
            'image': image.to_dict()
        }), 201
    else:
        return jsonify({'error': 'Failed to create image'}), 500

@sqlite_api_bp.route('/admin/recent-activity', methods=['GET'])
@admin_required
def get_recent_activity():
    """Obtiene la actividad reciente de usuarios (solo admins)"""
    try:
        limit = request.args.get('limit', 6, type=int)
        activity = db_service.get_recent_user_activity(limit)
        return jsonify({'activity': activity})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Rutas de estadísticas
@sqlite_api_bp.route('/admin/stats', methods=['GET'])
@admin_required
def get_general_stats():
    """Obtiene estadísticas generales del sistema (solo admins)"""
    stats = db_service.get_general_stats()
    return jsonify(stats)

@sqlite_api_bp.route('/stats', methods=['GET'])
@login_required
def get_user_stats():
    """Obtiene estadísticas del usuario actual"""
    user_id = session['user_id']
    stats = db_service.get_user_stats(user_id)
    return jsonify(stats)

# Endpoint para análisis de rendimiento (solo para desarrollo)
@sqlite_api_bp.route('/dev/performance', methods=['GET'])
@login_required
def analyze_performance():
    """Analiza el rendimiento de consultas críticas (solo desarrollo)"""
    import time
    from flask import current_app
    
    # Solo permitir en modo debug
    if not current_app.debug:
        return jsonify({'error': 'Not available in production'}), 403
    
    user_id = session['user_id']
    results = {}
    
    # Timing para get_user_stats
    start = time.time()
    stats = db_service.get_user_stats(user_id)
    results['get_user_stats_ms'] = round((time.time() - start) * 1000, 2)
    
    # Timing para get_general_stats
    start = time.time()
    general_stats = db_service.get_general_stats()
    results['get_general_stats_ms'] = round((time.time() - start) * 1000, 2)
    
    # Timing para get_recent_user_activity
    start = time.time()
    activity = db_service.get_recent_user_activity(6)
    results['get_recent_user_activity_ms'] = round((time.time() - start) * 1000, 2)
    
    return jsonify(results)

# Manejo de errores
@sqlite_api_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@sqlite_api_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500
