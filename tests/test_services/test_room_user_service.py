from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.room_user_service import (
    create_room_user,
    join_room_by_code,
    read_role_room_user,
)


def make_room(**overrides):
    data = {
        "id": 10,
        "code": "ABC123",
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def make_room_user(**overrides):
    data = {
        "id": 1,
        "room_id": 10,
        "user_id": 5,
        "role": "master",
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def make_scalar_result(value):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


@pytest.mark.asyncio
async def test_create_room_user_creates_master_membership():
    db = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()

    result = await create_room_user(db, room_id=10, user_id=5)

    assert result.room_id == 10
    assert result.user_id == 5
    assert result.role == "master"

    db.add.assert_called_once_with(result)
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(result)
    db.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_room_user_rolls_back_and_reraises_on_error():
    db = MagicMock()
    db.commit = AsyncMock(side_effect=RuntimeError("commit failed"))
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()

    with pytest.raises(RuntimeError, match="commit failed"):
        await create_room_user(db, room_id=10, user_id=5)

    db.rollback.assert_awaited_once()
    db.refresh.assert_not_awaited()


@pytest.mark.asyncio
async def test_read_role_room_user_returns_membership_when_found():
    room_user = make_room_user(role="player")
    db = MagicMock()
    db.execute = AsyncMock(return_value=make_scalar_result(room_user))
    db.rollback = AsyncMock()

    result = await read_role_room_user(db, room_id=10, user_id=5)

    assert result is room_user
    db.execute.assert_awaited_once()
    db.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_read_role_room_user_returns_none_when_missing():
    db = MagicMock()
    db.execute = AsyncMock(return_value=make_scalar_result(None))
    db.rollback = AsyncMock()

    result = await read_role_room_user(db, room_id=10, user_id=5)

    assert result is None
    db.execute.assert_awaited_once()
    db.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_read_role_room_user_rolls_back_and_reraises_on_error():
    db = MagicMock()
    db.execute = AsyncMock(side_effect=RuntimeError("db failed"))
    db.rollback = AsyncMock()

    with pytest.raises(RuntimeError, match="db failed"):
        await read_role_room_user(db, room_id=10, user_id=5)

    db.rollback.assert_awaited_once()


@pytest.mark.asyncio
@patch(
    "app.services.room_user_service.read_role_room_user",
    new_callable=AsyncMock
)
async def test_join_room_by_code_creates_player_membership(mock_read_role):
    room = make_room(id=10)
    db = MagicMock()
    db.execute = AsyncMock(return_value=make_scalar_result(room))
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()
    mock_read_role.return_value = None

    result = await join_room_by_code(db, code="ABC123", user_id=5)

    assert result.room_id == 10
    assert result.user_id == 5
    assert result.role == "player"

    mock_read_role.assert_awaited_once_with(db, 10, 5)
    db.add.assert_called_once_with(result)
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(result)
    db.rollback.assert_not_awaited()


@pytest.mark.asyncio
@patch(
    "app.services.room_user_service.read_role_room_user",
    new_callable=AsyncMock
)
async def test_join_room_by_code_returns_none_when_room_does_not_exist(
    mock_read_role
):
    db = MagicMock()
    db.execute = AsyncMock(return_value=make_scalar_result(None))
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()

    result = await join_room_by_code(db, code="ABC123", user_id=5)

    assert result is None

    mock_read_role.assert_not_awaited()
    db.add.assert_not_called()
    db.commit.assert_not_awaited()
    db.refresh.assert_not_awaited()
    db.rollback.assert_not_awaited()


@pytest.mark.asyncio
@patch(
    "app.services.room_user_service.read_role_room_user",
    new_callable=AsyncMock
)
async def test_join_room_by_code_raises_conflict_when_user_already_joined(
    mock_read_role
):
    room = make_room(id=10)
    db = MagicMock()
    db.execute = AsyncMock(return_value=make_scalar_result(room))
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()
    mock_read_role.return_value = make_room_user(role="player")

    with pytest.raises(HTTPException) as exc_info:
        await join_room_by_code(db, code="ABC123", user_id=5)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "User already joined"

    mock_read_role.assert_awaited_once_with(db, 10, 5)
    db.add.assert_not_called()
    db.commit.assert_not_awaited()
    db.refresh.assert_not_awaited()
    db.rollback.assert_not_awaited()


@pytest.mark.asyncio
@patch(
    "app.services.room_user_service.read_role_room_user",
    new_callable=AsyncMock
)
async def test_join_room_by_code_rolls_back_and_reraises_on_commit_error(
    mock_read_role
):
    room = make_room(id=10)
    db = MagicMock()
    db.execute = AsyncMock(return_value=make_scalar_result(room))
    db.commit = AsyncMock(side_effect=RuntimeError("commit failed"))
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()
    mock_read_role.return_value = None

    with pytest.raises(RuntimeError, match="commit failed"):
        await join_room_by_code(db, code="ABC123", user_id=5)

    db.rollback.assert_awaited_once()
    db.refresh.assert_not_awaited()


@pytest.mark.asyncio
async def test_join_room_by_code_rolls_back_and_reraises_on_query_error():
    db = MagicMock()
    db.execute = AsyncMock(side_effect=RuntimeError("db failed"))
    db.rollback = AsyncMock()

    with pytest.raises(RuntimeError, match="db failed"):
        await join_room_by_code(db, code="ABC123", user_id=5)

    db.rollback.assert_awaited_once()
