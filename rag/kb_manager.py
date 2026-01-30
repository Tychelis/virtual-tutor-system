import os
import logging
from pymilvus import connections, utility, Collection, CollectionSchema, FieldSchema, DataType, MilvusClient
from rag.config import EMBEDDED_DB_PATH,PAGE_EMBED_DIM,CHUNK_EMBED_DIM,IMG_DIR,MODE
from rag.data_parser import pdf_to_imgs
from rag.embedding import embed_images_for_page,embed_texts_for_chunks
from rag.data_parser import get_chunks_from_pdf

logging.info(EMBEDDED_DB_PATH)
client = MilvusClient(EMBEDDED_DB_PATH)
connections.connect(uri=EMBEDDED_DB_PATH)


# colpali fields
page_fields = [
    FieldSchema("id",        DataType.INT64,        is_primary=True, auto_id=True),
    FieldSchema("embedding", DataType.FLOAT_VECTOR, dim=PAGE_EMBED_DIM),
    FieldSchema("token_id",    DataType.INT16),
    FieldSchema("source_id",    DataType.VARCHAR,      max_length=255),
    FieldSchema("file_path", DataType.VARCHAR,   max_length=65535),
    FieldSchema("source_file",    DataType.VARCHAR,      max_length=255)
]

# text fields
chunk_fields = [
    FieldSchema("id",        DataType.INT64,        is_primary=True, auto_id=True),
    FieldSchema("text",      DataType.VARCHAR,      max_length=4096),
    FieldSchema("embedding", DataType.FLOAT_VECTOR, dim=CHUNK_EMBED_DIM), 
    FieldSchema("source",    DataType.VARCHAR,      max_length=255),
    FieldSchema("page_num",      DataType.INT32),
    FieldSchema("chunk_index", DataType.INT32),
]

class KnowledgeBaseManager:
    def __init__(self):
        self.client = client
        self.public_chunk_col_name = "kb_admin_public_chunk"
        self.chunk_schema = CollectionSchema(chunk_fields, description="RAG KB Chunk-level")
        self.mode = MODE
        if self.mode == 1:
            self.public_page_col_name = "kb_admin_public_page"
            self.page_schema = CollectionSchema(page_fields, description="RAG KB Page-level")

    def ensure_public_collection(self):
        self.ensure_chunk_collection(self.public_chunk_col_name)
        if self.mode == 1:
            self.ensure_page_collection(self.public_page_col_name)

    def ensure_personal_collection(self,user_id):
        self.personal_chunk_col_name = f"kb_user_{user_id}_chunk"
        self.ensure_chunk_collection(self.personal_chunk_col_name)
        if self.mode == 1:
            self.personal_page_col_name = f"kb_user_{user_id}_page"
            self.ensure_page_collection(self.personal_page_col_name)

    def _create_chunk_index(self,collection_name):
        index_params = self.client.prepare_index_params()
        index_params.add_index(
            field_name = "embedding",
            index_type="IVF_FLAT",
            metric_type="COSINE",
            params = {
                "nlist": 256
                }
        )

        self.client.create_index(
            collection_name=collection_name, 
            index_params=index_params
        )
        logging.info("Chunk level: embedding index created!")
    
    def _create_chunk_collection(self,collection_name):
        self.client.create_collection(collection_name=collection_name,schema = self.chunk_schema)
        self._create_chunk_index(collection_name)
        logging.info(f"Collection {collection_name} created!")

    def ensure_chunk_collection(self,collection_name):
        if not self.client.has_collection(collection_name):
            self._create_chunk_collection(collection_name)
        if not self.has_loaded(collection_name):
            self.client.load_collection(collection_name)
    
    def _create_page_index(self,collection_name):
        self.client.release_collection(collection_name=collection_name)
        self.client.drop_index(
            collection_name=collection_name, index_name="embedding_index"
        )

        index_params = self.client.prepare_index_params()

        # add embedding index
        index_params.add_index(
            field_name="embedding",
            index_name="embedding_index",
            index_type="IVF_FLAT",
            metric_type="COSINE",
            params = {
                "nlist": 256
            }
        )
        logging.info("Page level: Embedding index created!")

        # add scalar index
        index_params.add_index(
            field_name="source_id",
            index_name="source_index",
            index_type="INVERTED",
        )

        logging.info("Page level:Scalar index created!")

        self.client.create_index(
            collection_name=collection_name, index_params=index_params, sync=True
        )
        logging.info("Page level: index created!")

    def _create_page_collection(self,collection_name):
        self.client.create_collection(collection_name=collection_name,schema = self.page_schema)
        self._create_page_index(collection_name)
        logging.info(f"Collection {collection_name} created!")

    def ensure_page_collection(self,collection_name):
        if not self.client.has_collection(collection_name):
            self._create_page_collection(collection_name)
        if not self.has_loaded(collection_name):
            self.client.load_collection(collection_name)

    def has_loaded(self,collection_name):
        state = self.client.get_load_state(collection_name)['state'].name
        return state!='NotLoad'

    def ingest_to_collection(self,file_path,is_admin):
        ingestion_information={
            "page_collection": "",
            "chunk_collection": "",
            "ingest_file": os.path.basename(file_path),
            "page_count": None,
            "page_embs_num":None,
            "chunk_embs_num":None
        }
        chunk_info = self.ingest_to_chunk_collection(file_path,is_admin)
        ingestion_information["chunk_embs_num"] = chunk_info
        ingestion_information["chunk_collection"] = self.public_chunk_col_name if is_admin else self.personal_chunk_col_name
        if self.mode == 1:
            ingestion_information["page_collection"] = self.public_page_col_name if is_admin else self.personal_page_col_name
            if not file_path.lower().endswith((".docx", ".txt")):
                page_info = self.ingest_to_page_collection(file_path,is_admin)
                ingestion_information["page_count"]=page_info[1]
                ingestion_information["page_embs_num"] = page_info[2]
        return ingestion_information
    
    def ingest_to_page_collection(self,file_path,is_admin):
        if is_admin:
            collection_name = self.public_page_col_name
        else:
            collection_name = self.personal_page_col_name
        logging.info(f"Ingesting file to {collection_name}")
        pdf_to_imgs(file_path,IMG_DIR)
        file_name = os.path.basename(file_path)
        base_name = os.path.splitext(file_name)[0]
        save_dir = os.path.join(IMG_DIR, base_name)
        img_embeddings = embed_images_for_page(save_dir)
        img_paths = [name for name in os.listdir(save_dir)]
        count = 0
        for idx,img_path in enumerate(img_paths):
            page_id = int(img_path.split("_")[1].split(".")[0])
            page_embeddings = img_embeddings[idx].float().numpy()
            embedding_list = [emb for emb in page_embeddings]
            data = [
                {
                    "embedding": emb,
                    "token_id": j,
                    "source_id": f"{file_name}_{page_id}",
                    "file_path": img_path,
                    "source_file": file_name
                }
                for j,emb in enumerate(embedding_list)
            ]
            count+=len(data)
            self.client.insert(collection_name = collection_name,data=data)
        
        return file_name,len(img_paths),count

    def ingest_to_chunk_collection(self,file_path,is_admin):
        if is_admin:
            collection_name = self.public_chunk_col_name
        else:
            collection_name = self.personal_chunk_col_name
        logging.info(f"Ingesting file to {collection_name}")

        chunks = get_chunks_from_pdf(file_path)
        if not chunks:
            return 0
        texts = [chunk.page_content for chunk in chunks]
        chunk_embeddings = embed_texts_for_chunks(texts)
        data = [
                {
                    "text": chunk.page_content,
                    "embedding":  chunk_embeddings[idx],
                    "source":os.path.basename(file_path),
                    "page_num": chunk.metadata.get("page"),
                    "chunk_index": idx
                }
                for idx,chunk in enumerate(chunks)
            ]
        self.client.insert(collection_name=collection_name,data=data)
        return len(chunks)

    def delete_from_user_collection(self,user_id,file_name):
        self.personal_page_col_name = f"kb_user_{user_id}_page"
        self.personal_chunk_col_name = f"kb_user_{user_id}_chunk"
        deleted_page_count,deleted_chunk_count=0,0
        res_chunk = self.client.delete(collection_name=self.personal_chunk_col_name ,
                           filter=f'source == "{file_name}"')
        if isinstance(res_chunk, list):
            deleted_chunk_count = len(res_chunk)
        elif isinstance(res_chunk, dict):
            deleted_chunk_count = res_chunk['delete_count']
        if self.mode == 1:
            res_page = self.client.delete(collection_name=self.personal_page_col_name ,
                            filter=f'source_file == "{file_name}"')
            if isinstance(res_page, list):
                deleted_page_count = len(res_page)
            elif isinstance(res_chunk, dict):
                deleted_page_count = res_page['delete_count']
        return deleted_page_count,deleted_chunk_count
    
    def delete_from_public_collection(self,file_name):
        deleted_page_count,deleted_chunk_count=0,0
        res_chunk = self.client.delete(collection_name=self.public_chunk_col_name ,
                           filter=f'source == "{file_name}"')
        if isinstance(res_chunk, list):
            deleted_chunk_count = len(res_chunk)
        elif isinstance(res_chunk, dict):
            deleted_chunk_count = res_chunk['delete_count']
        if self.mode == 1:
            if not file_name.lower().endswith((".docx", ".txt")):
                res_page = self.client.delete(collection_name=self.public_page_col_name ,
                                filter=f'source_file == "{file_name}"')
                if isinstance(res_page, list):
                    deleted_page_count = len(res_page)
                elif isinstance(res_chunk, dict):
                    deleted_page_count = res_page['delete_count']
        return deleted_page_count,deleted_chunk_count
    
    def get_all_user_ids(self,prefix="kb_user_", suffix="_chunk"):
        all_collections = self.client.list_collections()
        user_ids = [
            name[len(prefix):-len(suffix)]
            for name in all_collections
            if name.startswith(prefix) and name.endswith(suffix)
        ]
        return user_ids
    
    def get_user_files(self):
        collection_name = self.personal_chunk_col_name
        print(collection_name)
        res = client.query(
            collection_name=collection_name,
            filter="",
            output_fields=["source"],
            limit=10000
        )
        file_lists = [r["source"] for r in res]
        file_lists = set(file_lists)
        return list(file_lists)
    
    def get_public_files(self):
        collection_name = self.public_chunk_col_name
        res = client.query(
            collection_name=collection_name,
            filter="",
            output_fields=["source"],
            limit=10000
        )
        file_lists = [r["source"] for r in res]
        file_lists = set(file_lists)
        return list(file_lists)

    def get_page_embedding_number(self,file,collection):
        expr =  f'source_file == "{file}"'
        logging.info(type(file))
        iterator = collection.query_iterator(
            filter = f'source_file == "{file}"',
            output_fields=["token_id", "embedding", "file_path", "source_id"],
            batch_size=1000, 
        )
        all_results = []
        while True:
            batch = iterator.next()
            if not batch:
                break
            all_results.extend(batch)
        iterator.close()

        return len(all_results),len(all_results)/1031
    
    def get_chunk_embedding_number(self,file,collection):
        iterator = collection.query_iterator(
            expr=f'source_file == "{file}"',
            output_fields=["text"],
            batch_size=1000, 
        )
        all_results = []
        while True:
            batch = iterator.next()
            if not batch:
                break
            all_results.extend(batch)
        iterator.close()

        return len(all_results)
