# from sentence_transformers import SentenceTransformer
# import numpy as np
# import torch.nn.functional as F
# from rag.milvus_kb.config import MODEL_ID,MODEL_DIR,EMBED_DIM
# import torch
# # embedding model for test
# model = SentenceTransformer("all-MiniLM-L12-v2")
from sentence_transformers import SentenceTransformer
import numpy as np
# embedding model for test
model = SentenceTransformer("all-MiniLM-L12-v2")

def embed_texts(texts: list[str]) -> list[list[float]]:
    embs = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    norms = np.linalg.norm(embs, axis=1, keepdims=True)
    embs = embs / norms
    return embs.tolist()
# model = SentenceTransformer("Qwen/Qwen3-Embedding-4B")
# device = "cpu"
# model = SentenceTransformer(MODEL_DIR,
#                             trust_remote_code=True,
#                             device=device,
#                             truncate_dim=EMBED_DIM)

# def embed_texts(texts,normalize=True,batch_size = 32) -> list[list[float]]:
#     embs = model.encode(texts, 
#                         convert_to_tensor=True,
#                         normalize_embeddings=False,
#                         show_progress_bar=False,
#                         batch_size=batch_size
#                         )
    
#     if normalize == True:
#         embs = F.normalize(embs, p=2, dim=1)
#     return embs.cpu().numpy().astype("float32")

# def embed_texts(texts,normalize=True,batch_size = 32) -> list[list[float]]:
#     embs = model.encode(texts, 
#                         convert_to_tensor=True,
#                         normalize_embeddings=False,
#                         show_progress_bar=False,
#                         batch_size=batch_size
#                         )
    
#     if normalize == True:
#         embs = F.normalize(embs, p=2, dim=1)
#     return embs.cpu().numpy().astype("float32")


