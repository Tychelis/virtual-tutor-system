import os
from pymilvus import connections, utility, Collection, CollectionSchema, FieldSchema, DataType, MilvusClient
from rag.milvus_kb.config import EMBEDDED_DB_PATH,EMBED_DIM

# MODE = os.getenv("MILVUS_MODE", "embedded")  # "embedded" 或 "server"
MODE = "embedded"
# MILVUS_HOST = os.getenv("MILVUS_HOST", "127.0.0.1")
# MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")
# EMBEDDED_DB_PATH = os.getenv("MILVUS_EMBEDDED_PATH", "/home/jialu/workspace/jialu/capstone-project-25t2-9900-h16c-bread1/rag/milvus_kb/KB/milvus_test.db")
# EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", 384))
COLLECTION_PREFIX = os.getenv("MILVUS_DB_PREFIX", "kb_")

print(EMBEDDED_DB_PATH)
client = MilvusClient(EMBEDDED_DB_PATH)
print(client.list_collections())
_fields = [
    FieldSchema("id",        DataType.INT64,        is_primary=True, auto_id=True),
    FieldSchema("text",      DataType.VARCHAR,      max_length=4096),
    FieldSchema("embedding", DataType.FLOAT_VECTOR, dim=EMBED_DIM),
    FieldSchema("file_id",   DataType.VARCHAR,      max_length=64),
    FieldSchema("source",    DataType.VARCHAR,      max_length=255),
    FieldSchema("page",      DataType.INT32),
    FieldSchema("chunk_index", DataType.INT32),
]
_schema = CollectionSchema(_fields, description="RAG KB")


def _create_index(client,collection_name):
    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name = "embedding",
        index_type="FLAT",
        metric_type="COSINE",
    )
    client.create_index(
        collection_name=collection_name, 
        index_params=index_params
    )
    print("Index created!")

def create_collection(client,collection_name):
    client.create_collection(collection_name=collection_name,schema = _schema)
    _create_index(client,collection_name)
    print(f"Collection {collection_name} created!")

def load_user_collection(user_id:str):
    name = f"{COLLECTION_PREFIX}user_{user_id}"
    if not client.has_collection(name):
        create_collection(client,collection_name=name)
    client.load_collection(name,schema = _schema)

def load_public_collection():
    name = f"{COLLECTION_PREFIX}admin_public"
    if not client.has_collection(name):
        create_collection(client,collection_name=name)
    client.load_collection(name,schema = _schema)

# def release