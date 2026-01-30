import os, sys
import logging
pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

if pkg_root not in sys.path:
    sys.path.insert(0, pkg_root)

from flask import Flask,request,jsonify
from pymilvus import Collection
from rag.multimodal_kb.kb_manager import KnowledgeBaseManager
from rag.multimodal_kb.retriever import CompositeRetriever

LOG_PATH = os.path.join(os.path.dirname(__file__), 'app.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_PATH, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


app = Flask(__name__)
TEMP_DIR = "/home/jialu/workspace/jialu/tmp"

@app.route('/user/upload', methods=['POST'])
def user_upload():
    user_id = request.form.get('user_id')
    f = request.files.get('file')
    if not user_id or not f:
        logger.warning('Missing user_id or file in request')
        return jsonify({
            'error': True,
            'message': 'Request must include both user_id and file'
        }), 400
    
    tmp_dir  = f"{TEMP_DIR}/{user_id}"
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_path = os.path.join(tmp_dir, f.filename)

    try:
        # Save the uploaded file
      f.save(tmp_path)
      logger.info(f"Saved file for user {user_id} to {tmp_path}")
  
      kb_manager = KnowledgeBaseManager()
      kb_manager.ensure_personal_collection(user_id=user_id)
      ingestion_information = kb_manager.ingest_to_collection(tmp_path,is_admin=False)

      logger.info(f"Successfully ingested file {tmp_path}: {ingestion_information}")
    
      return jsonify({
            'admin': False,
            'user_id': user_id,
            **ingestion_information
      }), 200
    
    except Exception as exc:
        logger.exception(f"Error uploading file for user {user_id}")
        return jsonify({
            'error': True,
            'message': 'File upload or processing failed, please try again later',
            'detail': str(exc)
        }), 500

@app.route('/user/delete', methods=['POST'])
def user_delete():
    user_id = request.form.get('user_id')
    source = request.form.get('source_name')

    if not user_id or not source:
        logger.warning('Missing user_id or source_name in request')
        return jsonify({
            'error': True,
            'message': 'Request must include both user_id and source_name'
        }), 400
    

    try:
        # Ensure the user's personal collection exists
        kb_manager = KnowledgeBaseManager()
        kb_manager.ensure_personal_collection(user_id=user_id)

        # Perform the deletion
        deleted_page_embs, deleted_chunks = kb_manager.delete_from_user_collection(user_id, source)
        logger.info(
            f"Deleted {deleted_page_embs} page embeddings and {deleted_chunks} chunks "
            f"for user {user_id}, source {source}"
        )

        return jsonify({
            'deleted_page_embs': deleted_page_embs,
            'deleted_chunks': deleted_chunks
        }), 200

    except Exception as exc:
        logger.exception(f"Error deleting data for user {user_id}, source {source}")
        return jsonify({
            'error': True,
            'message': 'Deletion failed, please try again later',
            'detail': str(exc)
        }), 500

@app.route('/admin/upload', methods=['POST'])
def admin_upload():
    f = request.files.get('file')

    if not f:
      logger.warning('Missing file in request')
      return jsonify({
          'error': True,
          'message': 'Request must include file'
      }), 400

    tmp_dir = os.path.join(TEMP_DIR, 'admin')
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_path = os.path.join(tmp_dir, f.filename)
    
    try:
      f.save(tmp_path)
      logger.info(f"Saved public file to {tmp_path}")

      kb_manager = KnowledgeBaseManager()
      kb_manager.ensure_public_collection()
      ingestion_information = kb_manager.ingest_to_collection(tmp_path,is_admin=True)
      
      logger.info(f"Successfully ingested public file {tmp_path}: {ingestion_information}")

      return jsonify({
          'admin': True,
          **ingestion_information
      }), 200
    
    except Exception as exc:
        logger.exception(f"Error uploading public file {f.filename}")
        return jsonify({
            'error': True,
            'message': 'Public file upload or processing failed, please try again later',
            'detail': str(exc)
        }), 500

@app.route('/admin/delete', methods=['POST'])
def admin_delete():
    source = request.form.get('source_name')

    if not source:
        logger.warning('Missing source_name in request')
        return jsonify({
            'error': True,
            'message': 'Request must include source_name'
        }), 400
    

    try:
        kb_manager = KnowledgeBaseManager()
        kb_manager.ensure_public_collection()

        deleted_page_embs, deleted_chunks = kb_manager.delete_from_public_collection(source)
        logger.info(
            f"Deleted {deleted_page_embs} page embeddings and {deleted_chunks} chunks "
            f"for source {source} in public KB"
        )

        return jsonify({
            'deleted_page_embs': deleted_page_embs,
            'deleted_chunks': deleted_chunks
        }), 200

    except Exception as exc:
        logger.exception(f"Error deleting data for source {source} in public KB")
        return jsonify({
            'error': True,
            'message': 'Deletion failed, please try again later',
            'detail': str(exc)
        }), 500

@app.route("/retriever", methods=["POST"])
def retrieve():
    data = request.get_json()
    question   = data.get('question')
    user_id    = data.get('user_id')
    personal_k = data.get('personal_k')
    public_k   = data.get('public_k')
    final_k    = data.get('final_k')
    threshold  = data.get('threshold', None)

    # Validate required parameters
    if not question or user_id is None or personal_k is None \
       or public_k is None or final_k is None:
        logger.warning(
            'Missing retrieval parameters: question, user_id, '
            'personal_k, public_k, and final_k are all required'
        )
        return jsonify({
            'error': True,
            'message': (
                'Request must include question, user_id, '
                'personal_k, public_k, and final_k'
            )
        }), 400
    
    try:
        # Perform retrieval
        kb_manager = KnowledgeBaseManager()
        kb_manager.ensure_personal_collection(user_id)
        retriever = CompositeRetriever(
            kb_manager, user_id
        )
        hits = retriever.chunk_retrieve_with_reranker(question,personal_k,public_k,final_k)
        logger.info(
            f"Retrieval for user {user_id!r} question {question!r}: "
            f"{len(hits)} hits"
        )
        return jsonify({
            'hits':     hits
        }), 200

    except Exception as exc:
        logger.exception(
            f"Error during retrieval for user {user_id!r}, question {question!r}"
        )
        return jsonify({
            'error': True,
            'message': 'Retrieval failed, please try again later',
            'detail': str(exc)
        }), 500

@app.route("/multimodal_retriever", methods=["POST"])
def multimodal_retrieve():
    data = request.get_json()
    question   = data.get('question')
    user_id    = data.get('user_id')
    personal_k = data.get('personal_k')
    public_k   = data.get('public_k')
    final_k    = data.get('final_k')

    # Validate required parameters
    if not question or user_id is None or personal_k is None \
       or public_k is None or final_k is None:
        logger.warning(
            'Missing retrieval parameters: question, user_id, '
            'personal_k, public_k, and final_k are all required'
        )
        return jsonify({
            'error': True,
            'message': (
                'Request must include question, user_id, '
                'personal_k, public_k, and final_k'
            )
        }), 400
    
    try:
        # Perform retrieval
        kb_manager = KnowledgeBaseManager()
        retriever = CompositeRetriever(
            kb_manager, user_id
        )
        hits,img_path = retriever.cascade_retrieve(question,alpha=0.6,personal_k=personal_k,public_k=public_k,final_chunk_k=final_k)
        logger.info(
            f"Retrieval for user {user_id!r} question {question!r}: "
            f"{len(hits)} hits, img_path = {img_path}"
        )
        return jsonify({
            'hits':     hits,
            'img_path':     img_path
        }), 200

    except Exception as exc:
        logger.exception(
            f"Error during retrieval for user {user_id!r}, question {question!r}"
        )
        return jsonify({
            'error': True,
            'message': 'Retrieval failed, please try again later',
            'detail': str(exc)
        }), 500

@app.route("/api/users")
def get_users():
    try:
        kb_manager = KnowledgeBaseManager()
        user_ids = kb_manager.get_all_user_ids()
        logger.info(f"Retrieved {len(user_ids)} user IDs")
        return jsonify({
            'users': user_ids
        }), 200

    except Exception as exc:
        logger.exception("Error retrieving user IDs")
        return jsonify({
            'error': True,
            'message': 'Failed to retrieve user list, please try again later',
            'detail': str(exc)
        }), 500

@app.route("/api/user_files")
def get_user_file_info():
    user_id = request.args.get("user_id")
    if not user_id:
        logger.warning("Missing user_id in request for user files")
        return jsonify({
            'error': True,
            'message': 'Request must include user_id'
        }), 400

    try:
        kb_manager = KnowledgeBaseManager()
        kb_manager.ensure_personal_collection(user_id=user_id)
        files = kb_manager.get_user_files()
        logger.info(f"Retrieved {len(files)} files for user {user_id}")
        return jsonify({
            'files': files
        }), 200

    except Exception as exc:
        logger.exception(f"Error retrieving files for user {user_id}")
        return jsonify({
            'error': True,
            'message': 'Failed to retrieve user files, please try again later',
            'detail': str(exc)
        }), 500


@app.route("/api/public_files")
def list_public_files():
    try:
      kb_manager = KnowledgeBaseManager()
      kb_manager.ensure_public_collection()
      files = kb_manager.get_public_files()

      logger.info(f"Retrieved {len(files)} public files")
      return jsonify({
          'files': files
      }), 200

    except Exception as exc:
        logger.exception("Error retrieving public files")
        return jsonify({
            'error': True,
            'message': 'Failed to retrieve public files, please try again later',
            'detail': str(exc)
        }), 500
   
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=9090,
        use_reloader=False
    )
