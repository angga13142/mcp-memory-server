"""ChromaDB vector store for semantic search."""

from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from src.utils.config import Settings, get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class VectorMemoryStore:
    """ChromaDB-backed semantic search for memory entries.

    Uses sentence-transformers for local embedding generation
    and ChromaDB for vector storage and similarity search.
    """

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._client: chromadb.ClientAPI | None = None
        self._collection: chromadb.Collection | None = None
        self._encoder = None

    async def init(self) -> None:
        """Initialize ChromaDB client and collection."""
        chroma_settings = self.settings.storage.chroma
        persist_dir = chroma_settings.persist_directory

        # Ensure directory exists
        Path(persist_dir).mkdir(parents=True, exist_ok=True)

        self._client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(
                anonymized_telemetry=False,
            ),
        )

        self._collection = self._client.get_or_create_collection(
            name=chroma_settings.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        # Lazy load encoder to speed up startup
        logger.info(f"Vector store initialized: {persist_dir}")

    def _get_encoder(self) -> Any:
        """Lazy load sentence transformer encoder."""
        if self._encoder is None:
            from sentence_transformers import SentenceTransformer

            model_name = self.settings.storage.chroma.embedding_model
            self._encoder = SentenceTransformer(model_name)
            logger.info(f"Loaded embedding model: {model_name}")
        return self._encoder

    async def add_memory(
        self,
        id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add a memory entry with auto-generated embedding.

        Args:
            id: Unique identifier for the memory
            content: Text content to embed and store
            metadata: Optional metadata for filtering
        """
        if not self._collection:
            raise RuntimeError("Vector store not initialized. Call init() first.")

        # Generate embedding
        encoder = self._get_encoder()
        embedding = encoder.encode(content).tolist()

        # Prepare metadata (ChromaDB requires string values)
        clean_metadata = {}
        if metadata:
            for key, value in metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    clean_metadata[key] = value
                elif isinstance(value, list):
                    clean_metadata[key] = ",".join(str(v) for v in value)
                else:
                    clean_metadata[key] = str(value)

        # Upsert to handle updates
        self._collection.upsert(
            ids=[id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[clean_metadata] if clean_metadata else None,
        )
        logger.debug(f"Added memory: {id}")

    async def search(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Semantic search for similar memories.

        Args:
            query: Search query text
            n_results: Maximum number of results to return
            filter_metadata: Optional metadata filter (ChromaDB where clause)

        Returns:
            List of search results with id, content, metadata, and distance
        """
        if not self._collection:
            raise RuntimeError("Vector store not initialized. Call init() first.")

        # Generate query embedding
        encoder = self._get_encoder()
        query_embedding = encoder.encode(query).tolist()

        # Build query args
        query_args: dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": min(n_results, self._collection.count() or n_results),
            "include": ["documents", "metadatas", "distances"],
        }

        if filter_metadata:
            query_args["where"] = filter_metadata

        results = self._collection.query(**query_args)

        # Format results
        formatted_results = []
        if results and results["ids"] and results["ids"][0]:
            for i, id in enumerate(results["ids"][0]):
                formatted_results.append(
                    {
                        "id": id,
                        "content": results["documents"][0][i]
                        if results["documents"]
                        else "",
                        "metadata": results["metadatas"][0][i]
                        if results["metadatas"]
                        else {},
                        "distance": results["distances"][0][i]
                        if results["distances"]
                        else 0.0,
                        "score": 1
                        - (results["distances"][0][i] if results["distances"] else 0.0),
                    }
                )

        logger.debug(
            f"Search found {len(formatted_results)} results for: {query[:50]}..."
        )
        return formatted_results

    async def delete(self, id: str) -> None:
        """Delete a memory entry by ID."""
        if not self._collection:
            raise RuntimeError("Vector store not initialized. Call init() first.")

        self._collection.delete(ids=[id])
        logger.debug(f"Deleted memory: {id}")

    async def delete_many(self, ids: list[str]) -> None:
        """Delete multiple memory entries."""
        if not self._collection:
            raise RuntimeError("Vector store not initialized. Call init() first.")

        if ids:
            self._collection.delete(ids=ids)
            logger.debug(f"Deleted {len(ids)} memories")

    async def count(self) -> int:
        """Get total number of stored memories."""
        if not self._collection:
            return 0
        return self._collection.count()

    async def clear(self) -> None:
        """Delete all memories from the collection."""
        if self._collection and self._client:
            collection_name = self._collection.name
            self._client.delete_collection(collection_name)
            self._collection = self._client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("Cleared all memories from vector store")


# Global vector store instance
_vector_store: VectorMemoryStore | None = None


async def get_vector_store(settings: Settings | None = None) -> VectorMemoryStore:
    """Get or create global vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorMemoryStore(settings)
        await _vector_store.init()
    return _vector_store


async def close_vector_store() -> None:
    """Close global vector store instance."""
    global _vector_store
    if _vector_store:
        _vector_store = None
