import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams, Distance, PointStruct,
    PayloadSchemaType, SparseVectorParams, SparseIndexParams
)
from qdrant_client.models import Prefetch, FusionQuery, Fusion, Filter, FieldCondition, MatchValue
from qdrant_client.models import NamedVector
from services.ai.rag.embedder import Embedder

# Load environment variables from .env file
load_dotenv()

# Initialize Qdrant client using credentials from .env
client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

# Initialize embedder singleton
embedder = Embedder()

# Qdrant collection name
COLLECTION_NAME = "persona_chunks"


def ensure_collection():
    """
    Create Qdrant collection with dense and sparse vector support if it doesn't exist.
    Also creates a payload index on user_id for fast filtering.
    """
    existing = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME not in existing:
        # Create collection with named dense and sparse vectors
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config={
                "dense": VectorParams(size=384, distance=Distance.COSINE)
            },
            sparse_vectors_config={
                "sparse": SparseVectorParams(
                    index=SparseIndexParams(on_disk=False)
                )
            }
        )

        # Create payload index on user_id for fast per-user filtering
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="user_id",
            field_schema=PayloadSchemaType.KEYWORD
        )


def index(user_id: str, chunks: list) -> int:
    """
    Embed and store a list of text chunks in Qdrant for a specific user.
    Args:
        user_id: Unique identifier for the user
        chunks: List of Chunk objects to index
    Returns:
        Number of chunks successfully indexed
    """
    ensure_collection()

    points = []

    for i, chunk in enumerate(chunks):
        # Generate dense and sparse vectors for chunk text
        vectors = embedder.embed(chunk.text)

        # Build Qdrant point with vectors and metadata payload
        point = PointStruct(
            id=abs(hash(f"{user_id}_{chunk.source_id}_{i}")) % (2**63),
            vector={
                "dense": vectors["dense"].tolist(),
                "sparse": {
                    "indices": vectors["sparse"].indices.tolist(),
                    "values": vectors["sparse"].values.tolist()
                }
            },
            payload={
                "user_id": user_id,
                "text": chunk.text,
                "source": chunk.source,
                "source_id": chunk.source_id,
                "created_at": chunk.created_at.isoformat(),
                "metadata": chunk.metadata
            }
        )
        points.append(point)

    # Upload all points to Qdrant in one batch
    client.upsert(collection_name=COLLECTION_NAME, points=points)

    return len(points)


def search(user_id: str, query: str, k: int = 8) -> list:
    """
    Search for relevant chunks using dense vector similarity.
    Args:
        user_id: Filter results to this user only
        query: Search query text
        k: Number of top results to return (default 8)
    Returns:
        List of matching chunks with scores
    """
    # Embed the query to get dense vector
    vectors = embedder.embed(query)

    # Search Qdrant using dense vector, filtered by user_id
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=vectors["dense"].tolist(),
        using="dense",
        query_filter=Filter(
            must=[FieldCondition(
                key="user_id",
                match=MatchValue(value=user_id)
            )]
        ),
        limit=k
    ).points

    # Format results as list of dicts
    return [
        {
            "text": r.payload["text"],
            "source": r.payload["source"],
            "score": r.score
        }
        for r in results
    ]
def search_hybrid(user_id: str, query: str, k: int = 8) -> list:
    """
    Search using both dense and sparse vectors fused via RRF.
    Better than dense-only search for persona memory retrieval.
    Args:
        user_id: Filter results to this user only
        query: Search query text
        k: Number of top results to return (default 8)
    Returns:
        List of matching chunks with scores
    """

    # Embed query to get both dense and sparse vectors
    vectors = embedder.embed(query)

    # User filter — only return chunks belonging to this user
    user_filter = Filter(
        must=[FieldCondition(
            key="user_id",
            match=MatchValue(value=user_id)
        )]
    )

    # Run hybrid search with RRF fusion
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        prefetch=[
            # Dense search prefetch
            Prefetch(
                query=vectors["dense"].tolist(),
                using="dense",
                limit=k * 2
            ),
            # Sparse search prefetch
            Prefetch(
                query={
                    "indices": vectors["sparse"].indices.tolist(),
                    "values": vectors["sparse"].values.tolist()
                },
                using="sparse",
                limit=k * 2
            )
        ],
        query=FusionQuery(fusion=Fusion.RRF),
        query_filter=user_filter,
        limit=k
    ).points

    # Apply recency boost
    now = datetime.now(timezone.utc)
    boosted = []

    for r in results:
        score = r.score
        created_at = datetime.fromisoformat(r.payload["created_at"])
        days_old = (now - created_at).days

        # Boost recent chunks (last 14 days)
        if days_old <= 14:
            score = score * 1.5

        boosted.append({
            "text": r.payload["text"],
            "source": r.payload["source"],
            "score": round(score, 3)
        })

    from shared.contracts.retriever import RetrievedChunk, RetrievalResult

    boosted.sort(key=lambda x: x["score"], reverse=True)

    return RetrievalResult(
        user_id=user_id,
        query=query,
        chunks=[RetrievedChunk(**c) for c in boosted],
        total=len(boosted)
    )

def delete(user_id: str, source: str = None) -> int:
    """
    Delete chunks for a user. Optionally filter by source.
    Args:
        user_id: User whose chunks to delete
        source: Optional source filter (e.g. "whatsapp")
    Returns:
        Number of chunks deleted
    """
    # Build filter
    conditions = [FieldCondition(key="user_id", match=MatchValue(value=user_id))]

    if source:
        conditions.append(
            FieldCondition(key="source", match=MatchValue(value=source))
        )

    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=Filter(must=conditions)
    )

    return 1


def stats(user_id: str) -> dict:
    """
    Get chunk statistics for a user.
    Args:
        user_id: User to get stats for
    Returns:
        Dictionary with total chunks and breakdown by source
    """
    # Count total chunks for user
    result = client.count(
        collection_name=COLLECTION_NAME,
        count_filter=Filter(
            must=[FieldCondition(
                key="user_id",
                match=MatchValue(value=user_id)
            )]
        )
    )

    return {
        "user_id": user_id,
        "total_chunks": result.count
    }
# Quick test for Dense Search
# if __name__ == "__main__":
#     from shared.contracts.chunk import Chunk
#     from datetime import datetime, timezone
#
#     # Create 3 sample chunks
#     test_chunks = [
#         Chunk(
#             text="I love cricket and follow every match.",
#             source="interview",
#             source_id="q1",
#             created_at=datetime.now(timezone.utc),
#             metadata={}
#         ),
#         Chunk(
#             text="I am a software engineer from Lahore.",
#             source="interview",
#             source_id="q2",
#             created_at=datetime.now(timezone.utc),
#             metadata={}
#         ),
#         Chunk(
#             text="My favorite food is biryani.",
#             source="interview",
#             source_id="q3",
#             created_at=datetime.now(timezone.utc),
#             metadata={}
#         ),
#     ]
#
#     # Test index
#     count = index("test-user-1", test_chunks)
#     print(f"Indexed {count} chunks")
#
#     # Test search
#     results = search("test-user-1", "what do I like to eat?")
#     print(f"\nSearch results:")
#     for r in results:
#         print(f"  Score: {r['score']:.3f} | {r['text']}")

# Smoke test with 100 chunks
# if __name__ == "__main__":
#     from shared.contracts.chunk import Chunk
#     from datetime import datetime, timezone
#
#     # Generate 100 sample chunks
#     test_chunks = [
#         Chunk(
#             text=f"Sample chunk number {i}. I love cricket, biryani, and software engineering. I live in Lahore.",
#             source="interview",
#             source_id=f"q{i}",
#             created_at=datetime.now(timezone.utc),
#             metadata={}
#         )
#         for i in range(100)
#     ]
#
#     # Test index with 100 chunks
#     count = index("smoke-test-user", test_chunks)
#     print(f"✅ Indexed {count} chunks")
#
#     # Test search
#     results = search("smoke-test-user", "what food do I like?", k=5)
#     print(f"\n✅ Search results (top 5):")
#     for r in results:
#         print(f"  Score: {r['score']:.3f} | {r['text'][:60]}...")


# if __name__ == "__main__":
#     result = search_hybrid("demo-user", "what food do I like?", k=3)
#     print(f"user_id: {result.user_id}")
#     print(f"query: {result.query}")
#     print(f"total: {result.total}")
#     print("\nChunks:")
#     for chunk in result.chunks:
#         print(f"  Score: {chunk.score} | {chunk.text}")


# if __name__ == "__main__":
#     queries = [
#         "what food does this person like?",
#         "what do they do for work?",
#         "what are their hobbies?",
#         "what are they learning?",
#         "what is their dream?"
#     ]
#
#     print("=== End-to-End RAG Test (30 chunks) ===\n")
#     for query in queries:
#         result = search_hybrid("demo-user-30", query, k=3)
#         print(f"Query: {query}")
#         for chunk in result.chunks:
#             print(f"  {chunk.score:.2f} | {chunk.text}")
#         print()