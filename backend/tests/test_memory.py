import pytest
from unittest.mock import AsyncMock
from app.services.memory import MemoryService


@pytest.mark.asyncio
async def test_memory_service_initializes():
    mock_db = AsyncMock()
    service = MemoryService(mock_db)
    assert service.db == mock_db
