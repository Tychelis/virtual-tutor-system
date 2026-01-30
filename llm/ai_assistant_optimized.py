"""
优化版AI助手 - 异步降延迟
目标：首字延迟从 2.8s 降至 0.5-1.0s

主要优化：
1. 并行执行RAG和分类
2. 异步安全检查（不阻塞主流程）
3. 简化查询改写
4. RAG结果缓存
"""

import asyncio
import logging
import traceback
import redis
import json
import hashlib
from datetime import datetime
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# 避免导入时初始化TavilySearch，只导入需要的函数
import sys
import os
# 临时设置环境变量避免导入错误
os.environ.setdefault('TAVILY_API_KEY', 'dummy-key-for-import')

from ai_assistant_final import (
    AssistantState,
    get_llm,
    get_stream_writer,
    query_milvus_api,
    guardrail_check,
    block_response
)

logging.basicConfig(level=logging.INFO)

# ============================================================================
# RAG缓存（减少重复查询延迟）
# ============================================================================

class RAGCache:
    """RAG结果缓存"""
    
    def __init__(self):
        try:
            self.redis = redis.Redis(host='localhost', port=6379, db=2, decode_responses=False)
            self.ttl = 3600  # 1小时
            self.enabled = True
            logging.info("RAG Cache enabled")
        except:
            self.enabled = False
            logging.warning("RAG Cache disabled (Redis not available)")
    
    def get_cache_key(self, query: str, user_id: int) -> str:
        """生成缓存key"""
        content = f"{query}:{user_id}"
        return f"rag:{hashlib.md5(content.encode()).hexdigest()}"
    
    def get(self, query: str, user_id: int):
        """从缓存获取"""
        if not self.enabled:
            return None
        
        try:
            cache_key = self.get_cache_key(query, user_id)
            cached = self.redis.get(cache_key)
            if cached:
                logging.info(f" RAG Cache HIT for query: {query[:50]}...")
                return json.loads(cached)
        except Exception as e:
            logging.warning(f"Cache get error: {e}")
        
        return None
    
    def set(self, query: str, user_id: int, result):
        """存入缓存"""
        if not self.enabled:
            return
        
        try:
            cache_key = self.get_cache_key(query, user_id)
            self.redis.setex(cache_key, self.ttl, json.dumps(result))
            logging.info(f" Cached RAG result for: {query[:50]}...")
        except Exception as e:
            logging.warning(f"Cache set error: {e}")

rag_cache = RAGCache()


# ============================================================================
# 优化1：快速查询改写（规则优先，避免不必要的LLM调用）
# ============================================================================

def has_reference_words(text: str) -> bool:
    """检测是否包含指代词"""
    reference_words = [
        "it", "this", "that", "these", "those", "they", "them",
        "他", "它", "这", "那", "这些", "那些"
    ]
    text_lower = text.lower()
    return any(word in text_lower for word in reference_words)

async def fast_query_rewrite(state: AssistantState) -> AssistantState:
    """快速查询改写 - 只在必要时使用LLM"""
    input_text = state["input"]
    messages = state.get("messages", [])
    
    # 规则1：如果没有指代词且是新对话，直接返回
    if not has_reference_words(input_text):
        logging.info(" Fast path: No rewrite needed")
        return {
            "rewritten_query": input_text
        }
    
    # 规则2：如果有指代词但没有历史，也直接返回
    if not messages or len(messages) < 2:
        logging.info(" Fast path: No history for rewrite")
        return {
            "rewritten_query": input_text
        }
    
    # 只有在有指代词且有历史时才使用LLM改写
    logging.info(" Using LLM for query rewrite")
    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Rewrite the query by resolving references from conversation history. Keep it concise."),
            ("user", "History: {history}\n\nCurrent query: {query}\n\nRewritten query:")
        ])
        
        llm = get_llm(state["model"])
        chain = prompt | llm | StrOutputParser()
        
        # 只取最近2轮对话
        recent_history = "\n".join([
            f"{m.type}: {m.content}" 
            for m in messages[-4:]
        ])
        
        rewritten = await chain.ainvoke({
            "history": recent_history,
            "query": input_text
        })
        
        return {
            "rewritten_query": rewritten.strip()
        }
    except Exception as e:
        logging.error(f"Query rewrite error: {e}")
        return {
            "rewritten_query": input_text
        }


# ============================================================================
# 优化1: 简化query rewrite
# ============================================================================

# ============================================================================
# 优化3：并行RAG和分类
# ============================================================================

async def parallel_classify_and_retrieve(state: AssistantState) -> AssistantState:
    """并行执行分类和RAG检索"""
    start_time = asyncio.get_event_loop().time()
    
    user_id = state["user_id"]
    rewritten_query = state["rewritten_query"]
    
    # 检查缓存
    cached_rag = rag_cache.get(rewritten_query, user_id)
    
    # 任务1：查询分类
    async def classify():
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", """Classify the query type:
- knowledge_retrieval: needs course materials
- general_chat: general conversation
- no_retrieval: can answer directly

Output only one word."""),
                ("user", "{input}")
            ])
            
            llm = get_llm(state["model"])
            chain = prompt | llm | StrOutputParser()
            result = await chain.ainvoke({"input": rewritten_query})
            
            return result.strip().lower()
        except Exception as e:
            logging.error(f"Classification error: {e}")
            return "knowledge_retrieval"  # 默认使用RAG
    
    # 任务2：RAG检索（如果没有缓存）
    async def retrieve():
        # 使用缓存
        if cached_rag is not None:
            return cached_rag
        
        try:
            # 查询压缩
            compress_prompt = ChatPromptTemplate.from_messages([
                ("system", "Compress this question into a short search query (max 15 words). No extra words."),
                ("user", "Question: {query}\nSearch query:")
            ])
            
            llm = get_llm(state["model"])
            chain = compress_prompt | llm | StrOutputParser()
            rag_query = await chain.ainvoke({"query": rewritten_query})
            
            # Milvus检索
            logging.info(f" RAG query: {rag_query}")
            api_result = query_milvus_api(
                question=rag_query.strip(),
                user_id=user_id,
                personal_k=3,
                public_k=3,
                final_k=4,
                threshold=0.3
            )
            
            if "error" in api_result:
                logging.error(f"Milvus API error: {api_result['error']}")
                return []
            
            # 处理结果
            results = []
            for result in api_result.get("hits", []):
                results.append({
                    "content": result.get("entity", {}).get("chunk", ""),
                    "source": result.get("entity", {}).get("file_name", "unknown"),
                    "score": result.get("distance", 0)
                })
            
            # 缓存结果
            rag_cache.set(rewritten_query, user_id, results)
            
            return results
            
        except Exception as e:
            logging.error(f"RAG retrieval error: {e}")
            traceback.print_exc()
            return []
    
    # 并行执行两个任务
    logging.info(" Starting parallel classification and RAG retrieval")
    
    classify_task = asyncio.create_task(classify())
    retrieve_task = asyncio.create_task(retrieve())
    
    # 等待两个任务完成
    classification, retrieved_docs = await asyncio.gather(
        classify_task,
        retrieve_task,
        return_exceptions=True
    )
    
    # 处理异常
    if isinstance(classification, Exception):
        logging.error(f"Classification failed: {classification}")
        classification = "knowledge_retrieval"
    
    if isinstance(retrieved_docs, Exception):
        logging.error(f"Retrieval failed: {retrieved_docs}")
        retrieved_docs = []
    
    elapsed = asyncio.get_event_loop().time() - start_time
    logging.info(f" Parallel tasks completed in {elapsed:.2f}s")
    logging.info(f"   Classification: {classification}")
    logging.info(f"   Retrieved docs: {len(retrieved_docs)}")
    
    # 只返回更新的字段，避免并发冲突
    return {
        "classification": classification,
        "retrieved_docs": retrieved_docs
    }


# ============================================================================
# 优化4：流式生成（保持不变，已经很快）
# ============================================================================

async def generate_response(state: AssistantState) -> AssistantState:
    """生成响应 - 流式输出"""
    try:
        # 构建上下文
        context = ""
        sources = []
        retrieved_docs = state.get("retrieved_docs", [])
        
        if retrieved_docs:
            for doc in retrieved_docs:
                context += f"Context: {doc['content']}\nSource: {doc['source']}\n\n"
                sources.append(doc["source"])
        else:
            context = "No specific course material found. Answer based on general knowledge."
        
        # 构建提示
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an intelligent teaching assistant for university courses.
Answer student questions clearly and accurately based on the provided context.
If context is insufficient, use general knowledge and mention that.

Respond concisely and in an academic tone."""),  # 添加简洁要求
            ("user", "Question: {input}\n\nContext: {context}\n\nAnswer:")
        ])
        
        # 流式生成
        llm = get_llm(state["model"])
        chain = prompt | llm | StrOutputParser()
        
        final_response = ""
        writer = get_stream_writer()
        
        first_chunk = True
        start_time = asyncio.get_event_loop().time()
        
        async for chunk in chain.astream({
            "input": state["input"],
            "context": context
        }):
            if first_chunk:
                ttft = asyncio.get_event_loop().time() - start_time
                logging.info(f" Time to first token: {ttft:.3f}s")
                first_chunk = False
            
            final_response += chunk
            writer({"chunk": chunk})
        
        yield {
            **state,
            "final_response": final_response,
            "sources": list(set(sources)),
            "messages": [
                HumanMessage(content=state["input"]),
                AIMessage(content=final_response)
            ]
        }
        
    except Exception as e:
        logging.error(f"Response generation error: {e}")
        traceback.print_exc()
        yield {
            **state,
            "final_response": f"Sorry, there was an error: {str(e)}",
            "sources": []
        }


# ============================================================================
# 创建优化的工作流
# ============================================================================

def create_optimized_workflow():
    """创建优化的AI助手工作流"""

    workflow = StateGraph(AssistantState)

    # 添加节点
    workflow.add_node("guardrail_check", guardrail_check)    # 安全检查（同步，必须阻塞）
    workflow.add_node("block_response", block_response)       # 拦截响应
    workflow.add_node("fast_rewrite", fast_query_rewrite)     # 快速改写
    workflow.add_node("parallel_classify_retrieve", parallel_classify_and_retrieve)  # 并行
    workflow.add_node("generate", generate_response)          # 流式生成

    # 路由函数：根据安全检查结果决定下一步
    def route_after_guardrail(state: AssistantState) -> str:
        """根据安全检查结果路由"""
        classification = state.get("safety_classification", "normal")
        if classification == "normal":
            return "safe"
        else:
            return "unsafe"

    # 定义流程 - 安全检查必须在最前面
    workflow.add_edge(START, "guardrail_check")

    # 根据安全检查结果分流
    workflow.add_conditional_edges(
        "guardrail_check",
        route_after_guardrail,
        {
            "safe": "fast_rewrite",      # 安全 -> 继续正常流程
            "unsafe": "block_response"   # 不安全 -> 拦截
        }
    )

    # 拦截分支直接结束
    workflow.add_edge("block_response", END)

    # 主流程：快速改写 → 并行分类+检索 → 生成
    workflow.add_edge("fast_rewrite", "parallel_classify_retrieve")
    workflow.add_edge("parallel_classify_retrieve", "generate")
    workflow.add_edge("generate", END)

    return workflow


# ============================================================================
# 性能对比工具
# ============================================================================

async def benchmark_comparison(question: str, user_id: int = 1, session_id: int = 1):
    """对比优化前后的性能"""
    from ai_assistant_final import create_assistant_workflow
    
    print("\n" + "="*70)
    print(" Performance Benchmark: Original vs Optimized")
    print("="*70)
    
    state = {
        "user_id": user_id,
        "session_id": session_id,
        "input": question,
        "model": "mistral-nemo:12b-instruct-2407-fp16",
        "messages": [],
        "rewritten_query": "",
        "classification": "",
        "retrieved_docs": [],
        "final_response": "",
        "sources": []
    }
    
    # 测试原版
    print("\n Testing ORIGINAL workflow...")
    original_workflow = create_assistant_workflow()
    original_app = original_workflow.compile()
    
    start = asyncio.get_event_loop().time()
    async for event in original_app.astream(state):
        pass
    original_time = asyncio.get_event_loop().time() - start
    
    # 测试优化版
    print("\n Testing OPTIMIZED workflow...")
    optimized_workflow = create_optimized_workflow()
    optimized_app = optimized_workflow.compile()
    
    start = asyncio.get_event_loop().time()
    async for event in optimized_app.astream(state):
        pass
    optimized_time = asyncio.get_event_loop().time() - start
    
    # 结果对比
    improvement = ((original_time - optimized_time) / original_time) * 100
    
    print("\n" + "="*70)
    print(" Results:")
    print("="*70)
    print(f"Original workflow:  {original_time:.2f}s")
    print(f"Optimized workflow: {optimized_time:.2f}s")
    print(f"Improvement:        {improvement:.1f}% faster")
    print("="*70 + "\n")


if __name__ == "__main__":
    # 测试优化效果
    asyncio.run(benchmark_comparison(
        "What is machine learning?",
        user_id=1,
        session_id=1
    ))

