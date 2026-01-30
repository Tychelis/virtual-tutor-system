from langchain.schema import Document
from langchain.llms import OpenAI
from langchain.chains.question_answering import load_qa_chain
from rag.chroma_db.retriever import CompositeRetriever
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

default_ef = DefaultEmbeddingFunction()

import requests

def ollama_chat(prompt, model="llama3.1:8b-instruct-q4_K_M"):
    url = "http://127.0.0.1:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()["response"]

def rag_ask(query: str, retriever, top_k: int = 3):
    hits = retriever.get_relevant(query) 
    print(hits)
    context_docs = [hit["text"] for hit in hits[:top_k]]
    context = "\n\n---\n\n".join(context_docs)
    
    prompt = (
        f"Given the following retrieved data:\n\n{context}\n\n"
        f"User question: {query}\n\n"
        "Please answer in detail based on the materials."
    )
    
    return ollama_chat(prompt)

# def rag_ask_by_threshold(query: str, retriever, threshold):
#     hits = retriever.get_relevant_by_threshold(query,threshold)
    
#     context_docs = [hit["text"] for hit in hits[:top_k]]
#     context = "\n\n---\n\n".join(context_docs)
    
#     prompt = (
#         f"Given the following retrieved data:\n\n{context}\n\n"
#         f"User question: {query}\n\n"
#         "Please answer in detail based on the materials."
#     )
    
#     return ollama_chat(prompt)

# embedding_fn = DefaultEmbeddingFunction()
# user_id = "alice"
# retriever = CompositeRetriever(user_id, embedding_fn, personal_k=5, public_k=5, final_k=5)

# answer = rag_ask("你想问的问题内容", retriever, top_k=5)
# print(answer)


# 
# llm = OpenAI(temperature=0)
# qa_chain = load_qa_chain(llm, chain_type="stuff")
# embedding_fn = DefaultEmbeddingFunction()

# def rag_query_with_public(user_id: str, question: str):
#     retriever = CompositeRetriever(user_id, embedding_fn,
#                                    personal_k=5, public_k=5, final_k=5)
#     hits = retriever.get_relevant(question)
    
#     docs = [
#         Document(page_content=h["text"], metadata={**h["meta"], "source": h["source"]})
#         for h in hits
#     ]
#     answer = qa_chain.run(input_documents=docs, question=question)
#     return answer
