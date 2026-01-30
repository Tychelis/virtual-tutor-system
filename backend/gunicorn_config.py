"""Gunicorn Configuration - True Concurrency Support"""
import multiprocessing
import os
import sys

# Import unified port configuration
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.ports_config import BACKEND_PORT

# Number of worker processes (based on CPU cores)
# 降低worker数量以避免session同步问题
# 对于I/O密集型应用（avatar streaming），4-8个worker足够
workers = int(os.getenv('WORKERS', 4))

# Worker type
# - sync: synchronous worker (default, suitable for CPU-intensive)
# - gevent: coroutine worker (suitable for I/O-intensive, requires pip install gevent)
# - eventlet: another coroutine implementation (requires pip install eventlet)
worker_class = os.getenv('WORKER_CLASS', 'sync')

# Number of threads per worker (only effective for gthread worker_class)
threads = int(os.getenv('THREADS', 1))

# Maximum concurrent connections per worker (only effective for gevent/eventlet)
worker_connections = 1000

# Bind address (imported from unified configuration)
bind = f'0.0.0.0:{BACKEND_PORT}'

# Timeout (seconds)
timeout = 120

# Keep-alive connection timeout
keepalive = 5

# Performance optimization
max_requests = 1000  # Restart worker after processing N requests (prevents memory leaks)
max_requests_jitter = 100  # Randomize restart to avoid all workers restarting simultaneously
worker_tmp_dir = '/dev/shm'  # Use in-memory filesystem (Linux)

# Logging configuration
accesslog = 'logs/backend_access.log'
errorlog = 'logs/backend_error.log'
loglevel = 'info'

# Preload application (saves memory, but requires restarting all workers on reload)
preload_app = True

# Graceful shutdown timeout
graceful_timeout = 30

# Hooks
def on_starting(server):
    """Execute when service starts"""
    print(f" Starting Gunicorn with {workers} {worker_class} workers")
    print(f" Binding to {bind}")
    print(f"  Timeout: {timeout}s")

def worker_int(worker):
    """When worker is interrupted by SIGINT"""
    print(f"  Worker {worker.pid} received INT signal")

def post_worker_init(worker):
    """After worker initialization completes"""
    print(f" Worker {worker.pid} initialized")





