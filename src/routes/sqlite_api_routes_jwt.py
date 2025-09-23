"""
Rutas API para la aplicación de anotación colaborativa con SQLite con JWT Auth
"""
import os
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from services.database_service import DatabaseService
from services.jwt_service import jwt_required, admin_required, jwt_service
from services.security_utils import rate_limit, validate_json_input, SecurityUtils
from services.notification_service import notification_service
import time
import logging

# Configurar logger para este módulo
logger = logging.getLogger(__name__)

URL_API_PREFIX = '/api/v2'

# Blueprint para las rutas de la aplicación SQLite
api_bp = Blueprint('api', __name__, url_prefix=URL_API_PREFIX)

# Instancia del servicio de base de datos
db_service = DatabaseService()

# Instancia de utilidades de seguridad
security = SecurityUtils()

# Middleware para logging de códigos de estado HTTP
@api_bp.after_request
def log_response_status(response):
    """Middleware que registra el código de estado HTTP de cada respuesta"""
    endpoint = request.endpoint or 'unknown'
    method = request.method
    path = request.path
    status_code = response.status_code
    
    # Obtener información del usuario si está disponible
    user_info = ""
    if hasattr(request, 'current_user') and request.current_user:
        username = request.current_user.get('username', 'unknown')
        role = request.current_user.get('role', 'unknown')
        user_info = f" | Usuario: {username} ({role})"
    
    # Log con nivel apropiado según el código de estado
    if 200 <= status_code < 300:
        logger.info(f"HTTP {status_code} | {method} {path}{user_info}")
    elif 300 <= status_code < 400:
        logger.info(f"HTTP {status_code} | {method} {path}{user_info}")
    elif 400 <= status_code < 500:
        logger.warning(f"HTTP {status_code} | {method} {path}{user_info}")
    else:  # 500+
        logger.error(f"HTTP {status_code} | {method} {path}{user_info}")
    
    return response

# Rutas de autenticación
@api_bp.route('/login', methods=['POST'])
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

@api_bp.route('/logout', methods=['POST'])
@jwt_required
def logout():
    """Cerrar sesión (con JWT simplemente eliminamos el token del cliente)"""
    username = request.current_user.get('username', 'unknown')
    logger.info(f"Logout exitoso para usuario: {username}")
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@api_bp.route('/refresh', methods=['POST'])
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

@api_bp.route('/me', methods=['GET'])
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
@api_bp.route('/task/next', methods=['GET'])
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
        
        # Marcar que el usuario tiene tareas disponibles (resetea estado de notificación)
        notification_service.mark_user_has_tasks(user_id, username)
        
        return jsonify({
            'annotation_id': annotation.id,
            'image_id': image.id,
            'image_path': image.image_path,
            'initial_ocr_text': image.initial_ocr_text,
            'status': annotation.status
        })
    else:
        logger.info(f"No hay tareas pendientes para usuario: {username}")
        
        # Intentar enviar notificación al admin (con protección anti-spam)
        try:
            notification_sent = notification_service.send_no_tasks_notification(user_id, username)
            if notification_sent:
                logger.info(f"Notificación de 'sin tareas' enviada al admin para usuario: {username}")
            else:
                logger.debug(f"Notificación de 'sin tareas' no enviada (anti-spam o error) para usuario: {username}")
        except Exception as e:
            logger.error(f"Error enviando notificación de 'sin tareas' para usuario {username}: {e}")
        
        return jsonify({'message': 'No pending tasks available'}), 204

@api_bp.route('/task/history', methods=['GET'])
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

@api_bp.route('/task/pending-preview', methods=['GET'])
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

@api_bp.route('/task/load/<int:annotation_id>', methods=['GET'])
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

@api_bp.route('/annotations/<int:annotation_id>', methods=['PUT'])
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

@api_bp.route('/admin/annotations/<int:annotation_id>', methods=['PUT'])
@admin_required
@validate_json_input(required_fields=['status'], optional_fields=['corrected_text'])
def admin_update_annotation(annotation_id):
    """Permite a un admin actualizar una anotación (estado y texto)"""
    data = request.get_json()
    admin_username = request.current_user['username']

    try:
        status = data['status']
        corrected_text = data.get('corrected_text')

        logger.info(f"[ADMIN] Actualizando anotación {annotation_id} por {admin_username}: status={status}")

        # Validar entrada
        if corrected_text:
            corrected_text = security.validate_input(corrected_text, max_length=2000)

        # Validar estado permitido
        valid_statuses = ['pending', 'corrected', 'approved', 'discarded']
        if status not in valid_statuses:
            logger.warning(f"[ADMIN] Estado inválido para anotación {annotation_id}: {status}")
            return jsonify({'error': f'Invalid status. Must be one of: {valid_statuses}'}), 400

        # Ejecutar actualización sin filtrar por usuario
        success = db_service.admin_update_annotation(annotation_id, status, corrected_text)

        if success:
            logger.info(f"[ADMIN] Anotación {annotation_id} actualizada exitosamente a {status} por {admin_username}")
            return jsonify({'success': True, 'message': f'Annotation {status}'})
        else:
            logger.warning(f"[ADMIN] Fallo actualizando anotación {annotation_id}: no encontrada")
            return jsonify({'error': 'Annotation not found'}), 404

    except ValueError as e:
        logger.warning(f"[ADMIN] Error de validación actualizando anotación {annotation_id}: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"[ADMIN] Error interno actualizando anotación {annotation_id}: {e}")
        return jsonify({'error': 'Failed to update annotation'}), 500

@api_bp.route('/annotations/<int:annotation_id>', methods=['GET'])
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
@api_bp.route('/admin/assignments', methods=['POST'])
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

@api_bp.route('/admin/assignments/auto', methods=['POST'])
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
        
        if count <= 0 or count > 50000:  # Límite de seguridad
            logger.warning(f"Admin {admin_username} intentó crear {count} asignaciones (fuera de rango)")
            return jsonify({'error': 'Count must be between 1 and 50000'}), 400
        
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

@api_bp.route('/admin/images/<int:image_id>/annotations', methods=['GET'])
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

@api_bp.route('/admin/images', methods=['GET'])
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

@api_bp.route('/admin/users', methods=['GET'])
@admin_required
def get_all_users():
    """Obtiene todos los usuarios con estadísticas"""
    admin_username = request.current_user['username']
    
    logger.debug(f"Admin {admin_username} solicitando lista de usuarios")
    
    users = db_service.get_all_users_with_stats()
    
    logger.debug(f"Admin {admin_username} obtuvo {len(users)} usuarios")
    
    return jsonify({
        'users': users
    })

@api_bp.route('/admin/users', methods=['POST'])
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

@api_bp.route('/admin/images', methods=['POST'])
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

@api_bp.route('/admin/recent-activity', methods=['GET'])
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
@api_bp.route('/admin/stats', methods=['GET'])
@admin_required
def get_general_stats():
    """Obtiene estadísticas generales del sistema"""
    admin_username = request.current_user['username']
    
    logger.debug(f"Admin {admin_username} solicitando estadísticas generales")
    
    stats = db_service.get_general_stats()
    
    logger.debug(f"Admin {admin_username} obtuvo estadísticas generales")
    
    return jsonify(stats)

@api_bp.route('/stats', methods=['GET'])
@jwt_required
def get_user_stats():
    """Obtiene estadísticas del usuario actual"""
    user_id = request.current_user['user_id']
    username = request.current_user['username']
    
    logger.debug(f"Usuario {username} solicitando sus estadísticas")
    
    stats = db_service.get_user_stats(user_id)
    
    logger.debug(f"Estadísticas obtenidas para usuario {username}")
    
    return jsonify(stats)

@api_bp.route('/admin/users/<int:user_id>/stats', methods=['GET'])
@admin_required
def get_user_detailed_stats(user_id):
    """Obtiene estadísticas detalladas de un usuario específico"""
    admin_username = request.current_user['username']
    
    logger.debug(f"Admin {admin_username} solicitando estadísticas detalladas para usuario {user_id}")
    
    # Obtener información básica del usuario
    user = db_service.get_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Obtener estadísticas del usuario
    stats = db_service.get_user_stats(user_id)
    
    logger.debug(f"Admin {admin_username} obtuvo estadísticas detalladas para usuario {user_id}")
    
    return jsonify({
        'user': user.to_dict(),
        'stats': stats
    })

@api_bp.route('/admin/users/<int:user_id>/annotations', methods=['GET'])
@admin_required
def get_user_annotations(user_id):
    """Obtiene todas las anotaciones de un usuario específico"""
    admin_username = request.current_user['username']
    
    logger.debug(f"Admin {admin_username} solicitando anotaciones para usuario {user_id}")
    
    annotations = db_service.get_user_annotations_detailed(user_id)
    
    logger.debug(f"Admin {admin_username} obtuvo {len(annotations)} anotaciones para usuario {user_id}")
    
    return jsonify({
        'user_id': user_id,
        'annotations': annotations
    })

@api_bp.route('/admin/users/<int:user_id>/annotations/<int:annotation_id>', methods=['DELETE'])
@admin_required
def delete_user_annotation(user_id, annotation_id):
    """Elimina una anotación específica de un usuario"""
    admin_username = request.current_user['username']
    
    logger.info(f"Admin {admin_username} eliminando anotación {annotation_id} del usuario {user_id}")
    
    success = db_service.delete_user_annotation(annotation_id, user_id)
    
    if success:
        logger.info(f"Admin {admin_username} eliminó anotación {annotation_id} exitosamente")
        return jsonify({
            'success': True,
            'message': 'Annotation deleted successfully'
        })
    else:
        logger.warning(f"Admin {admin_username} falló eliminando anotación {annotation_id}")
        return jsonify({'error': 'Annotation not found or could not be deleted'}), 404

@api_bp.route('/admin/users/<int:user_id>/annotations/bulk-delete', methods=['POST'])
@admin_required
@validate_json_input(required_fields=['statuses'])
def bulk_delete_user_annotations(user_id):
    """Elimina anotaciones de un usuario por estado"""
    data = request.get_json()
    admin_username = request.current_user['username']
    
    try:
        statuses = data['statuses']
        if not isinstance(statuses, list) or not all(status in ['pending', 'corrected', 'approved', 'discarded'] for status in statuses):
            return jsonify({'error': 'Invalid statuses provided'}), 400
        
        logger.info(f"Admin {admin_username} eliminando anotaciones del usuario {user_id} con estados {statuses}")
        
        deleted_count = db_service.delete_user_annotations_by_status(user_id, statuses)
        
        logger.info(f"Admin {admin_username} eliminó {deleted_count} anotaciones del usuario {user_id}")
        
        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'message': f'{deleted_count} annotations deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error eliminando anotaciones masivamente para admin {admin_username}: {e}")
        return jsonify({'error': 'Failed to delete annotations'}), 500

@api_bp.route('/admin/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Elimina un usuario completamente"""
    admin_username = request.current_user['username']
    
    # Prevenir que el admin se elimine a sí mismo
    if user_id == request.current_user['user_id']:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    logger.info(f"Admin {admin_username} eliminando usuario {user_id}")
    
    success = db_service.delete_user_completely(user_id)
    
    if success:
        logger.info(f"Admin {admin_username} eliminó usuario {user_id} exitosamente")
        return jsonify({
            'success': True,
            'message': 'User and all annotations deleted successfully'
        })
    else:
        logger.warning(f"Admin {admin_username} falló eliminando usuario {user_id}")
        return jsonify({'error': 'User not found or could not be deleted'}), 404

@api_bp.route('/admin/users/<int:from_user_id>/transfer-annotations', methods=['POST'])
@admin_required
@validate_json_input(required_fields=['to_user_id'], optional_fields=['include_pending', 'include_reviewed'])
def transfer_user_annotations(from_user_id):
    """Transfiere anotaciones de un usuario a otro"""
    data = request.get_json()
    admin_username = request.current_user['username']
    
    try:
        to_user_id = int(data['to_user_id'])
        include_pending = data.get('include_pending', True)
        include_reviewed = data.get('include_reviewed', False)
        
        if from_user_id == to_user_id:
            return jsonify({'error': 'Source and destination users cannot be the same'}), 400
        
        logger.info(f"Admin {admin_username} transfiriendo anotaciones de usuario {from_user_id} a {to_user_id}")
        
        result = db_service.transfer_user_annotations(
            from_user_id, to_user_id, include_pending, include_reviewed
        )
        
        if result['success']:
            logger.info(f"Admin {admin_username} transfirió {result['transferred']} anotaciones exitosamente")
            return jsonify(result)
        else:
            logger.warning(f"Admin {admin_username} falló transfiriendo anotaciones: {result['error']}")
            return jsonify(result), 400
            
    except ValueError as e:
        logger.warning(f"Error de validación transfiriendo anotaciones para admin {admin_username}: {e}")
        return jsonify({'error': 'Invalid user ID provided'}), 400
    except Exception as e:
        logger.error(f"Error interno transfiriendo anotaciones para admin {admin_username}: {e}")
        return jsonify({'error': 'Failed to transfer annotations'}), 500

# Rutas de Control de Calidad
@api_bp.route('/admin/quality-control', methods=['GET'])
@admin_required
def get_quality_control_annotations():
    """Obtiene anotaciones para control de calidad: misma imagen anotada por admin y usuario con textos diferentes"""
    admin_username = request.current_user['username']
    
    logger.debug(f"Admin {admin_username} solicitando datos de control de calidad")
    # Filtros opcionales: user_ids (csv) o usernames (csv)
    raw_user_ids = request.args.get('user_ids')
    raw_usernames = request.args.get('usernames')
    user_ids = None
    usernames = None
    if raw_user_ids:
        try:
            user_ids = [int(x) for x in raw_user_ids.split(',') if x.strip()]
        except Exception:
            user_ids = None
    if raw_usernames:
        usernames = [x.strip() for x in raw_usernames.split(',') if x.strip()]

    quality_data = db_service.get_quality_control_annotations(user_ids=user_ids, usernames=usernames)
    
    logger.debug(f"Admin {admin_username} obtuvo {len(quality_data)} discrepancias para control de calidad")
    
    return jsonify({
        'quality_control_data': quality_data,
        'total_discrepancies': len(quality_data)
    })

@api_bp.route('/admin/quality-control/consolidate', methods=['POST'])
@admin_required
@validate_json_input(required_fields=['user_annotation_id', 'admin_annotation_id'])
def consolidate_annotation():
    """Consolida una anotación: actualiza la anotación del admin con el texto del usuario"""
    data = request.get_json()
    admin_username = request.current_user['username']
    
    try:
        user_annotation_id = data['user_annotation_id']
        admin_annotation_id = data['admin_annotation_id']
        
        logger.info(f"Admin {admin_username} consolidando anotación: user={user_annotation_id}, admin={admin_annotation_id}")
        
        success = db_service.consolidate_annotation(user_annotation_id, admin_annotation_id)
        
        if success:
            logger.info(f"Admin {admin_username} consolidó anotación exitosamente")
            return jsonify({
                'success': True,
                'message': 'Annotation consolidated successfully'
            })
        else:
            logger.warning(f"Fallo consolidando anotación por admin {admin_username}")
            return jsonify({'error': 'Failed to consolidate annotation'}), 400
            
    except Exception as e:
        logger.error(f"Error consolidando anotación por admin {admin_username}: {e}")
        return jsonify({'error': 'Failed to consolidate annotation'}), 500

# Endpoint para análisis de rendimiento (solo para desarrollo)
@api_bp.route('/dev/performance', methods=['GET'])
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
@api_bp.route('/debug/auth', methods=['GET'])
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

@api_bp.route('/debug/admin', methods=['GET'])
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
@api_bp.errorhandler(404)
def not_found(error):
    logger.warning(f"Recurso no encontrado: {error}")
    return jsonify({'error': 'Resource not found'}), 404

@api_bp.errorhandler(500)
def internal_error(error):
    logger.error(f"Error interno del servidor: {error}")
    return jsonify({'error': 'Internal server error'}), 500

@api_bp.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429

@api_bp.route('/admin/users/agreement-stats', methods=['GET'])
@admin_required
def get_users_agreement_stats():
    """Obtiene estadísticas de agreement con el admin para todos los usuarios"""
    admin_username = request.current_user['username']
    
    logger.debug(f"Admin {admin_username} solicitando estadísticas de agreement")
    
    try:
        # Obtener estadísticas de agreement para todos los usuarios
        agreement_stats = db_service.get_all_users_agreement_stats()
        
        logger.debug(f"Admin {admin_username} obtuvo estadísticas de agreement para {len(agreement_stats)} usuarios")
        
        return jsonify({
            'success': True,
            'agreement_stats': agreement_stats
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de agreement: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

# Rutas de gestión de notificaciones
@api_bp.route('/admin/notifications/status', methods=['GET'])
@admin_required
def get_notifications_status():
    """Obtiene el estado de las notificaciones para todos los usuarios"""
    admin_username = request.current_user['username']
    
    logger.debug(f"Admin {admin_username} solicitando estado de notificaciones")
    
    try:
        # Obtener todos los usuarios
        users = db_service.get_all_users()
        
        notification_statuses = []
        for user in users:
            status = notification_service.get_notification_status(user.id)
            status['username'] = user.username
            status['role'] = user.role
            notification_statuses.append(status)
        
        logger.debug(f"Admin {admin_username} obtuvo estado de notificaciones para {len(notification_statuses)} usuarios")
        
        return jsonify({
            'success': True,
            'notification_statuses': notification_statuses
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estado de notificaciones: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@api_bp.route('/admin/notifications/reset/<int:user_id>', methods=['POST'])
@admin_required
def reset_user_notification_status(user_id):
    """Resetea el estado de notificación para un usuario específico"""
    admin_username = request.current_user['username']
    
    logger.debug(f"Admin {admin_username} reseteando estado de notificación para usuario ID: {user_id}")
    
    try:
        # Verificar que el usuario existe
        user = db_service.get_user_by_id(user_id)
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Resetear estado de notificación
        notification_service.mark_user_has_tasks(user_id, user.username)
        
        logger.info(f"Admin {admin_username} reseteó estado de notificación para usuario {user.username} (ID: {user_id})")
        
        return jsonify({
            'success': True,
            'message': f'Estado de notificación reseteado para usuario {user.username}'
        })
        
    except Exception as e:
        logger.error(f"Error reseteando estado de notificación: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@api_bp.route('/admin/notifications/test', methods=['POST'])
@admin_required
@validate_json_input(optional_fields=['message'])
def test_notification():
    """Envía una notificación de prueba al admin"""
    admin_username = request.current_user['username']
    data = request.get_json()
    
    custom_message = data.get('message', 'Esta es una notificación de prueba desde la aplicación de anotaciones.')
    
    logger.debug(f"Admin {admin_username} enviando notificación de prueba")
    
    try:
        success = notification_service.send_admin_notification(
            f"🧪 <b>Notificación de Prueba</b>\n\n"
            f"👤 <b>Enviado por:</b> {admin_username}\n"
            f"📝 <b>Mensaje:</b> {custom_message}\n"
            f"⏰ <b>Hora:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        if success:
            logger.info(f"Admin {admin_username} envió notificación de prueba exitosamente")
            return jsonify({
                'success': True,
                'message': 'Notificación de prueba enviada exitosamente'
            })
        else:
            logger.warning(f"Error enviando notificación de prueba para admin {admin_username}")
            return jsonify({
                'success': False,
                'error': 'Error enviando notificación de prueba'
            }), 500
        
    except Exception as e:
        logger.error(f"Error enviando notificación de prueba: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@api_bp.route('/admin/notifications/config', methods=['GET'])
@admin_required
def get_notification_config():
    """Obtiene la configuración actual de notificaciones"""
    admin_username = request.current_user['username']
    
    logger.debug(f"Admin {admin_username} solicitando configuración de notificaciones")
    
    try:
        config = {
            'min_notification_interval_seconds': notification_service.min_notification_interval,
            'min_notification_interval_hours': notification_service.min_notification_interval / 3600,
            'notification_timeout_seconds': notification_service.notification_timeout,
            'notification_timeout_hours': notification_service.notification_timeout / 3600,
            'telegram_configured': bool(os.getenv('TELEGRAM_BOT_TOKEN') and 
                                      os.getenv('TELEGRAM_BOT_TOKEN') != "123456789:ABCdefGhIjKlMnOpQrStUvWxYz" and
                                      os.getenv('TELEGRAM_ADMIN_CHAT_ID') and 
                                      os.getenv('TELEGRAM_ADMIN_CHAT_ID') != "123456789")
        }
        
        return jsonify({
            'success': True,
            'config': config
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo configuración de notificaciones: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500
