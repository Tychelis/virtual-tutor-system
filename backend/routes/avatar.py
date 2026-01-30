from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
import httpx
from models.user import User
from services.http_client import http_client
from services.avatar_session_manager import get_avatar_session_manager
import os
import sys
import json
import logging

# 导入统一端口配置
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from scripts.ports_config import AVATAR_BASE_PORT, AVATAR_MANAGER_API_PORT, LIVE_SERVER_PORT, get_avatar_manager_url, get_live_server_url

# Blueprint for avatar-related routes
avatar_bp = Blueprint("avatar", __name__)
logger = logging.getLogger(__name__)


@avatar_bp.route("/webrtc/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
@jwt_required(optional=True)  # 允许带或不带JWT
def webrtc_proxy(path):
    """Proxy WebRTC requests to user's avatar port (supports concurrent users)"""
    # 处理 CORS 预检请求（OPTIONS）
    # Flask-CORS 会自动添加必要的 CORS 响应头
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
    
    # 尝试获取用户信息来确定端口
    port = AVATAR_BASE_PORT  # 使用统一配置的默认端口
    avatar_name = "unknown"
    
    try:
        # 正确处理optional JWT
        from flask_jwt_extended import verify_jwt_in_request
        verify_jwt_in_request(optional=True)
        current_user_email = get_jwt_identity()
        
        if current_user_email:
            user = User.query.filter_by(email=current_user_email).first()
            if user:
                # 关键修复：每次都直接从Redis Hash读取（多worker环境）
                try:
                    from services.redis_client import redis_client
                    import json as json_module
                    user_id_str = str(user.id)
                    user_info_bytes = redis_client.hget('avatar:user_mappings', user_id_str)
                    
                    if user_info_bytes:
                        user_info_str = user_info_bytes.decode('utf-8') if isinstance(user_info_bytes, bytes) else user_info_bytes
                        user_avatar_info = json_module.loads(user_info_str)
                        port = user_avatar_info['port']
                        avatar_name = user_avatar_info['avatar_id']
                        logger.info(f"🎥 WebRTC Proxy: User {user.id} → Avatar '{avatar_name}' on port {port} (path: /{path})")
                    else:
                        logger.warning(f"⚠️ WebRTC Proxy: User {user.id} has no avatar mapping in Redis, using default port {port}")
                except Exception as redis_err:
                    logger.error(f"❌ Failed to read from Redis Hash: {redis_err}, using default port {port}")
    except Exception as e:
        # 如果获取用户信息失败，使用默认端口
        logger.debug(f"WebRTC Proxy: No JWT or error: {e}, using default port {port}")
    
    webrtc_url = f"http://localhost:{port}/{path}"
    
    try:
        # Prepare headers
        headers = {k: v for k, v in request.headers if k.lower() not in ['host', 'content-length', 'authorization']}
        
        # Forward request using connection pool
        if request.method == "POST":
            resp = http_client.post(
                webrtc_url, 
                headers=headers, 
                content=request.get_data(),
                timeout=30.0
            )
        elif request.method == "GET":
            resp = http_client.get(
                webrtc_url, 
                headers=headers, 
                params=request.args,
                timeout=30.0
            )
        else:
            resp = http_client.request(
                request.method, 
                webrtc_url, 
                headers=headers, 
                content=request.get_data(),
                timeout=30.0
            )
        
        # Return response
        return Response(resp.content, status=resp.status_code, headers=dict(resp.headers))
    except httpx.TimeoutException:
        return jsonify(msg="Proxy timeout"), 504
    except httpx.RequestError as e:
        return jsonify(msg=f"Proxy error: {str(e)}"), 502
    except Exception as e:
        return jsonify(msg=f"Unexpected error: {str(e)}"), 502


@avatar_bp.route("/avatar/list", methods=["GET"])
@jwt_required()
def fetch_avatars():
    """Fetch list of available avatars from the avatar service."""
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email).first()

    try:
        live_server_url = get_live_server_url()
        response = http_client.get(
            f"{live_server_url}/avatar/get_avatars", 
            timeout=10.0
        )
        data = response.json()
        
        # 前端期望对象格式：{avatar_name: {clone: bool, description: str, ...}}
        if data.get('status') == 'success' and 'avatars' in data:
            avatars = data['avatars']
            # 如果avatars已经是字典格式（新版API），直接使用
            if isinstance(avatars, dict):
                # 添加clone字段（基于support_clone）
                for avatar_name, config in avatars.items():
                    config['clone'] = config.get('support_clone', False)
                return jsonify(avatars), 200
            # 如果avatars是列表格式（旧版API），转换为对象格式
            elif isinstance(avatars, list):
                avatar_dict = {}
                for avatar_name in avatars:
                    avatar_dict[avatar_name] = {
                        "clone": False,
                        "description": f"Avatar: {avatar_name}",
                        "status": "active",
                        "timbre": "",
                        "tts_model": "",
                        "avatar_model": ""
                    }
                return jsonify(avatar_dict), 200
        return jsonify(data), response.status_code
    except httpx.TimeoutException:
        return jsonify(msg="Avatar service timeout"), 504
    except httpx.RequestError as e:
        return jsonify(msg="Failed to connect to avatar service", error=str(e)), 500
    except Exception as e:
        return jsonify(msg="Unexpected error", error=str(e)), 500


@avatar_bp.route("/avatar/preview", methods=["POST"])
@jwt_required()
def forward_avatar_preview():
    """Request an avatar preview from the avatar service and return the image."""
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email).first()

    avatar_name = request.form.get("avatar_name")
    if not avatar_name:
        return jsonify(msg="Missing avatar_name in form-data"), 400

    try:
        live_server_url = get_live_server_url()
        response = http_client.post(
            f"{live_server_url}/avatar/preview",
            data={"avatar_name": avatar_name},
            timeout=10.0
        )

        if response.status_code != 200:
            return jsonify(msg="Failed to get avatar preview", detail=response.text), response.status_code

        # Forward image content directly to the client
        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get("Content-Type", "image/png")
        )

    except httpx.TimeoutException:
        return jsonify(msg="Avatar service timeout"), 504
    except httpx.RequestError as e:
        return jsonify(msg="Error forwarding to avatar service", error=str(e)), 500
    except Exception as e:
        return jsonify(msg="Unexpected error", error=str(e)), 500


@avatar_bp.route("/avatar/add", methods=["POST"])
@jwt_required()
def add_avatar():
    """Forward avatar creation request to the avatar service (tutor only)."""
    admin_email = get_jwt_identity()
    admin = User.query.filter_by(email=admin_email).first()

    if not admin or admin.role.lower() != "tutor":
        return jsonify({"msg": "Permission denied"}), 403

    # Collect form fields
    form_fields = [
        "name", "avatar_blur", "support_clone", "timbre",
        "tts_model", "avatar_model", "description"
    ]
    data = {field: request.form.get(field) for field in form_fields if field in request.form}

    prompt_face = request.files.get("prompt_face")
    prompt_voice = request.files.get("prompt_voice")

    files = {}
    if prompt_face:
        files["prompt_face"] = (prompt_face.filename, prompt_face.stream.read(), prompt_face.mimetype)
    if prompt_voice:
        files["prompt_voice"] = (prompt_voice.filename, prompt_voice.stream.read(), prompt_voice.mimetype)

    try:
        live_server_url = get_live_server_url()
        response = http_client.post(
            f"{live_server_url}/avatar/add",
            data=data,
            files=files,
            timeout=900.0  # 15分钟超时，创建avatar需要较长时间
        )

        try:
            response_data = response.json()
        except ValueError:
            return jsonify(msg="Invalid JSON response from avatar service", raw=response.text), 500

        if response_data.get("status") == "success":
            return jsonify(response_data), 200
        else:
            return jsonify(msg="Avatar creation failed", detail=response_data), 400

    except httpx.TimeoutException:
        return jsonify(msg="Avatar creation timeout (exceeded 15 minutes)"), 504
    except httpx.RequestError as e:
        return jsonify(msg="Error forwarding to avatar service", error=str(e)), 500
    except Exception as e:
        return jsonify(msg="Unexpected error", error=str(e)), 500


@avatar_bp.route("/tts/models", methods=["GET"])
@jwt_required()
def get_tts_models():
    """Fetch available TTS models from the model_info.json file."""
    current_user_email = get_jwt_identity()
    try:
        # 直接从model_info.json文件读取TTS模型列表
        # 获取model_info.json文件路径
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        model_info_file = os.path.join(project_root, "tts", "model_info.json")
        
        if not os.path.exists(model_info_file):
            return jsonify(msg="Model information file not found"), 404
        
        # 读取模型信息
        with open(model_info_file, 'r', encoding='utf-8') as f:
            contents = json.load(f)
        
        # 构造返回数据格式
        model_info = {}
        for model_name, info in contents.items():
            clone = info.get("clone", False)
            if clone:
                timbres = None
                cur_timbre = None
            else:
                timbres = info.get("timbres", [])
                cur_timbre = info.get("cur_timbre", None)
            
            model_info[model_name] = {
                "full_name": info.get("full_name", ""),
                "clone": clone,
                "status": info.get("status", "unknown"),
                "license": info.get("license", "unknown"),
                "timbres": timbres,
                "cur_timbre": cur_timbre
            }
        
        return jsonify(model_info), 200

    except Exception as e:
        return jsonify(msg="Error reading TTS models", error=str(e)), 500


@avatar_bp.route("/avatar/delete", methods=["POST"])
@jwt_required()
def forward_delete_avatar():
    """Forward avatar deletion request to the avatar service."""
    current_user_email = get_jwt_identity()

    avatar_name = request.form.get("name")
    if not avatar_name:
        return jsonify(msg="Missing 'name' in form-data"), 400

    try:
        live_server_url = get_live_server_url()
        response = http_client.post(
            f"{live_server_url}/avatar/delete",
            data={"name": avatar_name},
            timeout=10.0
        )

        try:
            response_data = response.json()
        except ValueError:
            return jsonify(msg="Invalid JSON response", raw=response.text), 500

        if response_data.get("status") == "success":
            return jsonify(response_data), 200
        else:
            return jsonify(msg="Avatar deletion failed", detail=response_data), 400

    except httpx.TimeoutException:
        return jsonify(msg="Avatar service timeout"), 504
    except httpx.RequestError as e:
        return jsonify(msg="Error forwarding to avatar service", error=str(e)), 500
    except Exception as e:
        return jsonify(msg="Unexpected error", error=str(e)), 500


@avatar_bp.route("/avatar/start", methods=["POST"])
@jwt_required()
def forward_start_avatar():
    """Start avatar instance using Avatar Manager (supports concurrent users)."""
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email).first()

    avatar_name = request.form.get("avatar_name")
    if not avatar_name:
        return jsonify(msg="Missing 'avatar_name' in form-data"), 400

    session_manager = get_avatar_session_manager()
    
    # 为每个用户创建唯一的Avatar实例ID（避免多用户冲突）
    user_avatar_id = f"{avatar_name}_user_{user.id}"
    
    #  切换Avatar时，先断开用户的旧Avatar连接
    old_avatar_info = session_manager.user_avatar_map.get(str(user.id))  # 使用字符串key
    if old_avatar_info:
        old_avatar_name = old_avatar_info['avatar_id']  # 真实avatar名称
        old_port = old_avatar_info.get('port', 'unknown')
        
        # 如果用户切换到不同的Avatar，断开旧的连接
        if old_avatar_name != avatar_name:
            try:
                logger.info(f"Avatar Switch: User {user.id} changing from '{old_avatar_name}' (port {old_port}) to '{avatar_name}'")
                avatar_manager_url = get_avatar_manager_url()
                disconnect_response = http_client.post(
                    f"{avatar_manager_url}/avatar/disconnect",
                    json={"avatar_name": old_avatar_name},  # 使用真实avatar名称
                    headers={"Content-Type": "application/json"},
                    timeout=5.0
                )
                # ⭐ 立即清除session映射，避免重复disconnect
                session_manager.remove_user(user.id)
                logger.info(f"Disconnected: User {user.id} from avatar '{old_avatar_name}' (port {old_port})")
            except Exception as e:
                logger.warning(f"Failed to disconnect from old avatar {old_avatar_name}: {e}")
                # 即使失败也清除映射
                session_manager.remove_user(user.id)
        else:
            logger.info(f"Reconnecting: User {user.id} to same avatar '{avatar_name}' (port {old_port})")

    try:
        # 调用Avatar Manager启动用户专属的Avatar实例
        # instance_id用于管理，avatar_name是真实Avatar名称
        avatar_manager_url = get_avatar_manager_url()
        response = http_client.post(
            f"{avatar_manager_url}/avatar/start",
            json={
                "avatar_id": user_avatar_id,     # 实例ID（用于管理）：g_user_1
                "avatar_name": avatar_name       # 真实Avatar名称：g
            },
            headers={"Content-Type": "application/json"},
            timeout=60.0
        )

        try:
            response_data = response.json()
        except ValueError:
            return jsonify(msg="Invalid JSON response from Avatar Manager", raw=response.text), 500

        if response_data.get("status") == "success":
            avatar_info = response_data.get("data", {})
            port = avatar_info.get("port")
            
            # 保存用户的Avatar端口映射（包含实例ID用于后续停止）
            # set_user_avatar 现在会原子性地保存到Redis Hash
            session_manager.set_user_avatar(user.id, avatar_name, port, user_avatar_id)
            logger.info(f"Avatar Started: User {user.id} → Avatar '{avatar_name}' (instance: {user_avatar_id}) on port {port}")
            
            # 判断是否是新启动的实例（连接数=1表示新实例，>1表示复用）
            connections = avatar_info.get("connections", 1)
            is_new_instance = (connections == 1)
            
            # 返回Avatar实例信息
            return jsonify({
                "status": "success",
                "avatar_id": avatar_info.get("avatar_id"),
                "port": port,
                "webrtc_url": f"/api/webrtc/offer",  # 使用proxy路径，前端无需知道具体端口
                "gpu": avatar_info.get("gpu"),
                "connections": connections,
                "is_new_instance": is_new_instance,  # ⭐ 新增：是否是新启动的实例
                "message": f"Avatar {'started' if is_new_instance else 'reused'} successfully (port {port}, connections: {connections})"
            }), 200
        else:
            error_msg = response_data.get("message", "Avatar start failed")
            return jsonify(msg=error_msg, detail=response_data), 400

    except httpx.TimeoutException:
        return jsonify(msg="Avatar Manager timeout"), 504
    except httpx.RequestError as e:
        return jsonify(msg="Error connecting to Avatar Manager", error=str(e)), 500
    except Exception as e:
        return jsonify(msg="Unexpected error", error=str(e)), 500


@avatar_bp.route("/avatar/disconnect", methods=["POST"])
@jwt_required()
def disconnect_avatar():
    """Disconnect from avatar (reduce connection count)"""
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email).first()
    
    if not user:
        return jsonify(msg="User not found"), 404
    
    session_manager = get_avatar_session_manager()
    avatar_info = session_manager.user_avatar_map.get(user.id)
    
    if not avatar_info:
        # 用户没有活跃的avatar连接
        return jsonify(msg="No active avatar connection"), 200
    
    avatar_name = avatar_info.get('avatar_id')  # 真实avatar名称
    
    try:
        # 调用Avatar Manager的disconnect API（不强制关闭）
        avatar_manager_url = get_avatar_manager_url()
        response = http_client.post(
            f"{avatar_manager_url}/avatar/disconnect",
            json={"avatar_name": avatar_name},  # 使用真实avatar名称
            headers={"Content-Type": "application/json"},
            timeout=5.0
        )
        
        # ⭐ 重要：清除session manager中的用户映射
        session_manager.remove_user(user.id)
        logger.info(f"✓ User {user.id} disconnected from avatar {avatar_name} and cleared session")
        
        return jsonify({
            "status": "success",
            "message": f"Disconnected from avatar {avatar_name}"
        }), 200
        
    except Exception as e:
        logger.warning(f"Failed to disconnect user {user.id} from avatar {avatar_name}: {e}")
        # 即使Avatar Manager调用失败，也清除本地映射
        session_manager.remove_user(user.id)
        return jsonify({
            "status": "success",
            "message": "Disconnection noted"
        }), 200
