import os
import torch
from tqdm import tqdm
import numpy as np
from PIL import Image
from typing import cast
from torch.utils.data import DataLoader
from colpali_engine.models import ColPali
from colpali_engine.utils.torch_utils import ListDataset, get_torch_device
from colpali_engine.models.paligemma.colpali.processing_colpali import ColPaliProcessor
from pymilvus.model.hybrid import BGEM3EmbeddingFunction
from sentence_transformers import SentenceTransformer

_page_emb_model = None
_processor = None
_chunk_emb_model = None
page_model_name = "vidore/colpali-v1.3"

def get_page_embedder():
  global _page_emb_model
  if _page_emb_model is None:
    _page_emb_model = ColPali.from_pretrained(
      page_model_name,
      torch_dtype=torch.bfloat16,
      device_map="cuda" if torch.cuda.is_available() else "cpu",
    ).eval()
  return _page_emb_model

def get_processor():
  global _processor
  if _processor is None:
    _processor = cast(ColPaliProcessor, ColPaliProcessor.from_pretrained(page_model_name,use_fast=True))
  return _processor

def get_chunk_embedder():
  global _chunk_emb_model
  if _chunk_emb_model is None:
    _chunk_emb_model = SentenceTransformer("all-MiniLM-L6-v2")
  return _chunk_emb_model

#query embedding
def embed_queries_for_page(query):
  processor = get_processor()
  page_model = get_page_embedder()
  batch_queries = processor.process_queries(query).to(page_model.device)
  embeddings = []
  with torch.inference_mode():
    query_embedding = page_model(**batch_queries)
  embeddings.extend(list(torch.unbind(query_embedding.to("cpu"))))
  return embeddings
  
#file embedding
def embed_images_for_page(img_dir):
  processor = get_processor()
  page_model = get_page_embedder()
  print(f"Processing images under {img_dir}")
  images = [Image.open(os.path.join(img_dir,name)) for name in os.listdir(img_dir)]
  dataloader = DataLoader(
    dataset=ListDataset[str](images),
    batch_size=1,
    shuffle=False,
    collate_fn=lambda x: processor.process_images(x),
  )

  embeddings= []
  for batch_page in tqdm(dataloader):
    with torch.inference_mode():
        batch_page = {k: v.to(page_model.device) for k, v in batch_page.items()}
        embeddings_page = page_model(**batch_page)
    embeddings.extend(list(torch.unbind(embeddings_page.to("cpu"))))
  return embeddings

# --- embedding for chunk --- #
def embed_texts_for_chunks(chunks):
  chunk_embedding_function = get_chunk_embedder()
  chunk_embeddings = chunk_embedding_function.encode(chunks, convert_to_numpy=True, show_progress_bar=False)
  norms = np.linalg.norm(chunk_embeddings, axis=1, keepdims=True)
  chunk_embeddings = chunk_embeddings / norms
  return chunk_embeddings.tolist()

def embed_queries_for_chunks(queries):
  chunk_embedding_function = get_chunk_embedder()
  queries_embedding = chunk_embedding_function.encode(queries, convert_to_numpy=True, show_progress_bar=False)
  norms = np.linalg.norm(queries_embedding, axis=1, keepdims=True)
  queries_embedding = queries_embedding / norms
  return queries_embedding