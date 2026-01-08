"""Integration tests for database operations."""

import sqlite3
import time

import pytest


@pytest.mark.integration
class TestDatabaseOperations:
    """Test database operations."""

    @pytest.fixture(scope="class")
    def test_db_path(self, tmp_path_factory):
        """Create temporary test database."""
        db_dir = tmp_path_factory.mktemp("db")
        return db_dir / "test_memory.db"

    @pytest.fixture(scope="class")
    def db_connection(self, test_db_path):
        """Database connection."""
        conn = sqlite3.connect(str(test_db_path))

        # Create test schema
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS journal_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                session_date TEXT NOT NULL,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                content TEXT NOT NULL,
                embedding_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES journal_sessions(id)
            )
        """
        )

        conn.commit()

        yield conn

        conn.close()
        # Cleanup
        if test_db_path.exists():
            test_db_path.unlink()

    def test_database_connection(self, db_connection):
        """Test database connection."""
        cursor = db_connection.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1

    def test_database_tables_exist(self, db_connection):
        """Test required tables exist."""
        cursor = db_connection.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table'
        """
        )

        tables = [row[0] for row in cursor.fetchall()]

        assert "journal_sessions" in tables
        assert "memories" in tables

    def test_insert_journal_session(self, db_connection):
        """Test inserting journal session."""
        cursor = db_connection.execute(
            """
            INSERT INTO journal_sessions (user_id, session_date, content)
            VALUES (?, ?, ?)
        """,
            ("test_user", "2025-01-08", "Test journal content"),
        )

        db_connection.commit()

        assert cursor.lastrowid > 0

        # Verify insert
        cursor = db_connection.execute(
            """
            SELECT * FROM journal_sessions WHERE id = ?
        """,
            (cursor.lastrowid,),
        )

        row = cursor.fetchone()
        assert row is not None
        assert row[1] == "test_user"  # user_id

    def test_insert_memory(self, db_connection):
        """Test inserting memory."""
        # First create session
        cursor = db_connection.execute(
            """
            INSERT INTO journal_sessions (user_id, session_date, content)
            VALUES (?, ?, ?)
        """,
            ("test_user", "2025-01-08", "Session for memory"),
        )
        db_connection.commit()
        session_id = cursor.lastrowid

        # Insert memory
        cursor = db_connection.execute(
            """
            INSERT INTO memories (session_id, content, embedding_id)
            VALUES (?, ?, ?)
        """,
            (session_id, "Test memory content", "embed_123"),
        )
        db_connection.commit()

        assert cursor.lastrowid > 0

        # Verify
        cursor = db_connection.execute(
            """
            SELECT * FROM memories WHERE id = ?
        """,
            (cursor.lastrowid,),
        )

        row = cursor.fetchone()
        assert row is not None
        assert row[1] == session_id

    def test_foreign_key_constraint(self, db_connection):
        """Test foreign key relationships."""
        # Enable foreign keys
        db_connection.execute("PRAGMA foreign_keys = ON")

        # Try to insert memory with invalid session_id
        with pytest.raises(sqlite3.IntegrityError):
            db_connection.execute(
                """
                INSERT INTO memories (session_id, content)
                VALUES (?, ?)
            """,
                (99999, "Should fail"),
            )
            db_connection.commit()

    def test_query_with_join(self, db_connection):
        """Test querying with join."""
        # Create session and memory
        cursor = db_connection.execute(
            """
            INSERT INTO journal_sessions (user_id, session_date, content)
            VALUES (?, ?, ?)
        """,
            ("test_user", "2025-01-08", "Session content"),
        )
        db_connection.commit()
        session_id = cursor.lastrowid

        db_connection.execute(
            """
            INSERT INTO memories (session_id, content)
            VALUES (?, ?)
        """,
            (session_id, "Memory content"),
        )
        db_connection.commit()

        # Query with join
        cursor = db_connection.execute(
            """
            SELECT s.user_id, s.content, m.content
            FROM journal_sessions s
            JOIN memories m ON s.id = m.session_id
            WHERE s.id = ?
        """,
            (session_id,),
        )

        row = cursor.fetchone()
        assert row is not None
        assert row[0] == "test_user"

    def test_database_integrity_check(self, db_connection):
        """Test database integrity."""
        cursor = db_connection.execute("PRAGMA integrity_check")
        result = cursor.fetchone()[0]

        assert result == "ok"

    def test_database_performance_simple_query(self, db_connection):
        """Test simple query performance."""
        # Insert test data
        for i in range(100):
            db_connection.execute(
                """
                INSERT INTO journal_sessions (user_id, session_date, content)
                VALUES (?, ?, ?)
            """,
                (f"user_{i}", "2025-01-08", f"Content {i}"),
            )
        db_connection.commit()

        # Time query
        start = time.time()
        cursor = db_connection.execute(
            """
            SELECT COUNT(*) FROM journal_sessions
        """
        )
        count = cursor.fetchone()[0]
        duration = time.time() - start

        assert count >= 100
        assert duration < 0.1  # Should be very fast

    def test_transaction_rollback(self, db_connection):
        """Test transaction rollback."""
        # Start transaction
        db_connection.execute("BEGIN")

        # Insert data
        cursor = db_connection.execute(
            """
            INSERT INTO journal_sessions (user_id, session_date, content)
            VALUES (?, ?, ?)
        """,
            ("rollback_user", "2025-01-08", "Will be rolled back"),
        )
        inserted_id = cursor.lastrowid

        # Rollback
        db_connection.rollback()

        # Verify not inserted
        cursor = db_connection.execute(
            """
            SELECT * FROM journal_sessions WHERE id = ?
        """,
            (inserted_id,),
        )

        assert cursor.fetchone() is None
