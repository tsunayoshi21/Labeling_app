# services/notification_service.py
import time
import logging
from typing import Dict, Set
from datetime import datetime, timedelta
from utils.telegram import send_admin_notification

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Servicio para manejar notificaciones con protección anti-spam
    """
    
    def __init__(self):
        # Diccionario para trackear últimas notificaciones por usuario
        # user_id -> timestamp de última notificación
        self._last_notifications: Dict[int, float] = {}
        
        # Set de usuarios que ya fueron notificados y aún no tienen tareas nuevas
        self._notified_users: Set[int] = set()
        
        # Tiempo mínimo entre notificaciones para el mismo usuario (en segundos)
        self.min_notification_interval = 3600  # 1 hora
        
        # Tiempo máximo para considerar una notificación como "reciente"
        self.notification_timeout = 24 * 3600  # 24 horas
    
    def should_notify_no_tasks(self, user_id: int, username: str) -> bool:
        """
        Determina si se debe enviar una notificación de "sin tareas" para un usuario
        
        Args:
            user_id: ID del usuario
            username: Nombre del usuario
        
        Returns:
            bool: True si se debe enviar la notificación
        """
        current_time = time.time()
        
        # Verificar si el usuario ya fue notificado recientemente
        if user_id in self._notified_users:
            logger.debug(f"Usuario {username} (ID: {user_id}) ya fue notificado anteriormente")
            return False
        
        # Verificar el intervalo mínimo desde la última notificación
        last_notification = self._last_notifications.get(user_id, 0)
        time_since_last = current_time - last_notification
        
        if time_since_last < self.min_notification_interval:
            minutes_remaining = int((self.min_notification_interval - time_since_last) / 60)
            logger.debug(f"Notificación para {username} bloqueada por anti-spam. "
                        f"Faltan {minutes_remaining} minutos")
            return False
        
        # Limpiar notificaciones antiguas
        self._cleanup_old_notifications()
        
        return True
    
    def send_no_tasks_notification(self, user_id: int, username: str) -> bool:
        """
        Envía una notificación al admin cuando un usuario no tiene más tareas
        
        Args:
            user_id: ID del usuario
            username: Nombre del usuario
        
        Returns:
            bool: True si la notificación se envió correctamente
        """
        if not self.should_notify_no_tasks(user_id, username):
            return False
        
        # Preparar el mensaje
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = (
            f"🚨 <b>Usuario sin tareas</b>\n\n"
            f"👤 <b>Usuario:</b> {username} (ID: {user_id})\n"
            f"📋 <b>Estado:</b> Ya completó todas sus tareas pendientes\n"
            f"⏰ <b>Hora:</b> {current_time}\n\n"
            f"💡 <i>¡Asígnale más tareas para que pueda continuar!</i>"
        )
        
        # Intentar enviar la notificación
        success = send_admin_notification(message)
        
        if success:
            # Marcar como notificado
            current_timestamp = time.time()
            self._last_notifications[user_id] = current_timestamp
            self._notified_users.add(user_id)
            
            logger.info(f"Notificación de 'sin tareas' enviada exitosamente para usuario {username} (ID: {user_id})")
            return True
        else:
            logger.error(f"Error enviando notificación de 'sin tareas' para usuario {username} (ID: {user_id})")
            return False
    
    def mark_user_has_tasks(self, user_id: int, username: str = None):
        """
        Marca que un usuario ahora tiene tareas disponibles
        Esto resetea el estado de notificación para permitir futuras notificaciones
        
        Args:
            user_id: ID del usuario
            username: Nombre del usuario (opcional, para logging)
        """
        if user_id in self._notified_users:
            self._notified_users.remove(user_id)
            user_info = f"{username} (ID: {user_id})" if username else f"ID: {user_id}"
            logger.debug(f"Usuario {user_info} ahora tiene tareas disponibles - estado de notificación reseteado")
    
    def _cleanup_old_notifications(self):
        """
        Limpia notificaciones antiguas del cache
        """
        current_time = time.time()
        cutoff_time = current_time - self.notification_timeout
        
        # Limpiar notificaciones antiguas
        old_notifications = [
            user_id for user_id, timestamp in self._last_notifications.items()
            if timestamp < cutoff_time
        ]
        
        for user_id in old_notifications:
            del self._last_notifications[user_id]
            self._notified_users.discard(user_id)
        
        if old_notifications:
            logger.debug(f"Limpiadas {len(old_notifications)} notificaciones antiguas")
    
    def get_notification_status(self, user_id: int) -> Dict:
        """
        Obtiene el estado de notificaciones para un usuario (útil para debugging)
        
        Args:
            user_id: ID del usuario
        
        Returns:
            dict: Estado de notificaciones del usuario
        """
        current_time = time.time()
        last_notification = self._last_notifications.get(user_id, 0)
        time_since_last = current_time - last_notification if last_notification > 0 else None
        
        return {
            'user_id': user_id,
            'was_notified': user_id in self._notified_users,
            'last_notification_timestamp': last_notification if last_notification > 0 else None,
            'time_since_last_notification_seconds': time_since_last,
            'can_notify': self.should_notify_no_tasks(user_id, f"user_{user_id}")
        }

# Instancia global del servicio de notificaciones
notification_service = NotificationService()
