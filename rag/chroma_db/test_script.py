import os, sys
pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

if pkg_root not in sys.path:
    sys.path.insert(0, pkg_root)

from storage import (
    ingest_user_file,
    ingest_public_file,
    delete_user_file_by_name,
    delete_public_file_by_name,
)
from client_manager import (
    get_public_client,
    get_user_client,
    get_public_collection,
    get_user_collection
)
import chromadb
from retriever import CompositeRetriever
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from qa import rag_ask
from rag.chroma_db.config import EMBED_FUNCTION,CHROMA_ROOT


#check collection counts
def list_collections_for(client):
    cols = client.list_collections()
    return [col.name for col in cols]

def count_collection(collection):
    data = collection.peek(5)  
    return collection.count()

#----ingest_all_files_to_admin---#
print(CHROMA_ROOT)
path = "/home/jialu/workspace/jialu/materials"
files = [os.path.join(path, f) for f in os.listdir(path)]
# #ingest file to admin
# file_path = "/home/jialu/workspace/jialu/capstone-project-25t2-9900-h16c-bread1/rag/materials/Course_Intro.pdf"
# for file in files:
#     print(ingest_public_file(file))
   
# ---- ingest file to admin --
file_path = "/home/jialu/workspace/jialu/materials/Course_Intro.pdf"
print(ingest_public_file(file_path))
# db_list = admin_client.list_databases()

# public_client = get_public_client()
# user_client = get_user_client(user_id)
# print(public_client.__dict__)      # 底层属性，保存了 path
# # print(list_collections_for(public_client))

# collection = get_public_collection()
# user_collection = get_user_collection(user_id)
# print(count_collection(collection))



user_id = "alice"
# # # tmp_client = get_user_client(user_id)
# # # collection = tmp_client.get_or_create_collection(name=f"user_kb_{user_id}")
# # # db_list = admin_client.list_databases()
# # # print(db_list)
embedding_fn =  EMBED_FUNCTION
retriever = CompositeRetriever(user_id, embedding_fn, personal_k=5, public_k=5, final_k=5)
question = "Tutors"
threshold = None
hits = retriever.get_relevant(question,threshold)
print(hits) 
# # answer = rag_ask("Course Staff", retriever, top_k=5)
# print(answer)

# ## delete admin file
# # count collection before delete
# print("count of collection before delete:")
# print(count_collection(public_client,"public_kb"))
# print("deleting")
# source_name=  os.path.basename(file_path)
# print(delete_public_file_by_name(source_name))
# print("count of collection after delete:")
# print(count_collection(public_client,"public_kb"))

# user_id = "aaa"
# embedding_fn =  DefaultEmbeddingFunction()
# retriever = CompositeRetriever(user_id, embedding_fn, personal_k=5, public_k=5, final_k=5)
# answer = rag_ask("What is domain name system", retriever, top_k=5)
# print(answer)

#----upload_to_user_kb----#
# user_id = "alice"
# alice_client = get_user_client(user_id)
# print("before upload to alice")
# print(count_collection(alice_client,f"user_kb_{user_id}"))
# print("ingesting")
# user_chunk_ids =ingest_user_file(user_id,file_path)
# print("User ingest returned file IDs:", user_chunk_ids)
# print(count_collection(alice_client,f"user_kb_{user_id}"))

#ask
# embedding_fn =  DefaultEmbeddingFunction()
# retriever = CompositeRetriever(user_id, embedding_fn, personal_k=5, public_k=5, final_k=5)

# answer = rag_ask("Course Staff", retriever, top_k=5)
# print(answer)

#----delete_to_user_kb----#
# print("count of collection before delete:")
# print(count_collection(alice_client,f"user_kb_{user_id}"))
# print("deleting")
# source_name= os.path.basename(file_path)
# delete_user_file_by_name(user_id, source_name)
# print("count of collection after delete:")
# print(count_collection(alice_client,f"user_kb_{user_id}"))

# embedding_fn =  DefaultEmbeddingFunction()
# # retriever = CompositeRetriever(user_id, embedding_fn, personal_k=5, public_k=5, final_k=5)
# # answer = rag_ask("Course Staff", retriever, top_k=5)
# # print(answer)

# #----upload_to_another_user_kb----#
# user_id = "ben"
# ben_collection = get_user_collection(user_id)
# file_id,count =ingest_user_file(user_id, file_path)
# print(file_id)
# print(count)
# print(count_collection(ben_collection))
# retriever = CompositeRetriever(user_id, embedding_fn, personal_k=5, public_k=5, final_k=5)
# answer = rag_ask("Course Staff", retriever, top_k=5)
# print(answer)

# #----delete_from_another_user_kb----#
# print("count of collection before delete:")
# print(count_collection(ben_collection))
# print("deleting")
# source_name= os.path.basename(file_path)
# delete_user_file_by_name(user_id, source_name)
# print("count of collection after delete:")
# print(count_collection(ben_collection))



# user_id = "alice"
# print(user_id)
# retriever = CompositeRetriever(user_id, embedding_fn, personal_k=5, public_k=5, final_k=5)
# answer = rag_ask("Course Staff", retriever, top_k=5)
# print(answer)

# print("before upload to ben")
# print(count_collection(ben_client,f"user_kb_{user_id}"))
# print("ingesting")
# user_chunk_ids =ingest_user_file(user_id,file_path)
# print("User ingest returned file IDs:", user_chunk_ids)
# print(count_collection(ben_client,f"user_kb_{user_id}"))
# print(admin_client.list_databases())
