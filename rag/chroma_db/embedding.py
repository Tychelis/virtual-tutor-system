from typing import List, Union
import numpy as np
from chromadb import Documents, EmbeddingFunction, Embeddings

class NormalizedEmbeddingFunction(EmbeddingFunction):
    def __init__(self, base_ef: EmbeddingFunction, eps: float = 1e-12):
        self.base_ef = base_ef
        self.eps     = eps

    def __call__(self, inputs: Documents) -> Embeddings:
        embs = np.array(self.base_ef(inputs), dtype=np.float32)  # (n_docs, dim)
        norms = np.linalg.norm(embs, axis=1, keepdims=True)
        embs = embs / np.clip(norms, a_min=self.eps, a_max=None)
        return embs.tolist()
