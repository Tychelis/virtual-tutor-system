from fastapi import FastAPI, Form, Request, Query
from fastapi.responses import HTMLResponse
from fastapi import HTTPException
from fastapi.templating import Jinja2Templates
import requests
import subprocess
import time


app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def form_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
@app.post("/submit", response_class=HTMLResponse)
async def submit_form(
    request: Request,
    model_name: str = Form(...),
    port: int = Form(...),
    use_gpu: bool = Form(...)
):
    try:
        response = requests.post(
            "http://160.250.71.211:37646/tts/start",
            files={
                "model_name": (None, model_name),
                "port": (None, str(port)),
                "use_gpu": (None, str(use_gpu).lower()),
            }
        )
        # 打印响应状态码和文本
        print(f"Status Code: {response.status_code}")
        print(f"Response Text: {response.text}")

        # 判断是否为 JSON 响应
        if response.headers.get("Content-Type", "").startswith("application/json"):
            data = response.json()
        else:
            data = {
                "status": "error",
                "message": "Invalid response format from API",
                "raw_response": response.text
            }

    except Exception as e:
        print(f"Error: {e}")
        data = {"status": "error", "message": str(e)}

    return templates.TemplateResponse("index.html", {
        "request": request,
        "result": data
    })


from fastapi.responses import JSONResponse

from typing import Dict, Any
from fastapi.responses import JSONResponse

@app.get("/tts/models", response_class=JSONResponse)
async def get_tts_models():
    try:
        response = requests.get("http://160.250.71.211:37646/tts/models")
        response.raise_for_status()
        models_data: Dict[str, Any] = response.json()

        # 构造更清晰的列表结构
        parsed_models = []
        for model_name, info in models_data.items():
            parsed_models.append({
                "model_name": model_name,
                "full_name": info.get("full_name"),
                "status": info.get("status"),
                "license": info.get("license"),
                "timbres": info.get("timbres"),
                "cur_timbre": info.get("cur_timbre"),
                "env_path": info.get("env_path"),
                "server_path": info.get("server_path"),
            })

        return {"models": parsed_models}

    except Exception as e:
        return {"status": "error", "message": str(e)}



@app.post("/tts/choose_timbre", response_class=JSONResponse)
async def choose_timbre(
    model_name: str = Form(...),
    timbre: str = Form(None)  # 可选参数
):
    try:
        post_data = {
            "model_name": (None, model_name)
        }
        if timbre:
            post_data["timbre"] = (None, timbre)

        response = requests.post(
            "http://160.250.71.211:37646/tts/choose_timbre",
            files=post_data
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/switch_avatar")
def switch_avatar(
    avatar_id: str = Query(..., description="Avatar ID，例如 avator_1"),
    ref_file: str = Query(..., description="参考音频文件路径")
):

    print("test /switch_avatar ：")
    url = "http://160.250.71.211:37646/switch_avatar"
    params = {
        "avatar_id": avatar_id,
        "ref_file": ref_file
    }
    response = requests.post(url, params=params)
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.json()}")