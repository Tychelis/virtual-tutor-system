import os, sys
pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

if pkg_root not in sys.path:
    sys.path.insert(0, pkg_root)
from flask import Flask,request,jsonify
from rag.milvus_kb.client_manager import client,COLLECTION_PREFIX
from rag.milvus_kb.storage import ingest_public_file,ingest_user_file,delete_public_file,delete_user_file
from rag.milvus_kb.retriever import CompositeRetriever
from rag.milvus_kb.embedding import embed_texts
from rag.milvus_kb.qa import rag_ask
from rag.milvus_kb.check_kb import get_user_files,get_all_user_ids,get_public_files

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
    file_id,count = ingest_user_file(client,user_id, tmp_path)
    print("File uploaded")
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
    # os.remove(tmp_path)
    delete_count = delete_user_file(client,user_id,f"{user_id}_{source}")
    print(f"{source} deleted")
    return jsonify({'deleted_chunks': delete_count})

@app.route('/admin/upload', methods=['POST'])
def admin_upload():
    f = request.files['file']
    tmp_dir  = f"{TEMP_DIR}/admin"
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_path = os.path.join(tmp_dir, f.filename)
    f.save(tmp_path)
    file_id,count = ingest_public_file(client,tmp_path)
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
    # os.remove(tmp_path)
    count = delete_public_file(client,source)
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
    retriever = CompositeRetriever(client,user_id, embed_texts, personal_k, public_k,final_k)
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
    threshold = data.get("threshold",None)
    retriever = CompositeRetriever(client,user_id, embed_texts, personal_k, public_k, final_k)
    hits = retriever.retrieve(question,threshold) 
    return jsonify({"hits": hits})

@app.route("/api/users")
def get_users():
    user_ids = get_all_user_ids()
    return jsonify({"users": user_ids})

@app.route("/api/user_files")
def get_user_file_info():
    user_id = request.args.get("user_id")
    data = get_user_files(user_id)
    return jsonify({"files" : data})

@app.route("/api/public_files")
def list_public_files():
    return jsonify({"files": get_public_files()})

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=9090,
        use_reloader=False
    )