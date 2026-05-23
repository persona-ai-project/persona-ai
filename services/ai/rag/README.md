# RAG — Persona Memory System

This package gives the AI twin long-term memory. It stores everything a user shares during interviews and retrieves the most relevant pieces when the twin is chatting.

---

## What it does

- Splits user text into 512-word chunks with 20% overlap
- Embeds each chunk using dense (semantic) and sparse (BM25) vectors
- Stores chunks in Qdrant Cloud, tagged by user_id
- Retrieves the most relevant chunks using hybrid search + RRF fusion
- Boosts recently created chunks (last 14 days) by 1.5x

---

## How to call it (for P2)

```python
from services.ai.rag.retriever import index, search_hybrid
from shared.contracts.chunk import Chunk
from shared.contracts.retriever import RetrievalResult
from datetime import datetime, timezone

# Index chunks
chunks = [
    Chunk(
        text="I love cricket.",
        source="interview",
        source_id="q1",
        created_at=datetime.now(timezone.utc),
        metadata={}
    )
]
index("user-123", chunks)

# Search
result: RetrievalResult = search_hybrid("user-123", "what sport do they like?", k=5)

for chunk in result.chunks:
    print(chunk.text, chunk.score)
```

---

## CLI

```bash
# Index a user's chunks from a jsonl file
python -m services.ai.rag index <user_id> <file.jsonl>
```

---

## Eval

```bash
# Run recall@5 evaluation
python services/ai/rag/eval/recall_eval.py
```

Current result: **Recall@5 = 1.00** (20/20 pairs) ✅

---

## Files

| File | What it does |
|---|---|
| `chunker.py` | Splits text into overlapping chunks |
| `embedder.py` | Generates dense + sparse vectors |
| `retriever.py` | index, search, search_hybrid, delete, stats |
| `__main__.py` | CLI entry point |
| `eval/` | Recall evaluation harness |