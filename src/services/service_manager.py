"""Service manager for dependency injection."""

from src.services.memory_service import MemoryService
from src.services.search_service import SearchService
from src.services.journal_service import JournalService
from src.storage.database import Database
from src.storage.vector_store import VectorMemoryStore
from src.utils.config import Settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ServiceManager:
    """Manages service lifecycle with proper dependency injection."""

    def __init__(self):
        self._db: Database | None = None
        self._vector: VectorMemoryStore | None = None
        self._memory: MemoryService | None = None
        self._search: SearchService | None = None
        self._journal: JournalService | None = None
        self._initialized = False

    async def initialize(self, settings: Settings) -> None:
        """Initialize all services.

        Args:
            settings: Application settings
        """
        if self._initialized:
            logger.warning("ServiceManager already initialized")
            return

        # Initialize storage layers
        self._db = Database(settings)
        await self._db.init()

        self._vector = VectorMemoryStore(settings)
        await self._vector.init()

        self._memory: MemoryService | None = None
        self._search: SearchService | None = None
        self._journal: JournalService | None = None
        
        # Initialize services
        self._memory = MemoryService(self._db, self._vector)
        self._search = SearchService(self._vector)
        self._journal = JournalService(self._db, self._vector, self._search)

        self._initialized = True
        logger.info("ServiceManager initialized")

    async def cleanup(self) -> None:
        """Cleanup all resources."""
        if self._db:
            await self._db.close()
            self._db = None

        # Vector store cleanup if needed
        self._vector = None
        self._memory = None
        self._search = None
        self._journal = None
        self._initialized = False
        logger.info("ServiceManager cleanup complete")

    def get_services(self) -> tuple[MemoryService, SearchService, JournalService]:
        """Get memory, search and journal services.

        Returns:
            Tuple of (MemoryService, SearchService, JournalService)

        Raises:
            RuntimeError: If services not initialized
        """
        if not self._initialized or not self._memory or not self._search or not self._journal:
            raise RuntimeError("Services not initialized. Call initialize() first.")
        return self._memory, self._search, self._journal
