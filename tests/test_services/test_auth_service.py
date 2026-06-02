from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
from fastapi import HTTPException
from jwt.exceptions import InvalidTokenError

from app.services import auth_service
from app.services.auth_service import (
    REFRESH_TTL_SECONDS,
    authenticate_user,
    consume_refresh_token,
    create_access_token,
    delete_refresh_token,
    get_current_user_id,
    get_current_user_ws_id,
    save_refresh_token,
    validate_refresh_token,
)


def make_user(**overrides):
    data = {
        "id": 1,
        "email": "gui@email.com",
        "password": "hashed-password",
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def make_scalar_result(value):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


def make_db_with_user(user):
    db = MagicMock()
    db.execute = AsyncMock(return_value=make_scalar_result(user))
    return db


def assert_http_exception(exc_info, status_code, detail):
    assert exc_info.value.status_code == status_code
    assert exc_info.value.detail == detail


@pytest.mark.asyncio
@patch("app.services.auth_service.verifify_password", return_value=True)
async def test_authenticate_user_returns_user_when_credentials_are_valid(
    mock_verify
):
    user = make_user()
    db = make_db_with_user(user)

    result = await authenticate_user(
        db,
        email="gui@email.com",
        password="aB123456"
    )

    assert result is user

    db.execute.assert_awaited_once()
    mock_verify.assert_called_once_with("aB123456", "hashed-password")


@pytest.mark.asyncio
@patch("app.services.auth_service.verifify_password")
async def test_authenticate_user_raises_401_when_user_is_missing(
    mock_verify
):
    db = make_db_with_user(None)

    with pytest.raises(HTTPException) as exc_info:
        await authenticate_user(
            db,
            email="missing@email.com",
            password="aB123456"
        )

    assert_http_exception(exc_info, 401, "Invalid credentials")
    db.execute.assert_awaited_once()
    mock_verify.assert_not_called()


@pytest.mark.asyncio
@patch("app.services.auth_service.verifify_password", return_value=False)
async def test_authenticate_user_raises_401_when_password_is_invalid(
    mock_verify
):
    user = make_user()
    db = make_db_with_user(user)

    with pytest.raises(HTTPException) as exc_info:
        await authenticate_user(
            db,
            email="gui@email.com",
            password="wrongPassword1"
        )

    assert_http_exception(exc_info, 401, "Invalid credentials")
    db.execute.assert_awaited_once()
    mock_verify.assert_called_once_with("wrongPassword1", "hashed-password")


@pytest.mark.asyncio
async def test_authenticate_user_reraises_database_error():
    db = MagicMock()
    db.execute = AsyncMock(side_effect=RuntimeError("db failed"))

    with pytest.raises(RuntimeError, match="db failed"):
        await authenticate_user(
            db,
            email="gui@email.com",
            password="aB123456"
        )


@pytest.mark.asyncio
@patch("app.services.auth_service.jwt.decode", return_value={"id": "42"})
async def test_get_current_user_id_returns_id_from_cookie_token(mock_decode):
    result = await get_current_user_id(token="access-token")

    assert result == 42
    mock_decode.assert_called_once_with(
        "access-token",
        auth_service.JWT_SECRET,
        algorithms=[auth_service.JWT_ALGORITHM]
    )


@pytest.mark.asyncio
async def test_get_current_user_id_raises_401_when_token_is_missing():
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_id(token=None)

    assert_http_exception(exc_info, 401, "Invalid credentials")


@pytest.mark.asyncio
@patch("app.services.auth_service.jwt.decode", return_value={})
async def test_get_current_user_id_raises_401_when_payload_has_no_id(
    mock_decode
):
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_id(token="access-token")

    assert_http_exception(exc_info, 401, "Invalid credentials")
    mock_decode.assert_called_once()


@pytest.mark.asyncio
@patch(
    "app.services.auth_service.jwt.decode",
    side_effect=InvalidTokenError()
)
async def test_get_current_user_id_raises_401_when_token_is_invalid(
    mock_decode
):
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_id(token="invalid-token")

    assert_http_exception(exc_info, 401, "Invalid credentials")
    mock_decode.assert_called_once()


@pytest.mark.asyncio
@patch(
    "app.services.auth_service.jwt.decode",
    side_effect=RuntimeError("unexpected")
)
async def test_get_current_user_id_raises_500_on_unexpected_error(
    mock_decode
):
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_id(token="access-token")

    assert_http_exception(exc_info, 500, "Internal server error")
    mock_decode.assert_called_once()


@pytest.mark.asyncio
@patch("app.services.auth_service.jwt.decode", return_value={"id": "7"})
async def test_get_current_user_ws_id_returns_id_from_websocket_cookie(
    mock_decode
):
    websocket = SimpleNamespace(cookies={"accessToken": "access-token"})

    result = await get_current_user_ws_id(websocket)

    assert result == 7
    mock_decode.assert_called_once_with(
        "access-token",
        auth_service.JWT_SECRET,
        algorithms=[auth_service.JWT_ALGORITHM]
    )


@pytest.mark.asyncio
async def test_get_current_user_ws_id_raises_401_when_cookie_is_missing():
    websocket = SimpleNamespace(cookies={})

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_ws_id(websocket)

    assert_http_exception(exc_info, 401, "Invalid credentials")


@pytest.mark.asyncio
@patch("app.services.auth_service.jwt.decode", return_value={})
async def test_get_current_user_ws_id_raises_401_when_payload_has_no_id(
    mock_decode
):
    websocket = SimpleNamespace(cookies={"accessToken": "access-token"})

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_ws_id(websocket)

    assert_http_exception(exc_info, 401, "Invalid credentials")
    mock_decode.assert_called_once()


@pytest.mark.asyncio
@patch(
    "app.services.auth_service.jwt.decode",
    side_effect=InvalidTokenError()
)
async def test_get_current_user_ws_id_raises_401_when_token_is_invalid(
    mock_decode
):
    websocket = SimpleNamespace(cookies={"accessToken": "invalid-token"})

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_ws_id(websocket)

    assert_http_exception(exc_info, 401, "Invalid credentials")
    mock_decode.assert_called_once()


@pytest.mark.asyncio
@patch(
    "app.services.auth_service.jwt.decode",
    side_effect=RuntimeError("unexpected")
)
async def test_get_current_user_ws_id_raises_500_on_unexpected_error(
    mock_decode
):
    websocket = SimpleNamespace(cookies={"accessToken": "access-token"})

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_ws_id(websocket)

    assert_http_exception(exc_info, 500, "Internal server error")
    mock_decode.assert_called_once()


@patch("app.services.auth_service.jwt.encode", return_value="encoded-token")
def test_create_access_token_adds_expiration_and_encodes_token(mock_encode):
    result = create_access_token(
        {"id": 1},
        expires_delta=timedelta(minutes=30)
    )

    assert result == "encoded-token"

    kwargs = mock_encode.call_args.kwargs
    assert kwargs["payload"]["id"] == 1
    assert "exp" in kwargs["payload"]
    assert kwargs["key"] == auth_service.JWT_SECRET
    assert kwargs["algorithm"] == auth_service.JWT_ALGORITHM


def test_create_access_token_does_not_mutate_original_data():
    data = {"id": 1}

    create_access_token(data, expires_delta=timedelta(minutes=30))

    assert data == {"id": 1}


@pytest.mark.asyncio
@patch("app.services.auth_service.token_hash", return_value="hashed-token")
async def test_save_refresh_token_stores_hashed_token_with_ttl(mock_hash):
    connection = MagicMock()
    connection.setex = AsyncMock()

    await save_refresh_token(1, "refresh-token", connection)

    mock_hash.assert_called_once_with("refresh-token")
    connection.setex.assert_awaited_once_with(
        name="refresh:hashed-token",
        value="1",
        time=REFRESH_TTL_SECONDS
    )


@pytest.mark.asyncio
@patch("app.services.auth_service.token_hash", return_value="hashed-token")
async def test_validate_refresh_token_returns_user_id_when_token_exists(
    mock_hash
):
    connection = MagicMock()
    connection.get = AsyncMock(return_value="15")

    result = await validate_refresh_token("refresh-token", connection)

    assert result == 15
    mock_hash.assert_called_once_with("refresh-token")
    connection.get.assert_awaited_once_with("refresh:hashed-token")


@pytest.mark.asyncio
@patch("app.services.auth_service.token_hash", return_value="hashed-token")
async def test_validate_refresh_token_returns_false_when_token_is_missing(
    mock_hash
):
    connection = MagicMock()
    connection.get = AsyncMock(return_value=None)

    result = await validate_refresh_token("refresh-token", connection)

    assert result is False
    mock_hash.assert_called_once_with("refresh-token")
    connection.get.assert_awaited_once_with("refresh:hashed-token")


@pytest.mark.asyncio
@patch("app.services.auth_service.token_hash", return_value="hashed-token")
async def test_delete_refresh_token_deletes_hashed_token(mock_hash):
    connection = MagicMock()
    connection.delete = AsyncMock()

    await delete_refresh_token("refresh-token", connection)

    mock_hash.assert_called_once_with("refresh-token")
    connection.delete.assert_awaited_once_with("refresh:hashed-token")


@pytest.mark.asyncio
@patch("app.services.auth_service.token_hash", return_value="hashed-token")
async def test_consume_refresh_token_returns_user_id_when_token_exists(
    mock_hash
):
    connection = MagicMock()
    connection.getdel = AsyncMock(return_value="15")

    result = await consume_refresh_token("refresh-token", connection)

    assert result == 15
    mock_hash.assert_called_once_with("refresh-token")
    connection.getdel.assert_awaited_once_with("refresh:hashed-token")


@pytest.mark.asyncio
@patch("app.services.auth_service.token_hash", return_value="hashed-token")
async def test_consume_refresh_token_returns_false_when_token_is_missing(
    mock_hash
):
    connection = MagicMock()
    connection.getdel = AsyncMock(return_value=None)

    result = await consume_refresh_token("refresh-token", connection)

    assert result is False
    mock_hash.assert_called_once_with("refresh-token")
    connection.getdel.assert_awaited_once_with("refresh:hashed-token")
