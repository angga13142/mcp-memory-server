"""Integration tests for Redis."""

import time

import pytest

# Redis is optional - skip if not available
try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


@pytest.mark.integration
@pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis package not installed")
class TestRedisIntegration:
    """Test Redis integration."""

    @pytest.fixture(scope="class")
    def redis_client(self):
        """Redis client."""
        try:
            client = redis.Redis(
                host="localhost",
                port=6379,
                db=0,
                decode_responses=True,
                socket_connect_timeout=5,
            )
            # Test connection
            client.ping()
            return client
        except (redis.ConnectionError, redis.TimeoutError):
            pytest.skip("Redis not available")

    def test_redis_connection(self, redis_client):
        """Test Redis connection."""
        response = redis_client.ping()
        assert response is True

    def test_redis_info(self, redis_client):
        """Test Redis info command."""
        info = redis_client.info()

        assert "redis_version" in info
        assert "used_memory" in info
        assert "connected_clients" in info

    def test_redis_set_get(self, redis_client):
        """Test basic set/get operations."""
        key = "test:integration:key"
        value = "test_value_123"

        # Set
        result = redis_client.set(key, value)
        assert result is True

        # Get
        retrieved = redis_client.get(key)
        assert retrieved == value

        # Cleanup
        redis_client.delete(key)

    def test_redis_expiry(self, redis_client):
        """Test key expiration."""
        key = "test:integration:expiry"
        value = "expires_soon"

        # Set with 2 second expiry
        redis_client.setex(key, 2, value)

        # Should exist immediately
        assert redis_client.exists(key) == 1

        # Wait for expiry
        time.sleep(3)

        # Should not exist
        assert redis_client.exists(key) == 0

    def test_redis_hash_operations(self, redis_client):
        """Test hash operations."""
        key = "test:integration:hash"

        # Set hash fields
        redis_client.hset(key, "field1", "value1")
        redis_client.hset(key, "field2", "value2")

        # Get hash fields
        assert redis_client.hget(key, "field1") == "value1"
        assert redis_client.hget(key, "field2") == "value2"

        # Get all
        all_data = redis_client.hgetall(key)
        assert all_data == {"field1": "value1", "field2": "value2"}

        # Cleanup
        redis_client.delete(key)

    def test_redis_list_operations(self, redis_client):
        """Test list operations."""
        key = "test:integration:list"

        # Push items
        redis_client.rpush(key, "item1", "item2", "item3")

        # Get length
        length = redis_client.llen(key)
        assert length == 3

        # Get items
        items = redis_client.lrange(key, 0, -1)
        assert items == ["item1", "item2", "item3"]

        # Pop item
        item = redis_client.lpop(key)
        assert item == "item1"

        # Cleanup
        redis_client.delete(key)

    def test_redis_memory_usage(self, redis_client):
        """Test Redis memory usage."""
        info = redis_client.info("memory")

        used_memory = info["used_memory"]
        assert used_memory > 0

        # Should be reasonable (< 100MB for tests)
        assert used_memory < 100 * 1024 * 1024

    def test_redis_persistence(self, redis_client):
        """Test Redis persistence settings."""
        config = redis_client.config_get("save")

        # Should have save config (may be empty string for no persistence)
        assert "save" in config

    def test_redis_max_memory(self, redis_client):
        """Test Redis max memory configuration."""
        config = redis_client.config_get("maxmemory")

        assert "maxmemory" in config
