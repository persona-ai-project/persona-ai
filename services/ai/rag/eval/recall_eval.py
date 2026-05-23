import json
import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../'))

from services.ai.rag.retriever import index, search_hybrid
from shared.contracts.chunk import Chunk
from datetime import datetime, timezone

def run_eval():
    """
    Run recall@5 evaluation on 20 hand-built query/chunk pairs.
    Recall@5 >= 0.8 means 16/20 queries return correct chunk in top 5.
    """
    # Load eval pairs
    eval_path = os.path.join(os.path.dirname(__file__), 'eval_pairs.json')
    with open(eval_path, 'r') as f:
        pairs = json.load(f)

    # First index the demo chunks
    demo_chunks = [
        Chunk(text="I love cricket and follow every match closely.", source="interview", source_id="q1", created_at=datetime.now(timezone.utc), metadata={}),
        Chunk(text="I am a software engineer and graduated from GCU Lahore.", source="interview", source_id="q2", created_at=datetime.now(timezone.utc), metadata={}),
        Chunk(text="My favorite food is biryani, I could eat it every day.", source="interview", source_id="q3", created_at=datetime.now(timezone.utc), metadata={}),
        Chunk(text="I live in Lahore and have been here my whole life.", source="interview", source_id="q4", created_at=datetime.now(timezone.utc), metadata={}),
        Chunk(text="I am currently learning machine learning and finding it exciting.", source="interview", source_id="q5", created_at=datetime.now(timezone.utc), metadata={}),
    ]

    print("Indexing demo chunks...")
    index("eval-user", demo_chunks)

    # Run eval
    hits = 0
    misses = []

    print(f"\nRunning {len(pairs)} queries...\n")

    for pair in pairs:
        query = pair["query"]
        expected_snippet = pair["expected_text_snippet"]

        # Search top 5
        results = search_hybrid("eval-user", query, k=5)

        # Check if expected snippet appears in any top 5 result
        found = any(
            expected_snippet.lower() in r["text"].lower()
            for r in results
        )

        if found:
            hits += 1
            print(f"  ✅ {query}")
        else:
            misses.append(query)
            print(f"  ❌ {query}")

    # Calculate recall@5
    recall = hits / len(pairs)

    print(f"\n{'='*50}")
    print(f"Recall@5: {hits}/{len(pairs)} = {recall:.2f}")

    if recall >= 0.8:
        print("✅ PASSED — recall@5 >= 0.8")
    else:
        print("❌ FAILED — recall@5 < 0.8")
        print("\nMissed queries:")
        for m in misses:
            print(f"  - {m}")

    print(f"{'='*50}")
    return recall


if __name__ == "__main__":
    run_eval()