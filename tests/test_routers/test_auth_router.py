from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


async def override_get_db():
    yield MagicMock()


@patch("app.routers.auth_router.aus.authenticate_user", new_callable=AsyncMock)
@patch("app.routers.auth_router.aus.create_access_token")
@patch("app.routers.auth_router.create_opaque_token")
@patch("app.routers.auth_router.aus.save_refresh_token", new_callable=AsyncMock)
def test_login_success(
    mock_save_refresh_token,
    mock_create_opaque_token,
    mock_create_access_token,
    mock_authenticate_user
):
    fake_user = MagicMock()
    fake_user.id = 1

    app.dependency_overrides[get_db] = override_get_db

    mock_authenticate_user.return_value = fake_user
    mock_create_access_token.return_value = "fake_access_token"
    mock_create_opaque_token.return_value = "fake_refresh_token"

    response = client.post(
        "/auth/login/",
        data={
            "username": "gui@email.com",
            "password": "aB123456"
        }
    )

    assert response.status_code == 200

    assert response.json() == {
        "message": "Login successful"
    }

    assert response.cookies.get("accessToken") == "fake_access_token"

    assert response.cookies.get("refreshToken") == "fake_refresh_token"

    mock_authenticate_user.assert_awaited_once()

    mock_create_access_token.assert_called_once()

    mock_create_opaque_token.assert_called_once()

    mock_save_refresh_token.assert_awaited_once()
