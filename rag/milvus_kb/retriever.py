from rag.milvus_kb.client_manager import (
  client,
  COLLECTION_PREFIX,
  load_public_collection,
  load_user_collection
)

class CompositeRetriever:
    def __init__(self, client,user_id: str, embedding_fn,
                 personal_k: int = 5, public_k: int = 5,final_k:int=5):
        # self.user_coll   = get_user_collection(user_id)
        # self.public_coll = get_public_collection()
        self.client = client
        self.personal_col_name = f"{COLLECTION_PREFIX}user_{user_id}"
        self.public_col_name = f"{COLLECTION_PREFIX}admin_public"
        load_user_collection(user_id)
        load_public_collection()
        self.embedding_fn = embedding_fn
        self.personal_k  = personal_k
        self.public_k    = public_k
        self.final_k = final_k

    def retrieve(self, query: str,threshold):
        q_emb = self.embedding_fn([query])[0]
        personal_hits,public_hits = [],[]

        if self.personal_col_name in self.client.list_collections():
            personal_hits = self.client.search(
                collection_name = self.personal_col_name,
                data=[q_emb],
                limit=self.personal_k,
                output_fields=["text","source","chunk_index","page"],
                search_params={"metric_type": "COSINE"}
            )

        public_hits = self.client.search(
            collection_name = self.public_col_name,
            data=[q_emb],
            limit=self.public_k,
            output_fields=["text","source","chunk_index","page"],
            search_params={"metric_type": "COSINE"}
        )

        personal_results = personal_hits[0] if personal_hits else []
        public_results  = public_hits[0]   if public_hits else []

        results = []
        for hit in personal_results:
            results.append({
                "id":        hit.id,
                "score":     hit.distance,
                "text":      hit.entity["text"],
                "source":    hit.entity["source"],
                "chunk_idx": hit.entity["chunk_index"],
                "db":        "personal"
            })
        for hit in public_results:
            results.append({
                "id":        hit.id,
                "score":     hit.distance,
                "text":      hit.entity["text"],
                "source":    hit.entity["source"],
                "chunk_idx": hit.entity["chunk_index"],
                "db":        "public"
            })

        sorted(results, key=lambda x: x["score"],reverse=True)
        results = results[:self.final_k]
        
        if threshold !=None:
            filtered_results = []
            for result in results:
                if result["score"] >= threshold:
                    filtered_results.append(result)
            results = filtered_results

        return sorted(results, key=lambda x: x["score"],reverse=True)
    
    
