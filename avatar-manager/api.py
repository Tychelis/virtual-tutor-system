"""Avatar Manager REST API服务"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import threading
import time

from manager import get_manager
from config import API_PORT, IDLE_TIMEOUT, HEALTH_CHECK_INTERVAL
from monitor import get_monitor

app = Flask(__name__)
CORS(app)  # 启用CORS

logger = logging.getLogger('API')


# ============================================================================
# API端点
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """API健康检查"""
    return jsonify({
        'status': 'healthy',
        'service': 'avatar-manager',
        'version': '1.0.0'
    })


@app.route('/avatar/start', methods=['POST'])
def start_avatar():
    """启动Avatar实例"""
    try:
        data = request.get_json()
        instance_id = data.get('avatar_id')  # 实例ID（如 g_user_1）
        avatar_name = data.get('avatar_name')  # 真实Avatar名称（如 g）
        
        if not instance_id:
            return jsonify({
                'status': 'error',
                'message': '缺少avatar_id参数'
            }), 400
        
        # 如果没提供avatar_name，从instance_id中提取（向后兼容）
        if not avatar_name:
            # 尝试从 g_user_1 提取 g
            avatar_name = instance_id.split('_user_')[0] if '_user_' in instance_id else instance_id
            logger.info(f"未提供avatar_name，从instance_id提取: {instance_id} → {avatar_name}")
        else:
            logger.info(f"接收到avatar_name: {avatar_name}")
        
        manager = get_manager()
        info = manager.start(instance_id, real_avatar_name=avatar_name)
        
        return jsonify({
            'status': 'success',
            'message': f'Avatar {instance_id} (真实名称: {avatar_name}) 启动成功',
            'data': info
        })
        
    except Exception as e:
        logger.error(f"启动Avatar失败: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400


@app.route('/avatar/stop', methods=['POST'])
def stop_avatar():
    """停止Avatar实例（强制关闭）"""
    try:
        data = request.get_json()
        avatar_id = data.get('avatar_id')
        force = data.get('force', True)  # 默认强制关闭
        
        if not avatar_id:
            return jsonify({
                'status': 'error',
                'message': '缺少avatar_id参数'
            }), 400
        
        manager = get_manager()
        manager.stop(avatar_id, force=force)
        
        return jsonify({
            'status': 'success',
            'message': f'Avatar {avatar_id} 已停止'
        })
        
    except Exception as e:
        logger.error(f"停止Avatar失败: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400


@app.route('/avatar/disconnect', methods=['POST'])
def disconnect_avatar():
    """断开Avatar连接（减少连接计数，不强制关闭）"""
    try:
        data = request.get_json()
        avatar_id = data.get('avatar_id')
        avatar_name = data.get('avatar_name')
        
        # 优先使用avatar_name，如果没有则使用avatar_id
        target_id = avatar_name if avatar_name else avatar_id
        
        if not target_id:
            return jsonify({
                'status': 'error',
                'message': '缺少avatar_id或avatar_name参数'
            }), 400
        
        manager = get_manager()
        manager.stop(target_id, force=False)  # 不强制关闭
        
        return jsonify({
            'status': 'success',
            'message': f'Avatar {target_id} 连接已断开'
        })
        
    except Exception as e:
        logger.error(f"断开Avatar连接失败: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400


@app.route('/avatar/restart', methods=['POST'])
def restart_avatar():
    """重启Avatar实例"""
    try:
        data = request.get_json()
        avatar_id = data.get('avatar_id')
        
        if not avatar_id:
            return jsonify({
                'status': 'error',
                'message': '缺少avatar_id参数'
            }), 400
        
        manager = get_manager()
        info = manager.restart(avatar_id)
        
        return jsonify({
            'status': 'success',
            'message': f'Avatar {avatar_id} 重启成功',
            'data': info
        })
        
    except Exception as e:
        logger.error(f"重启Avatar失败: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400


@app.route('/avatar/list', methods=['GET'])
def list_avatars():
    """列出所有Avatar"""
    try:
        manager = get_manager()
        avatars = manager.list_all()
        
        return jsonify({
            'status': 'success',
            'count': len(avatars),
            'data': avatars
        })
        
    except Exception as e:
        logger.error(f"列出Avatar失败: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/avatar/info/<avatar_id>', methods=['GET'])
def get_avatar_info(avatar_id):
    """获取Avatar信息"""
    try:
        manager = get_manager()
        info = manager.get_info(avatar_id)
        
        if info is None:
            return jsonify({
                'status': 'error',
                'message': f'Avatar {avatar_id} 不存在'
            }), 404
        
        return jsonify({
            'status': 'success',
            'data': info
        })
        
    except Exception as e:
        logger.error(f"获取Avatar信息失败: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/status', methods=['GET'])
def get_status():
    """获取系统状态"""
    try:
        manager = get_manager()
        monitor = get_monitor()
        
        status = manager.get_status()
        gpu_stats = monitor.get_gpu_stats()
        
        return jsonify({
            'status': 'success',
            'data': {
                'manager': status,
                'gpu': gpu_stats
            }
        })
        
    except Exception as e:
        logger.error(f"获取状态失败: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/avatar/stop-all', methods=['POST'])
def stop_all():
    """停止所有Avatar"""
    try:
        manager = get_manager()
        manager.stop_all()
        
        return jsonify({
            'status': 'success',
            'message': '所有Avatar已停止'
        })
        
    except Exception as e:
        logger.error(f"停止所有Avatar失败: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# ============================================================================
# 后台任务
# ============================================================================

def background_tasks():
    """后台任务：健康检查和清理"""
    logger.info("后台任务线程启动")
    
    while True:
        try:
            # 健康检查
            manager = get_manager()
            manager.health_check()
            
            # 清理空闲实例
            if IDLE_TIMEOUT > 0:
                manager.cleanup_idle(IDLE_TIMEOUT)
            
        except Exception as e:
            logger.error(f"后台任务错误: {e}")
        
        # 等待下一次检查
        time.sleep(HEALTH_CHECK_INTERVAL)


# ============================================================================
# 启动服务
# ============================================================================

if __name__ == '__main__':
    logger.info(f"启动Avatar Manager API服务 (端口: {API_PORT})")
    
    # 启动后台任务线程
    bg_thread = threading.Thread(target=background_tasks, daemon=True)
    bg_thread.start()
    
    # 启动Flask应用
    app.run(
        host='0.0.0.0',
        port=API_PORT,
        debug=False,
        threaded=True
    )

