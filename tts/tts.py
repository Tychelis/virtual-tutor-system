from fastapi import FastAPI, Form, UploadFile, File, HTTPException, Query
from fastapi.responses import Response
from typing import Optional
import subprocess
import asyncio
import psutil
import httpx
import json
import time
import os
import numpy as np
import io
import soundfile as sf  # pip install soundfile
from fastapi import Response, HTTPException
from fastapi.responses import StreamingResponse

# ========== Configuration =========
CURENT_TTS_SERVER = None
TTS_SERVER_PORT = 5033
TTS_SERVER_PID = None
TTS_SERVER_USE_GPU = True
TTS_TIMBRE = None

PROJ_ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(PROJ_ROOT, "config.json")
MODEL_INFO_FILE = os.path.join(PROJ_ROOT, "model_info.json")
AVATAR_FILE = os.path.join(PROJ_ROOT, "avatars.json")

EDGE_TIMVRES_MAP = {
    "Default": "en-US-GuyNeural",
    "MaleA": "en-US-GuyNeural",
    "MaleB": "en-US-ChristopherNeural",
    "MaleC": "en-US-DavisNeural",
    "MaleD": "en-US-AndrewNeural",
    "MaleE": "en-US-JacobNeural",
    "MaleF": "en-US-SteffanNeural",
    "FemaleA": "en-US-EmmaNeural",
    "FemaleB": "en-US-JennyMultilingualNeural",
    "FemaleC": "en-US-JennyNeural",
    "FemaleD": "en-US-AriaNeural",
    "FemaleE": "en-US-AnaNeural",
    "FemaleF": "en-US-SaraNeural",
    "ChineseMaleA": "zh-CN-YunjianNeural",
    "ChineseMaleB": "zh-CN-YunxiNeural",
    "ChineseFemaleA": "zh-CN-XiaoxiaoNeural",
    "ChineseFemaleB": "zh-CN-XiaoyiNeural",
}

TACO_TIMVRES_MAP = {
    "MaleA": "40",
    "MaleB": "45",
    "Default": "50",
    "FemaleA": "55",
    "FemaleB": "60",
}


# ========== Tool Functions =========
def load_config():
    if not os.path.exists(CONFIG_FILE):
        default_config = {
            "tts_server_port": TTS_SERVER_PORT,
            "tts_server_use_gpu": TTS_SERVER_USE_GPU,
            "current_tts_server": None,
            "tts_server_pid": None,
            "tts_timbre": TTS_TIMBRE
        }
        save_config(default_config)
        return default_config
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)


def load_model_info():
    if not os.path.exists(MODEL_INFO_FILE):
        return None
    with open(MODEL_INFO_FILE, 'r', encoding='utf-8') as f:
        contents = json.load(f)
    return contents


def load_avatars():
    if not os.path.exists(AVATAR_FILE):
        return None
    with open(AVATAR_FILE, 'r', encoding='utf-8') as f:
        contents = json.load(f)
    return contents


def find_pid_on_port(port):
    for conn in psutil.net_connections(kind='inet'):
        if conn.status == psutil.CONN_LISTEN and conn.laddr.port == port:
            return conn.pid
    return None


def stop_tts_server():
    """ Stop the currently running TTS server if it exists.
    用port找到运行中的process, 然后kill掉它
    trick: 不应该kill掉记录的进程, 因为运行的进程并不是服务器的实际进程, 而是server脚本的进程!!
    实际上记录进程号这件事完全没有必要！
    """
    global CURENT_TTS_SERVER, TTS_SERVER_PID, TTS_SERVER_PORT, TTS_SERVER_USE_GPU, TTS_TIMBRE
    if TTS_SERVER_PORT and CURENT_TTS_SERVER:
        pid = find_pid_on_port(TTS_SERVER_PORT)
        if pid:
            print(f">>> Stopping TTS server [{CURENT_TTS_SERVER}] on port {TTS_SERVER_PORT} ...")
            os.kill(pid, 9)  # 强制终止进程
            print(f">>> TTS server on port {TTS_SERVER_PORT} stopped successfully.")
        else:
            print(f">>> No TTS server is running on port {TTS_SERVER_PORT}.")

    # Reset global variables
    CURENT_TTS_SERVER = None
    TTS_SERVER_PID = None
    TTS_SERVER_PORT = None
    TTS_SERVER_USE_GPU = True
    TTS_TIMBRE = None
    print(">>> TTS server stopped and reset global variables.")


def generate_pcm_stream(wav_bytes: bytes, chunk_size=4096):
    import wave
    with wave.open(io.BytesIO(wav_bytes), 'rb') as wav_file:
        while True:
            chunk = wav_file.readframes(chunk_size // 2)  # 每帧是2字节
            if not chunk:
                break
            yield chunk


def generate_pcm_bytes(wav_bytes: bytes) -> bytes:
    import wave
    with wave.open(io.BytesIO(wav_bytes), 'rb') as wav_file:
        return wav_file.readframes(wav_file.getnframes())

# ========== FastAPI Application =========
app = FastAPI()


# start a new TTS server, and stop old tts server if it exists
@app.post("/tts/start")
async def start_tts_server(
        model_name: str = Form(...),
        port: int = Form(TTS_SERVER_PORT),
        use_gpu: bool = Form(TTS_SERVER_USE_GPU),
):
    """
    Start a TTS server with the specified model and port.
    If a TTS server is already running, it will be stopped before starting a new one.
    Args:
        model_name (str): The name of the TTS model to use.
        port (int): The port on which the TTS server will run (optional, default as 5033).
        use_gpu (bool): Whether to use GPU for TTS processing (optional, default as True).
    Returns:
        {
            "status": str,
            "message": str,
            "port": int
            "model_name": str
            "use_gpu": bool
        }
    """
    global CURENT_TTS_SERVER, TTS_SERVER_PID, TTS_SERVER_PORT, TTS_SERVER_USE_GPU, TTS_TIMBRE
    env_path = None
    server_path = None

    # 1. check model_name is valid
    model_infos = load_model_info()
    if not model_infos:
        raise HTTPException(status_code=500, detail="Model information not found.")
    if model_name not in model_infos:
        raise HTTPException(status_code=400, detail=f"Model '{model_name}' not found in available models.")

    if model_name in model_infos:
        model_info = model_infos[model_name]

        if not model_info.get("status", None) == "active":
            raise HTTPException(status_code=400, detail=f"Model '{model_name}' is not valid to use.")

        env_path = model_info.get("env_path", None)
        if not env_path:
            raise HTTPException(status_code=400, detail=f"Model '{model_name}' does not have a valid environment path.")
        if not os.path.exists(env_path):
            raise HTTPException(status_code=400, detail=f"Model '{model_name}' does not have a valid environment path.")

        server_path = model_info.get("server_path", None)
        if not server_path or not os.path.exists(server_path):
            raise HTTPException(status_code=400, detail=f"Model '{model_name}' server path is not valid.")

    # 2. stop the current TTS server if it exists (even if it is the same model)
    if CURENT_TTS_SERVER:
        stop_tts_server()

    # 3. Check if the port is already in use
    if find_pid_on_port(port):
        raise HTTPException(status_code=400, detail=f"Port {port} is already in use. Please choose a different port.")

    # 4. start a new TTS server
    python_exec = os.path.join(env_path, "bin", "python")
    command = [
        python_exec, server_path,
        "--model_name", model_name,
        "--port", str(port),
        "--use_gpu", str(use_gpu)
    ]
    env = os.environ.copy()
    env["PATH"] = os.path.join(env_path, "bin") + ":" + env["PATH"]

    process = subprocess.Popen(command, env=env)
    CURENT_TTS_SERVER = model_name
    TTS_SERVER_PID = process.pid
    TTS_SERVER_PORT = port
    TTS_SERVER_USE_GPU = use_gpu
    TTS_TIMBRE = model_info.get("cur_timbre", None)  # Get the current timbre if available

    # 5. 等待 TTS 端口启动成功
    timeout = 60
    interval = 0.5
    start_time = time.time()
    while True:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"http://localhost:{port}/health",
                                        timeout=2.0)  # 假设 TTS server 有个 /ping 或 /health 接口
                if resp.status_code == 200:
                    break
        except Exception:
            pass

        if time.time() - start_time > timeout:
            stop_tts_server()  # 启动失败，自动关闭刚开的进程
            print(f"TTS server '{model_name}' failed to start within {timeout} seconds.")
            raise HTTPException(status_code=500, detail=f"TTS 模型服务启动超时（超过 {timeout} 秒）")

        await asyncio.sleep(interval)

    # write config
    config = {
        "tts_server_port": TTS_SERVER_PORT,
        "tts_server_use_gpu": TTS_SERVER_USE_GPU,
        "current_tts_server": CURENT_TTS_SERVER,
        "tts_server_pid": TTS_SERVER_PID,
        "tts_timbre": TTS_TIMBRE
    }
    save_config(config)

    if CURENT_TTS_SERVER:
        return {
            "status": "success",
            "message": f"TTS server '{model_name}' started successfully.",
            "port": port,
            "model_name": model_name,
            "use_gpu": use_gpu,
            "timbre": TTS_TIMBRE
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to start TTS server.")


# generate TTS response
@app.post("/tts/response")
async def get_tts_response(
        tts_text: str = Form(...),
        prompt_text: Optional[str] = Form(None),
        prompt_wav: Optional[UploadFile] = File(None)
):
    """
    if a TTS server running, send a request to the TTS server to generate a response wav.
    Args:
        tts_text (str): The text to be converted to speech.
        prompt_text (str): The text prompt for the TTS model.
        prompt_wav (UploadFile): An optional audio file to use as a prompt.
    Returns:
        Response: The generated audio file in WAV format.
    """
    # Check if a TTS server is running
    global CURENT_TTS_SERVER, TTS_SERVER_PID, TTS_TIMBRE
    if not CURENT_TTS_SERVER:
        raise HTTPException(status_code=503, detail="No TTS server is currently running.")

    if CURENT_TTS_SERVER == "edgeTTS":
        prompt_text = EDGE_TIMVRES_MAP[TTS_TIMBRE] if TTS_TIMBRE else "en-US-GuyNeural"  # todo
        print(f">>> Using timbre: {prompt_text} for edgeTTS")
    elif CURENT_TTS_SERVER == "tacotron":
        prompt_text = TACO_TIMVRES_MAP[TTS_TIMBRE] if TTS_TIMBRE else "40"  # todo
        print(f">>> Using timbre: {prompt_text} for tacotron")
    elif CURENT_TTS_SERVER == "sovits":
        prompt_text = TTS_TIMBRE if TTS_TIMBRE else "The course name COMP9331 is simply compained 3331."
        print(f">>> prompt text is : {prompt_text} for sovits")

    # Prepare the request data
    files = {
        "tts_text": (None, tts_text),
        "prompt_text": (None, prompt_text or "")
    }

    if prompt_wav:
        files["prompt_wav"] = (prompt_wav.filename, await prompt_wav.read(), prompt_wav.content_type)

    async with httpx.AsyncClient() as client:
        # TODO: change to actual api
        response = await client.post(f"http://localhost:{TTS_SERVER_PORT}/generate", files=files, timeout=30.0)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to get response from TTS server")

    wav_bytes = response.content
    # totalyly return wav bytes
    pcm_data = generate_pcm_bytes(wav_bytes)
    return Response(content=pcm_data, media_type="application/octet-stream")

    # stream response as PCM data
    return StreamingResponse(generate_pcm_stream(wav_bytes), media_type="application/octet-stream")


# get all valid TTS models
@app.get("/tts/models")
async def get_tts_models():
    """
    Get a list of all valid TTS models available for use.
    Returns:
        {
            "model_name": {
                "full_name": str,
                "clone": bool,
                "status": str,
                "license": str,
                "timbres": list,
                "cur_timbre": str
            }
        }
    """
    contents = load_model_info()
    if not contents:
        raise HTTPException(status_code=500, detail="Model information not found.")

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
    return model_info


# get TTS server config list
@app.post("/tts/choose_timbre")
async def get_tts_config(
        model_name: str = Form(...),
        timbre: Optional[str] = Form(None)
):
    """
    Get supported TTS server config for the specified model.
    Args:
        model_name (str): The name of the TTS model to query.
        timbre (Optional[str]): The specific timbre to query, if any.
    Returns:
        {
            "model_name": str, the name of the TTS model,
            "timbres": list, the list of available timbres for the model,
            "cur_timbre": str, the currently selected timbre for the model
        }
    """
    global CURENT_TTS_SERVER, TTS_SERVER_PID, TTS_SERVER_PORT, TTS_SERVER_USE_GPU, TTS_TIMBRE
    contents = load_model_info()
    if not contents:
        raise HTTPException(status_code=500, detail="Model information not found.")
    if model_name not in contents:
        raise HTTPException(status_code=400, detail=f"Model '{model_name}' not found in available models.")
    model_info = contents[model_name]
    if not model_info.get("status", None) == "active":
        raise HTTPException(status_code=400, detail=f"Model '{model_name}' is not valid to use.")
    timbres = model_info.get("timbres", [])
    if not timbres:
        raise HTTPException(status_code=400, detail=f"Model '{model_name}' does not have any valid timbres.")
    if timbre not in timbres:
        raise HTTPException(status_code=400,
                            detail=f"Timbre '{timbre}' is not valid for model '{model_name}'. Available timbres: {', '.join(timbres)}")

    # Update the current timbre in the model info
    model_info["cur_timbre"] = timbre if timbre else timbres[0]
    # Update the global variable
    TTS_TIMBRE = model_info["cur_timbre"]

    # Save the updated model info back to the file
    with open(MODEL_INFO_FILE, 'w', encoding='utf-8') as f:
        json.dump(contents, f, indent=4, ensure_ascii=False)
    # Return the model info with timbres and current timbre
    return {
        "model_name": model_name,
        "timbres": timbres,
        "cur_timbre": model_info["cur_timbre"]
    }


@app.post("/switch_avatar")
def switch_avatar(
        avatar_id: str = Query(..., description="Avatar ID，例如 avator_1"),
        ref_file: str = Query(..., description="参考音频文件路径")
):
    """在已有的 screen 会话中停止当前命令并运行新的脚本命令"""
    screen_session_name = "live"
    # 固定的命令参数
    transport = "webrtc"
    model = "musetalk"
    max_session = 8
    listenport = 8205
    tts = "cosyvoice"
    tts_server = "http://127.0.0.1:8604"
    ref_text = "This is a test demo. This is a test demo."

    avatar_id = avatar_id.strip() if avatar_id else "avator_1"
    ref_file = ref_file.strip() if ref_file else "data/audio/ref_liu.wav"

    # 构建命令
    command = (
        f"python3 app.py --transport {transport} --model {model} --avatar_id {avatar_id} "
        f"--max_session {max_session} --listenport {listenport} --tts {tts} "
        f"--TTS_SERVER {tts_server} --REF_FILE {ref_file} --REF_TEXT '{ref_text}' 2>&1 | tee log.txt"
    )

    try:
        # 检查 screen 会话是否存在
        result = subprocess.run(f"screen -ls | grep {screen_session_name}", shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"screen 会话 '{screen_session_name}' 不存在")

        # 向已有的 screen 会话发送 Ctrl+C 停止当前命令
        subprocess.run(f"screen -S {screen_session_name} -X stuff $'\\003'", shell=True, check=True)  # Ctrl+C
        subprocess.run(f"screen -S {screen_session_name} -X stuff $'\\003'", shell=True, check=True)  # Ctrl+C
        subprocess.run(f"screen -S {screen_session_name} -X stuff $'\\003'", shell=True, check=True)  # Ctrl+C
        # 等待一段时间以确保命令停止
        time.sleep(0.5)

        # 向已有的 screen 会话发送新命令
        subprocess.run(f"screen -S {screen_session_name} -X stuff \"{command}\\n\"", shell=True, check=True)

        return {
            "status": "success",
            "message": f"命令已停止并发送新命令到 screen 会话 '{screen_session_name}' 中运行"
        }
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "returncode": e.returncode,
            "stderr": e.stderr
        }
