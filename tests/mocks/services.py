"""Mock service objects for testing."""

import time
from typing import Any


class MockPrometheusClient:
    """Mock Prometheus client."""

    def __init__(self):
        self.queries: list[dict[str, Any]] = []
        self.query_results: dict[str, Any] = {}

    def query(self, query_string: str) -> dict[str, Any]:
        """Mock query method."""
        self.queries.append({"query": query_string, "timestamp": time.time()})

        if query_string in self.query_results:
            return self.query_results[query_string]

        return {
            "status": "success",
            "data": {
                "resultType": "vector",
                "result": [
                    {"metric": {"__name__": query_string}, "value": [time.time(), "42"]}
                ],
            },
        }

    def set_query_result(self, query: str, result: dict[str, Any]):
        """Set mock result for a query."""
        self.query_results[query] = result

    def get_query_count(self, query: str) -> int:
        """Get number of times a query was executed."""
        return sum(1 for q in self.queries if q["query"] == query)


class MockGrafanaClient:
    """Mock Grafana client."""

    def __init__(self):
        self.dashboards: list[dict[str, Any]] = []
        self.datasources: list[dict[str, Any]] = []

    def get_dashboards(self) -> list[dict[str, Any]]:
        """Get all dashboards."""
        return self.dashboards

    def get_dashboard(self, uid: str) -> dict[str, Any] | None:
        """Get specific dashboard."""
        for dashboard in self.dashboards:
            if dashboard.get("uid") == uid:
                return dashboard
        return None

    def add_dashboard(self, dashboard: dict[str, Any]):
        """Add mock dashboard."""
        self.dashboards.append(dashboard)

    def get_datasources(self) -> list[dict[str, Any]]:
        """Get all datasources."""
        return self.datasources

    def add_datasource(self, datasource: dict[str, Any]):
        """Add mock datasource."""
        self.datasources.append(datasource)


class MockDatabase:
    """Mock database connection."""

    def __init__(self):
        self.data: dict[str, list[dict[str, Any]]] = {
            "journal_sessions": [],
            "memories": [],
            "learnings": [],
            "challenges": [],
        }
        self.queries: list[str] = []

    def execute(self, query: str, params: tuple = ()) -> "MockCursor":
        """Execute query."""
        self.queries.append(query)
        return MockCursor(self, query, params)

    def commit(self):
        """Commit transaction."""
        pass

    def rollback(self):
        """Rollback transaction."""
        pass

    def close(self):
        """Close connection."""
        pass


class MockCursor:
    """Mock database cursor."""

    def __init__(self, db: MockDatabase, query: str, params: tuple):
        self.db = db
        self.query = query
        self.params = params
        self.lastrowid = 1
        self._results: list[tuple] = []

    def fetchone(self) -> tuple | None:
        """Fetch one result."""
        if self._results:
            return self._results[0]
        return None

    def fetchall(self) -> list[tuple]:
        """Fetch all results."""
        return self._results

    def __iter__(self):
        """Iterate over results."""
        return iter(self._results)


class MockRedisClient:
    """Mock Redis client."""

    def __init__(self):
        self.data: dict[str, Any] = {}
        self.expirations: dict[str, float] = {}

    def get(self, key: str) -> str | None:
        """Get value."""
        self._check_expiration(key)
        return self.data.get(key)

    def set(self, key: str, value: Any, ex: int | None = None) -> bool:
        """Set value."""
        self.data[key] = str(value)
        if ex:
            self.expirations[key] = time.time() + ex
        return True

    def delete(self, *keys) -> int:
        """Delete keys."""
        count = 0
        for key in keys:
            if key in self.data:
                del self.data[key]
                count += 1
        return count

    def exists(self, *keys) -> int:
        """Check if keys exist."""
        count = 0
        for key in keys:
            self._check_expiration(key)
            if key in self.data:
                count += 1
        return count

    def hget(self, name: str, key: str) -> str | None:
        """Get hash field."""
        hash_data = self.data.get(name, {})
        if isinstance(hash_data, dict):
            return hash_data.get(key)
        return None

    def hset(self, name: str, key: str, value: Any) -> int:
        """Set hash field."""
        if name not in self.data:
            self.data[name] = {}
        if not isinstance(self.data[name], dict):
            self.data[name] = {}
        self.data[name][key] = str(value)
        return 1

    def hgetall(self, name: str) -> dict[str, str]:
        """Get all hash fields."""
        data = self.data.get(name, {})
        return data if isinstance(data, dict) else {}

    def _check_expiration(self, key: str):
        """Check if key has expired."""
        if key in self.expirations and time.time() > self.expirations[key]:
            del self.data[key]
            del self.expirations[key]


class MockChromaDB:
    """Mock ChromaDB collection."""

    def __init__(self):
        self.documents: list[dict[str, Any]] = []

    def add(self, documents: list[str], metadatas: list[dict], ids: list[str]):
        """Add documents."""
        for doc, metadata, doc_id in zip(documents, metadatas, ids, strict=False):
            self.documents.append(
                {
                    "id": doc_id,
                    "document": doc,
                    "metadata": metadata,
                    "embedding": [0.1] * 1536,
                }
            )

    def query(
        self, query_embeddings: list[list[float]], n_results: int = 10
    ) -> dict[str, Any]:
        """Query similar documents."""
        results = self.documents[:n_results]

        return {
            "ids": [[r["id"] for r in results]],
            "documents": [[r["document"] for r in results]],
            "metadatas": [[r["metadata"] for r in results]],
            "distances": [[0.1 * i for i in range(len(results))]],
        }

    def count(self) -> int:
        """Count documents."""
        return len(self.documents)

    def delete(self, ids: list[str]):
        """Delete documents."""
        self.documents = [d for d in self.documents if d["id"] not in ids]


class MockOpenAIClient:
    """Mock OpenAI client."""

    def __init__(self):
        self.chat_responses: list[str] = []
        self.embedding_responses: list[list[float]] = []
        self.call_count = 0

    def set_chat_response(self, response: str):
        """Set next chat response."""
        self.chat_responses.append(response)

    def set_embedding_response(self, embedding: list[float]):
        """Set next embedding response."""
        self.embedding_responses.append(embedding)

    def create_chat_completion(self, messages: list[dict], **kwargs) -> dict[str, Any]:
        """Create chat completion."""
        self.call_count += 1

        response_text = (
            self.chat_responses.pop(0) if self.chat_responses else "Mock response"
        )

        return {
            "choices": [
                {
                    "message": {"content": response_text, "role": "assistant"},
                    "finish_reason": "stop",
                    "index": 0,
                }
            ],
            "usage": {
                "prompt_tokens": 50,
                "completion_tokens": 100,
                "total_tokens": 150,
            },
        }

    def create_embedding(self, input_text: str, **kwargs) -> dict[str, Any]:
        """Create embedding."""
        self.call_count += 1

        embedding = (
            self.embedding_responses.pop(0)
            if self.embedding_responses
            else [0.1] * 1536
        )

        return {
            "data": [{"embedding": embedding, "index": 0, "object": "embedding"}],
            "usage": {"prompt_tokens": 10, "total_tokens": 10},
        }
