from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


@patch("app.routers.auth_router.aus.authenticate_user")
@patch("app.routers.auth_router.aus.create_access_token")
@patch("app.routers.auth_router.create_opaque_token")
@patch("app.routers.auth_router.aus.save_refresh_token")
def test_login_success(
    mock_save_refresh_token,
    mock_create_opaque_token,
    mock_create_access_token,
    mock_authenticate_user
):
    fake_user = MagicMock()
    fake_user.id = 1

    mock_authenticate_user.return_value = fake_user
    mock_create_access_token.return_value = "fake_access_token"
    mock_create_opaque_token.return_value = "fake_refresh_token"

    response = client.post(
        "auth/login/",
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

    mock_authenticate_user.assert_called_once()

    mock_create_access_token.assert_called_once()

    mock_create_opaque_token.assert_called_once()

    mock_save_refresh_token.assert_called_once()
