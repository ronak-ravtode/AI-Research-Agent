# Task 21: Embeddings and pgvector Research Memory

## Status: DONE

## Commit
- **95ceaef** — feat: embeddings and pgvector research memory

## Files Created
- `backend/app/services/embeddings.py` — `EmbeddingService` class wrapping OpenAI embeddings API via httpx
- `backend/app/services/memory.py` — `MemoryService` class with `store_finding` and `search_similar` using pgvector cosine distance
- `backend/tests/test_memory.py` — Async init test for `MemoryService`

## Test Summary
- 1 test collected, 1 passed — `test_memory_service_initializes`

## Notes
- `EmbeddingService` uses `httpx.AsyncClient` to call OpenAI embeddings endpoint
- `MemoryService` accepts an `AsyncSession` and uses raw SQL with pgvector `<=>` cosine operator
- Config fields `EMBEDDING_API_KEY` and `EMBEDDING_MODEL` already exist in `Settings`
