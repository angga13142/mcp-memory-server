"""Search service - semantic search across memory."""

from typing import Any

from src.storage.vector_store import VectorMemoryStore
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SearchService:
    """Semantic search service for memory retrieval.

    Provides intelligent search across all memory types
    using vector embeddings and similarity matching.
    """

    def __init__(self, vector_store: VectorMemoryStore):
        self.vector_store = vector_store

    async def search(
        self,
        query: str,
        limit: int = 5,
        content_types: list[str] | None = None,
        tags: list[str] | None = None,
        min_score: float = 0.0,
    ) -> list[dict[str, Any]]:
        """Semantic search across all memory.

        Args:
            query: Search query text
            limit: Maximum number of results
            content_types: Filter by content types (decision, task, note, etc.)
            tags: Filter by tags
            min_score: Minimum similarity score (0-1)

        Returns:
            List of search results with content, metadata, and score
        """
        # Build filter
        filter_metadata = None
        if content_types and len(content_types) == 1:
            filter_metadata = {"content_type": content_types[0]}

        # Execute search
        results = await self.vector_store.search(
            query=query,
            n_results=limit * 2,  # Get extra for post-filtering
            filter_metadata=filter_metadata,
        )

        # Post-filter by tags and score
        filtered_results = []
        for result in results:
            # Check score threshold
            if result.get("score", 0) < min_score:
                continue

            # Check content type filter (for multiple types)
            if content_types and len(content_types) > 1:
                result_type = result.get("metadata", {}).get("content_type", "")
                if result_type not in content_types:
                    continue

            # Check tag filter
            if tags:
                result_tags = result.get("metadata", {}).get("tags", "")
                result_tag_list = result_tags.split(",") if result_tags else []
                if not any(t in result_tag_list for t in tags):
                    continue

            filtered_results.append(result)

            if len(filtered_results) >= limit:
                break

        logger.debug(f"Search '{query[:30]}...' returned {len(filtered_results)} results")
        return filtered_results

    async def search_similar(
        self,
        content: str,
        limit: int = 5,
        exclude_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Find similar memories to a given content.

        Args:
            content: Content to find similar items for
            limit: Maximum number of results
            exclude_ids: IDs to exclude from results

        Returns:
            List of similar memories
        """
        results = await self.vector_store.search(
            query=content,
            n_results=limit + len(exclude_ids or []),
        )

        # Filter excluded IDs
        if exclude_ids:
            results = [r for r in results if r.get("id") not in exclude_ids]

        return results[:limit]

    async def get_context_relevant(
        self,
        current_task: str,
        related_files: list[str] | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Get memories relevant to current context.

        Args:
            current_task: Current task description
            related_files: Files being worked on
            limit: Maximum number of results

        Returns:
            Contextually relevant memories
        """
        # Build context query
        query_parts = [current_task]
        if related_files:
            query_parts.append(f"Files: {', '.join(related_files[:5])}")

        query = " ".join(query_parts)

        return await self.search(
            query=query,
            limit=limit,
            min_score=0.3,  # Lower threshold for context
        )

    async def count(self) -> int:
        """Get total number of indexed memories."""
        return await self.vector_store.count()
