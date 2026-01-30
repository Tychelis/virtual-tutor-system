"""Gunicorn Configuration - LLM Service Concurrency Support"""
import multiprocessing
import os
import sys

# Import unified port configuration
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.ports_config import LLM_PORT

# Number of workers
# LLM service is resource-intensive, don't use too many workers
workers = int(os.getenv('WORKERS', 2))  # Default 2 workers

# Worker type
# Use sync instead of gevent because LLM processing is CPU-intensive
worker_class = os.getenv('WORKER_CLASS', 'sync')

# Number of threads (per worker)
threads = int(os.getenv('THREADS', 2))  # 2 threads per worker

# Bind address (imported from unified configuration)
bind = f'0.0.0.0:{LLM_PORT}'

# Timeout (LLM responses are slow, need long timeout)
timeout = 180  # 3 minutes

# Keep-alive
keepalive = 5

# Performance optimization
max_requests = 100  # LLM service restarts worker after processing 100 requests
max_requests_jitter = 20
worker_tmp_dir = '/dev/shm'

# Logs
accesslog = 'logs/llm_access.log'
errorlog = 'logs/llm_error.log'
loglevel = 'info'

# Preload application (share model memory)
preload_app = True

# Graceful shutdown timeout
graceful_timeout = 60

# Hooks
def on_starting(server):
    """Execute when service starts"""
    print(f"\n Starting LLM Service with Gunicorn")
    print(f"   Workers: {workers} ({worker_class})")
    print(f"   Threads per worker: {threads}")
    print(f"   Binding to {bind}")
    print(f"   Timeout: {timeout}s\n")

def post_worker_init(worker):
    """After worker initialization completes"""
    print(f" Worker {worker.pid} initialized")

def worker_exit(server, worker):
    """When worker exits"""
    print(f"  Worker {worker.pid} exiting")





