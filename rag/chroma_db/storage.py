import os
import uuid
from langchain.document_loaders import PyPDFLoader, Docx2txtLoader,TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from rag.chroma_db.client_manager import get_public_collection,get_user_collection

def _load_and_parse(
        file_path:str,
        chunk_size = 1000,
        chunk_overlap = 200,
):
    # file_id = str(uuid.uuid4())
    filename = os.path.basename(file_path)

    #will be seperated to parse 
    ext = os.path.splitext(filename)[1].lower()
    if ext == '.pdf':
        loader = PyPDFLoader(file_path)
    elif ext in ('.docx', '.doc'):
        loader = Docx2txtLoader(file_path)
    else:
        loader = TextLoader(file_path, encoding='utf8')

    #chunk(parse)
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, 
        chunk_overlap=chunk_overlap)
    chunks = splitter.split_documents(docs)
    return chunks

def _ingest_to_collection(collection, chunks, file_path,file_name: str ):
    file_id = str(uuid.uuid4())
    texts = [chunk.page_content for chunk in chunks]
    ids = [str(uuid.uuid4()) for _ in texts]

    metadatas = [
        {
            "page":       chunk.metadata.get("page"),
            "page_label": chunk.metadata.get("page_label"),
            "file_id":    file_id,
            "source":     file_name,
            "source_path":  file_path,
            "chunk_index": idx,
        }
        for idx, chunk in enumerate(chunks)
    ]
    # coll = client.get_collection(collection_name)
    collection.add(documents=texts, ids=ids, metadatas=metadatas)
    # client.persist()
    return file_id,len(chunks)

def ingest_user_file(user_id: str, file_path: str):
    """Ingest a user file into the user's collection."""
    chunks = _load_and_parse(file_path)
    prefix = os.path.basename(file_path)
    collection = get_user_collection(user_id)
    return _ingest_to_collection(collection, chunks,file_path, prefix)

def ingest_public_file(file_path: str):
    """Ingest a user file into the user's collection."""
    chunks = _load_and_parse(file_path)
    prefix = os.path.basename(file_path)
    collection = get_public_collection()
    return _ingest_to_collection(collection, chunks, file_path,prefix)

def _delete_by_name(collection,source_name) -> int:
    original_count = collection.count()
    filter_cond = {"source": source_name}
    collection.delete(where=filter_cond)
    current_count = collection.count()
    deleted_count = original_count-current_count
    print("file deleted")
    return deleted_count

def delete_user_file_by_name(user_id: str, source_name: str) -> int:
    # client = get_user_client(user_id)
    # collection_name = f"user_kb_{user_id}"
    collection = get_user_collection(user_id)
    return _delete_by_name(collection, source_name)

def delete_public_file_by_name(source_name: str) -> int:
    # client = get_public_client()
    # collection_name = "public_kb"
    collection = get_public_collection()
    return _delete_by_name(collection, source_name)
