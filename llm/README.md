# LLM Service (Original & Optimized)

This folder contains the LLM microservice for our Virtual Tutor.  
It exposes a streaming `/chat/stream` API that runs a LangGraph-based Retrieval-Augmented Generation (RAG) workflow with safety guardrails.  
We provide two variants:

- **Original pipeline**
  - Core logic: `ai_assistant_final.py`
  - API: `api_interface.py`

- **Latency-optimized pipeline**
  - Core logic: `ai_assistant_optimized.py`
  - API: `api_interface_optimized.py`

Both versions support RAG over Milvus, web search, and safety classification, but the optimized version reduces **time-to-first-token (TTFT)** via fast rewrite, parallel classification + retrieval, and optional Redis caching.

---

## Main Files

### Core LLM & APIs

- `ai_assistant_final.py` – original LangGraph workflow (RAG + web search + guardrails).
- `api_interface.py` – Flask API for the original service.
- `ai_assistant_optimized.py` – latency-focused LangGraph workflow.
- `api_interface_optimized.py` – Flask API for the optimized service.

### RAG & Milvus

- `milvus_config.py` – Milvus API base URL, endpoints, default `k` values, timeouts.
- `milvus_api_client.py` – HTTP client + simple CLI test for Milvus connectivity and retrieval.

### Serving & Deployment

- `gunicorn_config.py` – Gunicorn configuration for the LLM service (workers, threads, logging).
- `start_production.sh` – start the optimized service with Gunicorn.
- `switch_to_optimized.sh` / `switch_to_original.sh` – switch backend routing between optimized and original LLM services.

### Checkpoints

- `checkpoints.db`, `checkpoints_optimized.db` – LangGraph state stores for the two workflows.

### Testing Utilities

- `test_simple_api.py` – basic streaming test against an LLM endpoint.
- `test_current.py` – auto-detect running service (original vs optimized) and measure TTFT + total time.
- `test_latency_optimization.py` – single-endpoint latency test.
- `compare_latency.py` – multi-round latency comparison between original and optimized services.
- `quick_test.py` – small script to compare TTFT and total time for both ports (e.g. `8610` vs `8611`).

---

## How to Run

### Development Mode

From the `llm` folder:

```bash
# Original service (typically on port 8610)
python api_interface.py

# Optimized service (typically on port 8611)
python api_interface_optimized.py
````

Both services expose:

* `POST /chat/stream` – SSE streaming chat endpoint.
* `GET  /health` – simple health check.

The optimized API additionally exposes:

* `GET  /stats` – shows optimization configuration and expected TTFT.
* `POST /benchmark` – internal benchmark for latency and chunking.

### Production Mode (Optimized)

```bash
# From llm/
./start_production.sh
```

This script:

* Uses `gunicorn_config.py` and `api_interface_optimized:app`.
* Reads `WORKERS`, `WORKER_CLASS`, `THREADS`, and `PORT` from environment variables (with sensible defaults).
* Writes access and error logs to the `logs/` folder.


## Testing Approach and Coverage

Our goal is that the LLM service is **correct, performant, and reliable**.
We use a combination of **unit tests**, **integration tests**, and **end-to-end (E2E) / performance tests**. The high-level approach is summarised here for tutors and markers; more details are given in the project report.

### 1. Unit Tests (Logic-Level)

We write unit tests (e.g. with `pytest` or `unittest`) for code that we developed this term, focusing on:

* Configuration and helper logic (e.g. URL building, timeout configuration, validation in `milvus_config.py` and `milvus_api_client.py`).
* Small pure functions or simple rules (e.g. classification helpers, basic safety/routing decisions).
* Error-handling branches (e.g. handling invalid responses, JSON parsing errors).

**Mocking and stubbing**

When unit-testing code that interacts with external libraries or services (Milvus, Tavily, Redis, Ollama, HTTP clients, etc.), we **do not trust the real dependencies**. Instead, we:

* Mock the external clients to simulate:

  * **Happy cases**: valid responses with expected structure.
  * **Sad cases**: timeouts, HTTP errors, unexpected payloads, and empty results.
* Ensure our code under test behaves correctly in both situations (e.g. fallbacks and error messages instead of crashes).

This follows the guideline that behaviour of external dependencies is not guaranteed and should not be relied on in unit tests.

### 2. Integration Tests (Service-Level)

We treat `api_interface.py` and `api_interface_optimized.py` as black-box HTTP services and test them at the API boundary, typically using an HTTP client (or Flask test client). These tests focus on:

* Input validation:

  * Required fields: `user_id`, `session_id`, `input`.
  * Type checking and handling invalid payloads.
* Guardrails and safety logic:

  * **Happy path**: safe academic questions are accepted and streamed.
  * **Sad path**: harmful or direct-assignment-answer requests are blocked and return appropriate responses.
* Error handling:

  * Upstream services down (Milvus/Tavily/Redis not available).
  * Timeouts and HTTP errors from external APIs.
  * Ensuring the service responds with stable HTTP status codes and does not crash.

For these tests, we often **mock external services**, especially when checking sad paths or rare failure modes.
Where mocking is not appropriate (e.g. verifying real Milvus connectivity in a dedicated environment), we document that the tests may fail for reasons outside our control (network, remote service outages) and explain this in the report.

### 3. End-to-End Safeguard Test

In this folder we only keep **one dedicated end-to-end test**, focusing on the safeguard behaviour and logging:

```bash
# Safeguard logging test:
# Sends normal / homework-like / harmful-like queries to /chat/stream
# and then inspects backend/db/users.db for Safeguard records.
python test_safeguard.py
```

This test is used to verify that:

* The LLM guardrail correctly classifies:

  * **Normal academic questions** as allowed.
  * **Homework-like questions** as `homework_request`.
  * **Harmful queries** as `harmful`.
* Non-normal queries are written into the **Safeguard table** in `backend/db/users.db` with the expected fields (e.g. user id, raw input, classification, timestamp).
* The `/chat/stream` endpoint still returns a stable, well-formed streaming response even when a request is blocked for safety reasons.

If this safeguard E2E test fails for reasons outside our control (e.g. database file missing, schema not migrated, backend not running), we document the root cause and explain why it is an environment/configuration issue rather than a bug in the safeguard logic itself.

### 4. Scope of Tests in This Folder

This `llm/` folder focuses on:

* Safeguard-specific end-to-end behaviour (`test_safeguard.py`).
* The core LLM workflows and APIs (`ai_assistant_final.py`, `ai_assistant_optimized.py`, `api_interface*.py`).

Broader test coverage — including unit tests, integration tests, and other end-to-end / performance tests (e.g. latency comparison between original and optimized pipelines) — is defined and documented in the **root-level `tests/` directory** rather than duplicated here.

