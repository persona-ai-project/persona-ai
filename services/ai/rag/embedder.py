from qdrant_client import QdrantClient
from fastembed import TextEmbedding, SparseTextEmbedding


class Embedder:
    """
    Singleton class that generates dense and sparse vectors for text chunks.
    Dense vectors capture semantic meaning, sparse vectors capture exact keywords.
    """

    _instance = None  # Singleton instance

    def __new__(cls):
        # Create only one instance of Embedder (Singleton pattern)
        if cls._instance is None:
            cls._instance = super().__new__(cls)

            # Load dense embedding model (384 dimensions, CPU-optimized)
            cls._instance.dense_model = TextEmbedding("BAAI/bge-small-en-v1.5")

            # Load sparse embedding model (BM25 keyword matching)
            cls._instance.sparse_model = SparseTextEmbedding("Qdrant/bm25")

        return cls._instance

    def embed(self, text: str) -> dict:
        """
        Generate both dense and sparse vectors for a single text chunk.
        Args:
            text: Input text to embed
        Returns:
            Dictionary with 'dense' and 'sparse' vectors
        """
        # Generate dense vector (list of 384 floats)
        dense_vector = list(self.dense_model.embed([text]))[0]

        # Generate sparse vector (dictionary of token_id: weight pairs)
        sparse_vector = list(self.sparse_model.embed([text]))[0]

        return {
            "dense": dense_vector,
            "sparse": sparse_vector
        }

# Quick test
# if __name__ == "__main__":
#     embedder = Embedder()
#     result = embedder.embed("I love cricket")
#
#     print(f"Dense vector length: {len(result['dense'])}")
#     print(f"Sparse vector keys: {list(result['sparse'].indices[:5])}")