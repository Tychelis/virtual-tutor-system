# rag/build_kb/qa.py

from langchain.schema import Document
from rag.milvus_kb.retriever import CompositeRetriever
from rag.milvus_kb.embedding import embed_texts
import requests

def ollama_chat(prompt: str,
                model: str = "llama3.1:8b-instruct-q4_K_M") -> str:
    """
    调用本地 Ollama 服务生成回复
    """
    url = "http://127.0.0.1:11434/api/generate"
    payload = {
        "model":  model,
        "prompt": prompt,
        "stream": False
    }
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    return resp.json()["response"]

def rag_ask(query: str,
            retriever,
            top_k: int = 3) -> str:

    hits = retriever.retrieve(query,None)

    fragments = []
    context_docs = [hit["text"] for hit in hits[:top_k]]
    context = "\n\n---\n\n".join(context_docs)
   
    for hit in hits[:top_k]:
        text = hit["text"]
        src  = hit.get("source", "")
        score = hit["score"]
        idx  = hit.get("chunk_index", "")
        fragments.append(f"[{src}#{idx}]\n{text}")

    context = "\n\n---\n\n".join(fragments)

    prompt = (
        f"Given the following retrieved data:\n\n{context}\n\n"
        f"User question: {query}\n\n"
        "Please answer in detail based on the materials."
    )
    return ollama_chat(prompt)
