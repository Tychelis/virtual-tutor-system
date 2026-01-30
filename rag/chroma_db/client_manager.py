import os
from functools import lru_cache
import chromadb
from chromadb import Settings, DEFAULT_TENANT
from rag.chroma_db.config import CHROMA_ROOT,USER_CLIENT_CACHE,USER_COLLECTION_CACHE,EMBED_FUNCTION,METRIC
# Persistent admin client for tenant and database management
# CHROMA_ROOT = os.getenv("CHROMA_ROOT", "/home/jialu/workspace/jialu/chroma_db")
admin_client = chromadb.AdminClient(Settings(
    is_persistent=True,
    persist_directory=CHROMA_ROOT
))

# Cache size for hot-switched user clients
# USER_CLIENT_CACHE = int(os.getenv("USER_CLIENT_CACHE", 10))
# USER_COLLECTION_CACHE = int(os.getenv("USER_COLLECTION_CACHE", 10))

# EMBED_FUNCTION =DefaultEmbeddingFunction()

def get_or_create_db(user_id: str):
    db_name = f"db:{user_id}"
    try:
        admin_client.get_database(db_name)
    except Exception:
        admin_client.create_database(db_name, DEFAULT_TENANT)
    return DEFAULT_TENANT, db_name

@lru_cache(maxsize=USER_CLIENT_CACHE)
def get_user_client(user_id: str) -> chromadb.PersistentClient:
    tenant, db_name = get_or_create_db(user_id)
    return chromadb.PersistentClient(
        path=CHROMA_ROOT,
        tenant=tenant,
        database=db_name
    )

@lru_cache(maxsize=1)
def get_public_client() -> chromadb.PersistentClient:
    tenant, db_name = get_or_create_db("public_db")
    return chromadb.PersistentClient(
        path=CHROMA_ROOT,
        tenant=tenant,
        database=db_name
    )

@lru_cache(maxsize=USER_COLLECTION_CACHE)
def get_user_collection(user_id):
    client  = get_user_client(user_id)
    col_name = f"user_kb_{user_id}"
    return client.get_or_create_collection(
        name=col_name,
        embedding_function=EMBED_FUNCTION,
        configuration={
        "hnsw": {
            "space": METRIC,
        }
    }
    )

@lru_cache(maxsize=1)
def get_public_collection():
    client  = get_public_client()
    col_name = "public_kb"
    return client.get_or_create_collection(
        name=col_name,
        embedding_function=EMBED_FUNCTION,
        configuration={
        "hnsw": {
            "space": METRIC,
        }
    }
    )

