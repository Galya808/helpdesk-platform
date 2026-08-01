import pytest

from app.database.session import check_database_connection


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_database_connection_succeeds() -> None:
    # Act
    is_connected = await check_database_connection()

    # Assert
    assert is_connected is True
