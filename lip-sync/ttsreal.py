###############################################################################
#  Copyright (C) 2024 LiveTalking@lipku https://github.com/lipku/LiveTalking
#  email: lipku@foxmail.com
# 
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#  
#       http://www.apache.org/licenses/LICENSE-2.0
# 
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################
from __future__ import annotations
import time
import numpy as np
import soundfile as sf
import resampy
import asyncio
import edge_tts

import os
import hmac
import hashlib
import base64
import json
import uuid

from typing import Iterator

import requests

import queue
from queue import Queue
from io import BytesIO
from threading import Thread, Event
from enum import Enum

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from basereal import BaseReal

from logger import logger
class State(Enum):
    RUNNING=0
    PAUSE=1

class BaseTTS:
    def __init__(self, opt, parent:BaseReal):
        self.opt=opt
        self.parent = parent

        self.fps = opt.fps # 20 ms per frame
        self.sample_rate = 16000
        self.chunk = self.sample_rate // self.fps # 320 samples per chunk (20ms * 16000 / 1000)
        self.input_stream = BytesIO()

        self.msgqueue = Queue()
        self.state = State.RUNNING
        
        # 创建持久化的事件循环用于异步操作
        self.loop = None

    def flush_talk(self):
        self.msgqueue.queue.clear()
        self.state = State.PAUSE

    def put_msg_txt(self,msg:str,eventpoint=None): 
        if len(msg)>0:
            self.msgqueue.put((msg,eventpoint))

    def render(self,quit_event):
        process_thread = Thread(target=self.process_tts, args=(quit_event,))
        process_thread.start()
    
    def process_tts(self,quit_event):        
        # 为这个线程创建事件循环
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            while not quit_event.is_set():
                try:
                    msg = self.msgqueue.get(block=True, timeout=1)
                    self.state=State.RUNNING
                except queue.Empty:
                    continue
                
                # 如果是异步方法，使用事件循环执行
                if asyncio.iscoroutinefunction(self.txt_to_audio):
                    self.loop.run_until_complete(self.txt_to_audio(msg))
                else:
                    self.txt_to_audio(msg)
        finally:
            self.loop.close()
            logger.info('ttsreal thread stop')
    
    def txt_to_audio(self,msg):
        pass
    

###########################################################################################
class EdgeTTS(BaseTTS):
    """优化的EdgeTTS - 异步流式处理，降低延迟"""
    
    def __init__(self, opt, parent):
        super().__init__(opt, parent)
        # 创建音频缓冲区用于暂存不完整的chunk
        self.audio_buffer = np.array([], dtype=np.float32)
    
    async def txt_to_audio(self, msg):
        """异步流式TTS转换，边生成边播放（支持重试）"""
        voicename = self.opt.REF_FILE
        text, textevent = msg

        t_start = time.time()
        logger.info(f'[EdgeTTS] Starting TTS for text: {text[:50]}...')

        # 重试配置（增强网络容错）
        max_retries = 5  # 从3次增加到5次
        retry_delay = 1.5  # 从1秒增加到1.5秒
        any_audio_sent = False  # Track if we've sent any audio data

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    logger.warning(f'[EdgeTTS] Retry attempt {attempt}/{max_retries-1}')
                    await asyncio.sleep(retry_delay)

                communicate = edge_tts.Communicate(text, voicename)

                first_chunk = True
                chunk_count = 0

                # 流式接收音频块
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio" and self.state == State.RUNNING:
                        chunk_data = chunk["data"]
                        chunk_count += 1
                        any_audio_sent = True

                        if first_chunk:
                            elapsed = time.time() - t_start
                            logger.info(f'[EdgeTTS] Time to first audio chunk: {elapsed:.4f}s')
                            first_chunk = False

                        # 立即处理这个音频块，边接收边播放
                        await self._process_audio_chunk(chunk_data, text, textevent,
                                                        is_first=chunk_count==1)

                    elif chunk["type"] == "WordBoundary":
                        pass

                # 成功完成，处理缓冲区中剩余的音频
                if len(self.audio_buffer) > 0:
                    eventpoint = {'status':'end', 'text':text, 'msgevent':textevent}
                    # 填充到chunk大小
                    padding = np.zeros(self.chunk - len(self.audio_buffer), dtype=np.float32)
                    final_chunk = np.concatenate([self.audio_buffer, padding])
                    self.parent.put_audio_frame(final_chunk, eventpoint)
                    self.audio_buffer = np.array([], dtype=np.float32)
                    logger.info(f'[EdgeTTS] Sent final buffer with {len(self.audio_buffer) + len(padding)} samples')
                else:
                    # 发送结束信号
                    eventpoint = {'status':'end', 'text':text, 'msgevent':textevent}
                    self.parent.put_audio_frame(np.zeros(self.chunk, np.float32), eventpoint)

                total_time = time.time() - t_start
                logger.info(f'[EdgeTTS] ✅ Total TTS time: {total_time:.4f}s, chunks: {chunk_count}')

                # 成功，跳出重试循环
                break

            except asyncio.TimeoutError:
                logger.error(f'[EdgeTTS] ⏱️ Network Timeout on attempt {attempt+1}/{max_retries} (检查网络连接)')
                if attempt == max_retries - 1:
                    logger.error(f'[EdgeTTS] ❌ Max retries reached after {max_retries} attempts, TTS failed due to network timeout')
                    # 如果已经发送过音频，不发送静音；否则发送结束信号
                    if not any_audio_sent:
                        eventpoint = {'status':'end', 'text':text, 'msgevent':textevent}
                        self.parent.put_audio_frame(np.zeros(self.chunk, np.float32), eventpoint)
                    else:
                        logger.info('[EdgeTTS] Audio was partially sent, not sending silence to avoid gaps')
            except Exception as e:
                error_type = type(e).__name__
                logger.error(f'[EdgeTTS] ❌ {error_type} on attempt {attempt+1}/{max_retries}: {e}')
                if attempt == max_retries - 1:
                    logger.exception(f'[EdgeTTS] ❌ Max retries reached after {max_retries} attempts, TTS conversion failed')
                    # 如果已经发送过音频，确保发送结束信号；否则发送静音
                    if any_audio_sent:
                        # 如果缓冲区中还有数据，发送出去
                        if len(self.audio_buffer) > 0:
                            padding = np.zeros(self.chunk - len(self.audio_buffer), dtype=np.float32)
                            final_chunk = np.concatenate([self.audio_buffer, padding])
                            eventpoint = {'status':'end', 'text':text, 'msgevent':textevent}
                            self.parent.put_audio_frame(final_chunk, eventpoint)
                            self.audio_buffer = np.array([], dtype=np.float32)
                        else:
                            eventpoint = {'status':'end', 'text':text, 'msgevent':textevent}
                            self.parent.put_audio_frame(np.zeros(self.chunk, np.float32), eventpoint)
                    else:
                        # 没有发送过任何音频，发送静音
                        eventpoint = {'status':'end', 'text':text, 'msgevent':textevent}
                        self.parent.put_audio_frame(np.zeros(self.chunk, np.float32), eventpoint)
    
    async def _process_audio_chunk(self, chunk_data: bytes, text: str, textevent, is_first: bool):
        """处理单个音频块，立即转换并发送"""
        try:
            # 解码音频数据
            audio_io = BytesIO(chunk_data)
            stream, sample_rate = sf.read(audio_io)
            
            # 转换为float32
            stream = stream.astype(np.float32)
            
            # 处理多声道
            if stream.ndim > 1:
                stream = stream[:, 0]
            
            # 重采样
            if sample_rate != self.sample_rate and len(stream) > 0:
                stream = resampy.resample(x=stream, sr_orig=sample_rate, sr_new=self.sample_rate)
            
            # 将新数据加入缓冲区
            self.audio_buffer = np.concatenate([self.audio_buffer, stream])
            
            # 发送完整的chunk
            idx = 0
            while len(self.audio_buffer) >= self.chunk and self.state == State.RUNNING:
                eventpoint = None
                if is_first and idx == 0:
                    eventpoint = {'status':'start', 'text':text, 'msgevent':textevent}
                    is_first = False
                
                # 提取一个chunk并发送
                chunk_to_send = self.audio_buffer[:self.chunk]
                self.parent.put_audio_frame(chunk_to_send, eventpoint)
                
                # 移除已发送的数据
                self.audio_buffer = self.audio_buffer[self.chunk:]
                idx += 1
                
        except Exception as e:
            logger.exception('[EdgeTTS] Error processing audio chunk')
    
    def __create_bytes_stream(self,byte_stream):
        """兼容方法，保留用于其他可能的调用"""
        stream, sample_rate = sf.read(byte_stream)
        logger.info(f'[INFO]tts audio stream {sample_rate}: {stream.shape}')
        stream = stream.astype(np.float32)

        if stream.ndim > 1:
            logger.info(f'[WARN] audio has {stream.shape[1]} channels, only use the first.')
            stream = stream[:, 0]
    
        if sample_rate != self.sample_rate and stream.shape[0]>0:
            logger.info(f'[WARN] audio sample rate is {sample_rate}, resampling into {self.sample_rate}.')
            stream = resampy.resample(x=stream, sr_orig=sample_rate, sr_new=self.sample_rate)

        return stream

###########################################################################################
class FishTTS(BaseTTS):
    def __init__(self, opt, parent):
        super().__init__(opt, parent)
        # 添加音频缓冲区，避免数据丢失
        self.audio_buffer = np.array([], dtype=np.float32)
    
    def txt_to_audio(self,msg): 
        text,textevent = msg
        self.stream_tts(
            self.fish_speech(
                text,
                self.opt.REF_FILE,  
                self.opt.REF_TEXT,
                "zh", #en args.language,
                self.opt.TTS_SERVER, #"http://127.0.0.1:5000", #args.server_url,
            ),
            msg
        )

    def fish_speech(self, text, reffile, reftext,language, server_url) -> Iterator[bytes]:
        start = time.perf_counter()
        req={
            'text':text,
            'reference_id':reffile,
            'format':'wav',
            'streaming':True,
            'use_memory_cache':'on'
        }
        try:
            res = requests.post(
                f"{server_url}/v1/tts",
                json=req,
                stream=True,
                headers={
                    "content-type": "application/json",
                },
            )
            end = time.perf_counter()
            logger.info(f"fish_speech Time to make POST: {end-start}s")

            if res.status_code != 200:
                logger.error("Error:%s", res.text)
                return
                
            first = True
        
            for chunk in res.iter_content(chunk_size=17640): # 1764 44100*20ms*2
                #print('chunk len:',len(chunk))
                if first:
                    end = time.perf_counter()
                    logger.info(f"fish_speech Time to first chunk: {end-start}s")
                    first = False
                if chunk and self.state==State.RUNNING:
                    yield chunk
            #print("gpt_sovits response.elapsed:", res.elapsed)
        except Exception as e:
            logger.exception('fishtts')

    def stream_tts(self,audio_stream,msg):
        text,textevent = msg
        first = True
        
        # 重置缓冲区
        self.audio_buffer = np.array([], dtype=np.float32)
        
        for chunk in audio_stream:
            if chunk is not None and len(chunk)>0:          
                stream = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32767
                stream = resampy.resample(x=stream, sr_orig=44100, sr_new=self.sample_rate)
                
                # 将新数据加入缓冲区
                self.audio_buffer = np.concatenate([self.audio_buffer, stream])
                
                # 发送完整的chunk
                idx = 0
                while len(self.audio_buffer) >= self.chunk and self.state == State.RUNNING:
                    eventpoint=None
                    if first:
                        eventpoint={'status':'start','text':text,'msgevent':textevent}
                        first = False
                    # 提取一个chunk并发送
                    chunk_to_send = self.audio_buffer[:self.chunk]
                    self.parent.put_audio_frame(chunk_to_send, eventpoint)
                    # 移除已发送的数据
                    self.audio_buffer = self.audio_buffer[self.chunk:]
                    idx += 1
        
        # 处理缓冲区中剩余的音频（重要：避免数据丢失）
        if len(self.audio_buffer) > 0:
            # 填充到chunk大小
            padding = np.zeros(self.chunk - len(self.audio_buffer), dtype=np.float32)
            final_chunk = np.concatenate([self.audio_buffer, padding])
            eventpoint={'status':'end','text':text,'msgevent':textevent}
            self.parent.put_audio_frame(final_chunk, eventpoint)
            self.audio_buffer = np.array([], dtype=np.float32)
        else:
            # 发送结束信号
            eventpoint={'status':'end','text':text,'msgevent':textevent}
            self.parent.put_audio_frame(np.zeros(self.chunk,np.float32),eventpoint) 

###########################################################################################
class SovitsTTS(BaseTTS):
    def __init__(self, opt, parent):
        super().__init__(opt, parent)
        # 添加音频缓冲区，避免数据丢失
        self.audio_buffer = np.array([], dtype=np.float32)
    
    def txt_to_audio(self,msg): 
        text,textevent = msg
        self.stream_tts(
            self.gpt_sovits(
                text,
                self.opt.REF_FILE,  
                self.opt.REF_TEXT,
                "zh", #en args.language,
                self.opt.TTS_SERVER, #"http://127.0.0.1:5000", #args.server_url,
            ),
            msg
        )

    def gpt_sovits(self, text, reffile, reftext,language, server_url) -> Iterator[bytes]:
        start = time.perf_counter()
        req={
            'text':text,
            'text_lang':language,
            'ref_audio_path':reffile,
            'prompt_text':reftext,
            'prompt_lang':language,
            'media_type':'ogg',
            'streaming_mode':True
        }
        # req["text"] = text
        # req["text_language"] = language
        # req["character"] = character
        # req["emotion"] = emotion
        # #req["stream_chunk_size"] = stream_chunk_size  # you can reduce it to get faster response, but degrade quality
        # req["streaming_mode"] = True
        try:
            res = requests.post(
                f"{server_url}/tts",
                json=req,
                stream=True,
            )
            end = time.perf_counter()
            logger.info(f"gpt_sovits Time to make POST: {end-start}s")

            if res.status_code != 200:
                logger.error("Error:%s", res.text)
                return
                
            first = True
        
            for chunk in res.iter_content(chunk_size=None): #12800 1280 32K*20ms*2
                logger.info('chunk len:%d',len(chunk))
                if first:
                    end = time.perf_counter()
                    logger.info(f"gpt_sovits Time to first chunk: {end-start}s")
                    first = False
                if chunk and self.state==State.RUNNING:
                    yield chunk
            #print("gpt_sovits response.elapsed:", res.elapsed)
        except Exception as e:
            logger.exception('sovits')

    def __create_bytes_stream(self,byte_stream):
        #byte_stream=BytesIO(buffer)
        stream, sample_rate = sf.read(byte_stream) # [T*sample_rate,] float64
        logger.info(f'[INFO]tts audio stream {sample_rate}: {stream.shape}')
        stream = stream.astype(np.float32)

        if stream.ndim > 1:
            logger.info(f'[WARN] audio has {stream.shape[1]} channels, only use the first.')
            stream = stream[:, 0]
    
        if sample_rate != self.sample_rate and stream.shape[0]>0:
            logger.info(f'[WARN] audio sample rate is {sample_rate}, resampling into {self.sample_rate}.')
            stream = resampy.resample(x=stream, sr_orig=sample_rate, sr_new=self.sample_rate)

        return stream

    def stream_tts(self,audio_stream,msg):
        text,textevent = msg
        first = True
        
        # 重置缓冲区
        self.audio_buffer = np.array([], dtype=np.float32)
        
        for chunk in audio_stream:
            if chunk is not None and len(chunk)>0:          
                byte_stream=BytesIO(chunk)
                stream = self.__create_bytes_stream(byte_stream)
                
                # 将新数据加入缓冲区
                self.audio_buffer = np.concatenate([self.audio_buffer, stream])
                
                # 发送完整的chunk
                idx = 0
                while len(self.audio_buffer) >= self.chunk and self.state == State.RUNNING:
                    eventpoint=None
                    if first:
                        eventpoint={'status':'start','text':text,'msgevent':textevent}
                        first = False
                    # 提取一个chunk并发送
                    chunk_to_send = self.audio_buffer[:self.chunk]
                    self.parent.put_audio_frame(chunk_to_send, eventpoint)
                    # 移除已发送的数据
                    self.audio_buffer = self.audio_buffer[self.chunk:]
                    idx += 1
        
        # 处理缓冲区中剩余的音频（重要：避免数据丢失）
        if len(self.audio_buffer) > 0:
            # 填充到chunk大小
            padding = np.zeros(self.chunk - len(self.audio_buffer), dtype=np.float32)
            final_chunk = np.concatenate([self.audio_buffer, padding])
            eventpoint={'status':'end','text':text,'msgevent':textevent}
            self.parent.put_audio_frame(final_chunk, eventpoint)
            self.audio_buffer = np.array([], dtype=np.float32)
        else:
            # 发送结束信号
            eventpoint={'status':'end','text':text,'msgevent':textevent}
            self.parent.put_audio_frame(np.zeros(self.chunk,np.float32),eventpoint)

###########################################################################################
class CosyVoiceTTS(BaseTTS):
    def __init__(self, opt, parent):
        super().__init__(opt, parent)
        # 添加音频缓冲区，避免数据丢失
        self.audio_buffer = np.array([], dtype=np.float32)
    
    def txt_to_audio(self,msg):
        text,textevent = msg 
        self.stream_tts(
            self.cosy_voice(
                text,
                self.opt.REF_FILE,  
                self.opt.REF_TEXT,
                "zh", #en args.language,
                self.opt.TTS_SERVER, #"http://127.0.0.1:5000", #args.server_url,
            ),
            msg
        )

    def cosy_voice(self, text, reffile, reftext,language, server_url) -> Iterator[bytes]:
        start = time.perf_counter()
        payload = {
            'tts_text': text,
            'prompt_text': reftext
        }
        try:
            files = [('prompt_wav', ('prompt_wav', open(reffile, 'rb'), 'application/octet-stream'))]
            res = requests.request("POST", f"{server_url}/inference_zero_shot", data=payload, files=files, stream=True)
            
            end = time.perf_counter()
            logger.info(f"cosy_voice Time to make POST: {end-start}s")

            if res.status_code != 200:
                logger.error("Error:%s", res.text)
                return
                
            first = True
        
            for chunk in res.iter_content(chunk_size=9600): # 960 24K*20ms*2
                if first:
                    end = time.perf_counter()
                    logger.info(f"cosy_voice Time to first chunk: {end-start}s")
                    first = False
                if chunk and self.state==State.RUNNING:
                    yield chunk
        except Exception as e:
            logger.exception('cosyvoice')

    def stream_tts(self,audio_stream,msg):
        text,textevent = msg
        first = True
        
        # 重置缓冲区
        self.audio_buffer = np.array([], dtype=np.float32)
        
        for chunk in audio_stream:
            if chunk is not None and len(chunk)>0:          
                stream = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32767
                stream = resampy.resample(x=stream, sr_orig=24000, sr_new=self.sample_rate)
                
                # 将新数据加入缓冲区
                self.audio_buffer = np.concatenate([self.audio_buffer, stream])
                
                # 发送完整的chunk
                idx = 0
                while len(self.audio_buffer) >= self.chunk and self.state == State.RUNNING:
                    eventpoint=None
                    if first:
                        eventpoint={'status':'start','text':text,'msgevent':textevent}
                        first = False
                    # 提取一个chunk并发送
                    chunk_to_send = self.audio_buffer[:self.chunk]
                    self.parent.put_audio_frame(chunk_to_send, eventpoint)
                    # 移除已发送的数据
                    self.audio_buffer = self.audio_buffer[self.chunk:]
                    idx += 1
        
        # 处理缓冲区中剩余的音频（重要：避免数据丢失）
        if len(self.audio_buffer) > 0:
            # 填充到chunk大小
            padding = np.zeros(self.chunk - len(self.audio_buffer), dtype=np.float32)
            final_chunk = np.concatenate([self.audio_buffer, padding])
            eventpoint={'status':'end','text':text,'msgevent':textevent}
            self.parent.put_audio_frame(final_chunk, eventpoint)
            self.audio_buffer = np.array([], dtype=np.float32)
        else:
            # 发送结束信号
            eventpoint={'status':'end','text':text,'msgevent':textevent}
            self.parent.put_audio_frame(np.zeros(self.chunk,np.float32),eventpoint) 

###########################################################################################
_PROTOCOL = "https://"
_HOST = "tts.cloud.tencent.com"
_PATH = "/stream"
_ACTION = "TextToStreamAudio"

class TencentTTS(BaseTTS):
    def __init__(self, opt, parent):
        super().__init__(opt,parent)
        self.appid = os.getenv("TENCENT_APPID")
        self.secret_key = os.getenv("TENCENT_SECRET_KEY")
        self.secret_id = os.getenv("TENCENT_SECRET_ID")
        self.voice_type = int(opt.REF_FILE)
        self.codec = "pcm"
        self.sample_rate = 16000
        self.volume = 0
        self.speed = 0
    
    def __gen_signature(self, params):
        sort_dict = sorted(params.keys())
        sign_str = "POST" + _HOST + _PATH + "?"
        for key in sort_dict:
            sign_str = sign_str + key + "=" + str(params[key]) + '&'
        sign_str = sign_str[:-1]
        hmacstr = hmac.new(self.secret_key.encode('utf-8'),
                           sign_str.encode('utf-8'), hashlib.sha1).digest()
        s = base64.b64encode(hmacstr)
        s = s.decode('utf-8')
        return s

    def __gen_params(self, session_id, text):
        params = dict()
        params['Action'] = _ACTION
        params['AppId'] = int(self.appid)
        params['SecretId'] = self.secret_id
        params['ModelType'] = 1
        params['VoiceType'] = self.voice_type
        params['Codec'] = self.codec
        params['SampleRate'] = self.sample_rate
        params['Speed'] = self.speed
        params['Volume'] = self.volume
        params['SessionId'] = session_id
        params['Text'] = text

        timestamp = int(time.time())
        params['Timestamp'] = timestamp
        params['Expired'] = timestamp + 24 * 60 * 60
        return params

    def txt_to_audio(self,msg):
        text,textevent = msg 
        self.stream_tts(
            self.tencent_voice(
                text,
                self.opt.REF_FILE,  
                self.opt.REF_TEXT,
                "zh", #en args.language,
                self.opt.TTS_SERVER, #"http://127.0.0.1:5000", #args.server_url,
            ),
            msg
        )

    def tencent_voice(self, text, reffile, reftext,language, server_url) -> Iterator[bytes]:
        start = time.perf_counter()
        session_id = str(uuid.uuid1())
        params = self.__gen_params(session_id, text)
        signature = self.__gen_signature(params)
        headers = {
            "Content-Type": "application/json",
            "Authorization": str(signature)
        }
        url = _PROTOCOL + _HOST + _PATH
        try:
            res = requests.post(url, headers=headers,
                          data=json.dumps(params), stream=True)
            
            end = time.perf_counter()
            logger.info(f"tencent Time to make POST: {end-start}s")
                
            first = True
        
            for chunk in res.iter_content(chunk_size=6400): # 640 16K*20ms*2
                #logger.info('chunk len:%d',len(chunk))
                if first:
                    try:
                        rsp = json.loads(chunk)
                        #response["Code"] = rsp["Response"]["Error"]["Code"]
                        #response["Message"] = rsp["Response"]["Error"]["Message"]
                        logger.error("tencent tts:%s",rsp["Response"]["Error"]["Message"])
                        return
                    except:
                        end = time.perf_counter()
                        logger.info(f"tencent Time to first chunk: {end-start}s")
                        first = False                    
                if chunk and self.state==State.RUNNING:
                    yield chunk
        except Exception as e:
            logger.exception('tencent')

    def stream_tts(self,audio_stream,msg):
        text,textevent = msg
        first = True
        last_stream = np.array([],dtype=np.float32)
        for chunk in audio_stream:
            if chunk is not None and len(chunk)>0:          
                stream = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32767
                stream = np.concatenate((last_stream,stream))
                #stream = resampy.resample(x=stream, sr_orig=24000, sr_new=self.sample_rate)
                #byte_stream=BytesIO(buffer)
                #stream = self.__create_bytes_stream(byte_stream)
                streamlen = stream.shape[0]
                idx=0
                while streamlen >= self.chunk:
                    eventpoint=None
                    if first:
                        eventpoint={'status':'start','text':text,'msgevent':textevent}
                        first = False
                    self.parent.put_audio_frame(stream[idx:idx+self.chunk],eventpoint)
                    streamlen -= self.chunk
                    idx += self.chunk
                last_stream = stream[idx:] #get the remain stream
        eventpoint={'status':'end','text':text,'msgevent':textevent}
        self.parent.put_audio_frame(np.zeros(self.chunk,np.float32),eventpoint) 

###########################################################################################
class TacotronTTS(BaseTTS):
    def txt_to_audio(self,msg):
        text,textevent = msg 
        self.stream_tts(
            self.tacotron(
                text,
                self.opt.REF_FILE,  
                self.opt.REF_TEXT,
                self.opt.TTS_SERVER, #"http://127.0.0.1:8604",
            ),
            msg
        )

    def tacotron(self, text, reffile, reftext, server_url) -> Iterator[bytes]:
        start = time.perf_counter()
        # Tacotron server expects prompt_text as an integer for scale factor
        # Use reftext if it's a digit, otherwise try to extract number from reffile
        # If neither works, use default value (45)
        if reftext and isinstance(reftext, str) and reftext.isdigit():
            prompt_text = reftext
        elif reftext and isinstance(reftext, (int, float)):
            prompt_text = str(int(reftext))
        else:
            # Default scale factor for tacotron
            prompt_text = "45"

        payload = {
            'tts_text': text,
            'prompt_text': prompt_text
        }
        file_handle = None  # Track opened file for proper cleanup
        try:
            # Tacotron server requires prompt_wav file, use a dummy file if reffile is not available
            # Support both absolute and relative paths, and filenames in ref_audio directory
            reffile_full_path = None
            if reffile:
                # First check if it's an absolute or direct relative path
                if os.path.exists(reffile):
                    reffile_full_path = reffile
                else:
                    # Check if it's a filename in the ref_audio directory
                    ref_audio_dir = os.path.join(os.path.dirname(__file__), 'ref_audio')
                    potential_path = os.path.join(ref_audio_dir, reffile if reffile.endswith('.wav') else f'{reffile}.wav')
                    if os.path.exists(potential_path):
                        reffile_full_path = potential_path
                    else:
                        logger.warning(f"Reference audio file not found: {reffile} (tried {potential_path})")

            if reffile_full_path:
                file_handle = open(reffile_full_path, 'rb')
                files = [('prompt_wav', ('prompt_wav', file_handle, 'application/octet-stream'))]
            else:
                # Create a dummy file if no reference file is provided
                logger.warning(f"Using dummy file for Tacotron (reffile: {reffile})")
                dummy_file = BytesIO(b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00')
                files = [('prompt_wav', ('prompt_wav', dummy_file, 'application/octet-stream'))]

            res = requests.request("POST", f"{server_url}/generate", data=payload, files=files, stream=True)

            end = time.perf_counter()
            logger.info(f"[Tacotron] Time to make POST: {end-start}s")

            if res.status_code != 200:
                logger.error(f"[Tacotron] ✗ Error response: {res.text}")
                return

            first = True

            for chunk in res.iter_content(chunk_size=None): # Read entire response for wav file
                if first:
                    end = time.perf_counter()
                    logger.info(f"[Tacotron] Time to first chunk: {end-start}s")
                    first = False
                if chunk and self.state==State.RUNNING:
                    yield chunk
        except Exception as e:
            logger.exception('[Tacotron] ✗ Exception during TTS generation')
        finally:
            # Properly close file handle if opened
            if file_handle:
                try:
                    file_handle.close()
                    logger.debug('[Tacotron] Reference audio file closed')
                except Exception as e:
                    logger.warning(f'[Tacotron] Failed to close reference audio file: {e}')

    def stream_tts(self,audio_stream,msg):
        text,textevent = msg
        first = True
        # Tacotron returns a complete WAV file, not streaming chunks
        audio_data = b''
        for chunk in audio_stream:
            if chunk is not None and len(chunk) > 0:
                audio_data += chunk

        if len(audio_data) > 0:
            try:
                # Read WAV file from bytes
                byte_stream = BytesIO(audio_data)
                stream, sample_rate = sf.read(byte_stream)
                stream = stream.astype(np.float32)

                # Handle multi-channel audio
                if stream.ndim > 1:
                    stream = stream[:, 0]

                # Resample if needed
                if sample_rate != self.sample_rate and len(stream) > 0:
                    stream = resampy.resample(x=stream, sr_orig=sample_rate, sr_new=self.sample_rate)

                # Send audio in chunks
                streamlen = stream.shape[0]
                idx = 0
                while streamlen >= self.chunk:
                    eventpoint = None
                    if first:
                        eventpoint = {'status':'start','text':text,'msgevent':textevent}
                        first = False
                    self.parent.put_audio_frame(stream[idx:idx+self.chunk], eventpoint)
                    streamlen -= self.chunk
                    idx += self.chunk

                # 修复：处理最后不足一个chunk的音频数据（防止音频被丢弃）
                if streamlen > 0:
                    # 有剩余音频数据，填充到完整chunk大小后发送
                    remaining_audio = stream[idx:]
                    padding = np.zeros(self.chunk - len(remaining_audio), dtype=np.float32)
                    final_chunk = np.concatenate([remaining_audio, padding])
                    eventpoint = {'status':'end','text':text,'msgevent':textevent}
                    self.parent.put_audio_frame(final_chunk, eventpoint)
                    logger.info(f'[Tacotron] Sent final audio chunk with {len(remaining_audio)} samples (padded to {self.chunk})')
                else:
                    # 所有数据已发送完毕
                    eventpoint = {'status':'end','text':text,'msgevent':textevent}
                    self.parent.put_audio_frame(np.zeros(self.chunk,np.float32),eventpoint)
                    logger.info(f'[Tacotron] ✓ TTS generation complete for text: {text[:50]}...')
            except Exception as e:
                logger.exception('tacotron stream_tts error')
                # 异常时仍然发送结束信号
                eventpoint = {'status':'end','text':text,'msgevent':textevent}
                self.parent.put_audio_frame(np.zeros(self.chunk,np.float32),eventpoint)
        else:
            # 没有收到音频数据
            logger.warning(f'[Tacotron] No audio data received for text: {text[:50]}...')
            eventpoint = {'status':'end','text':text,'msgevent':textevent}
            self.parent.put_audio_frame(np.zeros(self.chunk,np.float32),eventpoint)

###########################################################################################

class XTTS(BaseTTS):
    def __init__(self, opt, parent):
        super().__init__(opt,parent)
        # 添加音频缓冲区，避免数据丢失
        self.audio_buffer = np.array([], dtype=np.float32)
        self.speaker = self.get_speaker(opt.REF_FILE, opt.TTS_SERVER)

    def txt_to_audio(self,msg):
        text,textevent = msg  
        self.stream_tts(
            self.xtts(
                text,
                self.speaker,
                "zh-cn", #en args.language,
                self.opt.TTS_SERVER, #"http://localhost:9000", #args.server_url,
                "20" #args.stream_chunk_size
            ),
            msg
        )

    def get_speaker(self,ref_audio,server_url):
        files = {"wav_file": ("reference.wav", open(ref_audio, "rb"))}
        response = requests.post(f"{server_url}/clone_speaker", files=files)
        return response.json()

    def xtts(self,text, speaker, language, server_url, stream_chunk_size) -> Iterator[bytes]:
        start = time.perf_counter()
        speaker["text"] = text
        speaker["language"] = language
        speaker["stream_chunk_size"] = stream_chunk_size  # you can reduce it to get faster response, but degrade quality
        try:
            res = requests.post(
                f"{server_url}/tts_stream",
                json=speaker,
                stream=True,
            )
            end = time.perf_counter()
            logger.info(f"xtts Time to make POST: {end-start}s")

            if res.status_code != 200:
                print("Error:", res.text)
                return

            first = True
        
            for chunk in res.iter_content(chunk_size=9600): #24K*20ms*2
                if first:
                    end = time.perf_counter()
                    logger.info(f"xtts Time to first chunk: {end-start}s")
                    first = False
                if chunk:
                    yield chunk
        except Exception as e:
            print(e)
    
    def stream_tts(self,audio_stream,msg):
        text,textevent = msg
        first = True
        
        # 重置缓冲区
        self.audio_buffer = np.array([], dtype=np.float32)
        
        for chunk in audio_stream:
            if chunk is not None and len(chunk)>0:          
                stream = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32767
                stream = resampy.resample(x=stream, sr_orig=24000, sr_new=self.sample_rate)
                
                # 将新数据加入缓冲区
                self.audio_buffer = np.concatenate([self.audio_buffer, stream])
                
                # 发送完整的chunk
                idx = 0
                while len(self.audio_buffer) >= self.chunk and self.state == State.RUNNING:
                    eventpoint=None
                    if first:
                        eventpoint={'status':'start','text':text,'msgevent':textevent}
                        first = False
                    # 提取一个chunk并发送
                    chunk_to_send = self.audio_buffer[:self.chunk]
                    self.parent.put_audio_frame(chunk_to_send, eventpoint)
                    # 移除已发送的数据
                    self.audio_buffer = self.audio_buffer[self.chunk:]
                    idx += 1
        
        # 处理缓冲区中剩余的音频（重要：避免数据丢失）
        if len(self.audio_buffer) > 0:
            # 填充到chunk大小
            padding = np.zeros(self.chunk - len(self.audio_buffer), dtype=np.float32)
            final_chunk = np.concatenate([self.audio_buffer, padding])
            eventpoint={'status':'end','text':text,'msgevent':textevent}
            self.parent.put_audio_frame(final_chunk, eventpoint)
            self.audio_buffer = np.array([], dtype=np.float32)
        else:
            # 发送结束信号
            eventpoint={'status':'end','text':text,'msgevent':textevent}
            self.parent.put_audio_frame(np.zeros(self.chunk,np.float32),eventpoint)  