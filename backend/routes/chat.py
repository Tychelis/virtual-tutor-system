import os
import sys
from flask import Blueprint, request, jsonify, current_app, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from utils.token_utils import token_in_redis_required
from utils.refresh_token import refresh_token_and_redis
from utils.refresh_redis import refresh_redis_only
import requests
from models.user import User, db
from services.redis_client import redis_client
from services.avatar_session_manager import get_avatar_session_manager
from services.http_client import http_client
from models.chat import Session, Message
from datetime import datetime, timedelta
import json
import re
import logging

logger = logging.getLogger(__name__)

# 导入统一端口配置
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from scripts.ports_config import LLM_PORT, AVATAR_BASE_PORT, RAG_PORT, get_llm_url, get_rag_url

# Blueprint for chat-related routes
chat_bp = Blueprint("chat", __name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Allowed file extensions for uploads
ALLOWED_IMAGE = {"png", "jpg", "jpeg"}
ALLOWED_AUDIO = {"wav", "mp3", "m4a"}
ALLOWED_DOCS = {"pdf", "txt", "docx"}


def allowed_file(filename, allowed_exts):
    """Check if a file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_exts


@chat_bp.route("/chat", methods=["POST"])
@jwt_required()
@token_in_redis_required
@refresh_redis_only
def chat():
    """Send user message to LLM service, stream response to frontend, and store in DB."""
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()
    if not user:
        return jsonify(msg="User not found"), 404

    # Check if client accepts streaming
    accept_header = request.headers.get('Accept', '')
    is_streaming = 'text/event-stream' in accept_header
    
    # Retrieve RTC session ID from Redis (default to 1 if invalid)
    session_bytes = redis_client.get(f"sessionid:{user.email}")
    try:
        session_id_safe = int(session_bytes)
    except (TypeError, ValueError):
        session_id_safe = 1

    # Find or create chat session
    session_id = request.form.get("session_id")
    if session_id:
        session = Session.query.filter_by(id=session_id, user_id=user.id).first()
        if not session:
            return jsonify({"msg": "Session not found"}), 404
    else:
        cutoff = datetime.utcnow() - timedelta(minutes=30)
        session = (
            Session.query
            .filter_by(user_id=user.id)
            .filter(Session.updated_at >= cutoff)
            .order_by(Session.updated_at.desc())
            .first()
        )
        if not session:
            session = Session(user_id=user.id, title="New Chat")
            db.session.add(session)
            db.session.commit()

    # Get user's avatar port (使用统一配置的默认端口)
    session_manager = get_avatar_session_manager()
    avatar_port = session_manager.get_user_port(user.id)
    if avatar_port is None:
        avatar_port = AVATAR_BASE_PORT  # 使用统一配置的默认端口
        print(f" User {user.id} has no avatar mapping, using default port {avatar_port}")
    else:
        print(f" User {user.id} chat will forward to avatar port {avatar_port}")

    # Process text input
    text = request.form.get("message")
    if text:
        # 如果客户端支持流式输出，使用 SSE 返回
        if is_streaming:
            def generate():
                output_segments = []
                buffer = ""
                
                try:
                    llm_url = get_llm_url(use_optimized=True)
                    with requests.post(
                        url=f"{llm_url}/chat/stream",
                        json={"input": text, "session_id": session.id, "user_id": user.id},
                        stream=True,
                        timeout=60,
                    ) as ask_response:
                        ask_response.raise_for_status()

                        for line in ask_response.iter_lines(decode_unicode=True):
                            if line and line.startswith("data:"):
                                chunk_data = json.loads(line.replace("data: ", ""))
                                chunk = chunk_data.get("chunk", "")
                                buffer += chunk
                                
                                # 发送chunk到前端
                                if chunk:
                                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"

                                # Final chunk
                                if chunk_data.get("status") == "finished":
                                    if buffer.strip():
                                        forward_payload = {
                                            "sessionid": session_id_safe,
                                            "text": buffer,
                                            "type": "echo",
                                        }
                                        try:
                                            requests.post(f"http://localhost:{avatar_port}/human", json=forward_payload, timeout=10)
                                        except Exception as e:
                                            print(f"[WARN] Final forward failed: {e}")
                                        output_segments.append(buffer)
                                    yield f"data: {json.dumps({'status': 'finished'})}\n\n"
                                    break

                                # Forward intermediate output to video model
                                if buffer.endswith((".", "!", "?", "。")) or len(buffer.split()) >= 15:
                                    forward_payload = {
                                        "sessionid": session_id_safe,
                                        "text": buffer,
                                        "type": "echo",
                                    }
                                    try:
                                        requests.post(f"http://localhost:{avatar_port}/human", json=forward_payload, timeout=10)
                                    except Exception as e:
                                        print(f"[WARN] Forward to video model failed: {e}")
                                    output_segments.append(buffer)
                                    buffer = ""

                    full_output = " ".join(output_segments)
                    
                    # Store messages in DB
                    db.session.add_all([
                        Message(session_id=session.id, role="user", content=text),
                        Message(session_id=session.id, role="assistant", content=full_output)
                    ])
                    session.message_count += 2
                    session.updated_at = datetime.utcnow()
                    db.session.commit()

                except Exception as e:
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"

            return Response(generate(), mimetype='text/event-stream')
        
        # 非流式输出（原有逻辑）
        response_data = {}
        response_data["rtc_session_id"] = session_id_safe
        response_data["text_input"] = text
        output_segments = []
        response_data["text_input"] = text
        output_segments = []

        # Stream LLM response
        try:
            llm_url = get_llm_url(use_optimized=True)
            with requests.post(
                url=f"{llm_url}/chat/stream",
                json={"input": text, "session_id": session.id, "user_id": user.id},
                stream=True,
                timeout=60,
            ) as ask_response:

                ask_response.raise_for_status()

                buffer = ""
                for line in ask_response.iter_lines(decode_unicode=True):
                    if line and line.startswith("data:"):
                        chunk_data = json.loads(line.replace("data: ", ""))
                        chunk = chunk_data.get("chunk", "")
                        buffer += chunk

                        # Final chunk
                        if chunk_data.get("status") == "finished":
                            if buffer.strip():
                                forward_payload = {
                                    "sessionid": session_id_safe,
                                    "text": buffer,
                                    "type": "echo",
                                }
                                try:
                                    requests.post(f"http://localhost:{avatar_port}/human", json=forward_payload, timeout=10)
                                except Exception as e:
                                    print(f"[WARN] Final forward failed: {e}")
                                output_segments.append(buffer)
                            break

                        # Forward intermediate output to video model
                        if buffer.endswith((".", "!", "?", "。")) or len(buffer.split()) >= 15:
                            forward_payload = {
                                "sessionid": session_id_safe,
                                "text": buffer,
                                "type": "echo",
                            }
                            try:
                                requests.post(f"http://localhost:{avatar_port}/human", json=forward_payload, timeout=10)
                            except Exception as e:
                                print(f"[WARN] Forward to video model failed: {e}")
                            output_segments.append(buffer)
                            buffer = ""

            response_data["text_output"] = " ".join(output_segments)

        except Exception as e:
            response_data["text_output"] = " ".join(output_segments) + f" [Error: {e}]"

        # Store user and assistant messages in DB
        db.session.add_all([
            Message(session_id=session.id, role="user", content=text),
            Message(session_id=session.id, role="assistant", content=response_data["text_output"])
        ])
        session.message_count += 2
        session.updated_at = datetime.utcnow()
        db.session.commit()

    return jsonify(response_data), 200


@chat_bp.route("/chat/upload", methods=["POST"])
@jwt_required()
@token_in_redis_required
@refresh_redis_only
def upload_file():
    """Handle file uploads, save them, and create a message record."""
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()
    if not user:
        return jsonify(msg="User not found"), 404

    if 'file' not in request.files:
        return jsonify(msg="No file part in the request"), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify(msg="No file selected for uploading"), 400

    # Get or create session
    session_id = request.form.get("session_id")
    if session_id:
        try:
            session = Session.query.filter_by(id=int(session_id), user_id=user.id).first()
            if not session:
                return jsonify({"msg": "Session not found"}), 404
        except ValueError:
            return jsonify({"msg": "Invalid session_id"}), 400
    else:
        session = Session(user_id=user.id, title=f"File: {file.filename[:30]}")
        db.session.add(session)
        db.session.commit()

    # Check file type and save
    filename = secure_filename(file.filename)
    if not filename:
        return jsonify(msg="Invalid filename"), 400
    
    file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    file_type = "other"

    if file_ext in ALLOWED_IMAGE:
        file_type = "image"
    elif file_ext in ALLOWED_AUDIO:
        file_type = "audio"
    elif file_ext in ALLOWED_DOCS:
        file_type = "document"
    else:
        return jsonify(msg=f"File type '.{file_ext}' not allowed. Allowed types: images ({', '.join(ALLOWED_IMAGE)}), audio ({', '.join(ALLOWED_AUDIO)}), documents ({', '.join(ALLOWED_DOCS)})"), 400

    # Create a unique path for the file
    user_upload_dir = os.path.join(UPLOAD_FOLDER, str(user.id))
    os.makedirs(user_upload_dir, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(user_upload_dir, f"{timestamp}_{filename}")
    
    try:
        file.save(file_path)
        logger.info(f"File saved: {file_path} for user {user.email}")
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        return jsonify(msg="Failed to save file"), 500

    # Create a message record for the file
    new_message = Message(
        session_id=session.id,
        role="user",
        content=f"Uploaded {file_type}: {filename}",
        file_type=file_type,
        file_path=file_path
    )
    db.session.add(new_message)
    session.message_count += 1
    session.updated_at = datetime.utcnow()
    db.session.commit()

    # Send document to RAG service for indexing (only for documents, not images/audio)
    rag_ingestion_success = False
    rag_error_msg = None
    if file_type == "document":
        try:
            rag_url = get_rag_url()
            with open(file_path, 'rb') as f:
                rag_response = requests.post(
                    f"{rag_url}/user/upload",
                    files={'file': (filename, f, 'application/octet-stream')},
                    data={'user_id': str(user.id)},
                    timeout=30
                )
            
            if rag_response.status_code == 200:
                rag_data = rag_response.json()
                logger.info(f"Document indexed in RAG: {rag_data}")
                rag_ingestion_success = True
            else:
                rag_error_msg = f"RAG indexing failed: {rag_response.status_code}"
                logger.warning(f"RAG indexing failed for {filename}: {rag_response.text}")
        except Exception as e:
            rag_error_msg = f"RAG service error: {str(e)}"
            logger.error(f"Error sending document to RAG: {e}")

    response_data = {
        "msg": "File uploaded successfully",
        "session_id": session.id,
        "message_id": new_message.id,
        "file_path": file_path,
        "file_type": file_type,
        "filename": filename
    }
    
    if file_type == "document":
        response_data["rag_indexed"] = rag_ingestion_success
        if rag_error_msg:
            response_data["rag_error"] = rag_error_msg
    
    return jsonify(response_data), 200


@chat_bp.route("/user_files", methods=["GET"])
@jwt_required()
@token_in_redis_required
@refresh_redis_only
def get_user_files():
    """Get all uploaded files for the current user."""
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()
    if not user:
        return jsonify(msg="User not found"), 404
    
    try:
        # Query all messages with files for this user
        user_sessions = Session.query.filter_by(user_id=user.id).all()
        session_ids = [s.id for s in user_sessions]
        
        file_messages = Message.query.filter(
            Message.session_id.in_(session_ids),
            Message.file_path.isnot(None)
        ).order_by(Message.created_at.desc()).all()
        
        files = []
        for msg in file_messages:
            file_info = {
                "id": msg.id,
                "filename": os.path.basename(msg.file_path) if msg.file_path else "",
                "file_type": msg.file_type,
                "file_path": msg.file_path,
                "content": msg.content,
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
                "session_id": msg.session_id,
                "size": os.path.getsize(msg.file_path) if msg.file_path and os.path.exists(msg.file_path) else 0
            }
            files.append(file_info)
        
        return jsonify({
            "msg": "Files retrieved successfully",
            "files": files,
            "total": len(files)
        }), 200
    except Exception as e:
        logger.error(f"Error retrieving user files: {e}")
        return jsonify(msg="Failed to retrieve files", error=str(e)), 500


@chat_bp.route("/chat/stream", methods=["POST"])
@jwt_required()
def chat_stream():
    """Stream chat responses (SSE format) for real-time display."""
    from flask import stream_with_context
    
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()
    
    # Get form data
    message = request.form.get("message", "").strip()
    session_id = request.form.get("session_id")
    
    if not message:
        return jsonify(msg="Message is required"), 400
    
    # Get or create session
    if session_id:
        try:
            session_id = int(session_id)
            session = Session.query.filter_by(id=session_id, user_id=user.id).first()
            if not session:
                return jsonify(msg="Session not found"), 404
        except ValueError:
            return jsonify(msg="Invalid session ID"), 400
    else:
        # Create new session
        session = Session(user_id=user.id, title=message[:50])
        db.session.add(session)
        db.session.commit()
        session_id = session.id
    
    # Get user's avatar port for TTS forwarding
    session_manager = get_avatar_session_manager()
    avatar_port = session_manager.get_user_port(user.id)
    if avatar_port is None:
        avatar_port = AVATAR_BASE_PORT
        logger.warning(f"⚠️ User {user.id} has no avatar mapping, using default port {avatar_port}. Please connect to avatar first!")
    else:
        logger.info(f"🎤 User {user.id} will forward TTS to avatar port {avatar_port}")
    
    # Get WebRTC session ID for TTS (从正确的 Redis 键读取)
    try:
        session_bytes = redis_client.get(f"sessionid:{user.email}")
        rtc_session_id = int(session_bytes) if session_bytes else 1
        logger.info(f"📡 WebRTC session ID for user {user.email}: {rtc_session_id}")
    except (TypeError, ValueError) as e:
        rtc_session_id = 1
        logger.warning(f"⚠️ Failed to get WebRTC session ID for {user.email}: {e}, using default 1")
    
    def generate():
        """Generator function for SSE streaming."""
        collected_text = []
        buffer = ""  # Buffer for TTS forwarding
        
        try:
            # Retrieve relevant context from RAG before calling LLM
            # Only use RAG when user explicitly asks about documents or uploaded content
            rag_context = ""
            
            # Keywords that indicate user wants to reference documents
            doc_keywords = [
                # File types and formats
                'document', 'file', 'uploaded', 'pdf', 'doc', 'docx', 'txt', '.txt', '.pdf', '.docx',
                '文档', '文件', '上传', '资料', '材料',
                
                # Content references
                'content', 'paper', 'article', 'report', 'summary', 'summarize',
                'what did i upload', 'in my document', 'from the file',
                'according to', 'based on', 'in the document',
                '内容', '摘要', '总结', '概括',
                '根据', '文档中', '文件中', '资料中', '里提到', '提到了什么',
                
                # Pronouns referring to previously uploaded files
                'it', 'this', 'that', 'them', 'the file', 'the document',
                '它', '这个', '那个', '这', '那',
                
                # Questions about uploaded content
                'repo', 'requirement', 'requirements', 'specification', 'spec',
                '需求', '要求', '规格', '说明'
            ]
            
            message_lower = message.lower()
            should_use_rag = any(keyword in message_lower for keyword in doc_keywords)
            
            # Also use RAG for longer, complex questions (likely academic queries)
            if not should_use_rag and len(message.split()) > 12:
                should_use_rag = True
            
            if should_use_rag:
                try:
                    rag_url = get_rag_url()
                    rag_response = requests.post(
                        f"{rag_url}/retriever",
                        json={
                            "question": message,
                            "user_id": str(user.id),
                            "personal_k": 3,  # Top 3 from personal KB
                            "public_k": 2,    # Top 2 from public KB
                            "final_k": 5      # Final top 5 after reranking
                        },
                        timeout=10
                    )
                    
                    if rag_response.status_code == 200:
                        rag_data = rag_response.json()
                        hits = rag_data.get('hits', [])
                        if hits:
                            rag_context = "\n\n=== CONTEXT FROM USER'S UPLOADED DOCUMENTS ===\n"
                            rag_context += "The following content is extracted from documents the user has uploaded:\n\n"
                            for i, hit in enumerate(hits[:3], 1):  # Use top 3
                                source = hit.get('source', 'Unknown')
                                text = hit.get('text', '')
                                rag_context += f"[Document: {source}]\n{text}\n\n"
                            rag_context += "=== END OF DOCUMENT CONTEXT ===\n"
                            rag_context += "Please answer the user's question based on the above document content."
                            logger.info(f"Retrieved {len(hits)} RAG results for user {user.id}")
                        else:
                            logger.info(f"No RAG results found for query: {message}")
                    else:
                        logger.warning(f"RAG retrieval failed: {rag_response.status_code}")
                except Exception as e:
                    logger.warning(f"RAG retrieval error (non-blocking): {e}")
            else:
                logger.info(f"Skipping RAG for short message: {message}")
            
            # Prepare enriched message with RAG context
            enriched_message = message
            if rag_context:
                enriched_message = f"{message}{rag_context}"
            
            # Call LLM streaming API
            llm_url = get_llm_url(use_optimized=True)
            
            # Use requests library for streaming
            llm_response = requests.post(
                f"{llm_url}/chat/stream",
                json={
                    "input": enriched_message,
                    "session_id": session_id,
                    "user_id": user.id
                },
                stream=True,
                timeout=120.0
            )
            
            # Forward each chunk from LLM to frontend
            for line in llm_response.iter_lines():
                if line:
                    line_str = line.decode('utf-8') if isinstance(line, bytes) else line
                    
                    # Forward SSE data line
                    if line_str.startswith("data:"):
                        yield f"{line_str}\n\n"
                        
                        # Parse and collect chunk text
                        try:
                            data_str = line_str[5:].strip()  # Remove "data:" prefix
                            chunk_data = json.loads(data_str)
                            
                            if chunk_data.get("status") == "streaming":
                                chunk_text = chunk_data.get("chunk", "")
                                if chunk_text:
                                    collected_text.append(chunk_text)
                                    buffer += chunk_text
                                    
                                    # 流式转发策略：更频繁地发送小片段以获得更低延迟
                                    # 当满足以下任一条件时就转发：
                                    # 1. 完整句子结束（标点符号）
                                    # 2. 累积了 5-8 个词（更小的批次，更快的响应）
                                    # 3. 遇到逗号等停顿符号
                                    should_forward = False
                                    if buffer.endswith((".", "!", "?", "。", "！", "？")):
                                        should_forward = True  # 句子结束
                                    elif buffer.endswith((",", ";", "，", "；", ":", "：")):
                                        should_forward = True  # 停顿位置
                                    elif len(buffer.split()) >= 5:
                                        should_forward = True  # 累积足够词汇（减少批次大小以降低延迟）
                                    
                                    if should_forward and buffer.strip():
                                        tts_payload = {
                                            "sessionid": rtc_session_id,
                                            "text": buffer.strip(),
                                            "type": "echo"
                                        }
                                        try:
                                            print(f"🔊 Forwarding to TTS: port={avatar_port}, sessionid={rtc_session_id}, text={buffer[:50]}...")
                                            tts_response = requests.post(
                                                f"http://localhost:{avatar_port}/human",
                                                json=tts_payload,
                                                timeout=3
                                            )
                                            print(f"✅ TTS Response: {tts_response.status_code}")
                                            logger.info(f"✅ Forwarded to TTS port {avatar_port} ({len(buffer.split())} words): {buffer[:50]}... Response: {tts_response.status_code}")
                                        except Exception as tts_error:
                                            print(f"❌ TTS forward failed: {tts_error}")
                                            logger.warning(f"TTS forward failed: {tts_error}")
                                        buffer = ""  # Clear buffer after forwarding
                                    
                        except json.JSONDecodeError:
                            pass
            
            # After streaming completes, save to database
            full_response = "".join(collected_text)
            
            # Forward any remaining text to TTS
            if buffer.strip():
                tts_payload = {
                    "sessionid": rtc_session_id,
                    "text": buffer,
                    "type": "echo"
                }
                try:
                    print(f"🔊 Forwarding FINAL to TTS: port={avatar_port}, text={buffer[:50]}...")
                    final_response = requests.post(
                        f"http://localhost:{avatar_port}/human",
                        json=tts_payload,
                        timeout=5
                    )
                    print(f"✅ FINAL TTS Response: {final_response.status_code}")
                    logger.info(f"✅ Forwarded final text to TTS port {avatar_port}: {buffer[:50]}... Response: {final_response.status_code}")
                except Exception as tts_error:
                    print(f"❌ FINAL TTS forward failed: {tts_error}")
                    logger.warning(f"Final TTS forward failed: {tts_error}")
            
            # Save messages to database
            db.session.add_all([
                Message(session_id=session.id, role="user", content=message, created_at=datetime.utcnow()),
                Message(session_id=session.id, role="assistant", content=full_response, created_at=datetime.utcnow())
            ])
            session.message_count += 2
            session.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Send final complete event with session info
            yield f'data: {json.dumps({"status": "complete", "session_id": session_id, "text": full_response})}\n\n'
            
        except Exception as e:
            import traceback
            logger.error(f"Error in chat stream: {e}")
            logger.error(traceback.format_exc())
            error_msg = str(e)
            yield f'data: {json.dumps({"status": "error", "error": error_msg})}\n\n'
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )


@chat_bp.route("/sessionid", methods=["POST"])
@jwt_required()
def receive_session_id():
    """Save WebRTC session ID in Redis for current user."""
    data = request.get_json()
    session_id = data.get("sessionid")
    if not session_id:
        return "No session ID provided", 400

    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()
    if not user:
        return "User not found", 404

    ttl = current_app.config["REDIS_TOKEN_TTL_SECONDS"]
    redis_client.setex(f"sessionid:{user.email}", ttl, session_id)
    return '', 200


@chat_bp.route("/chat/new", methods=["POST"])
@jwt_required()
def create_session():
    """Create a new chat session."""
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()

    data = request.get_json()
    title = data.get("title", "Untitled")

    new_session = Session(user_id=user.id, title=title)
    db.session.add(new_session)
    db.session.commit()

    return jsonify(session_id=new_session.id), 201


@chat_bp.route("/chat/history", methods=["GET"])
@jwt_required()
def list_sessions():
    """List all chat sessions for the current user."""
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()
    sessions = Session.query.filter_by(user_id=user.id).order_by(Session.updated_at.desc()).all()
    return jsonify([
        {
            "id": s.id,
            "title": s.title,
            "created_at": s.created_at.isoformat(),
            "updated_at": s.updated_at.isoformat(),
            "message_count": s.message_count,
            "is_favorite": s.is_favorite
        } for s in sessions
    ]), 200


@chat_bp.route("/message/list", methods=["GET"])
@jwt_required()
def get_messages():
    """Retrieve messages from a specific chat session."""
    user_email = get_jwt_identity()
    session_id = request.args.get("session_id")
    user = User.query.filter_by(email=user_email).first()

    session = Session.query.filter_by(id=session_id, user_id=user.id).first()
    if not session:
        return jsonify({"msg": "Session not found or not authorized."}), 404

    messages = Message.query.filter_by(session_id=session.id).order_by(Message.created_at).all()
    return jsonify([
        {
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat(),
            "file_type": m.file_type,
            "file_path": m.file_path
        } for m in messages
    ]), 200


@chat_bp.route("/chat/<int:chat_id>/favorite", methods=["POST"])
@jwt_required()
def set_session_favorite(chat_id):
    """Set a chat session as favorite (only one favorite per user)."""
    data = request.get_json()
    is_favorite = data.get("is_favorite", True)

    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()
    if not user:
        return jsonify(msg="User not found"), 404

    session = Session.query.filter_by(id=chat_id, user_id=user.id).first()
    if not session:
        return jsonify(msg="Session not found"), 404

    if is_favorite:
        # Unset favorite for all other sessions
        Session.query.filter(
            Session.user_id == user.id,
            Session.id != chat_id
        ).update({Session.is_favorite: False}, synchronize_session=False)

    session.is_favorite = bool(is_favorite)
    db.session.commit()

    return jsonify({
        "msg": "Favorite status updated",
        "session_id": session.id,
        "is_favorite": session.is_favorite
    }), 200


@chat_bp.route("/chat/<int:chat_id>", methods=["DELETE"])
@jwt_required()
def delete_session(chat_id):
    """Delete a chat session."""
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    session = Session.query.filter_by(id=chat_id, user_id=user.id).first()
    if not session:
        return jsonify({"msg": "Session not found or not authorized"}), 404

    db.session.delete(session)
    db.session.commit()

    return jsonify({"msg": f"Session {chat_id} deleted"}), 200


@chat_bp.route("/llm/activate", methods=["POST"])
@jwt_required()
def forward_activate_model():
    """Forward model activation request to the LLM service."""
    current_user_email = get_jwt_identity()
    data = request.get_json()
    if not data or "model" not in data:
        return jsonify(msg="Missing 'model' in JSON payload"), 400

    try:
        llm_url = get_llm_url(use_optimized=True)
        response = requests.post(
            f"{llm_url}/activate_model",  # 使用优化版LLM服务
            json=data,
            timeout=15
        )

        try:
            response_data = response.json()
        except ValueError:
            return jsonify(msg="Invalid JSON response from model service", raw=response.text), 500

        if response.status_code == 200:
            return jsonify(response_data), 200
        else:
            return jsonify(msg="Model activation failed", detail=response_data), response.status_code

    except requests.RequestException as e:
        return jsonify(msg="Failed to connect to model service", error=str(e)), 500
