import os
import uuid
from rag.milvus_kb.embedding import embed_texts
from rag.milvus_kb.client_manager import COLLECTION_PREFIX,load_public_collection,load_user_collection
from rag.milvus_kb.data_parser import get_chunks_from_pdf

def _load_and_parse(file_path):
    chunks = get_chunks_from_pdf(file_path)
    return chunks

def _ingest_to_collection(client,collection_name, chunks, source_name: str):
    file_id = str(uuid.uuid4())
    texts = [chunk.page_content for chunk in chunks]
    embeddings = embed_texts(texts)  
    ids = [None] * len(embeddings)

    data = [
        {
            "text":         chunk.page_content,
            "embedding":    embeddings[idx],
            "file_id":      file_id,
            "source":       source_name,
            "page":         chunk.metadata.get("page"),
            "chunk_index":  idx

        }
        for idx,chunk in enumerate(chunks)
    ]
    client.insert(collection_name=collection_name,data=data)
    return file_id, len(chunks)

def _delete_from_collection(client,collection_name,source_name):
    res = client.delete(collection_name=collection_name,filter=f'source == "{source_name}"')
    return len(res)

def ingest_user_file(client,user_id: str, file_path: str):
    chunks = _load_and_parse(file_path)
    name = f"{COLLECTION_PREFIX}user_{user_id}"
    load_user_collection(user_id)
    return _ingest_to_collection(client,name, chunks, os.path.basename(file_path))

def ingest_public_file(client,file_path: str):
    chunks = _load_and_parse(file_path)
    name = f"{COLLECTION_PREFIX}admin_public"
    load_public_collection()
    return _ingest_to_collection(client,name, chunks, os.path.basename(file_path))

def delete_user_file(client,user_id: str, source_name: str) -> int:
    name = f"{COLLECTION_PREFIX}user_{user_id}"
    return _delete_from_collection(client,name,source_name)

def delete_public_file(client,source_name: str) -> int:
    name = f"{COLLECTION_PREFIX}admin_public"
    return _delete_from_collection(client,name,source_name)
