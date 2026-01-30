from flask import Flask, request, jsonify, Response, send_from_directory
from ai_assistant_final import create_assistant_workflow, AssistantState
import asyncio
import json
from datetime import datetime
import nest_asyncio
import os
import threading
import queue
import logging
import requests
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
import traceback

OLLAMA_HOST = "http://localhost:11434"

logging.basicConfig(level=logging.INFO)

app = Flask(__name__, static_folder='static')

# create global workflow instance
workflow = None


def list_running_models():
    # call /api/tags to get all models
    response = requests.get(f"{OLLAMA_HOST}/api/tags")
    response.raise_for_status()
    models = response.json().get("models", [])
    logging.info(f"models: {models}")
    return [m["name"] for m in models]
def run_model(model_name):
    # run model (lazy load)
    response = requests.post(f"{OLLAMA_HOST}/api/generate", json={"model": model_name, "prompt": "Hello"})
    full_text = ""
    logging.info(f"response: {response}")
    for line in response.iter_lines():
        # print(line)
        if line:
            chunk = json.loads(line)
            full_text += chunk.get("response", "")

            if chunk.get("done"):
                return f'load model {model_name} success'

    return f'load model {model_name} failed: {response.text}'

def unload_model(model_name):
    response = requests.post(f"{OLLAMA_HOST}/api/generate", json={"model": model_name, "keep_alive": 0})
    if response.status_code != 200:
        logging.error(f"unload model {model_name} failed: {response.text}")
    logging.info(f"unload model {model_name} success")

@app.route('/activate_model', methods=['POST'])
def activate_model():
    data = request.get_json()
    model_to_activate = data.get("model")
    logging.info(f"model_to_activate: {model_to_activate}")
    model_list = ["mistral-nemo:12b-instruct-2407-fp16","llama3.1:8b-instruct-q4_K_M"]

    if model_to_activate not in model_list:
        return jsonify({"error": "Please specify the model name to activate, e.g. {'model': 'mistral-nemo:12b-instruct-2407-fp16'}"}), 400

    try:
        running_models = list_running_models()

        # remove all models except the target model
        for model in running_models:
            if model != model_to_activate:
                unload_model(model)

        # run target model
        result = run_model(model_to_activate)
        logging.info(f"result: {result}")

        return jsonify({"message": f"Model {model_to_activate} has been activated, other models have been closed."})
    except Exception as e:
        logging.error(f"Error: {e}")
        logging.error(f"Error: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

@app.route('/chat/stream', methods=['POST'])
def chat_stream():
    """stream chat interface"""
    try:
        data = request.get_json()
        
        # validate required fields
        required_fields = ['user_id', 'session_id', 'input']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        user_id = data['user_id']
        session_id = data['session_id']
        input_text = data['input']
        model = "mistral-nemo:12b-instruct-2407-fp16"
        logging.info(f"model: {model}")
        logging.info(f"session_id: {session_id}")
        logging.info(f"user_id: {user_id}")
        # create input state
        inputs: AssistantState = {
            "user_id": user_id,
            "session_id": session_id,
            "input": input_text,
            "messages": [],
            "model": model,
            "safety_classification": "",
            "is_safe": True,
            "classification": "",
            "retrieved_docs": [],
            "search_results": [],
            "reranked_results": [],
            "final_response": "",
            "response_chunks": [],
            "sources": []
        }
        # print(f"inputs: {inputs}")
        # get workflow
        
            
        """run async workflow in thread"""
        def generate_stream():
            q = queue.Queue()
            
            async def async_worker():
                try:
                     async with AsyncSqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
                        final_response = ""
                        builder = create_assistant_workflow()
                        app_workflow = builder.compile(checkpointer=checkpointer)
                        async for event in app_workflow.astream(inputs, config={"configurable": {"thread_id": session_id}},stream_mode=["custom"]):
                            chunk_data = {
                                "chunk": event[1]['chunk'],
                                "status": "streaming",
                                "timestamp": datetime.now().isoformat(),
                            }
                            # logging.info(f"[{datetime.now().isoformat()}]chunk_data: {chunk_data}")
                            final_response += chunk_data['chunk']
                            q.put(f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n".encode('utf-8'))
            
                        # last end signal
                        logging.info(f"final_response: {final_response}")
                        q.put(f"data: {json.dumps({'status': 'finished', 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n".encode('utf-8'))
                except Exception as e:
                    q.put(f"data: {json.dumps({'status': 'error', 'error': str(e)}, ensure_ascii=False)}\n\n".encode('utf-8'))

            def run_async_in_thread():
                asyncio.run(async_worker())

            threading.Thread(target=run_async_in_thread, daemon=True).start()

            while True:
                item = q.get()
                if item is None:
                    break
                yield item
        return Response(
            generate_stream(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            direct_passthrough=True
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """health check interface"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})


if __name__ == '__main__':
    import os
    import sys
    # 导入统一端口配置
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from scripts.ports_config import LLM_PORT_ORIGINAL
    
    app.run(debug=True, host='0.0.0.0', port=LLM_PORT_ORIGINAL) 