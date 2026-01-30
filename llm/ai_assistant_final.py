import asyncio
import re
from typing import Annotated, List, Dict, Any, TypedDict
from langchain_tavily import TavilySearch
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_ollama import ChatOllama
import operator
from langchain_core.messages import BaseMessage
import traceback
from functools import lru_cache
from langgraph.types import StreamWriter
from langgraph.config import get_stream_writer
import logging
logging.basicConfig(level=logging.INFO)
from milvus_api_client import query_milvus_api
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.models.user import Safeguard, UserProfile


# define state type
class AssistantState(TypedDict):
    user_id: str
    session_id: str
    input: str
    messages: Annotated[List[Any], operator.add]
    model: str
    safety_classification: str
    is_safe: bool
    classification: str
    retrieved_docs: List[Dict[str, Any]]
    search_results: List[Dict[str, Any]]
    reranked_results: List[Dict[str, Any]]
    final_response: str
    sources: List[str]
    rewritten_query: str


# initialize LLM
@lru_cache(maxsize=1)
def get_llm(model:str="mistral-nemo:12b-instruct-2407-fp16"):
    return ChatOllama(
            temperature=0.4,
            disable_streaming=False,  # default is False, enable streaming
            model=model,
            base_url="http://127.0.0.1:11434"
        )

def format_messages_to_text(messages: list[BaseMessage], max_turns=5) -> str:
    try:
                        # only keep the last max_turns*2 messages (user + assistant)
        turns = messages[-max_turns*2:]
        seen = set()
        unique_questions = []

        for m in turns:
            if m.type == "human":
                norm = m.content.strip().lower()
                if norm not in seen:
                    seen.add(norm)
                    unique_questions.append(m.content)

        return unique_questions
    except Exception as e:
        logging.info(f"format_messages_to_text error: {e}")
        traceback.print_exc()
        return ""

search_tool = TavilySearch(
        max_results=5
    )

# 数据库操作函数 - 将非normal的安全分类记录到safeguard表
async def log_to_safeguard(user_id: str, input_text: str, safety_classification: str):
    """将非normal的安全分类记录到safeguard表 - 使用SQLAlchemy ORM方式"""
    try:
        # 从当前文件位置向上两级（llm目录 -> 项目根目录），然后进入backend/db
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, 'backend', 'db', 'users.db')

        # 检查数据库文件是否存在
        if not os.path.exists(db_path):
            logging.error(f"数据库文件不存在: {db_path}")
            return

        # 创建SQLAlchemy引擎 - 与backend中的配置保持一致
        engine_url = f"sqlite:///{db_path}"
        engine = create_engine(engine_url, connect_args={"check_same_thread": False})

        # 启用外键约束
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            dbapi_connection.execute('pragma foreign_keys=ON')

        # 创建会话
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        # 处理user_id格式，去除前缀并转换为整数
        user_id_str = str(user_id)
        if user_id_str.startswith('user_'):
            user_id_int = int(user_id_str.replace('user_', ''))
        else:
            try:
                user_id_int = int(user_id_str)
            except ValueError:
                # 如果无法转换为整数，使用默认值
                user_id_int = 0

        # 使用ORM查询用户信息
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id_int).first()

        # 设置username，找不到时使用默认值
        username = user_profile.username if user_profile else f"user_{user_id}"

        # 准备guardrail文本
        guardrail_text = f"{safety_classification}: {input_text}"

        # 创建Safeguard记录 - 使用ORM方式
        new_safeguard = Safeguard(
            user_id=user_id_int,
            username=username,
            guardrail=guardrail_text
        )

        # 添加到数据库并提交
        db.add(new_safeguard)
        db.commit()
        logging.info(f"Safeguard record created: user_id={user_id_int}, classification={safety_classification}")

    except Exception as e:
        logging.error(f"Error logging to safeguard: {e}")
        traceback.print_exc()
    finally:
        try:
            if db:
                db.close()
        except:
            pass

# guardrail check node
async def guardrail_check(state: AssistantState) -> AssistantState:
    """Guardrail check: filter inappropriate or non-academic requests."""
    try:
        query = state["input"]
        logging.info("enter guardrail_check")

        # --- quick rule-based filter before LLM call ---
        # Only catch obvious homework cheating attempts (combined phrases)
        homework_pattern = re.compile(r"\b(solve (this|my) (problem|question|homework)|do my (homework|assignment|exam)|give me the answer to|what is the answer to (question|problem) \d+|complete my assignment)\b", re.IGNORECASE)
        harmful_pattern = re.compile(r"\b(violence|hate|kill people|sex|porn|child abuse|weapon|bomb|suicide)\b", re.IGNORECASE)

        if harmful_pattern.search(query):
            safety_classification = "harmful"
        elif homework_pattern.search(query):
            safety_classification = "homework_request"
        else:
            # --- build LLM-based guardrail prompt ---
            guardrail_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a content classifier for a university course assistant.
Given a student's question, classify it into one of the following categories:

1. "normal" — general academic queries, clarifications, explanations of course concepts, or logistics such as assignment deadlines, grading, submission instructions, or course staff info.

2. "homework_request" — questions that ask for **direct answers or solutions** to assignments, quizzes, exams, or any assessment task. Includes phrases like "what is the answer", "solve this", "explain question 3", or "can you do my assignment".

3. "harmful" — content that is sexually explicit, violent, hateful, abusive, dangerous, or violates academic policy.

Guidelines:
- Mentioning "assignment" does NOT mean "homework_request" by default.
- Asking for details about due dates, instructions, or structure = "normal".
- Asking for answers, explanations of specific questions, or to complete the task = "homework_request".

Respond ONLY with one of the following labels: normal, homework_request, harmful. Do not add any other text."""),
                ("user", "Student question: {input}")
            ])

            # --- get LLM ---
            llm = get_llm(state["model"])

            # --- retry mechanism for async chain ---
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    chain = guardrail_prompt | llm | StrOutputParser()
                    safety_classification = await chain.ainvoke({"input": query})
                    break
                except RuntimeError as e:
                    if "Event loop is closed" in str(e) and attempt < max_retries - 1:
                        logging.warning(f"event loop error, retry {attempt + 1}")
                        await asyncio.sleep(0.1)
                        continue
                    else:
                        raise e

        # --- normalize result ---
        safety_classification = safety_classification.strip().lower()

        # --- determine safety and log if needed ---
        is_safe = safety_classification == "normal"
        if not is_safe:
            await log_to_safeguard(state["user_id"], query, safety_classification)

        logging.info(f"guardrail check result: {safety_classification} (safe: {is_safe})")

        yield {
            **state,
            "safety_classification": safety_classification,
            "is_safe": is_safe,
            "messages": []
        }

    except Exception as e:
        logging.error(f"guardrail check error: {e}")
        traceback.print_exc()
        yield {
            **state,
            "safety_classification": "unclear",
            "is_safe": False,
            "messages": []
        }

# block response node
async def block_response(state: AssistantState) -> AssistantState:
    """block inappropriate response"""
    safety_classification = state.get("safety_classification", "normal")
    logging.info(f"enter block_response")
    if safety_classification == "homework_request":
        response = "I'm here to help you understand the material, but I can't provide direct answers to assignment or exam questions. Let me know what concept you're struggling with, and I'll be happy to explain it."
    elif safety_classification == "harmful":
        response = "I'm sorry, but I can't help with that request. Please ensure your questions are appropriate and follow academic policies."
    else:
        # default fallback prompt
        response = "Sorry, your question couldn't be processed due to safety concerns. Please try rephrasing it."
    writer = get_stream_writer()
    writer({"chunk": response})
    return {
        **state,
        "final_response": response,
        "sources": [],
        "messages": [
            HumanMessage(content=state["input"]),
            AIMessage(content=response)
        ]
    }

# rewrite user query, generate suitable retrieval independent question
async def query_rewrite(state: AssistantState) -> AssistantState:
    """rewrite user query, generate suitable retrieval independent question"""
    try:
        messages = state.get("messages", [])
        user_query = state["input"]

        # extract the last 5 user questions
        history = format_messages_to_text(messages)

        logging.info(f"enter query_rewrite")
        logging.info(f"query_history: {history}")
        # build prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", 
                "You are a helpful assistant that rewrites student questions into clear, standalone queries suitable for searching a course-related knowledge base.\n\n"
                "You will be given the conversation history (from the student) and their latest message. Your task is to:\n"
                "1. ONLY use the history to resolve ambiguity or pronouns (like “this”, “that”, “how about it”).\n"
                "2. If the latest message is clearly unrelated to the previous conversation (i.e., it introduces a new topic), IGNORE the history and rewrite the latest message independently.\n"
                "3. If the latest message is a greeting, too vague, or off-topic, return it as-is without modification.\n"
                "4. Otherwise, rewrite the question into a self-contained, academically phrased query suitable for retrieval.\n"
                ),

                ("user", 
                "---\nConversation History:\n{history}\n\nLatest Student Question:\n{query}\n\n---\nRewritten Query:")
                ])
        llm = get_llm(state["model"])
        chain = prompt | llm | StrOutputParser()
        rewritten = await chain.ainvoke({"history": "\n".join(history), "query": user_query})
        rewritten = rewritten.strip()

        logging.info(f"query_rewrite result: {user_query} → {rewritten}")
        return {**state, "rewritten_query": rewritten, "messages": []}
    except Exception as e:
        logging.info(f"query_rewrite error: {e}")
        traceback.print_exc()
        return {**state, "rewritten_query": state["input"], "messages": []}

# classify node
async def classify_query(state: AssistantState) -> AssistantState:
    """classify user query, decide whether to retrieve or search"""
    try:
        query = state["rewritten_query"]
        logging.info(f"enter classify_query")
        # build classify prompt
        classify_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an intelligent assistant for a university course on Computer Networks (COMP9331 at UNSW). 

                Your task is to analyze the user's current query, along with recent message history, and determine whether answering the query requires any external knowledge retrieval. 

                You must return exactly one of the following actions:  
                1. "no_retrieval" — if the query can be fully answered using general networking knowledge or conversation context.  
                2. "need_rag" — if the query is likely related to lecture materials, assignments, uploaded files, or specific course documents.  
                3. "need_web_search" — if the query needs public real-time data like news, recent tech updates, etc.

                Important guidelines:  
                - Use "no_retrieval" for general networking concepts (e.g., OSI model, TCP/IP), protocol behaviors, or theoretical discussions.  
                - Use "need_rag" if the question relates to:
                    - course slides and lecture content  
                    - assignments and assessments  
                    - course outline and grading policy  
                    - course staff and tutors (e.g., "who is teaching", "how to contact the tutor")  
                    - anything specific to the COMP9331 course materials or documentation  
                    - anything specific to the user's personal information, uploaded files or private data
                - Use "need_web_search" for asking about current events, job opportunities, recent tech trends, real-world product specs, etc.

                Conversation history is provided to help resolve ambiguity (e.g., pronouns like “this”, “that”).  
                **If the latest query clearly introduces a new, unrelated topic, you may ignore the history and make your judgment based only on the new query.**

                Return ONLY one of the strings: no_retrieval, need_rag, or need_web_search. No explanations.
            """),
            ("user", "Previous context: {chat_history}\nUser query: {input}")
        ])  
        
        # get LLM
        llm = get_llm(state["model"])
        messages = state.get("messages", [])
 
        # execute classification - add retry mechanism
        max_retries = 3
        for attempt in range(max_retries):
            try:
                chain = classify_prompt | llm | StrOutputParser()

                chat_history = format_messages_to_text(messages)
                logging.info(f"chat_history: {chat_history}")
                classification = await chain.ainvoke({"input": query, "chat_history": chat_history})
                break  # success then break loop
            except RuntimeError as e:
                if "Event loop is closed" in str(e) and attempt < max_retries - 1:
                    print(f"classification query event loop error, retry {attempt + 1} times...")
                    await asyncio.sleep(0.1)  # short delay
                    continue
                else:
                    raise e
        
        # clean classification result (remove possible extra text)
        classification = classification.strip().lower()
        if "no_retrieval" in classification:
            classification = "no_retrieval"
        elif "need_rag" in classification:
            classification = "need_rag"
        elif "need_web_search" in classification:
            classification = "need_web_search"
        else:
            # default use RAG
            classification = "need_rag"
        
        logging.info(f"classification result: {classification}")
        
        return {
            **state,
            "classification": classification,
            "messages": []
        }
    except Exception as e:
        print(f"classification query error: {e}")
        print("stack trace:")
        traceback.print_exc()
        return {
            **state,
            "classification": "need_rag",  # default use RAG
            "messages": []
        }

# retrieve node
async def retrieve_documents(state: AssistantState) -> AssistantState:
    """retrieve related documents from external Chroma API service"""
    try:
        user_id = state["user_id"]
        rewritten_query = state["rewritten_query"]
        logging.info(f"enter retrieve_documents")
        logging.info(f"rewritten_query: {rewritten_query}")
        prompt = ChatPromptTemplate.from_messages([
        ("system", 
            "You are a query compressor. Rewrite the following academic question into a short, focused phrase for semantic retrieval. Keep it under 15 words. Do not include extra words or structure."
            ),

            ("user", 
            "Original question: {rewritten_query}\nOptimized retrieval query:"),

            ])
        llm = get_llm(state["model"])
        chain = prompt | llm | StrOutputParser()
        rag_query = await chain.ainvoke({"rewritten_query": rewritten_query})

        logging.info(f"enter retrieve_documents")
        logging.info(f"rag_query: {rag_query}")
        # call external Chroma API
        api_result = query_milvus_api(
            question=rag_query.strip(),
            user_id=user_id,
            personal_k=3,
            public_k=3,
            final_k=4,
            threshold=0.3
        )
        
        # check if API call is successful
        if "error" in api_result:
            print(f"Milvus API call failed: {api_result['error']}")
            return {
                **state,
                "retrieved_docs": [],
                "messages": []
            }
        
        # process API return results
        all_results = []
        api_results = api_result.get("hits", [])
        
        for result in api_results:
            # adjust according to the data structure returned by the API
            # assume the API returns the format containing content, source, score, etc.
            doc_result = {
                "content": result.get("text", ""),
                "source": result.get("source", "unknown"),
                "score": result.get("score", 0.3),
            }
            all_results.append(doc_result)
        
        logging.info(f"retrieved {len(all_results)} results from Milvus API")
        
        return {
            **state,
            "retrieved_docs": all_results,
            "messages": []
        }
    except Exception as e:
        print(f"retrieve documents error: {e}")
        print("stack trace:")
        traceback.print_exc()  
        return {
            **state,
            "retrieved_docs": [],
            "messages": []
        }

# external search node
async def search_external(state: AssistantState) -> AssistantState:
    """use Tavily for external search"""
    try:
        query = state["rewritten_query"]
        logging.info(f"enter search_external")
        logging.info(f"external_search_query: {query}")
        # only perform external search when no retrieved documents
        if not state.get("retrieved_docs"):
            search_results = await search_tool.ainvoke(query)
            if not isinstance(search_results, dict) or "results" not in search_results:
                print(f"Tavily search failed or returned no results: {search_results}")
                return {
                    **state,
                    "search_results": [],
                    "messages": []
                }
            # print(f"search_results: {search_results}")
            formatted_results = []
            for result in search_results["results"]:
                formatted_results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("content", ""),
                    "source": f" {result.get('url', 'unknown')}"
                })
            
            return {
                **state,
                "search_results": formatted_results,
                "messages": []
            }
        else:
            return {
                **state,
                "search_results": [],
                "messages": []
            }
    except Exception as e:
        logging.info(f"search_external error: {e}")
        logging.info("stack trace:")
        traceback.print_exc()
        return {
            **state,
            "search_results": [],
            "messages": []
        }

# rerank node
#async def rerank_results(state: AssistantState) -> AssistantState:
    """rerank retrieved results"""
    try:
        # merge all retrieved results
        all_results = []
        
        # add retrieved documents
        for doc in state.get("retrieved_docs", []):
            all_results.append({
                "content": doc["content"],
                "source": doc["source"],
                "score": doc["score"],
                "type": "retrieved"
            })
        
        # add search results
        for result in state.get("search_results", []):
            all_results.append({
                "content": result["content"],
                "source": result["source"],
                "score": 0.5,  # default score
                "type": "searched"
            })
        
        if not all_results:
            return {
                **state,
                "reranked_results": [],
                "messages": []
            }
        
        # use simple relevance sorting
        reranked = sorted(all_results, key=lambda x: x["score"], reverse=True)
        
        # only keep the top 10 most relevant results
        reranked = reranked[:3]
        logging.info(f"reranked: {reranked}")
        return {
            **state,
            "reranked_results": reranked,
            "messages": []
        }
    except Exception as e:
        print(f"rerank error: {e}")
        print("stack trace:")
        traceback.print_exc()
        return {
            **state,
            "reranked_results": [],
            "messages": []
        }

# generate response node
async def generate_response(state: AssistantState) -> AssistantState:
    """generate final response"""
    try:
        # build context
        context = ""
        sources = []
        logging.info(f"enter generate_response")
        # check if there are retrieved results
        reranked_results = state.get("retrieved_docs", []) + state.get("search_results", [])
        
        logging.info(f"input: {state['input']}")
        def format_latest_unique_qa(messages: list[BaseMessage], max_turns=5) -> str:
            turns = messages[-max_turns*2:]
            seen = set()
            qa_pairs = []

            i = len(turns) - 1
            while i >= 0:
                if turns[i].type == "ai" and i > 0 and turns[i-1].type == "human":
                    user_msg = turns[i-1]
                    norm = user_msg.content.strip().lower()
                    if norm not in seen:
                        seen.add(norm)
                        qa_pairs.append((user_msg, turns[i]))
                    i -= 2
                else:
                    i -= 1

            qa_pairs.reverse()
            
            # flatten to message list
            result = []
            for user, ai in qa_pairs:
                result.extend([user, ai])
            return result
        chat_history = format_latest_unique_qa(state.get("messages", []))
        logging.info(f"chat_history_unique: {chat_history}")
        if reranked_results:
            for result in reranked_results:
                context += f"Retrieved context: {result['content']}\nSource: {result['source']}\n\n"
                sources.append(result["source"])
        else:
            # if no retrieved results, check classification result
            classification = state.get("classification", "")
            if classification == "no_retrieval":
                context = "this is a question that can be answered directly without retrieving external information."
            else:
                context = "no relevant retrieval results found."
        logging.info(f"context: {context}")
        # build prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", 
                    """You are an intelligent assistant for a university course (e.g., COMP9331 at UNSW). Your job is to help students answer academic questions clearly and accurately.

                You will receive two types of context:
                1. Conversation history — recent multi-turn dialogue with the student. Use this only to resolve ambiguous references (e.g., 'this', 'that', 'how about it').
                2. Retrieved context — excerpts from course materials or knowledge base. This is your **primary source** of factual information.

                Guidelines:
                - Use retrieved context if it is relevant and sufficient.
                - If retrieved context is missing, unrelated, or insufficient, fall back to general knowledge and mention that clearly.
                - Do NOT rely on conversation history unless it helps resolve ambiguity in the current question.
                - Do NOT make up course-specific details unless grounded in the retrieved context.

                Respond concisely, formally, and in an academic tone.
                """),

                    ("placeholder", "{messages}"),

                    ("user", 
                    """Question:
                {input}

                Retrieved Context:
                {context}

                Your task:
                - Answer the student's question based primarily on the retrieved context.
                - If retrieved context is not helpful, fall back to general understanding and state that.
                - Do not reference or include the conversation history directly in your answer.""")
                ])
        
        # generate response - support streaming
        llm = get_llm(state["model"])
        
        
        chain = prompt | llm | StrOutputParser()
        
        # stream generate response
        final_response = ""
        writer = get_stream_writer()
        # use real streaming - add error handling
        try:
            async for chunk in chain.astream({
                "context": context,
                "input": state["input"],
                "messages": chat_history
            }):
                # print(f"[{datetime.now().isoformat()}]chunk: {chunk}")
                final_response += chunk
                writer({"chunk": chunk})
   
        except RuntimeError as e:
            if "Event loop is closed" in str(e):
                logging.info("generate_response error: event loop is closed, use fallback")
                # use non-streaming as fallback
                final_response = await chain.ainvoke({
                    "context": context,
                    "input": state["input"],
                    "messages": state["messages"]
                })
            else:
                raise e

        # 添加二次安全检查 - 检查生成的回复是否包含违反安全的内容
        safety_classification = state.get("safety_classification", "normal")
        is_safe = state.get("is_safe", True)

        # 定义违反安全的关键词模式
        homework_pattern = re.compile(r"\b(answer|solution|correct answer|the answer is|the solution is)\b", re.IGNORECASE)
        harmful_pattern = re.compile(r"\b(violence|hate|kill|sex|porn|abuse|weapon|bomb)\b", re.IGNORECASE)

        # 检查生成的回复内容
        if harmful_pattern.search(final_response):
            # 如果回复包含有害内容，将分类改为harmful
            safety_classification = "harmful"
            is_safe = False
            logging.warning(f"检测到生成内容包含有害信息: {final_response[:50]}...")
            # 记录到safeguard表
            await log_to_safeguard(state["user_id"], f"Generated response contains harmful content: {final_response[:100]}...", safety_classification)
            # 替换为安全提示
            safety_response = "I'm sorry, but I can't help with that request. Please ensure your questions are appropriate and follow academic policies."
            # 如果已经输出了内容，添加一个更正说明
            if final_response:
                correction = "\n\n[CONTENT REMOVED DUE TO SAFETY CONCERNS]\n"
                writer({"chunk": correction + safety_response})
                final_response = final_response + correction + safety_response
            else:
                writer({"chunk": safety_response})
                final_response = safety_response
        elif homework_pattern.search(final_response):
            # 如果回复包含直接答案，将分类改为homework_request
            safety_classification = "homework_request"
            is_safe = False
            logging.warning(f"检测到生成内容包含直接答案: {final_response[:50]}...")
            # 记录到safeguard表
            await log_to_safeguard(state["user_id"], f"Generated response contains direct answer: {final_response[:100]}...", safety_classification)
            # 添加教育性提示
            educational_note = "\n\n[NOTE: Instead of providing direct answers, I encourage you to understand the underlying concepts and work through problems yourself. This approach will help you build deeper knowledge and better prepare for assessments.]"
            writer({"chunk": educational_note})
            final_response = final_response + educational_note

        # add source information
        # if sources:
        #     source_chunk= f"\n\n[sources: {', '.join(set(sources))}]"
        #     writer({"chunk": source_chunk})

        yield {
            **state,
            "safety_classification": safety_classification,
            "is_safe": is_safe,
            "final_response": final_response,
            "sources": list(set(sources)),
            "messages": [
            HumanMessage(content=state["input"]),
            AIMessage(content=final_response)
        ]  # save history conversation
        }
    except Exception as e:
        logging.info(f"generate_response error: {e}")
        logging.info("stack trace:")
        traceback.print_exc()
        yield {
            **state,
            "final_response": f"sorry, there is an error when generating response: {str(e)}",
            "sources": []
        }



# route node
def route_after_guardrail(state: AssistantState) -> str:
    """decide next step according to guardrail check result"""
    classification = state.get("safety_classification", "normal")
    if classification in {"normal", "homework_request", "harmful"}:
        return classification
    return "harmful"  # fallback to safe side

def route_after_classification(state: AssistantState) -> str:
    """decide next step according to classification result"""
    classification = state.get("classification", "need_rag")
    
    if classification in ["no_retrieval", "need_rag", "need_web_search"]:
        return classification
    return "need_rag"  # fallback

def route_after_retrieval(state: AssistantState) -> str:
    """decide next step according to retrieval result"""
    if not state.get("retrieved_docs"):
        return "search_external"
    else:
        return "rerank_results"

# create workflow
def create_assistant_workflow(model:str="mistral-nemo:12b-instruct-2407-fp16"):
    """create AI assistant workflow"""
    model = model
    # create state graph
    workflow = StateGraph(AssistantState)
    
    # add nodes
    workflow.add_node("guardrail_check", guardrail_check)
    workflow.add_node("block_response", block_response)
    workflow.add_node("classify_query", classify_query)
    workflow.add_node("retrieve_documents", retrieve_documents)
    workflow.add_node("search_external", search_external)
    # workflow.add_node("rerank_results", rerank_results)
    workflow.add_node("generate_response", generate_response)
    workflow.add_node("query_rewrite", query_rewrite)

    # set edges
    workflow.add_edge(START, "guardrail_check")
    workflow.add_conditional_edges(
        "guardrail_check",
        route_after_guardrail,
        {
            "normal": "query_rewrite",
            "homework_request": "block_response",
            "harmful": "block_response"
        }
    )
    workflow.add_conditional_edges(
        "classify_query",
        route_after_classification,
        {
            "no_retrieval": "generate_response",
            "need_rag": "retrieve_documents",
            "need_web_search": "search_external"
        }
    )
    # workflow.add_conditional_edges(
    #     "retrieve_documents",
    #     route_after_retrieval,
    #     {
    #         "search_external": "search_external",
    #         "rerank_results": "rerank_results"
    #     }
    # )
    # workflow.add_edge("search_external", "rerank_results")
    # workflow.add_edge("rerank_results", "generate_response")
    workflow.add_edge("retrieve_documents", "generate_response")
    workflow.add_edge("search_external", "generate_response")
    workflow.add_edge("query_rewrite", "classify_query")    
    workflow.add_edge("generate_response", END)
    workflow.add_edge("block_response", END)
    
    return workflow

# main function
async def main():
    """main function example"""
    # create workflow
    app = create_assistant_workflow()

    graph_png = app.get_graph().draw_mermaid_png()
    with open("./langgraph_rag.png", "wb") as f:
        f.write(graph_png)
    
    # session ID, for MemorySaver
    thread_id = "session456"
    
    # first conversation
    print("=== 第一次对话 ===")
    inputs1: AssistantState = {
        "user_id": "user_123",
        "session_id": thread_id,
        "input": "what is tcp/ip model",
        "messages": [],
        "safety_classification": "",
        "is_safe": True,
        "classification": "",
        "retrieved_docs": [],
        "search_results": [],
        "reranked_results": [],
        "final_response": "",
        "sources": []
    }
    
    # execute workflow
    async for event in app.astream(inputs1, config={"configurable": {"thread_id": thread_id}},stream_mode=["custom"]):
        print(f"响应: {event[1]['chunk']}")

    
    print("\n=== second conversation ===")
    # second conversation - use the same thread_id, MemorySaver will automatically restore state
    inputs2: AssistantState = {
        "user_id": "user_123",
        "session_id": thread_id,
        "input": "in which week is the topic of this",
        "messages": [],
        "safety_classification": "",
        "is_safe": True,
        "classification": "",
        "retrieved_docs": [],
        "search_results": [],
        "reranked_results": [],
        "final_response": "",
        "sources": []
    }
    
    # execute workflow - state will automatically be restored from MemorySaver
    async for event in app.astream(inputs2, config={"configurable": {"thread_id": thread_id}},stream_mode=["custom"]):
        print(f"响应: {event[1]['chunk']}")

if __name__ == "__main__":
    asyncio.run(main()) 