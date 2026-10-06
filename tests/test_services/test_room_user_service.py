from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.services.room_user_service import (
    create_room_user,
    join_room_by_code,
    read_role_room_user,
)
from tests.helpers import (
    make_db,
    make_db_with_scalar,
    make_room,
    make_room_user,
)


@pytest.fixture
def mock_read_role():
    with patch(
        "app.services.room_user_service.read_role_room_user",
        new_callable=AsyncMock
    ) as mock:
        mock.return_value = None
        yield mock


# create_room_user

async def test_create_room_user_creates_master_membership():
    db = make_db()

    result = await create_room_user(db, room_id=10, user_id=5)

    assert result.room_id == 10
    assert result.user_id == 5
    assert result.role == "master"

    db.add.assert_called_once_with(result)
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(result)
    db.rollback.assert_not_awaited()


async def test_create_room_user_rolls_back_and_reraises_on_error():
    db = make_db()
    db.commit.side_effect = RuntimeError("commit failed")

    with pytest.raises(RuntimeError, match="commit failed"):
        await create_room_user(db, room_id=10, user_id=5)

    db.rollback.assert_awaited_once()
    db.refresh.assert_not_awaited()


# read_role_room_user

async def test_read_role_room_user_returns_membership_when_found():
    room_user = make_room_user(role="player")
    db = make_db_with_scalar(room_user)

    result = await read_role_room_user(db, room_id=10, user_id=5)

    assert result is room_user
    db.rollback.assert_not_awaited()


async def test_read_role_room_user_returns_none_when_missing():
    db = make_db_with_scalar(None)

    result = await read_role_room_user(db, room_id=10, user_id=5)

    assert result is None
    db.rollback.assert_not_awaited()


async def test_read_role_room_user_rolls_back_and_reraises_on_error():
    db = make_db()
    db.execute.side_effect = RuntimeError("db failed")

    with pytest.raises(RuntimeError, match="db failed"):
        await read_role_room_user(db, room_id=10, user_id=5)

    db.rollback.assert_awaited_once()


# join_room_by_code

async def test_join_room_by_code_creates_player_membership(mock_read_role):
    db = make_db_with_scalar(make_room(id=10))

    result = await join_room_by_code(db, code="ABC123", user_id=5)

    assert result.room_id == 10
    assert result.user_id == 5
    assert result.role == "player"

    mock_read_role.assert_awaited_once_with(db, 10, 5)
    db.add.assert_called_once_with(result)
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(result)
    db.rollback.assert_not_awaited()


async def test_join_room_by_code_returns_none_when_room_does_not_exist(
    mock_read_role
):
    db = make_db_with_scalar(None)

    result = await join_room_by_code(db, code="ABC123", user_id=5)

    assert result is None
    mock_read_role.assert_not_awaited()
    db.add.assert_not_called()
    db.commit.assert_not_awaited()


async def test_join_room_by_code_raises_conflict_when_user_already_joined(
    mock_read_role
):
    db = make_db_with_scalar(make_room(id=10))
    mock_read_role.return_value = make_room_user(role="player")

    with pytest.raises(HTTPException) as exc_info:
        await join_room_by_code(db, code="ABC123", user_id=5)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "User already joined"
    db.add.assert_not_called()
    db.commit.assert_not_awaited()
    db.rollback.assert_not_awaited()


async def test_join_room_by_code_rolls_back_and_reraises_on_commit_error(
    mock_read_role
):
    db = make_db_with_scalar(make_room(id=10))
    db.commit.side_effect = RuntimeError("commit failed")

    with pytest.raises(RuntimeError, match="commit failed"):
        await join_room_by_code(db, code="ABC123", user_id=5)

    db.rollback.assert_awaited_once()
    db.refresh.assert_not_awaited()


async def test_join_room_by_code_rolls_back_and_reraises_on_query_error():
    db = make_db()
    db.execute.side_effect = RuntimeError("db failed")

    with pytest.raises(RuntimeError, match="db failed"):
        await join_room_by_code(db, code="ABC123", user_id=5)

    db.rollback.assert_awaited_once()
