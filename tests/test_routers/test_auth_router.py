from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from tests.helpers import make_user


LOGIN_FORM = {"username": "gui@email.com", "password": "aB123456"}


@pytest.fixture
def auth_service():
    """Mocka o service e o gerador de token usados pelo auth_router."""
    with (
        patch(
            "app.routers.auth_router.aus.authenticate_user",
            new_callable=AsyncMock
        ) as authenticate_user,
        patch(
            "app.routers.auth_router.aus.create_access_token",
            return_value="fake_access_token"
        ) as create_access_token,
        patch(
            "app.routers.auth_router.create_opaque_token",
            return_value="fake_refresh_token"
        ) as create_opaque_token,
        patch(
            "app.routers.auth_router.aus.save_refresh_token",
            new_callable=AsyncMock
        ) as save_refresh_token,
        patch(
            "app.routers.auth_router.aus.consume_refresh_token",
            new_callable=AsyncMock
        ) as consume_refresh_token,
        patch(
            "app.routers.auth_router.aus.validate_refresh_token",
            new_callable=AsyncMock
        ) as validate_refresh_token,
        patch(
            "app.routers.auth_router.aus.delete_refresh_token",
            new_callable=AsyncMock
        ) as delete_refresh_token,
    ):
        authenticate_user.return_value = make_user(id=1)
        yield MagicMock(
            authenticate_user=authenticate_user,
            create_access_token=create_access_token,
            create_opaque_token=create_opaque_token,
            save_refresh_token=save_refresh_token,
            consume_refresh_token=consume_refresh_token,
            validate_refresh_token=validate_refresh_token,
            delete_refresh_token=delete_refresh_token,
        )


def get_set_cookie(response, name):
    """Retorna o header Set-Cookie de um cookie, em minúsculas."""
    for header in response.headers.get_list("set-cookie"):
        if header.startswith(f"{name}="):
            return header.lower()
    raise AssertionError(f"Cookie {name} não foi definido")


# login

def test_login_success_sets_access_and_refresh_cookies(client, auth_service):
    response = client.post("/auth/login/", data=LOGIN_FORM)

    assert response.status_code == 200
    assert response.json() == {"message": "Login successful"}
    assert response.cookies.get("accessToken") == "fake_access_token"
    assert response.cookies.get("refreshToken") == "fake_refresh_token"

    auth_service.authenticate_user.assert_awaited_once()
    _, email, password = auth_service.authenticate_user.call_args.args
    assert (email, password) == ("gui@email.com", "aB123456")

    assert auth_service.create_access_token.call_args.args[0] == {"id": 1}
    auth_service.save_refresh_token.assert_awaited_once()
    assert auth_service.save_refresh_token.call_args.args[:2] == (
        1,
        "fake_refresh_token"
    )


@pytest.mark.parametrize("cookie", ["accessToken", "refreshToken"])
def test_login_cookies_are_httponly_and_samesite_strict(
    client,
    auth_service,
    cookie
):
    response = client.post("/auth/login/", data=LOGIN_FORM)

    header = get_set_cookie(response, cookie)
    # HttpOnly: JavaScript da página não consegue ler o token (protege de XSS)
    assert "httponly" in header
    # SameSite=strict: o navegador não envia o cookie em requisições de
    # outros sites (protege de CSRF)
    assert "samesite=strict" in header
    assert "path=/" in header


@pytest.mark.parametrize(
    "cookie, max_age",
    [("accessToken", 60 * 60), ("refreshToken", 60 * 60 * 24 * 7)],
)
def test_login_cookies_expire_at_expected_time(
    client,
    auth_service,
    cookie,
    max_age
):
    response = client.post("/auth/login/", data=LOGIN_FORM)

    assert f"max-age={max_age}" in get_set_cookie(response, cookie)


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Segurança: os cookies usam secure=False fixo, então o token pode "
        "trafegar por HTTP sem criptografia. Deveria ser True em produção "
        "(ex.: configurável por variável de ambiente)"
    ),
)
@pytest.mark.parametrize("cookie", ["accessToken", "refreshToken"])
def test_login_cookies_are_secure(client, auth_service, cookie):
    response = client.post("/auth/login/", data=LOGIN_FORM)

    assert "secure" in get_set_cookie(response, cookie)


def test_login_returns_401_with_invalid_credentials(client, auth_service):
    auth_service.authenticate_user.side_effect = HTTPException(
        401,
        detail="Invalid credentials"
    )

    response = client.post("/auth/login/", data=LOGIN_FORM)

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}
    assert "set-cookie" not in response.headers
    auth_service.save_refresh_token.assert_not_awaited()


def test_login_returns_401_when_user_is_not_authenticated(
    client,
    auth_service
):
    auth_service.authenticate_user.return_value = None

    response = client.post("/auth/login/", data=LOGIN_FORM)

    assert response.status_code == 401
    assert "set-cookie" not in response.headers


def test_login_returns_422_without_password(client, auth_service):
    response = client.post(
        "/auth/login/",
        data={"username": "gui@email.com"}
    )

    assert response.status_code == 422
    auth_service.authenticate_user.assert_not_awaited()


def test_login_returns_500_on_unexpected_error(client, auth_service):
    auth_service.save_refresh_token.side_effect = RuntimeError(
        "redis offline"
    )

    response = client.post("/auth/login/", data=LOGIN_FORM)

    assert response.status_code == 500
    assert "set-cookie" not in response.headers


# refresh

def test_refresh_rotates_tokens(client, auth_service):
    auth_service.consume_refresh_token.return_value = 1
    auth_service.create_opaque_token.return_value = "new_refresh_token"
    client.cookies.set("refreshToken", "old_refresh_token")

    response = client.post("/auth/refresh/")

    assert response.status_code == 200
    assert response.json() == {"message": "Refresh successful"}
    assert response.cookies.get("accessToken") == "fake_access_token"
    assert response.cookies.get("refreshToken") == "new_refresh_token"

    # o token antigo é consumido (uso único) antes de salvar o novo
    assert auth_service.consume_refresh_token.call_args.args[0] == (
        "old_refresh_token"
    )
    assert auth_service.save_refresh_token.call_args.args[:2] == (
        1,
        "new_refresh_token"
    )


def test_refresh_returns_401_without_cookie(client, auth_service):
    response = client.post("/auth/refresh/")

    assert response.status_code == 401
    auth_service.consume_refresh_token.assert_not_awaited()


def test_refresh_returns_401_with_unknown_or_reused_token(
    client,
    auth_service
):
    auth_service.consume_refresh_token.return_value = False
    client.cookies.set("refreshToken", "already_used_token")

    response = client.post("/auth/refresh/")

    assert response.status_code == 401
    assert "set-cookie" not in response.headers
    auth_service.save_refresh_token.assert_not_awaited()


def test_refresh_returns_500_on_unexpected_error(client, auth_service):
    auth_service.consume_refresh_token.side_effect = RuntimeError(
        "redis offline"
    )
    client.cookies.set("refreshToken", "refresh_token")

    response = client.post("/auth/refresh/")

    assert response.status_code == 500


# logout

def test_logout_revokes_valid_refresh_token_and_clears_cookies(
    client,
    auth_service
):
    auth_service.validate_refresh_token.return_value = 1
    client.cookies.set("refreshToken", "refresh_token")

    response = client.post("/auth/logout/")

    assert response.status_code == 200
    assert response.json() == {"message": "Logout successful"}
    assert auth_service.delete_refresh_token.call_args.args[0] == (
        "refresh_token"
    )
    for cookie in ("accessToken", "refreshToken"):
        assert "max-age=0" in get_set_cookie(response, cookie)


def test_logout_with_invalid_token_does_not_delete_anything(
    client,
    auth_service
):
    auth_service.validate_refresh_token.return_value = False
    client.cookies.set("refreshToken", "invalid_token")

    response = client.post("/auth/logout/")

    assert response.status_code == 200
    auth_service.delete_refresh_token.assert_not_awaited()


def test_logout_without_cookie_still_clears_cookies(client, auth_service):
    response = client.post("/auth/logout/")

    assert response.status_code == 200
    auth_service.validate_refresh_token.assert_not_awaited()
    assert "max-age=0" in get_set_cookie(response, "accessToken")
