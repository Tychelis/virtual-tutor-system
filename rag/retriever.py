import os
import logging
import numpy as np
from rag.embedding import embed_queries_for_page,embed_queries_for_chunks
from rag.config import IMG_DIR
from sentence_transformers import CrossEncoder

class CompositeRetriever:
    def __init__(self,kb_manager,user_id):
        self.kb_manager = kb_manager
        self.mode = self.kb_manager.mode
        self.user_id = user_id
        self.personal_chunk_collection_name = f"kb_user_{user_id}_chunk"
        self.personal_page_collection_name = f"kb_user_{user_id}_page"
        self.kb_manager.ensure_chunk_collection(self.kb_manager.public_chunk_col_name)
        self.kb_manager.ensure_chunk_collection(self.personal_chunk_collection_name)
        logging.info("Chunk collections loaded")

        if self.mode == 1:
            self.kb_manager.ensure_page_collection(self.kb_manager.public_page_col_name)
            self.kb_manager.ensure_page_collection(self.personal_page_collection_name)
            logging.info("Page collections loaded")

    def page_retrieve(self,query,personal_k=50,public_k=50,combined_k=30):
        search_params={"metric_type": "COSINE"}
        query_embedding = embed_queries_for_page([query])[0].float().numpy()
        
        combined_results = []
       
        #search in admin collection
        admin_results = self.kb_manager.client.search(
            self.kb_manager.public_page_col_name,
            query_embedding,
            limit = public_k,
            search_params=search_params,
            output_fields = ["embedding","token_id","source_id"]
        )
        combined_results.extend([(r["entity"]["source_id"], self.kb_manager.public_page_col_name) for res in admin_results for r in res])
      
        #search in user collection
        user_results = self.kb_manager.client.search(
            self.personal_page_collection_name,
            query_embedding,
            limit = personal_k,
            search_params=search_params,
            output_fields = ["embedding","token_id","source_id"]
        )
        combined_results.extend([(r["entity"]["source_id"], self.personal_page_collection_name) for res in user_results for r in res])
        combined_results = list(set(combined_results))

        score_source_pairs = []
        for combined_res in combined_results:
            score_source_pairs.append(self._rerank_by_page(query_embedding,combined_res[0],combined_res[1]))
        
        score_source_pairs.sort(key=lambda x: x[0], reverse=True)
        if len(score_source_pairs) >= combined_k:
            score_source_pairs =  score_source_pairs[:combined_k]
        
        page_hits = []
        for pair in score_source_pairs:
            prefix, suffix = pair[1].rsplit("_", 1)
            page_hits.append(
                {
                    "score": pair[0],
                    "source": prefix,
                    "page_num": int(suffix)
                }
            )
        
        return page_hits
    
    def page_retrieve_by_document(self,document,query):
        search_params={"metric_type": "COSINE"}
        query_embedding = embed_queries_for_page([query])[0].float().numpy()
        
        combined_results = []
       
        #search in admin collection
        admin_results = self.kb_manager.client.search(
            self.kb_manager.public_page_col_name,
            query_embedding,
            limit = 100,
            filter= f'source_file == "{document}"',
            search_params=search_params,
            output_fields = ["embedding","token_id","source_id"]
        )
        combined_results.extend([(r["entity"]["source_id"], self.kb_manager.public_page_col_name) for res in admin_results for r in res])
      
        #search in user collection
        user_results = self.kb_manager.client.search(
            self.personal_page_collection_name,
            query_embedding,
            limit = 100,
            filter= f'source_file == "{document}"',
            search_params=search_params,
            output_fields = ["embedding","token_id","source_id"]
        )
        combined_results.extend([(r["entity"]["source_id"], self.personal_page_collection_name) for res in user_results for r in res])
        combined_results = list(set(combined_results))

        score_source_pairs = []
        for combined_res in combined_results:
            score_source_pairs.append(self._rerank_by_page(query_embedding,combined_res[0],combined_res[1]))
        
        score_source_pairs.sort(key=lambda x: x[0], reverse=True)
        if len(score_source_pairs) >= self.top_k:
            score_source_pairs =  score_source_pairs[:self.top_k]
        
        page_hits = []
        for pair in score_source_pairs:
            prefix, suffix = pair[1].rsplit("_", 1)
            page_hits.append(
                {
                    "score": pair[0],
                    "source": prefix,
                    "page_num": int(suffix)
                }
            )
        
        return page_hits

    def _rerank_by_page(self,query_embedding,source_id,collection_name):
        embs = self.kb_manager.client.query(
            collection_name = collection_name,
            filter = f'source_id == "{source_id}"',
            limit = 1000,
            output_fields = ["token_id","embedding","file_path","source_id"],
        )
        pg_embs = np.vstack([item["embedding"] for item in embs])
        score = np.dot(query_embedding,pg_embs.T).max(1).sum()
        return (score,source_id)
    
    def chunk_retrieve(self,query,personal_k,public_k,combined_k):
        query_embeddings = embed_queries_for_chunks([query])[0]

        personal_hits,public_hits = [],[]
        personal_hits = self.kb_manager.client.search(
                collection_name = self.personal_chunk_collection_name,
                data=[query_embeddings],
                limit=personal_k,
                output_fields=["text","source","page_num"],
                search_params={"metric_type": "COSINE"}
        )

        public_hits = self.kb_manager.client.search(
                collection_name = self.kb_manager.public_chunk_col_name,
                data=[query_embeddings],
                limit=public_k,
                output_fields=["text","source","page_num"],
                search_params={"metric_type": "COSINE"}
        )

        personal_results = personal_hits[0] if personal_hits else []
        public_results  = public_hits[0]   if public_hits else []

        chunk_hits = []
        for res in public_results:
            chunk_hits.append({
                "id":       res.id,
                "score":    res.distance,
                "text":     res.entity["text"],
                "source":   res.entity["source"],
                "page_num": res.entity["page_num"],
                "knowledge_base": "public"
            })

        for res in personal_results:
            chunk_hits.append({
                "id":       res.id,
                "score":    res.distance,
                "text":     res.entity["text"],
                "source":   res.entity["source"],
                "page_num": res.entity["page_num"],
                "knowledge_base": "personal"
            })

        chunk_hits=sorted(chunk_hits, key=lambda x: x["score"],reverse=True)
        if len(chunk_hits)>=combined_k:
            chunk_hits=chunk_hits[:combined_k]
        for idx, chunk in enumerate(chunk_hits, start=1):
            chunk["rank"] = idx
        return chunk_hits
    
    def chunk_reranker(self,candidates,query,alpha=0.4,top_k_final=10):
        cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2",device =  "cpu")
        pairs = [(query, c["text"]) for c in candidates]
        cross_scores = cross_encoder.predict(pairs, batch_size=32)
        reranked = []
        nomalized_candidates_scores = self._min_max_normalize(np.array([c["score"] for c in candidates]))
        candidates_normalized_map = {
            (c["source"], c["page_num"],c["id"]): score
            for c, score in zip(candidates, nomalized_candidates_scores)
        }

        normalized_cross_scores = self._min_max_normalize(cross_scores)
        cross_normalized_map = {
            (c["source"],c["page_num"],c["id"]): score
            for c,score in zip(candidates,normalized_cross_scores)
        }

        for idx,c in enumerate(candidates):
            key = (c["source"],c["page_num"],c["id"])
            candidate_nomalized_score,cross_nomalized_score = candidates_normalized_map.get(key,0),cross_normalized_map.get(key,0)
            final_score = alpha * cross_nomalized_score + (1 - alpha) * candidate_nomalized_score
            reranked.append({
                "text": c["text"],
                "source": c["source"],
                "page_num" : c["page_num"],
                "first_score": float(c["score"]),
                "second_score": float(cross_scores[idx]),
                "final_score": float(final_score),
                "knowledge_base": c["knowledge_base"],
            })
        reranked.sort(key=lambda x: x["final_score"], reverse=True)
        return reranked[:top_k_final]
    
    def chunk_retrieve_with_reranker(self,query,personal_k,public_k,final_k):
        candidates = self.chunk_retrieve(query,50,50,50)
        final_results = self.chunk_reranker(candidates,query,alpha=0.4,top_k_final=final_k)
        return final_results
    
    def chunk_retrieve_with_filter(self,query,filter,personal_k,public_k,final_k):
        query_embeddings = embed_queries_for_chunks([query])[0]
        personal_hits = self.kb_manager.client.search(
                collection_name = self.personal_chunk_collection_name,
                data=[query_embeddings],
                limit=personal_k,
                filter = filter,
                output_fields=["text","source","page_num"],
                search_params={"metric_type": "COSINE"}
            )
        
        public_hits = self.kb_manager.client.search(
                collection_name = self.kb_manager.public_chunk_col_name,
                data=[query_embeddings],
                limit=public_k,
                filter = filter,
                output_fields=["text","source","page_num"],
                search_params={"metric_type": "COSINE"}
            )
        personal_results = personal_hits[0] if personal_hits else []
        public_results  = public_hits[0]   if public_hits else []

        chunk_hits = []
        for res in public_results:
            chunk_hits.append({
                "id":       res.id,
                "score":    res.distance,
                "text":     res.entity["text"],
                "source":   res.entity["source"],
                "page_num": res.entity["page_num"],
                "knowledge_base": "personal"
            })

        for res in personal_results:
            chunk_hits.append({
                "id":       res.id,
                "score":    res.distance,
                "text":     res.entity["text"],
                "source":   res.entity["source"],
                "page_num": res.entity["page_num"],
                "knowledge_base": "public"
            })

        return chunk_hits[:final_k]


    def hybrid_retrieve(self,chunk_hits,page_hits,final_k,alpha = 0.6):
        page_map = {
            (p["source"],p["page_num"]): p["score"]
            for p in page_hits
        }
        page_scores = self._min_max_normalize(np.array([p["score"] for p in page_hits]))
        
        page_normalized_map = {
            (p["source"], p["page_num"]): score
            for p, score in zip(page_hits, page_scores)
        }

        chunk_scores = self._min_max_normalize(np.array([c["score"] for c in chunk_hits]))

        fused_results = []
        for chunk,chunk_score in zip(chunk_hits,chunk_scores):
            page_score = page_normalized_map.get((chunk["source"],chunk["page_num"]),0.0)
            fused_score = alpha*chunk_score+(1-alpha)*page_score
            fused_results.append({
                "text": chunk["text"],
                "chunk_score": chunk["score"],
                "page_score": page_map.get((chunk["source"],chunk["page_num"]),0.0),
                "fused_score":fused_score,
                "source": chunk["source"],
                "page_num":chunk["page_num"]
            })
        fused_results = sorted(fused_results, key=lambda x: x["fused_score"], reverse=True)
        img_pth = self.get_img_paths(fused_results)
        return fused_results[:final_k],img_pth
    
    def cascade_retrieve(self,query,alpha = 0.6,personal_k=30,public_k=30,final_chunk_k = 10):
        page_hits = self.page_retrieve(query)
        page_map = {
            (p["source"],p["page_num"]): p["score"]
            for p in page_hits
        }
        page_scores = self._min_max_normalize(np.array([p["score"] for p in page_hits]))
        
        page_normalized_map = {
            (p["source"], p["page_num"]): score
            for p, score in zip(page_hits, page_scores)
        }
        
            
        expr_clauses = [f'(source == "{p["source"]}" && page_num == {p["page_num"]})' for p in page_hits]
        expr = " || ".join(expr_clauses)

        # query_embeddings = embed_queries_for_chunks([query])[0]
        
        chunk_hits = self.chunk_retrieve_with_filter(query,expr,personal_k,public_k,final_k = 60)
        chunk_hits = sorted(chunk_hits, key=lambda x: x["score"], reverse=True)
        
        chunk_normalized_scores = self._min_max_normalize(np.array([c["score"] for c in chunk_hits]))
        chunk_normalized_map = {
            (hit["source"], hit["page_num"], hit["id"]): score
            for hit,score in zip(chunk_hits,chunk_normalized_scores)
        }

        fused_chunks = []
        for hit in chunk_hits:
            page_key = (hit["source"], hit["page_num"])
            chunk_key = (hit["source"], hit["page_num"], hit["id"])

            page_normalized_score = page_normalized_map.get(page_key, 0)
            chunk_normalized_score = chunk_normalized_map.get(chunk_key, 0)

            fused_score = alpha*page_normalized_score + (1-alpha)*chunk_normalized_score

            fused_chunks.append({
                "text": hit["text"],
                "source": hit["source"],
                "page_num": hit["page_num"],
                "page_score": page_map.get((hit["source"],hit["page_num"]),0),
                "chunk_score": hit["score"],
                "fused_score": fused_score
            })

        fused_chunks = sorted(fused_chunks, key=lambda x: x["fused_score"], reverse=True)[:final_chunk_k]

        for i, item in enumerate(fused_chunks):
            item["rank"] = i + 1

        img_pth = self.get_img_paths(fused_chunks)
        return fused_chunks, img_pth
        
    def get_img_paths(self,results,thrshold = 0.8):
        top_1 = results[0]
        name_without_ext, ext = os.path.splitext(top_1["source"])
        if top_1['fused_score'] > thrshold:
            img_pth = os.path.join(IMG_DIR,f"{name_without_ext}/page_{top_1["page_num"]}.png")
        else:
            img_pth = None
        return img_pth
    
    def _min_max_normalize(self,scores, eps=1e-8):
        mn, mx = np.min(scores), np.max(scores)
        return (scores - mn) / (mx - mn + eps)



        
    

