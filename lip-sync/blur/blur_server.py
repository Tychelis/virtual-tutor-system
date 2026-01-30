"""
video_bg_service.py

Jina Executor: 给视频做人像抠图 → 背景模糊 / 替换 → 保留原音轨
运行示例：
    python video_bg_service.py         # 启动服务 (端口 23002)
客户端调用参考见文末注释。
"""

import os
import subprocess
import multiprocessing
import tempfile
from pathlib import Path

import cv2 as cv
import numpy as np
from jina import Executor, Deployment, requests, Client
from docarray import BaseDoc, DocList

# ---------- 全局配置 ----------
WORKSPACE = "./"   # 所有输入/输出文件所在根目录
MODEL_PATH = "/workspace/murphy/capstone-project-25t3-9900-virtual-tutor-phase-2/lip-sync/blur/human_segmentation_pphumanseg_2023mar.onnx" # Download here: https://github.com/opencv/opencv_zoo/tree/main/models/human_segmentation_pphumanseg
PORT = 23004


# ---------- Doc 定义 ----------
class VideoBGTask(BaseDoc):
    input_video_path: str                  # 必填：相对于 WORKSPACE
    output_video_path: str   # 结果文件，相对 WORKSPACE
    blur_background: bool = False          # 二选一
    background_image: str = ""             # 二选一：相对 WORKSPACE
    blur_kernel: int = 101                 # 高斯核（奇数）
    resize: int = 192                      # PPHumanSeg 输入大小


class Result(BaseDoc):
    result: str  # 'success' / 'error'
    info: str    # 输出文件路径 / 错误信息


# ---------- Executor ----------
class VideoBGExecutor(Executor):
    def __init__(self, model_path: str = MODEL_PATH, **kwargs):
        super().__init__(**kwargs)
        self.net = cv.dnn.readNet(model_path)   # CPU 推理
        self.model_in = 192

    # ---------- 工具 ----------
    @staticmethod
    def _pre(frame_bgr, in_size):
        rgb = cv.cvtColor(frame_bgr, cv.COLOR_BGR2RGB)
        blob = cv.resize(rgb, (in_size, in_size)).astype(np.float32) / 255.0
        return blob.transpose(2, 0, 1)[np.newaxis]

    @staticmethod
    def _post(mask, wh):
        w, h = wh
        mask = mask[0, 0].astype(np.float32)           # 0/1, 背景=1
        mask = cv.resize(mask, (w, h), cv.INTER_NEAREST)
        mask = 1.0 - mask                              # 人物=1
        mask = cv.GaussianBlur(mask, (15, 15), 0)
        return mask[..., None]                         # HW1

    @staticmethod
    def _compose(frame, mask, mode, kernel, bg_img=None):
        if mode == 'blur':
            bg = cv.GaussianBlur(frame, (kernel, kernel), 0)
        elif mode == 'replace' and bg_img is not None:
            bg = bg_img
        else:
            bg = frame
        comp = frame.astype(np.float32) * mask + bg.astype(np.float32) * (1 - mask)
        return comp.astype(np.uint8)

    # ---------- 主入口 ----------
    @requests
    def process(self, docs: DocList[VideoBGTask], **kwargs) -> DocList[Result]:
        out_docs: list[Result] = []

        for d in docs:
            try:
                # 1. 参数校验
                if not (d.blur_background ^ bool(d.background_image)):
                    raise ValueError("必须二选一：blur_background 或 background_image")

                inp = Path(WORKSPACE) / d.input_video_path
                if not inp.exists():
                    raise FileNotFoundError(f"找不到 {inp}")

                cap = cv.VideoCapture(str(inp))
                w, h = int(cap.get(cv.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv.CAP_PROP_FPS) or 30

                # 2. 背景图预处理（如需要）
                bg_img = None
                if d.background_image:
                    bg_path = Path(WORKSPACE) / d.background_image
                    bg_img = cv.imread(str(bg_path))
                    if bg_img is None:
                        raise FileNotFoundError(f"无法读取背景图 {bg_path}")
                    bg_img = cv.resize(bg_img, (w, h))

                # 3. 临时无声视频
                tmp_path = Path(tempfile.mkstemp(suffix=".mp4")[1])
                writer = cv.VideoWriter(
                    str(tmp_path),
                    cv.VideoWriter_fourcc(*"mp4v"),
                    fps,
                    (w, h),
                )

                # 4. 帧级循环
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    blob = self._pre(frame, d.resize)
                    self.net.setInput(blob)
                    mask = self.net.forward()
                    mask = self._post(mask, (w, h))
                    mode = "blur" if d.blur_background else "replace"
                    out_frame = self._compose(frame, mask, mode, d.blur_kernel, bg_img)
                    writer.write(out_frame)

                cap.release()
                writer.release()

                # 5. 合并音轨
                out_path = Path(WORKSPACE) / (d.output_video_path or f"{inp.stem}_out.mp4")
                cmd = [
                    "/usr/bin/ffmpeg",
                    "-y",
                    "-i",
                    str(tmp_path),  # 无声
                    "-i",
                    str(inp),       # 原声
                    "-c",
                    "copy",
                    "-c:v",
                    "libx264",
                    "-map",
                    "0:v:0",
                    "-map",
                    "1:a:0?",
                    str(out_path),
                ]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                os.remove(tmp_path)

                out_docs.append(Result(result="success", info=str(out_path)))
            except Exception as e:
                out_docs.append(Result(result="error", info=str(e)))

        return DocList[Result](out_docs)


# ---------- 启动服务 ----------
if __name__ == "__main__":
    
    dep = Deployment(uses=VideoBGExecutor, port=PORT, timeout_ready=-1)

    with dep:
        print(f" 服务已启动，端口 {PORT}")
        dep.block()


"""
# ---------- 客户端示例 ----------
from docarray import DocList
from jina import Client
from video_bg_service import VideoBGTask, Result

cli = Client(port=23002)

req = VideoBGTask(
    input_video_path="input_demo.mp4",
    output_video_path="output_demo.mp4",
    blur_background=True,
)

resp = cli.post(
    on="/",
    inputs=DocList[VideoBGTask]([req]),
    return_type=DocList[Result],
)

print(resp[0].result, resp[0].info)
"""