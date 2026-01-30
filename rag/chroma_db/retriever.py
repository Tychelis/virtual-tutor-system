from rag.chroma_db.client_manager import (
  get_public_collection,
  get_user_collection
)
# from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

# default_ef = DefaultEmbeddingFunction()

class CompositeRetriever:
    def __init__(self, user_id: str, embedding_fn, 
                 personal_k: int = 5, public_k: int = 5, final_k: int = 5):
        # personal store
        # personal_client = get_user_client(user_id)
        # self.personal_col = personal_client.get_collection(name=f"user_kb_{user_id}")
        self.personal_col = get_user_collection(user_id)
        # public store 
        # public_client = get_public_client()
        # self.public_col = public_client.get_collection(name="public_kb")
        self.public_col = get_public_collection()
        #default: Sentence Transformers all-MiniLM-L6-v2
        self.embedding_fn = embedding_fn
        self.personal_k, self.public_k, self.final_k = personal_k, public_k, final_k

    def get_relevant(self, query: str,threshold):
        q_emb = self.embedding_fn([query])
        per_res = self.personal_col.query(
            query_embeddings=q_emb, n_results=self.personal_k,
            include=["documents","metadatas","distances"]
        )
        public_count   = self.public_col.count()
        pub_res = self.public_col.query(
            query_embeddings=q_emb, n_results=public_count,
            include=["documents","metadatas","distances"]
        )

        # combine
        combined = []
        for doc, meta, dist in zip(*per_res["documents"], *per_res["metadatas"], *per_res["distances"]):
            combined.append({"text": doc, "meta": meta, "dist": dist, "source": "personal"})
        for doc, meta, dist in zip(*pub_res["documents"], *pub_res["metadatas"], *pub_res["distances"]):
            combined.append({"text": doc, "meta": meta, "dist": dist, "source": "public"})

        # top final k
        combined = sorted(combined, key=lambda x: x["dist"])[: self.final_k]

        if threshold != None:
            results = []
            for instance in combined:
                if instance["dist"]<=threshold:
                    results.append(instance)
        else:
            results = combined
        return results

    def get_relevant_by_threshold(self,query,threshold,top_k=None):
        q_emb = self.embedding_fn([query])

        personal_count = self.personal_col.count()
        public_count   = self.public_col.count()

        per_docs, per_metas, per_scores = [], [], []
        if personal_count >0 :
            per_res = self.personal_col.query(
                query_embeddings=q_emb, n_results=personal_count,
                include=["documents","metadatas","distances"]
            )
            per_docs   = per_res["documents"][0]
            per_metas  = per_res["metadatas"][0]
            per_scores = per_res["distances"][0]

        pub_res = self.public_col.query(
            query_embeddings=q_emb, n_results=public_count,
            include=["documents","metadatas","distances"]
        )
        pub_docs   = pub_res["documents"][0]
        pub_metas  = pub_res["metadatas"][0]
        pub_scores = pub_res["distances"][0]

        results = []

        for doc, meta, score in zip(per_docs, per_metas, per_scores):
            if score >= threshold:
                results.append({
                    "text":   doc,
                    "page":   meta["page"],
                    "score": score,
                    "source_file": meta["source"],
                    "source_db": "personal",
                })

        for doc, meta, score in zip(pub_docs, pub_metas, pub_scores):
            if score >= threshold:
                results.append({
                    "text":   doc,
                    "page":   meta["page"],
                    "score": score,
                    "source_file": meta["source"],
                    "source_db": "public",
                })
        
        results.sort(key=lambda x: x["score"])
        if top_k != None:
            results = results[: top_k]
        return results
