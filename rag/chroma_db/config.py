import os
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from rag.chroma_db.embedding import NormalizedEmbeddingFunction

# Persistent admin client for tenant and database management
CHROMA_ROOT = os.getenv("CHROMA_ROOT", "/home/jialu/workspace/jialu/chroma_db")
USER_CLIENT_CACHE = int(os.getenv("USER_CLIENT_CACHE", 10))
USER_COLLECTION_CACHE = int(os.getenv("USER_COLLECTION_CACHE", 10))

# EMBED_FUNCTION =DefaultEmbeddingFunction()
ef = DefaultEmbeddingFunction()
EMBED_FUNCTION = NormalizedEmbeddingFunction(ef)
METRIC = "l2"