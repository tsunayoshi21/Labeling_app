# Configuración de Gunicorn para la aplicación de anotación colaborativa
import multiprocessing
import os

# Servidor
bind = f"{os.getenv('HOST', '0.0.0.0')}:{os.getenv('PORT', '8080')}"
backlog = 2048

# Workers - configuración más conservadora
workers = int(os.getenv('WORKERS', min(multiprocessing.cpu_count() * 2 + 1, 16)))  # Máximo 8 workers
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 2

# Restart workers after this many requests, with up to this much jitter
max_requests = 1000
max_requests_jitter = 100

# Preload app for better performance
preload_app = True

# Logging
accesslog = os.getenv('ACCESS_LOG', "-")  # stdout por defecto
errorlog = os.getenv('ERROR_LOG', "-")    # stderr por defecto
loglevel = os.getenv('LOG_LEVEL', 'debug').lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Seguridad y límites
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Process naming
proc_name = 'labeling_app'

# Server mechanics
daemon = False
pidfile = None
user = None
group = None

# SSL (descomentado para usar HTTPS)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

print(f"Gunicorn configurado: {workers} workers en {bind}")
