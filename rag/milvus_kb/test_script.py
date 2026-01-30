import os, sys
pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

if pkg_root not in sys.path:
    sys.path.insert(0, pkg_root)

from rag.milvus_kb.client_manager import (
    client,
    load_public_collection,
    load_user_collection
)
from rag.milvus_kb.storage import (
    ingest_public_file,
    delete_public_file,
    ingest_user_file,
    delete_user_file
)
from rag.milvus_kb.retriever import CompositeRetriever
from rag.milvus_kb.embedding import embed_texts
from rag.milvus_kb.qa import rag_ask

client.drop_collection("kb_user_test")
# file_path = "/home/jialu/workspace/jialu/materials/Week3_Application Layer (DNS, P2P, Video Streaming and CDN).pdf"
# path = "/home/jialu/workspace/jialu/materials"
# files = [os.path.join(path, f) for f in os.listdir(path)]
# for file in files:
#     print(file)
#     if file == "/home/jialu/workspace/jialu/materials/demob.pdf":
#         continue
#     ingest_public_file(client,file)
# file = "/home/jialu/workspace/jialu/materials/Course Outline & Logistics.pdf"
# print(ingest_public_file(client,file))
# # # #
# def delete_collections():
#     print(client.list_collections())
#     for col in client.list_collections():
#         client.drop_collection(col)
#     print(client.list_collections())

# delete_collections()

# ------ upload / delete file to public db ------ #
# print(client.list_collections())
# file = "/home/jialu/workspace/jialu/materials/Week3_Application Layer (DNS, P2P, Video Streaming and CDN).pdf"
# print(ingest_public_file(client,file))
# print(client.list_collections())
# res = check_collection(client,"kb_admin_public")
# print(res[0])
# stats = client.get_collection_stats("kb_admin_public")
# print("Row count:", stats["row_count"])
# description = client.describe_collection(collection_name="kb_admin_public")
# print(description)

# # print(delete_public_file(client,"Course_Intro.pdf"))

# # # ------ upload / delete file to user db ------ #

user_id = "test"
# source_name = "test_test_demob.pdf"
# print(delete_user_file(client,user_id, source_name))
# load_user_collection(user_id)
file_path = "/home/jialu/workspace/jialu/materials/Course Outline & Logistics.pdf"
print(ingest_user_file(client,user_id,file_path))
# # # # print(delete_user_file(client,user_id,"Intro_Applications.pdf"))

# # # # # # ------ retrieve from database ------#
# retriever = CompositeRetriever(client,user_id,embedding_fn=embed_texts,personal_k=10,public_k=10)
# query = "the best course in unsw"
# print(rag_ask(query,retriever,top_k=10))
