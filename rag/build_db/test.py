from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import requests


# 1. load pre-trained model
embedder = SentenceTransformer('all-MiniLM-L6-v2')

# 2. assume docs
docs = ["COMP9331 is the best course in the world.", "UNSW is the best school in Sydney.", "H19C is the most powerful team."]

# 3. embedding
embeddings = embedder.encode(docs, convert_to_numpy=True)

# 4. faiss indexing
index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings)


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

def rag_ask(query, top_k=3):
    # 1. query embedding
    q_emb = embedder.encode([query], convert_to_numpy=True)
    # 2. retrieval
    D, I = index.search(q_emb, top_k)
    context = "\n".join([docs[i] for i in I[0]])
    # 3. construct prompt
    prompt = f"given data：\n{context}\n\nuser question：{query}\n\nPlease answer in detail based on the materials.："
    # 4. Ollama
    return ollama_chat(prompt)

from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/ask", methods=["POST"])
def ask():
    print("request received")
    data = request.get_json()
    question = data.get("question")
    answer = rag_ask(question)
    return jsonify({"answer": answer})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8100)