import sys
import os
import json
from datetime import datetime, timezone
from shared.contracts.chunk import Chunk
from services.ai.rag.retriever import index, search

def main():
    """
    CLI entry point for RAG operations.
    Usage: python -m rag index <user_id> <file.jsonl>
    """
    if len(sys.argv) < 4:
        print("Usage: python -m rag index <user_id> <file.jsonl>")
        sys.exit(1)

    command = sys.argv[1]   # "index"
    user_id = sys.argv[2]   # "demo-user"
    filepath = sys.argv[3] if os.path.isabs(sys.argv[3]) else os.path.join(os.getcwd(), sys.argv[3])
    if command == "index":
        # Read chunks from jsonl file
        chunks = []
        with open(filepath, "r") as f:
            for line in f:
                data = json.loads(line)
                chunk = Chunk(
                    text=data["text"],
                    source=data["source"],
                    source_id=data["source_id"],
                    created_at=datetime.fromisoformat(data["created_at"]),
                    metadata=data.get("metadata", {})
                )
                chunks.append(chunk)

        # Index chunks
        count = index(user_id, chunks)
        print(f"✅ Indexed {count} chunks for user: {user_id}")

        # Test search after indexing
        results = search(user_id, "what do I like?", k=3)
        print(f"\n✅ Quick search test (top 3):")
        for r in results:
            print(f"  Score: {r['score']:.3f} | {r['text']}")

if __name__ == "__main__":
    main()