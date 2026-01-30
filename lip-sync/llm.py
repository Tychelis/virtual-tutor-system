import time
import os
from basereal import BaseReal
from logger import logger
import requests
import random
import re

def dispatch_text(response_text: str, nerfreal, min_len: int = 10):
    """
    按字符扫描，遇句末标点立即输出；保证每句 ≥ min_len 字符
    """
    puncts = ",.!;:，。！？：；\n"
    buffer = []                     # 暂存当前正在累积的句子
    first  = True
    start  = time.perf_counter()

    for ch in response_text:
        # 记录首字符耗时
        if first:
            logger.info(f"llm Time to first char: {time.perf_counter() - start:.4f}s")
            first = False

        buffer.append(ch)

        # 如果是句末标点，尝试输出
        if ch in puncts:
            sentence = ''.join(buffer).strip()
            buffer.clear()

            if len(sentence) >= min_len:
                logger.info(sentence)
                nerfreal.put_msg_txt(sentence)
            else:
                # 不足 min_len，先压回 buffer，等待后续字符补齐
                buffer.extend(sentence)

    # 扫描完毕，还有剩余
    tail = ''.join(buffer).strip()
    if tail:
        nerfreal.put_msg_txt(tail)

    logger.info(f"llm Time to last char: {time.perf_counter() - start:.4f}s")



def llm_response(message,nerfreal:BaseReal):
    # start = time.perf_counter()
    # from openai import OpenAI
    # client = OpenAI(
    #     # 如果您没有配置环境变量，请在此处用您的API Key进行替换
    #     api_key=os.getenv("DASHSCOPE_API_KEY"),
    #     # 填写DashScope SDK的base_url
    #     base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    # )
    # end = time.perf_counter()
    # logger.info(f"llm Time init: {end-start}s")
    # completion = client.chat.completions.create(
    #     model="qwen-plus",
    #     messages=[{'role': 'system', 'content': 'You are a helpful assistant.'},
    #               {'role': 'user', 'content': message}],
    #     stream=True,
    #     # 通过以下设置，在流式输出的最后一行展示token使用信息
    #     stream_options={"include_usage": True}
    # )

    # result=""
    # first = True
    # for chunk in completion:
    #     if len(chunk.choices)>0:
    #         #print(chunk.choices[0].delta.content)
    #         if first:
    #             end = time.perf_counter()
    #             logger.info(f"llm Time to first chunk: {end-start}s")
    #             first = False
    #         msg = chunk.choices[0].delta.content
    #         lastpos=0
    #         #msglist = re.split('[,.!;:，。！?]',msg)
    #         for i, char in enumerate(msg):
    #             if char in ",.!;:，。！？：；" :
    #                 result = result+msg[lastpos:i+1]
    #                 lastpos = i+1
    #                 if len(result)>10:
    #                     logger.info(result)
    #                     nerfreal.put_msg_txt(result)
    #                     result=""
    #         result = result+msg[lastpos:]
    # end = time.perf_counter()
    # logger.info(f"llm Time to last chunk: {end-start}s")
    # nerfreal.put_msg_txt(result)  


    response_data={}

    session_id =  random.randint(100000, 999999)


    try:
        ask_response = requests.post(
            "http://127.0.0.1:8100/ask",
            json={"question": message,"session_id":session_id},
            timeout=10,
            
        )
        ask_response.raise_for_status()
        response_data["text_output"] = ask_response.json().get("answer", "No answer")
        # response_data["text_output"] = ask_response.json()
    except Exception as e:
        response_data["text_output"] = f"Error contacting /ask endpoint: {e}"

    response_text = response_data["text_output"]

    response_text=re.sub(r'[\*\'\"]','',response_text)
    
    dispatch_text(response_text,nerfreal,20)
    # result = ""
    # first = True
    # start = time.perf_counter()

    # words = response_text.split()
    # chunk_size = 5
    # puncts = ",.!;:，。！？：；"


    # for i in range(0, len(words), chunk_size):
    #     chunk = " ".join(words[i:i + chunk_size])

    #     if first:
    #         logger.info(f"llm Time to first chunk: {time.perf_counter() - start:.4f}s")
    #         first = False

    #     lastpos = 0
    #     for j, char in enumerate(chunk):
    #         if char in puncts:
    #             result += chunk[lastpos:j + 1]
    #             lastpos = j + 1
    #             if len(result) > 10:
    #                 logger.info(result)
    #                 nerfreal.put_msg_txt(result)
    #                 result = ""
    #     result += chunk[lastpos:]

    # logger.info(f"llm Time to last chunk: {time.perf_counter() - start:.4f}s")
    # if result:
    #     nerfreal.put_msg_txt(result)
  
