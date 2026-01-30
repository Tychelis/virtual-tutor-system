# 📚 RAG Module of TutorNet

The Retrieval-Augmented Generation (RAG) module in TutorNet runs as an independent Flask microservice. It supports:

- **Pure-text retrieval** (production, integrated with TutorNet)
- **Multimodal retrieval** (text + page-level image features)
- **Multi-tenant knowledge bases**: per-user *personal KB* + global *public KB*

All documents are stored in a local **Milvus (lite) database file**, and exposed via HTTP APIs and an optional Streamlit management UI.

---
## 🧱 Architecture Overview

- **Service entrypoint:** `rag/app.py` – Flask HTTP API for upload, delete, and retrieval.
- **Management UI:** `rag/streamlit_app.py` – Streamlit dashboard for admins and power users. It talks to the same HTTP API (`/user/*`, `/admin/*`, `/retriever`, etc.).
- **Configuration:** `rag/config.py` – central config for mode, DB path, embedding dimensions and image directory.
- **Parsing & preprocessing:** `rag/data_parser.py` – converts PDFs to images, strips headers/footers, cleans text and chunks it into sentences.
- **Knowledge base manager:** `rag/kb_manager.py` – creates Milvus collections, ingests documents, and manages per-user / public KBs.
- **Embedding models:** `rag/embedding.py` – page-level ColPali encoder + text encoder (`all-MiniLM-L6-v2`).
- **Retriever logic:** `rag/retriever.py` – hybrid retrieval (chunk + page), reranking and multimodal fusion.
- **(Legacy demo)** `rag/build_vector_db.py` – a simple FAISS-based vector DB helper (not used in the main KB / retrieval pipeline).

Directory snapshot:

```text
rag/
  app.py              # Flask API service
  streamlit_app.py    # Streamlit management UI
  config.py           # Global RAG configuration
  data_parser.py      # PDF/DOCX/TXT parsing, header/footer removal, chunking
  embedding.py        # ColPali + SentenceTransformer embedding helpers
  kb_manager.py       # Milvus (lite) collection manager & ingest/delete APIs
  retriever.py        # Retrieval + reranking + multimodal fusion
  build_vector_db.py  # Legacy FAISS helper (experimental)
  tests/              # Pytest-based tests for mode 0/1
````

---
## ⚙️ Configuration

All RAG-related configuration lives in `rag/config.py`:

```python
MODE = 1  # 0 for single-modal (text-only), 1 for multimodal
EMBEDDED_DB_PATH = "./kb_test.db"
CHUNK_EMBED_DIM = 384
PAGE_EMBED_DIM = 128
IMG_DIR = "./imgs"
```

Key fields:

| Parameter          | Description                                                                                                                                        |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `MODE`             | RAG mode: <br>• `0` – **pure-text** (chunk-level retrieval only).<br>• `1` – **multimodal** (chunk + page-level image embeddings, extra GPU cost). |
| `EMBEDDED_DB_PATH` | Local Milvus (lite) DB file. No external Milvus server is required; the DB is stored in this file.                                                 |
| `CHUNK_EMBED_DIM`  | Dimension of text chunk embeddings (`all-MiniLM-L6-v2`, 384-d).                                                                                    |
| `PAGE_EMBED_DIM`   | Dimension of page-level image embeddings from ColPali.                                                                                             |
| `IMG_DIR`          | Root directory where page images are stored: one subdirectory per PDF, e.g. `./imgs/lecture1/page_1.png`.                                          |

> **Tip:** In production, TutorNet currently uses text-only retrieval; set `MODE = 0` for pure-text, or `MODE = 1` if GPU resources are sufficient for multimodal retrieval.

---
## 💾 Knowledge Base Design (Milvus)

The KB is stored inside Milvus (lite) via `MilvusClient(EMBEDDED_DB_PATH)`.

### Collections

* **Public chunk collection:** `kb_admin_public_chunk`
* **Per-user chunk collection:** `kb_user_{user_id}_chunk`
* **Public page collection (MODE=1):** `kb_admin_public_page`
* **Per-user page collection (MODE=1):** `kb_user_{user_id}_page`

Chunk-level schema (simplified):

* `id` (INT64, primary key, auto_id)
* `text` (VARCHAR) – the chunk text
* `embedding` (FLOAT_VECTOR, dim = `CHUNK_EMBED_DIM`)
* `source` (VARCHAR) – original filename
* `page_num` (INT32) – page index
* `chunk_index` (INT32) – chunk index within the document

Page-level schema (MODE=1):

* `id` (INT64, primary key, auto_id)
* `embedding` (FLOAT_VECTOR, dim = `PAGE_EMBED_DIM`)
* `token_id` (INT16) – token index within the page embedding
* `source_id` (VARCHAR) – logical page identifier, e.g. `file.pdf_3`
* `file_path` (VARCHAR) – image filename under `IMG_DIR`
* `source_file` (VARCHAR) – original filename

Indexes:

* Chunk collections: IVF_FLAT index on `embedding` with `COSINE` metric.
* Page collections (MODE=1): IVF_FLAT index on `embedding` + INVERTED index on `source_id`.

---
## 🧠 Embedding & Parsing Pipeline

### Document parsing

When a PDF is ingested:

1. **Images:** `pdf_to_imgs` converts each page to `page_{i}.png` and saves them under `IMG_DIR/<doc-name>/`.
2. **Text:** `get_chunks_from_pdf` uses PyMuPDF to extract page text, removes repeating headers/footers, normalizes bullets, splits into sentences, and then groups them into overlapping chunks.

Support for DOCX/TXT is implemented in `get_chunks_from_docx` and `get_chunks_from_txt` but currently only the PDF path is wired into the main ingestion function.

### Embedding models

* **Page-level image encoder:**

  * Model: `vidore/colpali-v1.3` (ColPali) loaded via `ColPali.from_pretrained`.
  * Device: `cuda` if available, otherwise CPU.
  * Used for both **page embeddings** during ingestion and **query embeddings** for multimodal retrieval.

* **Chunk-level text encoder:**

  * Model: `SentenceTransformer("all-MiniLM-L6-v2")`.
  * Embeddings are L2-normalized vectors of size 384.

* **Cross-encoder reranker (text-only):**

  * Model: `cross-encoder/ms-marco-MiniLM-L-6-v2` (currently runs on CPU).
  * Used to re-score candidate chunks for text-only retrieval.

---
## 🔍 Retrieval Logic

All retrieval logic lives in `rag/retriever.py` as the `CompositeRetriever` class.

### 1. Text-only retrieval (`/retriever`)

Endpoint: `POST /retriever` (JSON)

**Request body:**

```json
{
  "question": "What is gradient vanishing?",
  "user_id": "z1234567",
  "personal_k": 5,
  "public_k": 5,
  "final_k": 5
}
```

Pipeline:

1. Encode query with the text encoder.
2. Search top-`personal_k` chunks in the personal collection and top-`public_k` chunks in the public collection (COSINE similarity).
3. Merge and sort candidates by vector score.
4. Apply cross-encoder reranking and compute a combined score (candidate score + cross-encoder score, weighted by `alpha`).
5. Return top `final_k` chunks.

**Response (simplified):**

```json
{
  "hits": [
    {
      "text": "...chunk content...",
      "source": "Lecture1.pdf",
      "page_num": 3,
      "first_score": 0.82,
      "second_score": 5.43,
      "final_score": 0.91,
      "knowledge_base": "personal"
    }
  ]
}
```

### 2. Multimodal retrieval (`/multimodal_retriever`, MODE=1)

Endpoint: `POST /multimodal_retriever` (JSON)

**Request body (same shape):**

```json
{
  "question": "Explain the convolution operation in CNNs.",
  "user_id": "z1234567",
  "personal_k": 30,
  "public_k": 30,
  "final_k": 10
}
```

Pipeline (cascade retrieval):

1. **Page-level search:**

   * Encode query with ColPali.
   * Search page embeddings in both public and personal page collections.
   * Rerank pages by aggregating similarity across token embeddings.

2. **Chunk filtering by top pages:**

   * Build a filter such as `(source == "Lecture1.pdf" && page_num == 3) || ...`.
   * Search only chunks from those pages in both KBs.

3. **Score fusion:**

   * Normalize page scores and chunk scores, then compute fused scores with weight `alpha`.
   * Assign rank and pick top `final_k` chunks.

4. **Image selection:**

   * If the best chunk has fused score above a threshold, return the corresponding page image path under `IMG_DIR`.

**Response (simplified):**

```json
{
  "hits": [
    {
      "text": "...chunk content...",
      "source": "Lecture1.pdf",
      "page_num": 3,
      "page_score": 12.3,
      "chunk_score": 0.88,
      "fused_score": 0.95,
      "rank": 1
    }
  ],
  "img_path": "imgs/Lecture1/page_3.png"
}
```

---
## 👥 Multi-user & Admin Workflows

All KB operations go through the Flask API in `rag/app.py`.

### Endpoints

* **Upload personal file:** `POST /user/upload`

  * Form fields: `user_id`, `file` (multipart).
  * Creates/loads `kb_user_{user_id}_chunk` (and page collection in MODE=1).
  * Returns ingestion statistics: collection names, page count, number of embeddings.

* **Delete personal file:** `POST /user/delete`

  * Form fields: `user_id`, `source_name` (original filename).
  * Deletes all chunks (and pages in MODE=1) for that file.

* **Upload public file:** `POST /admin/upload`

  * Form field: `file`.
  * Ingests into public collections (`kb_admin_public_*`).

* **Delete public file:** `POST /admin/delete`

  * Form field: `source_name`.

* **List users:** `GET /api/users`

  * Returns user IDs inferred from collection names.

* **List user files:** `GET /api/user_files?user_id=...`

* **List public files:** `GET /api/public_files`

All operations are backed by `KnowledgeBaseManager`, which creates collections on demand and exposes helper methods such as `ingest_to_collection`, `delete_from_user_collection`, `get_user_files`, and `get_public_files`.

---
## 🖥️ Streamlit Management UI

The optional Streamlit app `streamlit_app.py` provides a simple web UI for:

* Viewing all users discovered from Milvus collections
* Uploading / deleting **personal** files for a selected user
* Uploading / deleting **public** files
* Running retrieval queries and inspecting raw hits / JSON

It talks to the same backend API via a configurable `API_BASE`.

### Start the UI

```bash
conda activate rag  # or your virtualenv
cd rag
streamlit run streamlit_app.py
```

Use the configuration expander at the top of the page to point `API_BASE` to the running Flask RAG service (e.g. `http://localhost:9090`).

---
## 🚀 Setup & Run

### 1. Clone & environment

```bash
git clone <repo-url>
cd <repo-root>/rag

# create env (example: conda)
conda create -n rag python=3.12
conda activate rag
```

### 2. System dependencies

For PDF → image conversion and ColPali:

```bash
# Poppler for pdf2image
conda install -c conda-forge poppler
```

### 3. Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure

Edit `rag/config.py`:

* Set `MODE = 0` (text-only) or `MODE = 1` (multimodal).
* Adjust `EMBEDDED_DB_PATH` and `IMG_DIR` for your environment.

### 5. Start RAG service

From the repo root or `rag/`:

```bash
# From project root
python -m rag.app

# or from inside rag/
cd rag
python app.py
```

By default the service listens on `0.0.0.0:9090` (or as configured in `app.py`).

---
## 📝 Notes

* Multimodal mode (`MODE = 1`) requires a GPU with sufficient VRAM for ColPali; CPU-only execution is possible but significantly slower.
* The legacy `chroma_db/`, `milvus_kb/`, and `multimodal_kb/` directories are kept for earlier experiments and are not part of the main production pipeline.

