import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.getcwd())

from src.services.journal_service import JournalService
from src.services.search_service import SearchService
from src.storage.database import Database
from src.storage.vector_store import VectorMemoryStore
from src.utils.config import get_settings


async def test_journal_flow():
    print("Testing Journal Flow...")

    settings = get_settings()

    # Initialize services
    db = Database(settings)
    await db.init()

    vector = VectorMemoryStore(settings)
    await vector.init()

    search = SearchService(vector)
    journal = JournalService(db, vector, search)

    try:
        # 1. Start a session
        print("\n1. Starting work session...")
        result = await journal.start_work_session("Implement Daily Journal Feature")
        print(f"Start Result: {result}")

        if not result["success"]:
            # If session active, end it first
            print("Session active, ending it first...")
            await journal.end_work_session(quick_note="Force clean previous session")
            result = await journal.start_work_session("Implement Daily Journal Feature")
            print(f"Retry Start Result: {result}")

        result.get("session_id")

        # 2. End session
        print("\n2. Ending work session...")
        # Mock some time passing
        await asyncio.sleep(0.1)
        result = await journal.end_work_session(
            learnings=[
                "Learned how to use Alembic",
                "FastMCP simplifies tool creation",
            ],
            challenges=["Finding the right python venv path"],
            quick_note="Implemented core features successfully",
        )
        print(f"End Result: {result}")

        # 3. Generate daily summary
        print("\n3. Generating daily summary...")
        result = await journal.generate_daily_summary()
        print(f"Summary Result: {result}")

        # 4. Get morning briefing (for "tomorrow")
        print("\n4. Getting morning briefing...")
        briefing = await journal.get_morning_briefing()
        print(f"Briefing:\n{briefing[:200]}...")

    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(test_journal_flow())
