import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams, Distance, PointStruct,
    PayloadSchemaType, SparseVectorParams, SparseIndexParams
)
from qdrant_client.models import Filter, FieldCondition, MatchValue, NamedVector
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

# Quick test
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