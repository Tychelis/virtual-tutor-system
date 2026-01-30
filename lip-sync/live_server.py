from fastapi import FastAPI, Query, HTTPException, File, UploadFile, Form
from fastapi.responses import Response
import subprocess
import os
import json
import time
import uvicorn
import tempfile
import shutil
import threading

# Import create_avatar related functions
from create_avatar import create_avatar

# Global configuration variable
CONFIG = {}

def load_config():
    """Load configuration file"""
    global CONFIG
    config_path = os.path.join(os.path.dirname(__file__), "lip-sync.json")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            CONFIG = json.load(f)
        print("Configuration file loaded successfully")
        return True
    except FileNotFoundError:
        print(f"Configuration file not found: {config_path}")
        return False
    except json.JSONDecodeError as e:
        print(f"Configuration file format error: {e}")
        return False
    except Exception as e:
        print(f"Error occurred while loading configuration file: {e}")
        return False

def get_config_value(key_path, default=None):
    """Get configuration value, supports nested keys"""
    keys = key_path.split('.')
    value = CONFIG
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    
    return value

app = FastAPI()

@app.post("/switch_avatar")
def switch_avatar(
    avatar_id: str = Query(..., description="Avatar ID, e.g., avator_1"),
    ref_file: str = Query(..., description="Reference audio file path")
):
    """Execute new script command using conda environment"""
    # Get parameters from configuration file
    transport = "webrtc"
    model = "musetalk"
    max_session = get_config_value("app_config.max_session", 8)
    listenport = get_config_value("servers.listenport", 8205)
    tts = "cosyvoice"
    tts_server = get_config_value("servers.tts_server", "http://127.0.0.1:8604")
    ref_text = get_config_value("default_texts.ref_text", "hello this is tutorNet speaking, what do you need? do you want a cup of coffee?")

    # Check if avatar_id exists
    working_directory = get_config_value("paths.working_directory", "/workspace/share/yuntao/LiveTalking")
    LIVEAVADIR = os.path.join(working_directory, "data", "avatars")
    avatar_folder_path = os.path.join(LIVEAVADIR, avatar_id)
    
    print(f"Checking Avatar path: {avatar_folder_path}")
    if not os.path.exists(avatar_folder_path):
        print(f"Avatar '{avatar_id}' does not exist")
        raise HTTPException(
            status_code=400,
            detail=f"Avatar '{avatar_id}' does not exist, please confirm avatar_id is correct"
        )
    
    if not os.path.isdir(avatar_folder_path):
        print(f"Avatar path '{avatar_folder_path}' is not a valid directory")
        raise HTTPException(
            status_code=400,
            detail=f"Avatar '{avatar_id}' path is not a valid directory"
        )
    
    # Check if ref_file exists
    # Support both relative and absolute paths
    if not os.path.isabs(ref_file):
        # Relative path, relative to working directory
        ref_file_path = os.path.join(working_directory, ref_file)
    else:
        # Absolute path
        ref_file_path = ref_file
    
    print(f"Checking reference audio file path: {ref_file_path}")
    if not os.path.exists(ref_file_path):
        print(f"Reference audio file '{ref_file_path}' does not exist")
        raise HTTPException(
            status_code=400,
            detail=f"Reference audio file does not exist: {ref_file_path}"
        )
    
    # Check file format
    audio_extensions = ('.wav', '.mp3', '.m4a', '.flac', '.aac', '.ogg')
    if not ref_file_path.lower().endswith(audio_extensions):
        print(f"Reference audio file format not supported: {ref_file_path}")
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format, please use one of the following formats: {', '.join(audio_extensions)}"
        )
    
    print(f"Avatar and reference audio file checks passed")

    # Build command
    app_command = (
        f"python3 app.py --transport {transport} --model {model} --avatar_id {avatar_id} "
        f"--max_session {max_session} --listenport {listenport} --tts {tts} "
        f"--TTS_SERVER {tts_server} --REF_FILE {ref_file} --REF_TEXT '{ref_text}'"
    )

    # Get paths from configuration file
    conda_env = get_config_value("paths.conda_env", "/workspace/conda_envs/nerfstream")
    conda_init = get_config_value("paths.conda_init", "/home/xinghua/workspace/share/conda/etc/profile.d/conda.sh")
    working_directory = get_config_value("paths.working_directory", "/workspace/share/yuntao/LiveTalking")
    
    print(f"Starting to switch to avatar: {avatar_id}")
    print(f"Using reference file: {ref_file}")
    
    # First kill any process on port 8205
    print(f"Checking and terminating processes on port {listenport}...")
    try:
        # Find processes using the port
        result = subprocess.run(
            ["lsof", "-t", "-i", f":{listenport}"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.stdout.strip():
            # Process found using the port, get the process ID
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    print(f"Terminating process PID: {pid}")
                    subprocess.run(["kill", "-9", pid], check=False)
            print(f"Terminated all processes on port {listenport}")
        else:
            print(f"Port {listenport} is not in use")
            
    except Exception as e:
        print(f"Error checking/terminating port processes: {e}")
        # Continue execution even if kill process fails
    
    # Wait for a while to ensure the port is released
    time.sleep(2)
    
    try:
        # Build command using specified conda environment
        command = [
            "bash", "-c",
            f"source {conda_init} && conda activate {conda_env} && cd {working_directory} && {app_command} | tee log.txt"
        ]
        
        # Execute using subprocess.Popen, capture output
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Target string (to detect successful service startup)
        target_string = f"start http server"
        success_detected = False
        
        # Continuously monitor output
        while True:
            # Check if process is still running
            if process.poll() is not None:
                # Process has ended, read remaining output
                remaining_output = process.stdout.read()
                if remaining_output:
                    print(remaining_output.rstrip())
                    # Check if target string is in remaining output
                    if target_string in remaining_output:
                        success_detected = True
                break
            
            # Read one line of output
            line = process.stdout.readline()
            if line:
                print(line.rstrip())
                # Check if line contains target string
                if target_string in line:
                    success_detected = True
                    print("Detected service startup success signal")
                    
                    # Start background thread to continue monitoring output
                    monitor_thread = threading.Thread(
                        target=monitor_process_output, 
                        args=(process, avatar_id, listenport),
                        daemon=True  # Set as daemon thread, will end automatically when main program exits
                    )
                    monitor_thread.start()
                    print(f"Started background monitoring thread, continuing to monitor Avatar {avatar_id}'s output")
                    
                    break  # Exit detection loop, return success response
        
        # Return based on detection results
        if success_detected:
            print("Service started successfully")
            return {
                "status": "success",
                "message": f"Successfully switched to avatar {avatar_id}, service started on port {listenport}"
            }
        else:
            # Process stopped on its own and success signal not detected
            return_code = process.returncode if process.returncode is not None else "unknown"
            print(f"Script unexpectedly stopped, return code: {return_code}")
            return {
                "status": "error",
                "message": f"Script execution failed, process unexpectedly stopped, return code: {return_code}"
            }
            
    except Exception as e:
        print(f"Error occurred while executing script: {e}")
        return {
            "status": "error",
            "message": f"Error occurred during execution: {str(e)}"
        }

def monitor_process_output(process, avatar_id, listenport):
    """Continuously monitor subprocess output in a background thread"""
    try:
        while True:
            if process.poll() is not None:
                # Process ended
                final_output = process.stdout.read()
                if final_output:
                    print(final_output.rstrip())
                print(f"Avatar {avatar_id} subprocess has ended (PID: {process.pid})")
                break
            
            line = process.stdout.readline()
            if line:
                print(f"[Avatar {avatar_id}] {line.rstrip()}")
            else:
                time.sleep(0.1)
                
    except Exception as e:
        print(f"Error occurred while monitoring Avatar {avatar_id} output: {e}")

@app.post("/create_avatar")
def api_create_avatar_from_path(
    avatar_name: str = Query(..., description="Avatar name, e.g., avatar_1"),
    video_path: str = Query(..., description="Video file path"),
    burr: bool = Query(False, description="Whether to apply blur processing")
):
    """
    Create avatar from a video file at specified path
    
    Args:
        avatar_name: avatar name
        video_path: complete path to video file
        burr: whether to apply blur processing
    
    Returns:
        Returns image path on success, error message on failure
    """
    try:
        print(f"Starting to create avatar: {avatar_name}")
        print(f"Video file path: {video_path}")
        print(f"Blur processing: {'Enabled' if burr else 'Disabled'}")
        
        # Check if file exists
        if not os.path.exists(video_path):
            raise HTTPException(
                status_code=400,
                detail=f"Video file does not exist: {video_path}"
            )
        
        # Check file format
        if not video_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            raise HTTPException(
                status_code=400,
                detail="Unsupported video format, please use .mp4, .avi, .mov or .mkv files"
            )
        
        # Call create_avatar function
        result = create_avatar(video_path, avatar_name, burr=burr)
        
        if result:
            print(f"Avatar created successfully: {avatar_name}")
            print(f"Image path: {result}")
            return {
                "status": "success",
                "message": "Avatar created successfully",
                "image_path": result
            }
        else:
            print(f"Avatar creation failed: {avatar_name}")
            return {
                "status": "error",
                "message": f"Failed to create avatar {avatar_name}, please check input file and parameters"
            }
            
    except HTTPException:
        # Re-raise HTTPException, let FastAPI handle it
        raise
    except Exception as e:
        print(f"Error occurred during avatar creation: {e}")
        return {
            "status": "error",
            "message": f"Error occurred during avatar creation: {str(e)}"
        }
    


@app.delete("/delete_avatar")
def delete_avatar(
    avatar_name: str = Query(..., description="Name of the Avatar to delete, e.g., avatar_1")
):
    """
    Delete specified avatar and all related files
    
    Args:
        avatar_name: name of avatar to delete
    
    Returns:
        Deletion result information
    """
    try:
        print(f"Starting to delete avatar: {avatar_name}")
        
        # Get working directory
        working_directory = get_config_value("paths.working_directory", "/workspace/share/yuntao/LiveTalking")
        LIVEAVADIR = os.path.join(working_directory, "data", "avatars")
        
        # Build avatar folder path
        avatar_folder_path = os.path.join(LIVEAVADIR, avatar_name)
        
        print(f"Avatar folder path: {avatar_folder_path}")
        
        # Check if avatar folder exists
        if not os.path.exists(avatar_folder_path):
            raise HTTPException(
                status_code=404,
                detail=f"Avatar '{avatar_name}' does not exist, cannot delete"
            )
        
        # Check if it's a directory
        if not os.path.isdir(avatar_folder_path):
            raise HTTPException(
                status_code=400,
                detail=f"'{avatar_name}' is not a valid avatar folder"
            )
        
        # Delete avatar folder and all its contents
        shutil.rmtree(avatar_folder_path)
        
        print(f"Successfully deleted avatar folder: {avatar_folder_path}")
        
        return {
            "status": "success",
            "message": f"Avatar '{avatar_name}' has been successfully deleted"
        }
        
    except PermissionError as e:
        print(f"Permission error while deleting avatar: {e}")
        return {
            "status": "error",
            "message": f"Failed to delete avatar '{avatar_name}': Insufficient permissions"
        }
    except OSError as e:
        print(f"System error while deleting avatar: {e}")
        return {
            "status": "error",
            "message": f"Failed to delete avatar '{avatar_name}': System error"
        }
    except Exception as e:
        print(f"Error occurred during avatar deletion: {e}")
        return {
            "status": "error",
            "message": f"Error occurred during avatar deletion: {str(e)}"
        }

@app.get("/avatar/get_avatars")
def get_avatars():
    """List all existing avatars with their configuration from working directory"""
    working_directory = get_config_value("paths.working_directory", "/workspace/share/yuntao/LiveTalking")
    base = os.path.join(working_directory, "data", "avatars")

    if not os.path.isdir(base):
        return {"status": "success", "avatars": {}}

    avatar_dict = {}
    for name in os.listdir(base):
        avatar_path = os.path.join(base, name)
        if os.path.isdir(avatar_path):
            # 读取avatar配置文件
            config_path = os.path.join(avatar_path, "config.json")
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    avatar_dict[name] = {
                        "tts_model": config.get("tts_model", "edgeTTS"),
                        "timbre": config.get("timbre", "Default"),
                        "avatar_model": config.get("avatar_model", "musetalk"),
                        "description": config.get("description", ""),
                        "support_clone": config.get("support_clone", False),
                        "avatar_blur": config.get("avatar_blur", False),
                        "created_at": config.get("created_at", None),
                        "status": "active"
                    }
                except Exception as e:
                    print(f"[WARN] Failed to read config for avatar {name}: {e}")
                    # 如果读取配置失败，使用默认值
                    avatar_dict[name] = {
                        "tts_model": "edgeTTS",
                        "timbre": "Default",
                        "avatar_model": "musetalk",
                        "description": f"Avatar: {name}",
                        "support_clone": False,
                        "avatar_blur": False,
                        "created_at": None,
                        "status": "active"
                    }
            else:
                # 如果没有配置文件，使用默认值
                avatar_dict[name] = {
                    "tts_model": "edgeTTS",
                    "timbre": "Default",
                    "avatar_model": "musetalk",
                    "description": f"Avatar: {name}",
                    "support_clone": False,
                    "avatar_blur": False,
                    "created_at": None,
                    "status": "active"
                }
    
    return {"status": "success", "avatars": avatar_dict}

@app.post("/avatar/preview")
def avatar_preview(avatar_name: str = Form(...)):
    """Avatar preview endpoint - returns avatar preview image"""
    from fastapi.responses import FileResponse
    
    working_directory = get_config_value("paths.working_directory", "/workspace/share/yuntao/LiveTalking")
    avatar_path = os.path.join(working_directory, "data", "avatars", avatar_name)
    
    # 查找预览图片
    img_path = os.path.join(avatar_path, "full_imgs", "00000000.png")
    
    if os.path.exists(img_path):
        return FileResponse(img_path, media_type="image/png")
    else:
        raise HTTPException(status_code=404, detail=f"Avatar preview image not found for {avatar_name}")

@app.post("/avatar/add")
async def avatar_add(
    name: str = Form(...),
    prompt_face: UploadFile = File(...),
    prompt_voice: UploadFile = File(None),
    avatar_blur: str = Form("false"),
    support_clone: str = Form("false"),
    timbre: str = Form(""),
    tts_model: str = Form(""),
    avatar_model: str = Form(""),
    description: str = Form("")
):
    """Avatar creation endpoint - handles file upload"""
    import tempfile
    from datetime import datetime
    
    try:
        # 临时保存视频文件
        video_suffix = os.path.splitext(prompt_face.filename)[1] or ".mp4"
        with tempfile.NamedTemporaryFile(delete=False, suffix=video_suffix) as tmp_vid:
            video_content = await prompt_face.read()
            if len(video_content) == 0:
                raise HTTPException(status_code=400, detail="Empty video file uploaded")
            tmp_vid.write(video_content)
            video_path = tmp_vid.name
        
        # 检查文件大小
        file_size = os.path.getsize(video_path)
        print(f"Received video file: {prompt_face.filename}, size: {file_size} bytes, saved to {video_path}")
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="Empty video file")

        # 校验格式
        if not video_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            raise HTTPException(status_code=400, detail="Unsupported video format.")

        # 调用 create_avatar 函数
        print(f"Starting avatar creation for: {name}")
        burr = (avatar_blur.lower() == "true")
        result = create_avatar(video_path, name, burr=burr)

        if result:
            print(f"Avatar created successfully: {result}")
            
            # 使用后台任务保存配置信息，避免阻塞和崩溃
            def save_avatar_config():
                try:
                    avatar_dir = os.path.join(os.path.dirname(__file__), "data", "avatars", name)
                    config_path = os.path.join(avatar_dir, "config.json")
                    
                    # 创建配置信息
                    config_data = {
                        "avatar_id": name,
                        "video_path": f"data/video/{name}.mp4",
                        "created_at": datetime.now().isoformat(),
                        "tts_model": tts_model if tts_model else "edgeTTS",
                        "timbre": timbre if timbre else "Default",
                        "avatar_model": avatar_model if avatar_model else "musetalk",
                        "description": description if description else "",
                        "support_clone": support_clone.lower() == "true",
                        "avatar_blur": burr
                    }
                    
                    # 保存配置文件
                    with open(config_path, 'w', encoding='utf-8') as f:
                        json.dump(config_data, f, indent=2, ensure_ascii=False)
                    print(f"Saved avatar config to: {config_path}")
                    
                    # 更新index.json
                    index_path = os.path.join(os.path.dirname(__file__), "data", "avatars", "index.json")
                    
                    # 读取现有的index.json
                    if os.path.exists(index_path):
                        with open(index_path, 'r', encoding='utf-8') as f:
                            index_data = json.load(f)
                    else:
                        index_data = []
                    
                    # 检查是否已存在该avatar
                    avatar_exists = False
                    for item in index_data:
                        if item.get("id") == name:
                            avatar_exists = True
                            break
                    
                    # 如果不存在，添加新条目
                    if not avatar_exists:
                        index_data.append({
                            "id": name,
                            "name": name.replace("_", " ").title(),
                            "ref": f"{name}/full_imgs/00000000.png"
                        })
                        
                        # 保存更新后的index.json
                        with open(index_path, 'w', encoding='utf-8') as f:
                            json.dump(index_data, f, indent=2, ensure_ascii=False)
                        print(f"Updated index.json with new avatar: {name}")
                        
                except Exception as save_err:
                    print(f"[ERROR] Failed to save avatar config: {save_err}")
            
            # 在后台线程中保存配置，不阻塞响应
            threading.Thread(target=save_avatar_config, daemon=True).start()
            
            # 如果有语音文件，也保存它
            if prompt_voice and prompt_voice.filename:
                try:
                    voice_content = await prompt_voice.read()
                    if len(voice_content) > 0:
                        avatar_dir = os.path.join(os.path.dirname(__file__), "data", "avatars", name)
                        voice_filename = f"prompt_voice{os.path.splitext(prompt_voice.filename)[1]}"
                        voice_path = os.path.join(avatar_dir, voice_filename)
                        with open(voice_path, 'wb') as f:
                            f.write(voice_content)
                        print(f"Saved prompt voice to: {voice_path}")
                except Exception as voice_err:
                    print(f"[WARN] Failed to save prompt voice: {voice_err}")
            
            return {"status": "success", "message": "Avatar created", "image_path": result}
        else:
            print(f"Avatar creation failed for: {name}")
            raise HTTPException(status_code=500, detail="Failed to create avatar - check video file format and content")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 清理临时文件
        try:
            if 'video_path' in locals() and os.path.exists(video_path):
                os.remove(video_path)
        except Exception as cleanup_err:
            print(f"[WARN] cleanup failed: {cleanup_err}")

@app.post("/avatar/delete")
def avatar_delete(name: str = Form(...)):
    """Avatar deletion endpoint - alias for delete_avatar"""
    return delete_avatar(avatar_name=name)

@app.post("/avatar/start")
def avatar_start(avatar_name: str = Form(...), ref_file: str = Form("ref_audio/complete_silence.wav")):
    """Avatar start endpoint - alias for switch_avatar"""
    return switch_avatar(avatar_id=avatar_name, ref_file=ref_file)

@app.get("/tts/models")
def get_tts_models():
    """Get available TTS models"""
    return {
        "cosyvoice": {"full_name": "CosyVoice2", "clone": True, "status": "active", "license": "MIT"},
        "edgeTTS": {"full_name": "edgeTTS", "clone": False, "status": "active", "license": "MIT"},
        "tacotron": {"full_name": "TacoTron2", "clone": False, "status": "active", "license": "MIT"},
        "sovits": {"full_name": "GPT-SoViTs", "clone": True, "status": "active", "license": "MIT"}
    }

@app.on_event("startup")
async def startup_event():
    """Load configuration when application starts"""
    if not load_config():
        print("Warning: Configuration file loading failed, default values will be used")

if __name__ == "__main__":
    # Load configuration before startup
    load_config()
    uvicorn.run(app, host="0.0.0.0", port=8606)