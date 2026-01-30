"""
优化版API接口 - 使用异步降延迟的工作流

启动方式：
python api_interface_optimized.py

对比测试：
curl -X POST http://localhost:8610/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "session_id": 1, "input": "What is AI?"}'
"""

from flask import Flask, request, jsonify, Response
from ai_assistant_optimized import (
    create_optimized_workflow,
    AssistantState,
    benchmark_comparison
)
import asyncio
import json
from datetime import datetime
import nest_asyncio
import threading
import queue
import logging
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

nest_asyncio.apply()
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)


@app.route('/chat/stream', methods=['POST'])
def chat_stream_optimized():
    """优化版流式聊天接口 - 降延迟"""
    try:
        data = request.get_json()
        
        # 验证字段
        required_fields = ['user_id', 'session_id', 'input']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        user_id = data['user_id']
        session_id = data['session_id']
        input_text = data['input']
        model = data.get('model', "mistral-nemo:12b-instruct-2407-fp16")
        
        logging.info(f" Optimized request - User: {user_id}, Session: {session_id}")
        logging.info(f"   Query: {input_text}")
        
        # 创建输入状态
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
            "rewritten_query": "",
            "final_response": "",
            "response_chunks": [],
            "sources": []
        }
        
        def generate_stream():
            q = queue.Queue()
            
            async def async_worker():
                try:
                    async with AsyncSqliteSaver.from_conn_string("checkpoints_optimized.db") as checkpointer:
                        final_response = ""
                        
                        # 使用优化的工作流
                        builder = create_optimized_workflow()
                        app_workflow = builder.compile(checkpointer=checkpointer)
                        
                        # 记录开始时间
                        request_start = asyncio.get_event_loop().time()
                        first_chunk_time = None
                        
                        async for event in app_workflow.astream(
                            inputs,
                            config={"configurable": {"thread_id": session_id}},
                            stream_mode=["custom"]
                        ):
                            chunk_data = {
                                "chunk": event[1]['chunk'],
                                "status": "streaming",
                                "timestamp": datetime.now().isoformat(),
                            }
                            
                            # 记录首字延迟
                            if first_chunk_time is None:
                                first_chunk_time = asyncio.get_event_loop().time()
                                ttft = first_chunk_time - request_start
                                logging.info(f" Time to First Token: {ttft:.3f}s")
                            
                            final_response += chunk_data['chunk']
                            q.put(f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n".encode('utf-8'))
                        
                        # 完成信号
                        total_time = asyncio.get_event_loop().time() - request_start
                        logging.info(f" Request completed in {total_time:.3f}s")
                        
                        q.put(f"data: {json.dumps({
                            'status': 'finished',
                            'timestamp': datetime.now().isoformat(),
                            'total_time': f"{total_time:.3f}s",
                            'ttft': f"{(first_chunk_time - request_start) if first_chunk_time else 0:.3f}s"
                        }, ensure_ascii=False)}\n\n".encode('utf-8'))
                        
                except Exception as e:
                    logging.error(f"Stream error: {e}")
                    import traceback
                    traceback.print_exc()
                    q.put(f"data: {json.dumps({
                        'status': 'error',
                        'error': str(e)
                    }, ensure_ascii=False)}\n\n".encode('utf-8'))
                finally:
                    q.put(None)
            
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
        logging.error(f"Request error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/benchmark', methods=['POST'])
def run_benchmark():
    """运行性能对比测试"""
    try:
        data = request.get_json()
        question = data.get('question', 'What is machine learning?')
        
        # 在后台运行benchmark
        def run_async_benchmark():
            asyncio.run(benchmark_comparison(question))
        
        threading.Thread(target=run_async_benchmark, daemon=True).start()
        
        return jsonify({
            'status': 'benchmark started',
            'question': question,
            'note': 'Check console for results'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'version': 'optimized',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/stats', methods=['GET'])
def stats():
    """显示优化统计"""
    from ai_assistant_optimized import rag_cache
    
    return jsonify({
        'rag_cache_enabled': rag_cache.enabled,
        'optimizations': [
            'Parallel classification and RAG retrieval',
            'Async safety check (non-blocking)',
            'Fast query rewrite (rule-based)',
            'RAG result caching'
        ],
        'expected_improvement': '50-70% latency reduction',
        'target_ttft': '< 1.0s'
    })


if __name__ == '__main__':
    import sys
    import os
    # 导入统一端口配置
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from scripts.ports_config import LLM_PORT
    
    # 优先使用命令行参数，否则使用统一配置
    port = int(sys.argv[1]) if len(sys.argv) > 1 else LLM_PORT
    
    print("\n" + "="*70)
    print(" Starting OPTIMIZED LLM Service")
    print("="*70)
    print(f"Port: {port}")
    print("Optimizations:")
    print("   Parallel RAG and classification")
    print("   Async safety check")
    print("   Fast query rewrite")
    print("   RAG caching")
    print("\nEndpoints:")
    print("  POST /chat/stream  - Optimized streaming chat")
    print("  POST /benchmark    - Run performance comparison")
    print("  GET  /health       - Health check")
    print("  GET  /stats        - Optimization statistics")
    print("="*70 + "\n")
    
    app.run(debug=False, host='0.0.0.0', port=port)

