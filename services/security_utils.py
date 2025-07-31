"""
Utilidades de seguridad adicionales para la aplicación
"""
import hashlib
import hmac
import time
import logging
from functools import wraps
from flask import request, jsonify
import re

# Configurar logger para este módulo
logger = logging.getLogger(__name__)

class SecurityUtils:
    """Utilidades de seguridad adicionales"""
    
    @staticmethod
    def validate_input(data: str, max_length: int = 1000, allow_html: bool = False) -> str:
        """Valida y sanitiza entrada de usuario"""
        if not data or not isinstance(data, str):
            logger.warning("Intento de validar entrada inválida")
            raise ValueError("Invalid input data")
        
        # Limitar longitud
        if len(data) > max_length:
            logger.warning(f"Entrada demasiado larga: {len(data)} caracteres (máx: {max_length})")
            raise ValueError(f"Input too long (max {max_length} characters)")
        
        # Remover HTML si no está permitido
        if not allow_html:
            if re.search(r'<[^>]+>', data):
                logger.debug("HTML removido de entrada de usuario")
            data = re.sub(r'<[^>]+>', '', data)
        
        # Remover caracteres peligrosos
        data = data.replace('\x00', '').replace('\r', '').replace('\n', ' ')
        
        logger.debug(f"Entrada validada exitosamente: {len(data)} caracteres")
        return data.strip()
    
    @staticmethod
    def validate_password_strength(password: str) -> bool:
        """Valida la fortaleza de una contraseña"""
        if len(password) < 8:
            logger.debug("Contraseña rechazada: muy corta")
            return False
        
        # Al menos una mayúscula, una minúscula y un número
        if not re.search(r'[A-Z]', password):
            logger.debug("Contraseña rechazada: sin mayúscula")
            return False
        if not re.search(r'[a-z]', password):
            logger.debug("Contraseña rechazada: sin minúscula")  
            return False
        if not re.search(r'\d', password):
            logger.debug("Contraseña rechazada: sin número")
            return False
        
        logger.debug("Contraseña validada exitosamente")
        return True
    
    @staticmethod
    def create_csrf_token(secret_key: str, user_id: int) -> str:
        """Crea un token CSRF"""
        timestamp = str(int(time.time()))
        message = f"{user_id}:{timestamp}"
        signature = hmac.new(
            secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        logger.debug(f"Token CSRF creado para usuario {user_id}")
        return f"{message}:{signature}"
    
    @staticmethod
    def verify_csrf_token(token: str, secret_key: str, user_id: int, max_age: int = 3600) -> bool:
        """Verifica un token CSRF"""
        try:
            parts = token.split(':')
            if len(parts) != 3:
                logger.warning("Token CSRF con formato inválido")
                return False
            
            token_user_id, timestamp, signature = parts
            
            # Verificar user_id
            if int(token_user_id) != user_id:
                logger.warning(f"Token CSRF con user_id incorrecto: {token_user_id} vs {user_id}")
                return False
            
            # Verificar edad del token
            token_time = int(timestamp)
            if time.time() - token_time > max_age:
                logger.warning("Token CSRF expirado")
                return False
            
            # Verificar signature
            message = f"{token_user_id}:{timestamp}"
            expected_signature = hmac.new(
                secret_key.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            is_valid = hmac.compare_digest(signature, expected_signature)
            if is_valid:
                logger.debug(f"Token CSRF válido para usuario {user_id}")
            else:
                logger.warning(f"Token CSRF inválido para usuario {user_id}")
            return is_valid
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Error verificando token CSRF: {e}")
            return False

def rate_limit(max_requests: int = 60, window_seconds: int = 60):
    """Decorador para limitar tasa de requests por IP"""
    request_counts = {}
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            current_time = time.time()
            
            # Limpiar entradas antiguas
            request_counts[client_ip] = [
                req_time for req_time in request_counts.get(client_ip, [])
                if current_time - req_time < window_seconds
            ]
            
            # Verificar límite
            current_count = len(request_counts.get(client_ip, []))
            if current_count >= max_requests:
                logger.warning(f"Rate limit excedido para IP {client_ip}: {current_count}/{max_requests} requests")
                return jsonify({'error': 'Rate limit exceeded'}), 429
            
            # Agregar request actual
            if client_ip not in request_counts:
                request_counts[client_ip] = []
            request_counts[client_ip].append(current_time)
            
            logger.debug(f"Request aceptado para IP {client_ip}: {current_count + 1}/{max_requests}")
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def validate_json_input(required_fields: list = None, optional_fields: list = None):
    """Decorador para validar entrada JSON"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                logger.warning("Request sin Content-Type application/json")
                return jsonify({'error': 'Content-Type must be application/json'}), 400
            
            data = request.get_json()
            if not data:
                logger.warning("Request sin datos JSON")
                return jsonify({'error': 'No JSON data provided'}), 400
            
            # Verificar campos requeridos
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    logger.warning(f"Campos requeridos faltantes: {missing_fields}")
                    return jsonify({'error': f'Missing required fields: {missing_fields}'}), 400
            
            # Verificar que solo se envíen campos permitidos
            all_allowed = (required_fields or []) + (optional_fields or [])
            if all_allowed:
                invalid_fields = [field for field in data.keys() if field not in all_allowed]
                if invalid_fields:
                    logger.warning(f"Campos inválidos enviados: {invalid_fields}")
                    return jsonify({'error': f'Invalid fields: {invalid_fields}'}), 400
            
            logger.debug(f"Validación JSON exitosa - campos: {list(data.keys())}")
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
