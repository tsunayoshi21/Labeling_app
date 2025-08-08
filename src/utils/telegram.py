# utils/telegram.py
import os
import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Configuración desde variables de entorno
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', "123456789:ABCdefGhIjKlMnOpQrStUvWxYz")
ADMIN_CHAT_ID = os.getenv('TELEGRAM_ADMIN_CHAT_ID', "123456789")

def send_telegram_message(text: str, chat_id: Optional[str] = None) -> bool:
    """
    Envía un mensaje por Telegram
    
    Args:
        text: Texto del mensaje
        chat_id: ID del chat (por defecto usa ADMIN_CHAT_ID)
    
    Returns:
        bool: True si el mensaje se envió correctamente
    """
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "123456789:ABCdefGhIjKlMnOpQrStUvWxYz":
        logger.warning("Token de Telegram no configurado correctamente")
        return False
    
    target_chat_id = chat_id or ADMIN_CHAT_ID
    if not target_chat_id or target_chat_id == "123456789":
        logger.warning("Chat ID de Telegram no configurado correctamente")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": target_chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"Mensaje de Telegram enviado exitosamente a chat {target_chat_id}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Error enviando mensaje de Telegram: {e}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado enviando mensaje de Telegram: {e}")
        return False

def send_admin_notification(message: str) -> bool:
    """
    Envía una notificación al admin
    
    Args:
        message: Mensaje para el admin
    
    Returns:
        bool: True si se envió correctamente
    """
    return send_telegram_message(message, ADMIN_CHAT_ID)
