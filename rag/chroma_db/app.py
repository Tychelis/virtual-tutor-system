import os, sys
pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

if pkg_root not in sys.path:
    sys.path.insert(0, pkg_root)
from flask import Flask,request,jsonify
from rag.chroma_db.storage import ingest_public_file,ingest_user_file,delete_public_file_by_name,delete_user_file_by_name
from rag.chroma_db.qa import rag_ask
from rag.chroma_db.config import EMBED_FUNCTION
from rag.chroma_db.retriever import CompositeRetriever


app = Flask(__name__)
TEMP_DIR = "/home/jialu/workspace/jialu/tmp"

@app.route('/user/upload', methods=['POST'])
def user_upload():
    user_id = request.form['user_id']
    f = request.files['file']
    tmp_dir  = f"{TEMP_DIR}/{user_id}"
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_path = os.path.join(tmp_dir, f"{user_id}_{f.filename}")
    print(tmp_path)
    f.save(tmp_path)
    file_id,count = ingest_user_file(user_id, tmp_path)
    # os.remove(tmp_path)
    return jsonify({
        'admin':False,
        'user_id': user_id,
        'file_path': tmp_path,
        'file_id': file_id,
        'chunk_count': count
    })

@app.route('/user/delete', methods=['POST'])
def user_delete():
    user_id = request.form['user_id']
    source = request.form['source_name']
    # source_name = f"{user_id}_{source}"
    tmp_dir  = f"{TEMP_DIR}/{user_id}"
    tmp_path = os.path.join(tmp_dir, f"{user_id}_{source}")
    os.remove(tmp_path)
    delete_count = delete_user_file_by_name(user_id,f"{user_id}_{source}")
    return jsonify({'deleted_chunks': delete_count})

@app.route('/admin/upload', methods=['POST'])
def admin_upload():
    f = request.files['file']
    # tmp = f"/tmp/admin_{f.filename}"
    # f.save(tmp)
    tmp_dir  = f"{TEMP_DIR}/admin"
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_path = os.path.join(tmp_dir, f.filename)
    f.save(tmp_path)
    file_id,count = ingest_public_file(tmp_path)
    return jsonify({
        'admin':True,
        'file_path': tmp_path,
        'file_id': file_id,
        'chunk_count': count
    })

@app.route('/admin/delete', methods=['POST'])
def admin_delete():
    source = request.form['source_name']
    tmp_dir  = f"{TEMP_DIR}/admin"
    tmp_path = os.path.join(tmp_dir, source)
    os.remove(tmp_path)
    count = delete_public_file_by_name(source)
    return jsonify({'deleted_chunks': count})

@app.route("/ask", methods=["POST"])
def ask():
    print("request received")
    data = request.get_json()
    question = data.get("question")
    user_id  = data.get("user_id")
    personal_k = data.get("personal_k")
    public_k= data.get("public_k")
    final_k= data.get("final_k")
    retriever = CompositeRetriever(user_id, EMBED_FUNCTION, personal_k, public_k, final_k)
    answer = rag_ask(question,retriever,final_k)
    return jsonify({"answer": answer})

@app.route("/retriever", methods=["POST"])
def retrieve():
    print("request received")
    data = request.get_json()
    question = data.get("question")
    user_id  = data.get("user_id")
    personal_k = data.get("personal_k")
    public_k= data.get("public_k")
    final_k= data.get("final_k")
    threshold = data.get("threshold")
    retriever = CompositeRetriever(user_id, EMBED_FUNCTION, personal_k, public_k, final_k)
    hits = retriever.get_relevant(question,threshold) 
    return jsonify({"hits": hits})

@app.route("/threshold_retriever", methods=["POST"])
def retrieve_by_threshold():
    print("request received")
    data = request.get_json()
    question = data.get("question")
    user_id  = data.get("user_id")
    threshold = data.get("threshold")
    top_k = data.get("top_k")
    retriever = CompositeRetriever(user_id, EMBED_FUNCTION)
    hits = retriever.get_relevant_by_threshold(question,threshold,top_k) 
    return jsonify({"hits": hits})


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=8080,
        use_reloader=False
    )