"""
Servicio de autenticación JWT para mayor seguridad
"""
import jwt
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
import os
import secrets

# Configurar logger para este módulo
logger = logging.getLogger(__name__)

class JWTService:
    """Servicio para manejo de JWT tokens"""
    
    def __init__(self):
        # Generar clave secreta segura si no existe
        self.secret_key = os.environ.get('JWT_SECRET_KEY', self._generate_secret_key())
        self.algorithm = 'HS256'
        self.access_token_expire_minutes = 480  # 8 horas
        self.refresh_token_expire_days = 30
        
        # Log de configuración
        logger.info("JWT Service inicializado")
        logger.debug(f"Access token expira en: {self.access_token_expire_minutes} minutos")
        logger.debug(f"Refresh token expira en: {self.refresh_token_expire_days} días")
        logger.debug(f"Longitud de clave secreta: {len(self.secret_key)} caracteres")
    
    def _generate_secret_key(self):
        """Genera una clave secreta segura"""
        key = secrets.token_urlsafe(64)
        logger.warning("Generando nueva clave JWT secreta - usar JWT_SECRET_KEY en producción")
        return key
    
    def create_access_token(self, user_id: int, username: str, role: str) -> str:
        """Crea un token de acceso JWT"""
        payload = {
            'user_id': user_id,
            'username': username,
            'role': role,
            'exp': datetime.now() + timedelta(minutes=self.access_token_expire_minutes),
            'iat': datetime.now(),
            'type': 'access'
        }
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        logger.debug(f"Token de acceso creado para usuario {username} (ID: {user_id}, rol: {role})")
        return token
    
    def create_refresh_token(self, user_id: int) -> str:
        """Crea un token de refresh JWT"""
        payload = {
            'user_id': user_id,
            'exp': datetime.now() + timedelta(days=self.refresh_token_expire_days),
            'iat': datetime.now(),
            'type': 'refresh'
        }
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        logger.debug(f"Token de refresh creado para usuario ID: {user_id}")
        return token
    
    def decode_token(self, token: str) -> dict:
        """Decodifica y valida un JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            logger.debug(f"Token decodificado exitosamente para usuario {payload.get('username', payload.get('user_id'))}")
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Intento de uso de token expirado")
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token inválido: {e}")
            raise ValueError("Invalid token")
    
    def get_token_from_header(self) -> str:
        """Extrae el token del header Authorization"""
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            logger.debug("Header Authorization faltante")
            raise ValueError("Authorization header is missing")
        
        try:
            # Formato esperado: "Bearer <token>"
            bearer, token = auth_header.split(' ')
            if bearer.lower() != 'bearer':
                logger.warning(f"Formato de autorización inválido: {bearer}")
                raise ValueError("Invalid authorization format")
            logger.debug("Token extraído del header Authorization")
            return token
        except ValueError:
            logger.warning("Error parsing Authorization header")
            raise ValueError("Invalid authorization format")
    
    def verify_access_token(self, token: str) -> dict:
        """Verifica un token de acceso y retorna el payload"""
        payload = self.decode_token(token)
        if payload.get('type') != 'access':
            logger.warning(f"Tipo de token inválido: {payload.get('type')}")
            raise ValueError("Invalid token type")
        logger.debug("Token de acceso verificado exitosamente")
        return payload
    
    def verify_refresh_token(self, token: str) -> dict:
        """Verifica un token de refresh y retorna el payload"""
        payload = self.decode_token(token)
        if payload.get('type') != 'refresh':
            logger.warning(f"Tipo de refresh token inválido: {payload.get('type')}")
            raise ValueError("Invalid token type")
        logger.debug("Token de refresh verificado exitosamente")
        return payload

# Instancia global del servicio JWT
jwt_service = JWTService()

def jwt_required(f):
    """Decorador para requerir autenticación JWT"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            token = jwt_service.get_token_from_header()
            payload = jwt_service.verify_access_token(token)
            
            # Log de autenticación exitosa
            logger.info(f"Autenticación JWT exitosa para {payload.get('username')} (rol: {payload.get('role')})")
            
            # Agregar información del usuario al contexto de la request
            request.current_user = {
                'user_id': payload['user_id'],
                'username': payload['username'],
                'role': payload['role']
            }
            
            return f(*args, **kwargs)
            
        except ValueError as e:
            logger.warning(f"Fallo en autenticación JWT: {str(e)}")
            return jsonify({'error': str(e)}), 401
        except Exception as e:
            logger.error(f"Error en autenticación JWT: {str(e)}")
            return jsonify({'error': 'Authentication failed'}), 401
    
    return decorated_function

def admin_required(f):
    """Decorador para requerir permisos de administrador con JWT"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            token = jwt_service.get_token_from_header()
            payload = jwt_service.verify_access_token(token)
            
            if payload.get('role') != 'admin':
                logger.warning(f"Acceso de admin denegado para {payload.get('username')} (rol: {payload.get('role')})")
                return jsonify({'error': 'Admin access required'}), 403
            
            logger.info(f"Acceso de admin concedido para {payload.get('username')}")
            
            # Agregar información del usuario al contexto de la request
            request.current_user = {
                'user_id': payload['user_id'],
                'username': payload['username'],
                'role': payload['role']
            }
            
            return f(*args, **kwargs)
            
        except ValueError as e:
            logger.warning(f"Fallo en autenticación JWT para admin: {str(e)}")
            return jsonify({'error': str(e)}), 401
        except Exception as e:
            logger.error(f"Error en autenticación JWT para admin: {str(e)}")
            return jsonify({'error': 'Authentication failed'}), 401
    
    return decorated_function

def optional_jwt(f):
    """Decorador para JWT opcional (no bloquea si no hay token)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            token = jwt_service.get_token_from_header()
            payload = jwt_service.verify_access_token(token)
            
            request.current_user = {
                'user_id': payload['user_id'],
                'username': payload['username'],
                'role': payload['role']
            }
            logger.debug(f"JWT opcional - usuario autenticado: {payload.get('username')}")
        except:
            request.current_user = None
            logger.debug("JWT opcional - sin token válido")
            
        return f(*args, **kwargs)
    
    return decorated_function
