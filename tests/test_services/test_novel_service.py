import pytest
from unittest.mock import AsyncMock
from services.novel import NovelService
from models.novel import NovelState

@pytest.mark.asyncio
class TestNovelService:
    async def test_get_novel_state(self, mock_uow):
        # Arrange
        service = NovelService(mock_uow)
        user_id = 123
        expected_state = NovelState(user_id=user_id)
        mock_uow.novel_states = AsyncMock()
        mock_uow.novel_states.get_by_user_id.return_value = expected_state
        
        # Act
        result = await service.get_novel_state(user_id)
        
        # Assert
        assert result == expected_state
        mock_uow.novel_states.get_by_user_id.assert_called_once_with(user_id)
    
    async def test_create_novel_state(self, mock_uow):
        # Arrange
        service = NovelService(mock_uow)
        user_id = 123
        mock_uow.novel_states = AsyncMock()
        
        # Act
        await service.create_novel_state(user_id)
        
        # Assert
        mock_uow.novel_states.create.assert_called_once()
        mock_uow.commit.assert_called_once() 