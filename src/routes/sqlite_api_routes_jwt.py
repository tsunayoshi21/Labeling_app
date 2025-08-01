"""
Rutas API para la aplicación de anotación colaborativa con SQLite con JWT Auth
"""
from flask import Blueprint, request, jsonify
from services.database_service import DatabaseService
from services.jwt_service import jwt_required, admin_required, jwt_service
from services.security_utils import rate_limit, validate_json_input, SecurityUtils
import time
import logging

# Configurar logger para este módulo
logger = logging.getLogger(__name__)

URL_API_PREFIX = '/api/v2'

# Blueprint para las rutas de la aplicación SQLite
sqlite_api_bp = Blueprint('sqlite_api', __name__, url_prefix=URL_API_PREFIX)

# Instancia del servicio de base de datos
db_service = DatabaseService()

# Instancia de utilidades de seguridad
security = SecurityUtils()

# Rutas de autenticación
@sqlite_api_bp.route('/login', methods=['POST'])
@rate_limit(max_requests=5, window_seconds=60)  # Máximo 5 intentos por minuto
@validate_json_input(required_fields=['username', 'password'])
def login():
    """Autenticación de usuario con JWT"""
    data = request.get_json()
    
    try:
        # Validar entrada
        username = security.validate_input(data['username'], max_length=80)
        password = data['password']  # No validar password para preservar caracteres especiales
        
        logger.info(f"Intento de login para usuario: {username}")
        
        # Autenticar usuario
        user = db_service.authenticate_user(username, password)
        
        if user:
            # Crear tokens JWT
            access_token = jwt_service.create_access_token(user.id, user.username, user.role)
            refresh_token = jwt_service.create_refresh_token(user.id)
            
            logger.info(f"Login exitoso para usuario {username} (ID: {user.id}, rol: {user.role})")
            
            return jsonify({
                'success': True,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': user.to_dict(),
                'expires_in': jwt_service.access_token_expire_minutes * 60  # en segundos
            })
        else:
            logger.warning(f"Login fallido para usuario: {username}")
            return jsonify({'error': 'Invalid credentials'}), 401
            
    except ValueError as e:
        logger.warning(f"Error de validación en login: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error interno en login: {e}")
        return jsonify({'error': 'Authentication failed'}), 500

@sqlite_api_bp.route('/logout', methods=['POST'])
@jwt_required
def logout():
    """Cerrar sesión (con JWT simplemente eliminamos el token del cliente)"""
    username = request.current_user.get('username', 'unknown')
    logger.info(f"Logout exitoso para usuario: {username}")
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@sqlite_api_bp.route('/refresh', methods=['POST'])
@rate_limit(max_requests=10, window_seconds=60)
@validate_json_input(required_fields=['refresh_token'])
def refresh_token():
    """Renovar token de acceso usando refresh token"""
    data = request.get_json()
    
    try:
        refresh_token = data['refresh_token']
        payload = jwt_service.verify_refresh_token(refresh_token)
        
        logger.debug(f"Refresh token válido para usuario ID: {payload['user_id']}")
        
        # Obtener usuario actualizado
        user = db_service.get_user_by_id(payload['user_id'])
        if not user:
            logger.warning(f"Usuario no encontrado para refresh token: {payload['user_id']}")
            return jsonify({'error': 'User not found'}), 404
        
        # Crear nuevo access token
        new_access_token = jwt_service.create_access_token(user.id, user.username, user.role)
        
        logger.info(f"Token renovado exitosamente para usuario: {user.username}")
        
        return jsonify({
            'success': True,
            'access_token': new_access_token,
            'expires_in': jwt_service.access_token_expire_minutes * 60
        })
        
    except ValueError as e:
        logger.warning(f"Error renovando token: {e}")
        return jsonify({'error': str(e)}), 401
    except Exception as e:
        logger.error(f"Error interno renovando token: {e}")
        return jsonify({'error': 'Token refresh failed'}), 500

@sqlite_api_bp.route('/me', methods=['GET'])
@jwt_required
def get_current_user():
    """Obtiene información del usuario actual"""
    user_id = request.current_user['user_id']
    username = request.current_user['username']
    
    logger.debug(f"Solicitando información de usuario: {username}")
    
    user = db_service.get_user_by_id(user_id)
    if user:
        stats = db_service.get_user_stats(user.id)
        logger.debug(f"Información de usuario obtenida exitosamente: {username}")
        return jsonify({
            'user': user.to_dict(),
            'stats': stats
        })
    
    logger.warning(f"Usuario no encontrado: {user_id}")
    return jsonify({'error': 'User not found'}), 404

# Rutas para tareas (anotaciones)
@sqlite_api_bp.route('/task/next', methods=['GET'])
@jwt_required
def get_next_task():
    """Obtiene la siguiente tarea pendiente para el usuario actual"""
    user_id = request.current_user['user_id']
    username = request.current_user['username']
    
    logger.debug(f"Solicitando próxima tarea para usuario: {username}")
    
    task_data = db_service.get_next_pending_task(user_id)
    
    if task_data:
        annotation, image = task_data
        logger.info(f"Tarea asignada a {username}: anotación {annotation.id}, imagen {image.id}")
        return jsonify({
            'annotation_id': annotation.id,
            'image_id': image.id,
            'image_path': image.image_path,
            'initial_ocr_text': image.initial_ocr_text,
            'status': annotation.status
        })
    else:
        logger.info(f"No hay tareas pendientes para usuario: {username}")
        return jsonify({'message': 'No pending tasks available'}), 204

@sqlite_api_bp.route('/task/history', methods=['GET'])
@jwt_required
def get_task_history():
    """Obtiene el historial de tareas completadas del usuario (últimas 10)"""
    user_id = request.current_user['user_id']
    username = request.current_user['username']
    limit = int(request.args.get('limit', 10))
    
    logger.debug(f"Solicitando historial de tareas para {username} (límite: {limit})")
    
    history = db_service.get_user_task_history(user_id, limit)
    
    logger.debug(f"Historial obtenido para {username}: {len(history)} tareas")
    
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
@jwt_required
def get_pending_preview():
    """Obtiene una vista previa de las próximas tareas pendientes (máximo 10)"""
    user_id = request.current_user['user_id']
    username = request.current_user['username']
    limit = int(request.args.get('limit', 10))
    
    logger.debug(f"Solicitando vista previa de tareas pendientes para {username} (límite: {limit})")
    
    pending_tasks = db_service.get_pending_tasks_preview(user_id, limit)
    
    logger.debug(f"Vista previa obtenida para {username}: {len(pending_tasks)} tareas pendientes")
    
    return jsonify({
        'pending': [{
            'annotation_id': annotation.id,
            'image_id': image.id
        } for annotation, image in pending_tasks]
    })

@sqlite_api_bp.route('/task/load/<int:annotation_id>', methods=['GET'])
@jwt_required
def load_specific_task(annotation_id):
    """Carga una tarea específica por annotation_id"""
    user_id = request.current_user['user_id']
    username = request.current_user['username']
    
    logger.debug(f"Cargando tarea específica {annotation_id} para usuario: {username}")
    
    task_data = db_service.get_specific_task(annotation_id, user_id)
    
    if task_data:
        annotation, image = task_data
        logger.info(f"Tarea específica cargada para {username}: anotación {annotation_id}")
        return jsonify({
            'annotation_id': annotation.id,
            'image_id': image.id,
            'image_path': image.image_path,
            'initial_ocr_text': image.initial_ocr_text,
            'status': annotation.status,
            'corrected_text': annotation.corrected_text
        })
    else:
        logger.warning(f"Tarea específica no encontrada: {annotation_id} para usuario {username}")
        return jsonify({'error': 'Task not found'}), 404

@sqlite_api_bp.route('/annotations/<int:annotation_id>', methods=['PUT'])
@jwt_required
@validate_json_input(required_fields=['status'], optional_fields=['corrected_text'])
def update_annotation(annotation_id):
    """Actualiza una anotación"""
    data = request.get_json()
    user_id = request.current_user['user_id']
    username = request.current_user['username']
    
    try:
        status = data['status']
        corrected_text = data.get('corrected_text')
        
        logger.info(f"Actualizando anotación {annotation_id} para {username}: status={status}")
        
        # Validar entrada
        if corrected_text:
            corrected_text = security.validate_input(corrected_text, max_length=2000)
        
        # Validar estado
        valid_statuses = ['pending', 'corrected', 'approved', 'discarded']
        if status not in valid_statuses:
            logger.warning(f"Estado inválido para anotación {annotation_id}: {status}")
            return jsonify({'error': f'Invalid status. Must be one of: {valid_statuses}'}), 400
        
        # Para mantener compatibilidad, mapear 'approved' al comportamiento correcto
        if status == 'approved' and not corrected_text:
            status = 'approved'
        
        success = db_service.update_annotation(annotation_id, user_id, status, corrected_text)
        
        if success:
            logger.info(f"Anotación {annotation_id} actualizada exitosamente por {username} a {status}")
            return jsonify({'success': True, 'message': f'Annotation {status}'})
        else:
            logger.warning(f"Fallo actualizando anotación {annotation_id} para {username}: no encontrada o no autorizada")
            return jsonify({'error': 'Annotation not found or not authorized'}), 404
            
    except ValueError as e:
        logger.warning(f"Error de validación actualizando anotación {annotation_id}: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error interno actualizando anotación {annotation_id}: {e}")
        return jsonify({'error': 'Failed to update annotation'}), 500

@sqlite_api_bp.route('/annotations/<int:annotation_id>', methods=['GET'])
@jwt_required
def get_annotation(annotation_id):
    """Obtiene una anotación específica"""
    user_id = request.current_user['user_id']
    username = request.current_user['username']
    
    logger.debug(f"Obteniendo anotación {annotation_id} para usuario: {username}")
    
    annotation_data = db_service.get_annotation_with_image(annotation_id, user_id)
    
    if annotation_data:
        annotation, image = annotation_data
        logger.debug(f"Anotación {annotation_id} obtenida exitosamente para {username}")
        return jsonify({
            'annotation_id': annotation.id,
            'image_id': image.id,
            'image_path': image.image_path,
            'initial_ocr_text': image.initial_ocr_text,
            'status': annotation.status,
            'corrected_text': annotation.corrected_text,
            'updated_at': annotation.updated_at.isoformat() if annotation.updated_at else None
        })
    else:
        logger.warning(f"Anotación {annotation_id} no encontrada para usuario {username}")
        return jsonify({'error': 'Annotation not found'}), 404

# Rutas de administración
@sqlite_api_bp.route('/admin/assignments', methods=['POST'])
@admin_required
@validate_json_input(required_fields=['user_ids', 'image_ids'])
def create_assignments():
    """Crea asignaciones específicas entre usuarios e imágenes"""
    data = request.get_json()
    admin_username = request.current_user['username']
    
    try:
        user_ids = data['user_ids']
        image_ids = data['image_ids']
        
        logger.info(f"Admin {admin_username} creando asignaciones: {len(user_ids)} usuarios, {len(image_ids)} imágenes")
        
        # Validar que las listas no estén vacías
        if not user_ids or not image_ids:
            logger.warning(f"Admin {admin_username} intentó crear asignaciones con listas vacías")
            return jsonify({'error': 'User IDs and Image IDs cannot be empty'}), 400
        
        # Crear asignaciones
        assignments = db_service.assign_tasks(user_ids, image_ids)
        
        logger.info(f"Admin {admin_username} creó {assignments} asignaciones exitosamente")
        
        return jsonify({
            'success': True,
            'assignments_created': assignments,
            'message': f'Created {assignments} assignments'
        })
        
    except Exception as e:
        logger.error(f"Error creando asignaciones para admin {admin_username}: {e}")
        return jsonify({'error': str(e)}), 500

@sqlite_api_bp.route('/admin/assignments/auto', methods=['POST'])
@admin_required
@validate_json_input(required_fields=['count', 'priority_unannotated'], optional_fields=['user_id'])
def create_auto_assignments():
    """Crea asignaciones automáticas de N imágenes aleatorias"""
    data = request.get_json()
    admin_username = request.current_user['username']
    
    try:
        count = int(data['count'])
        user_id = data.get('user_id')
        priority_unannotated = data.get('priority_unannotated', True)
        
        logger.info(f"Admin {admin_username} creando {count} asignaciones automáticas" + 
                   (f" para usuario {user_id}" if user_id else ""))
        
        if count <= 0 or count > 1000:  # Límite de seguridad
            logger.warning(f"Admin {admin_username} intentó crear {count} asignaciones (fuera de rango)")
            return jsonify({'error': 'Count must be between 1 and 1000'}), 400
        
        assignments = db_service.assign_random_tasks(user_id, count, priority_unannotated)
        
        logger.info(f"Admin {admin_username} creó {assignments} asignaciones automáticas exitosamente")
        
        return jsonify({
            'success': True,
            'assignments_created': assignments,
            'message': f'Created {assignments} automatic assignments'
        })
        
    except ValueError as e:
        logger.warning(f"Error de validación en asignaciones automáticas para admin {admin_username}: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error creando asignaciones automáticas para admin {admin_username}: {e}")
        return jsonify({'error': 'Failed to create auto assignments'}), 500

@sqlite_api_bp.route('/admin/images/<int:image_id>/annotations', methods=['GET'])
@admin_required
def get_image_annotations(image_id):
    """Obtiene todas las anotaciones de una imagen específica"""
    admin_username = request.current_user['username']
    
    logger.debug(f"Admin {admin_username} solicitando anotaciones para imagen {image_id}")
    
    annotations = db_service.get_image_annotations(image_id)
    
    logger.debug(f"Admin {admin_username} obtuvo {len(annotations)} anotaciones para imagen {image_id}")
    
    return jsonify({
        'image_id': image_id,
        'annotations': [{
            'id': ann.id,
            'user_id': ann.user_id,
            'status': ann.status,
            'corrected_text': ann.corrected_text,
            'updated_at': ann.updated_at.isoformat() if ann.updated_at else None
        } for ann in annotations]
    })

@sqlite_api_bp.route('/admin/images', methods=['GET'])
@admin_required
def get_all_images():
    """Obtiene todas las imágenes con información de anotaciones"""
    admin_username = request.current_user['username']
    
    logger.debug(f"Admin {admin_username} solicitando todas las imágenes")
    
    images = db_service.get_all_images_with_annotations()
    
    logger.debug(f"Admin {admin_username} obtuvo {len(images)} imágenes")
    
    return jsonify({
        'images': images  # Ya viene formateado como lista de diccionarios
    })

@sqlite_api_bp.route('/admin/users', methods=['GET'])
@admin_required
def get_all_users():
    """Obtiene todos los usuarios"""
    admin_username = request.current_user['username']
    
    logger.debug(f"Admin {admin_username} solicitando lista de usuarios")
    
    users = db_service.get_all_users()
    
    logger.debug(f"Admin {admin_username} obtuvo {len(users)} usuarios")
    
    return jsonify({
        'users': [user.to_dict() for user in users]
    })

@sqlite_api_bp.route('/admin/users', methods=['POST'])
@admin_required
@validate_json_input(required_fields=['username', 'password'], optional_fields=['role'])
def create_user():
    """Crea un nuevo usuario"""
    data = request.get_json()
    admin_username = request.current_user['username']
    
    try:
        username = security.validate_input(data['username'], max_length=80)
        password = data['password']
        role = data.get('role', 'annotator')
        
        logger.info(f"Admin {admin_username} creando usuario: {username} con rol {role}")
        
        # Validar fortaleza de contraseña
        if not security.validate_password_strength(password):
            logger.warning(f"Admin {admin_username} intentó crear usuario {username} con contraseña débil")
            return jsonify({
                'error': 'Password must be at least 8 characters with uppercase, lowercase, and number'
            }), 400
        
        # Validar rol
        if role not in ['annotator', 'admin']:
            logger.warning(f"Admin {admin_username} intentó crear usuario {username} con rol inválido: {role}")
            return jsonify({'error': 'Role must be either "annotator" or "admin"'}), 400
        
        user = db_service.create_user(username, password, role)
        
        if user:
            logger.info(f"Admin {admin_username} creó usuario {username} exitosamente")
            return jsonify({
                'success': True,
                'user': user.to_dict(),
                'message': f'User {username} created successfully'
            })
        else:
            logger.warning(f"Admin {admin_username} falló creando usuario {username}: username ya existe")
            return jsonify({'error': 'Username already exists'}), 409
            
    except ValueError as e:
        logger.warning(f"Error de validación creando usuario para admin {admin_username}: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error interno creando usuario para admin {admin_username}: {e}")
        return jsonify({'error': 'Failed to create user'}), 500

@sqlite_api_bp.route('/admin/images', methods=['POST'])
@admin_required
@validate_json_input(required_fields=['image_path', 'initial_ocr_text'])
def create_image():
    """Crea una nueva imagen para anotar"""
    data = request.get_json()
    admin_username = request.current_user['username']
    
    try:
        image_path = security.validate_input(data['image_path'], max_length=255)
        initial_ocr_text = security.validate_input(data['initial_ocr_text'], max_length=2000)
        
        logger.info(f"Admin {admin_username} creando imagen: {image_path}")
        
        image = db_service.create_image(image_path, initial_ocr_text)
        
        logger.info(f"Admin {admin_username} creó imagen {image.id} exitosamente")
        
        return jsonify({
            'success': True,
            'image': image.to_dict(),
            'message': 'Image created successfully'
        })
        
    except ValueError as e:
        logger.warning(f"Error de validación creando imagen para admin {admin_username}: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error interno creando imagen para admin {admin_username}: {e}")
        return jsonify({'error': 'Failed to create image'}), 500

@sqlite_api_bp.route('/admin/recent-activity', methods=['GET'])
@admin_required
def get_recent_activity():
    """Obtiene actividad reciente de usuarios"""
    admin_username = request.current_user['username']
    limit = int(request.args.get('limit', 6))
    
    logger.debug(f"Admin {admin_username} solicitando actividad reciente (límite: {limit})")
    
    activity = db_service.get_recent_user_activity(limit)
    
    logger.debug(f"Admin {admin_username} obtuvo {len(activity)} actividades recientes")
    
    return jsonify({
        'recent_activity': activity  # Ya viene formateado como lista de diccionarios
    })

# Rutas de estadísticas
@sqlite_api_bp.route('/admin/stats', methods=['GET'])
@admin_required
def get_general_stats():
    """Obtiene estadísticas generales del sistema"""
    admin_username = request.current_user['username']
    
    logger.debug(f"Admin {admin_username} solicitando estadísticas generales")
    
    stats = db_service.get_general_stats()
    
    logger.debug(f"Admin {admin_username} obtuvo estadísticas generales")
    
    return jsonify(stats)

@sqlite_api_bp.route('/stats', methods=['GET'])
@jwt_required
def get_user_stats():
    """Obtiene estadísticas del usuario actual"""
    user_id = request.current_user['user_id']
    username = request.current_user['username']
    
    logger.debug(f"Usuario {username} solicitando sus estadísticas")
    
    stats = db_service.get_user_stats(user_id)
    
    logger.debug(f"Estadísticas obtenidas para usuario {username}")
    
    return jsonify(stats)

# Endpoint para análisis de rendimiento (solo para desarrollo)
@sqlite_api_bp.route('/dev/performance', methods=['GET'])
@jwt_required
def analyze_performance():
    """Analiza el rendimiento de endpoints críticos"""
    username = request.current_user['username']
    results = {}
    
    logger.info(f"Análisis de rendimiento solicitado por: {username}")
    
    try:
        # Test /me endpoint
        start_time = time.time()
        user_id = request.current_user['user_id']
        user = db_service.get_user_by_id(user_id)
        results['me_endpoint'] = f"{(time.time() - start_time) * 1000:.2f}ms"
        
        # Test /stats endpoint
        start_time = time.time()
        stats = db_service.get_user_stats(user_id)
        results['stats_endpoint'] = f"{(time.time() - start_time) * 1000:.2f}ms"
        
        # Test general stats (solo para admin)
        if request.current_user['role'] == 'admin':
            start_time = time.time()
            general_stats = db_service.get_general_stats()
            results['admin_stats_endpoint'] = f"{(time.time() - start_time) * 1000:.2f}ms"
        
        logger.info(f"Análisis de rendimiento completado para {username}: {results}")
        
        return jsonify({
            'performance_results': results,
            'timestamp': time.time()
        })
        
    except Exception as e:
        logger.error(f"Error en análisis de rendimiento para {username}: {e}")
        return jsonify({'error': str(e)}), 500

# Diagnóstico JWT (solo para desarrollo)
@sqlite_api_bp.route('/debug/auth', methods=['GET'])
@jwt_required
def debug_auth():
    """Endpoint de diagnóstico para verificar autenticación JWT"""
    username = request.current_user['username']
    logger.debug(f"Debug auth verificado para usuario: {username}")
    
    return jsonify({
        'authenticated': True,
        'user': request.current_user,
        'message': 'JWT authentication working'
    })

@sqlite_api_bp.route('/debug/admin', methods=['GET'])
@admin_required
def debug_admin():
    """Endpoint de diagnóstico para verificar autorización admin"""
    username = request.current_user['username']
    logger.debug(f"Debug admin verificado para admin: {username}")
    
    return jsonify({
        'authenticated': True,
        'admin': True,
        'user': request.current_user,
        'message': 'JWT admin authorization working'
    })

# Manejo de errores
@sqlite_api_bp.errorhandler(404)
def not_found(error):
    logger.warning(f"Recurso no encontrado: {error}")
    return jsonify({'error': 'Resource not found'}), 404

@sqlite_api_bp.errorhandler(500)
def internal_error(error):
    logger.error(f"Error interno del servidor: {error}")
    return jsonify({'error': 'Internal server error'}), 500

@sqlite_api_bp.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429
