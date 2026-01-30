"""Health check endpoints for monitoring and load balancing"""
from flask import Blueprint, jsonify
from models.user import db
from services.redis_client import redis_client
import requests
import os
import sys

# 导入统一端口配置
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from scripts.ports_config import get_llm_url, get_rag_url

health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "backend"
    }), 200


@health_bp.route('/health/detailed', methods=['GET'])
def detailed_health_check():
    """Detailed health check including dependencies"""
    health_status = {
        "status": "healthy",
        "service": "backend",
        "checks": {}
    }
    
    # Check database
    try:
        db.session.execute(db.text('SELECT 1'))
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Redis
    try:
        redis_client.ping()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check LLM service (optional, don't fail if not available)
    try:
        llm_url = get_llm_url(use_optimized=True)
        response = requests.get(f"{llm_url}/health", timeout=2)  # 使用优化版
        health_status["checks"]["llm"] = "healthy" if response.status_code == 200 else "unreachable"
    except:
        health_status["checks"]["llm"] = "unreachable"
    
    # Check RAG service (optional)
    try:
        rag_url = get_rag_url()
        response = requests.get(f"{rag_url}/health", timeout=2)
        health_status["checks"]["rag"] = "healthy" if response.status_code == 200 else "unreachable"
    except:
        health_status["checks"]["rag"] = "unreachable"
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return jsonify(health_status), status_code


@health_bp.route('/ping', methods=['GET'])
def ping():
    """Minimal ping endpoint"""
    return "pong", 200

