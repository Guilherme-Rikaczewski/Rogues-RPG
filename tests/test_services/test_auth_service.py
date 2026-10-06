from datetime import datetime, timedelta, timezone
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
from tests.helpers import make_db, make_db_with_scalar, make_user


TEST_SECRET = "test-secret-with-at-least-32-bytes!!"
TEST_ALGORITHM = "HS256"


@pytest.fixture
def jwt_settings(monkeypatch):
    """Configura um segredo real para testar a assinatura de ponta a ponta."""
    monkeypatch.setattr(auth_service, "JWT_SECRET", TEST_SECRET)
    monkeypatch.setattr(auth_service, "JWT_ALGORITHM", TEST_ALGORITHM)


def assert_http_exception(exc_info, status_code, detail):
    assert exc_info.value.status_code == status_code
    assert exc_info.value.detail == detail


# authenticate_user

@patch("app.services.auth_service.verifify_password", return_value=True)
async def test_authenticate_user_returns_user_when_credentials_are_valid(
    mock_verify
):
    user = make_user()
    db = make_db_with_scalar(user)

    result = await authenticate_user(
        db,
        email="gui@email.com",
        password="aB123456"
    )

    assert result is user
    db.execute.assert_awaited_once()
    mock_verify.assert_called_once_with("aB123456", "hashed-password")


@patch("app.services.auth_service.verifify_password")
async def test_authenticate_user_raises_401_when_user_is_missing(mock_verify):
    db = make_db_with_scalar(None)

    with pytest.raises(HTTPException) as exc_info:
        await authenticate_user(
            db,
            email="missing@email.com",
            password="aB123456"
        )

    assert_http_exception(exc_info, 401, "Invalid credentials")
    mock_verify.assert_not_called()


@patch("app.services.auth_service.verifify_password", return_value=False)
async def test_authenticate_user_raises_401_when_password_is_invalid(
    mock_verify
):
    db = make_db_with_scalar(make_user())

    with pytest.raises(HTTPException) as exc_info:
        await authenticate_user(
            db,
            email="gui@email.com",
            password="wrongPassword1"
        )

    assert_http_exception(exc_info, 401, "Invalid credentials")
    mock_verify.assert_called_once_with("wrongPassword1", "hashed-password")


async def test_authenticate_user_reraises_database_error():
    db = make_db()
    db.execute.side_effect = RuntimeError("db failed")

    with pytest.raises(RuntimeError, match="db failed"):
        await authenticate_user(
            db,
            email="gui@email.com",
            password="aB123456"
        )


# get_current_user_id

@patch("app.services.auth_service.jwt.decode", return_value={"id": "42"})
async def test_get_current_user_id_returns_id_from_cookie_token(mock_decode):
    result = await get_current_user_id(token="access-token")

    assert result == 42
    mock_decode.assert_called_once_with(
        "access-token",
        auth_service.JWT_SECRET,
        algorithms=[auth_service.JWT_ALGORITHM]
    )


async def test_get_current_user_id_raises_401_when_token_is_missing():
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_id(token=None)

    assert_http_exception(exc_info, 401, "Invalid credentials")


@patch("app.services.auth_service.jwt.decode", return_value={})
async def test_get_current_user_id_raises_401_when_payload_has_no_id(
    mock_decode
):
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_id(token="access-token")

    assert_http_exception(exc_info, 401, "Invalid credentials")


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


# get_current_user_ws_id

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


async def test_get_current_user_ws_id_raises_401_when_cookie_is_missing():
    websocket = SimpleNamespace(cookies={})

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_ws_id(websocket)

    assert_http_exception(exc_info, 401, "Invalid credentials")


@patch("app.services.auth_service.jwt.decode", return_value={})
async def test_get_current_user_ws_id_raises_401_when_payload_has_no_id(
    mock_decode
):
    websocket = SimpleNamespace(cookies={"accessToken": "access-token"})

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_ws_id(websocket)

    assert_http_exception(exc_info, 401, "Invalid credentials")


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


# create_access_token

@patch("app.services.auth_service.jwt.encode", return_value="encoded-token")
def test_create_access_token_sets_expiration_from_delta(mock_encode):
    before = datetime.now(timezone.utc)

    result = create_access_token(
        {"id": 1},
        expires_delta=timedelta(minutes=30)
    )

    after = datetime.now(timezone.utc)

    assert result == "encoded-token"

    kwargs = mock_encode.call_args.kwargs
    assert kwargs["payload"]["id"] == 1
    expire = kwargs["payload"]["exp"]
    assert before + timedelta(minutes=30) <= expire
    assert expire <= after + timedelta(minutes=30)
    assert kwargs["key"] == auth_service.JWT_SECRET
    assert kwargs["algorithm"] == auth_service.JWT_ALGORITHM


def test_create_access_token_does_not_mutate_original_data(jwt_settings):
    data = {"id": 1}

    create_access_token(data, expires_delta=timedelta(minutes=30))

    assert data == {"id": 1}


# JWT de ponta a ponta (sem mock do PyJWT)

async def test_access_token_round_trip_returns_user_id(jwt_settings):
    token = create_access_token(
        {"id": 42},
        expires_delta=timedelta(minutes=5)
    )

    assert await get_current_user_id(token=token) == 42


async def test_access_token_round_trip_works_for_websocket(jwt_settings):
    token = create_access_token(
        {"id": 42},
        expires_delta=timedelta(minutes=5)
    )
    websocket = SimpleNamespace(cookies={"accessToken": token})

    assert await get_current_user_ws_id(websocket) == 42


async def test_expired_access_token_is_rejected(jwt_settings):
    token = create_access_token(
        {"id": 42},
        expires_delta=timedelta(seconds=-1)
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_id(token=token)

    assert_http_exception(exc_info, 401, "Invalid credentials")


async def test_token_signed_with_other_secret_is_rejected(jwt_settings):
    forged_token = jwt.encode(
        {"id": 42},
        "another-secret-with-at-least-32-bytes!",
        algorithm=TEST_ALGORITHM
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_id(token=forged_token)

    assert_http_exception(exc_info, 401, "Invalid credentials")


async def test_unsigned_token_is_rejected(jwt_settings):
    # Ataque clássico: token com alg "none" e sem assinatura
    unsigned_token = jwt.encode({"id": 42}, None, algorithm="none")

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_id(token=unsigned_token)

    assert_http_exception(exc_info, 401, "Invalid credentials")


# Refresh token (Redis)

def make_redis(**methods):
    connection = MagicMock()
    for name, return_value in methods.items():
        setattr(connection, name, AsyncMock(return_value=return_value))
    return connection


@patch("app.services.auth_service.token_hash", return_value="hashed-token")
async def test_save_refresh_token_stores_hashed_token_with_ttl(mock_hash):
    connection = make_redis(setex=None)

    await save_refresh_token(1, "refresh-token", connection)

    mock_hash.assert_called_once_with("refresh-token")
    connection.setex.assert_awaited_once_with(
        name="refresh:hashed-token",
        value="1",
        time=REFRESH_TTL_SECONDS
    )


@patch("app.services.auth_service.token_hash", return_value="hashed-token")
async def test_validate_refresh_token_returns_user_id_when_token_exists(
    mock_hash
):
    connection = make_redis(get="15")

    result = await validate_refresh_token("refresh-token", connection)

    assert result == 15
    connection.get.assert_awaited_once_with("refresh:hashed-token")


@patch("app.services.auth_service.token_hash", return_value="hashed-token")
async def test_validate_refresh_token_returns_false_when_token_is_missing(
    mock_hash
):
    connection = make_redis(get=None)

    result = await validate_refresh_token("refresh-token", connection)

    assert result is False
    connection.get.assert_awaited_once_with("refresh:hashed-token")


@patch("app.services.auth_service.token_hash", return_value="hashed-token")
async def test_delete_refresh_token_deletes_hashed_token(mock_hash):
    connection = make_redis(delete=None)

    await delete_refresh_token("refresh-token", connection)

    connection.delete.assert_awaited_once_with("refresh:hashed-token")


@patch("app.services.auth_service.token_hash", return_value="hashed-token")
async def test_consume_refresh_token_returns_user_id_when_token_exists(
    mock_hash
):
    connection = make_redis(getdel="15")

    result = await consume_refresh_token("refresh-token", connection)

    assert result == 15
    connection.getdel.assert_awaited_once_with("refresh:hashed-token")


@patch("app.services.auth_service.token_hash", return_value="hashed-token")
async def test_consume_refresh_token_returns_false_when_token_is_missing(
    mock_hash
):
    connection = make_redis(getdel=None)

    result = await consume_refresh_token("refresh-token", connection)

    assert result is False
    connection.getdel.assert_awaited_once_with("refresh:hashed-token")


async def test_refresh_token_is_stored_hashed_not_in_plain_text():
    # Sem mock de token_hash: o token original nunca pode virar a chave
    connection = make_redis(setex=None)

    await save_refresh_token(1, "plain-refresh-token", connection)

    key = connection.setex.call_args.kwargs["name"]
    assert "plain-refresh-token" not in key
    assert key.startswith("refresh:")
