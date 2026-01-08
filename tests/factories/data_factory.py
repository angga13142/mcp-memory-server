"""Test data factories."""

import random
import uuid
from datetime import datetime, timedelta
from typing import Any


class JournalEntryFactory:
    """Factory for creating journal entries."""

    @staticmethod
    def create(
        user_id: str | None = None,
        session_date: str | None = None,
        content: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Create a journal entry."""
        return {
            "user_id": user_id or f"user_{random.randint(1, 1000)}",
            "session_date": session_date or datetime.now().strftime("%Y-%m-%d"),
            "content": content or JournalEntryFactory._random_content(),
            "mood": kwargs.get(
                "mood", random.choice(["happy", "productive", "stressed", "neutral"])
            ),
            "tags": kwargs.get("tags", JournalEntryFactory._random_tags()),
            "created_at": kwargs.get("created_at", datetime.now().isoformat()),
        }

    @staticmethod
    def create_batch(count: int, **kwargs) -> list[dict[str, Any]]:
        """Create multiple journal entries."""
        return [JournalEntryFactory.create(**kwargs) for _ in range(count)]

    @staticmethod
    def _random_content() -> str:
        """Generate random journal content."""
        templates = [
            "Today I worked on {task}. Made good progress on {achievement}.",
            "Learned about {topic}. Will apply this to {project}.",
            "Challenge: {problem}. Working on solution involving {approach}.",
            "Completed {task}. Next step is {next_step}.",
        ]

        template = random.choice(templates)
        return template.format(
            task=random.choice(["testing", "documentation", "coding", "design"]),
            achievement=random.choice(["metrics", "tests", "features", "bugs"]),
            topic=random.choice(["async patterns", "fixtures", "mocking", "TDD"]),
            project=random.choice(["API", "dashboard", "monitoring", "CI/CD"]),
            problem=random.choice(
                ["performance", "bugs", "architecture", "deployment"]
            ),
            approach=random.choice(
                ["refactoring", "optimization", "redesign", "testing"]
            ),
            next_step=random.choice(
                ["review", "testing", "deployment", "documentation"]
            ),
        )

    @staticmethod
    def _random_tags() -> list[str]:
        """Generate random tags."""
        all_tags = [
            "work",
            "learning",
            "project",
            "bug",
            "feature",
            "testing",
            "documentation",
        ]
        return random.sample(all_tags, k=random.randint(1, 3))


class MemoryFactory:
    """Factory for creating memories."""

    @staticmethod
    def create(
        content: str | None = None,
        memory_type: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Create a memory."""
        return {
            "id": kwargs.get("id", str(uuid.uuid4())),
            "content": content or MemoryFactory._random_content(),
            "memory_type": memory_type
            or random.choice(["episodic", "semantic", "procedural"]),
            "embedding_id": kwargs.get("embedding_id", f"emb_{uuid.uuid4().hex[:8]}"),
            "importance": kwargs.get("importance", random.uniform(0.5, 1.0)),
            "created_at": kwargs.get("created_at", datetime.now().isoformat()),
        }

    @staticmethod
    def create_batch(count: int, **kwargs) -> list[dict[str, Any]]:
        """Create multiple memories."""
        return [MemoryFactory.create(**kwargs) for _ in range(count)]

    @staticmethod
    def _random_content() -> str:
        """Generate random memory content."""
        templates = [
            "Learned {concept} while working on {context}",
            "Discovered {finding} during {activity}",
            "Realized {insight} when {trigger}",
            "Understood {topic} better through {method}",
        ]

        template = random.choice(templates)
        return template.format(
            concept=random.choice(["pattern", "technique", "approach", "principle"]),
            context=random.choice(["testing", "development", "debugging", "research"]),
            finding=random.choice(["bug", "optimization", "feature", "issue"]),
            activity=random.choice(["testing", "review", "implementation", "analysis"]),
            insight=random.choice(["connection", "pattern", "solution", "approach"]),
            trigger=random.choice(
                ["debugging", "discussing", "implementing", "testing"]
            ),
            topic=random.choice(["architecture", "testing", "performance", "design"]),
            method=random.choice(
                ["practice", "research", "experimentation", "collaboration"]
            ),
        )


class LearningFactory:
    """Factory for creating learnings."""

    @staticmethod
    def create(
        learning_text: str | None = None,
        category: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Create a learning."""
        return {
            "id": kwargs.get("id", random.randint(1, 10000)),
            "learning_text": learning_text or LearningFactory._random_learning(),
            "category": category
            or random.choice(["technical", "process", "soft-skills", "domain"]),
            "confidence": kwargs.get("confidence", random.uniform(0.6, 1.0)),
            "created_at": kwargs.get("created_at", datetime.now().isoformat()),
        }

    @staticmethod
    def create_batch(count: int, **kwargs) -> list[dict[str, Any]]:
        """Create multiple learnings."""
        return [LearningFactory.create(**kwargs) for _ in range(count)]

    @staticmethod
    def _random_learning() -> str:
        """Generate random learning text."""
        templates = [
            "Always {action} when {condition}",
            "Use {technique} for {purpose}",
            "{tool} is better for {scenario}",
            "Remember to {reminder} before {activity}",
        ]

        template = random.choice(templates)
        return template.format(
            action=random.choice(["test", "validate", "check", "verify"]),
            condition=random.choice(["deploying", "merging", "releasing", "updating"]),
            technique=random.choice(["mocking", "fixtures", "factories", "stubs"]),
            purpose=random.choice(
                ["testing", "validation", "verification", "isolation"]
            ),
            tool=random.choice(["pytest", "mock", "factory", "fixture"]),
            scenario=random.choice(["unit tests", "integration", "e2e", "performance"]),
            reminder=random.choice(["backup", "test", "review", "validate"]),
            activity=random.choice(["deploying", "merging", "pushing", "releasing"]),
        )


class MetricsDataFactory:
    """Factory for creating metrics data."""

    @staticmethod
    def create_timeseries(
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        interval_seconds: int = 15,
        base_value: float = 100.0,
        variance: float = 10.0,
    ) -> list[dict[str, Any]]:
        """Create time series data."""
        data_points = []
        current_time = start_time

        while current_time <= end_time:
            value = base_value + random.uniform(-variance, variance)
            data_points.append(
                {
                    "timestamp": current_time.timestamp(),
                    "value": max(0, value),
                    "metric": metric_name,
                }
            )
            current_time += timedelta(seconds=interval_seconds)

        return data_points

    @staticmethod
    def create_prometheus_response(
        metric_name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Create Prometheus query response."""
        return {
            "status": "success",
            "data": {
                "resultType": "vector",
                "result": [
                    {
                        "metric": {"__name__": metric_name, **(labels or {})},
                        "value": [datetime.now().timestamp(), str(value)],
                    }
                ],
            },
        }


class UserFactory:
    """Factory for creating users."""

    @staticmethod
    def create(
        user_id: str | None = None,
        username: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Create a user."""
        if not user_id:
            user_id = f"user_{uuid.uuid4().hex[:8]}"

        if not username:
            username = f"testuser_{random.randint(1, 1000)}"

        return {
            "id": user_id,
            "username": username,
            "email": kwargs.get("email", f"{username}@example.com"),
            "created_at": kwargs.get("created_at", datetime.now().isoformat()),
            "is_active": kwargs.get("is_active", True),
            "preferences": kwargs.get("preferences", {}),
        }

    @staticmethod
    def create_batch(count: int, **kwargs) -> list[dict[str, Any]]:
        """Create multiple users."""
        return [UserFactory.create(**kwargs) for _ in range(count)]
