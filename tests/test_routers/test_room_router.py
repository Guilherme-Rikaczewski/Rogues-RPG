from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.schemas.tabletop_schema import TabletopLayer
from tests.helpers import USER_ID, make_asset, make_room, make_room_user


MAX_FILE_SIZE = 10 * 1024 * 1024

SERVICES = {
    "create_room": "app.routers.room_router.rs.create_room",
    "update_room": "app.routers.room_router.rs.update_room",
    "get_room": "app.routers.room_router.rs.get_room",
    "get_all_rooms_from_user": "app.routers.room_router.rs.get_all_rooms_from_user",
    "get_recent_rooms_from_user": "app.routers.room_router.rs.get_recent_rooms_from_user",
    "delete_room": "app.routers.room_router.rs.delete_room",
    "upload_room_thumb_image": "app.routers.room_router.rs.upload_room_thumb_image",
    "create_room_user": "app.routers.room_router.rus.create_room_user",
    "read_role_room_user": "app.routers.room_router.rus.read_role_room_user",
    "join_room_by_code": "app.routers.room_router.rus.join_room_by_code",
    "create_asset": "app.routers.room_router.ts.create_asset",
    "upload_asset_image": "app.routers.room_router.ts.upload_asset_image",
    "get_all_assets_from_user_in_room": "app.routers.room_router.ts.get_all_assets_from_user_in_room",
}


@pytest.fixture
def services():
    """Mocka todos os services usados pelo room_router.

    Por padrão o usuário é mestre da sala 1 e a sala existe.
    """
    mocks = {}
    patchers = []
    for name, target in SERVICES.items():
        patcher = patch(target, new_callable=AsyncMock)
        mocks[name] = patcher.start()
        patchers.append(patcher)

    mocks["get_room"].return_value = make_room()
    mocks["update_room"].return_value = make_room()
    mocks["read_role_room_user"].return_value = make_room_user(role="master")

    yield SimpleNamespace(**mocks)

    for patcher in patchers:
        patcher.stop()


def image_file(content=b"fake image", content_type="image/png"):
    return {"file": ("image.png", content, content_type)}


# Sem autenticação

@pytest.mark.parametrize(
    "method, url",
    [
        ("post", "/rooms/"),
        ("get", "/rooms/1"),
        ("patch", "/rooms/1"),
        ("delete", "/rooms/1"),
        ("get", "/rooms/all/"),
        ("get", "/rooms/recent/"),
        ("post", "/rooms/join/ABC123"),
        ("get", "/rooms/assets/1"),
    ],
)
def test_room_routes_require_authentication(client, services, method, url):
    response = client.request(method, url, json={"room_name": "Sala"})

    assert response.status_code == 401


# POST /rooms/

def test_create_room_makes_creator_master(auth_client, services):
    services.create_room.return_value = make_room(room_name="Sala Teste")
    services.create_room_user.return_value = make_room_user(role="master")

    response = auth_client.post("/rooms/", json={"room_name": "Sala Teste"})

    assert response.status_code == 200
    assert response.json()["room_name"] == "Sala Teste"
    assert response.json()["role"] == "master"
    room_id, user_id = services.create_room_user.call_args.args[1:]
    assert (room_id, user_id) == (1, USER_ID)


def test_create_room_returns_422_with_empty_name(auth_client, services):
    response = auth_client.post("/rooms/", json={"room_name": ""})

    assert response.status_code == 422
    services.create_room.assert_not_awaited()


def test_create_room_returns_500_on_service_error(auth_client, services):
    services.create_room.side_effect = RuntimeError("db failed")

    response = auth_client.post("/rooms/", json={"room_name": "Sala Teste"})

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}


# PATCH /rooms/{room_id}

def test_update_room_as_master(auth_client, services):
    services.update_room.return_value = make_room(room_name="Nova")

    response = auth_client.patch("/rooms/1", json={"room_name": "Nova"})

    assert response.status_code == 200
    assert response.json()["room_name"] == "Nova"
    services.update_room.assert_awaited_once()


@pytest.mark.parametrize("room_user", [None, make_room_user(role="player")])
def test_update_room_returns_403_when_not_master(
    auth_client,
    services,
    room_user
):
    services.read_role_room_user.return_value = room_user

    response = auth_client.patch("/rooms/1", json={"room_name": "Nova"})

    assert response.status_code == 403
    services.update_room.assert_not_awaited()


def test_update_room_returns_404_when_room_missing(auth_client, services):
    services.update_room.return_value = None

    response = auth_client.patch("/rooms/1", json={"room_name": "Nova"})

    assert response.status_code == 404


# GET /rooms/{room_id}

def test_read_room_returns_room_with_user_role(auth_client, services):
    services.read_role_room_user.return_value = make_room_user(role="player")

    response = auth_client.get("/rooms/1")

    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["role"] == "player"


def test_read_room_returns_404_when_room_missing(auth_client, services):
    services.get_room.return_value = None

    response = auth_client.get("/rooms/999")

    assert response.status_code == 404


def test_read_room_returns_403_when_user_not_in_room(auth_client, services):
    services.read_role_room_user.return_value = None

    response = auth_client.get("/rooms/1")

    assert response.status_code == 403


# GET /rooms/all/ e /rooms/recent/

def test_read_all_rooms_returns_service_result(auth_client, services):
    services.get_all_rooms_from_user.return_value = [{"id": 1}, {"id": 2}]

    response = auth_client.get("/rooms/all/")

    assert response.status_code == 200
    assert response.json() == [{"id": 1}, {"id": 2}]
    assert services.get_all_rooms_from_user.call_args.args[1] == USER_ID


def test_read_all_rooms_returns_500_on_service_error(auth_client, services):
    services.get_all_rooms_from_user.side_effect = RuntimeError("db failed")

    response = auth_client.get("/rooms/all/")

    assert response.status_code == 500


def test_read_recent_rooms_returns_service_result(auth_client, services):
    services.get_recent_rooms_from_user.return_value = [{"id": 1}]

    response = auth_client.get("/rooms/recent/")

    assert response.status_code == 200
    assert response.json() == [{"id": 1}]


# DELETE /rooms/{room_id}

def test_delete_room_as_master_returns_204(auth_client, services):
    services.delete_room.return_value = True

    response = auth_client.delete("/rooms/1")

    assert response.status_code == 204
    services.delete_room.assert_awaited_once()


@pytest.mark.parametrize("room_user", [None, make_room_user(role="player")])
def test_delete_room_returns_403_when_not_master(
    auth_client,
    services,
    room_user
):
    services.read_role_room_user.return_value = room_user

    response = auth_client.delete("/rooms/1")

    assert response.status_code == 403
    services.delete_room.assert_not_awaited()


def test_delete_room_returns_404_when_room_missing(auth_client, services):
    services.delete_room.return_value = False

    response = auth_client.delete("/rooms/1")

    assert response.status_code == 404


# POST /rooms/join/{room_code}

def test_join_room_returns_room_as_player(auth_client, services):
    services.join_room_by_code.return_value = make_room_user(
        room_id=10,
        role="player"
    )
    services.get_room.return_value = make_room(id=10, room_name="Sala RPG")

    response = auth_client.post("/rooms/join/ABC123")

    assert response.status_code == 200
    assert response.json()["room_name"] == "Sala RPG"
    assert response.json()["role"] == "player"
    services.get_room.assert_awaited_once()
    assert services.get_room.call_args.args[1] == 10


def test_join_room_normalizes_code_to_uppercase(auth_client, services):
    services.join_room_by_code.return_value = make_room_user(role="player")

    auth_client.post("/rooms/join/abc123")

    assert services.join_room_by_code.call_args.args[1] == "ABC123"


def test_join_room_returns_404_when_code_does_not_exist(auth_client, services):
    services.join_room_by_code.return_value = None

    response = auth_client.post("/rooms/join/ZZZ999")

    assert response.status_code == 404
    services.get_room.assert_not_awaited()


def test_join_room_returns_422_with_invalid_code_length(auth_client, services):
    response = auth_client.post("/rooms/join/ABC")

    assert response.status_code == 422
    services.join_room_by_code.assert_not_awaited()


# PATCH /rooms/upload/thumb/{room_id}

def test_upload_thumb_as_master(auth_client, services):
    services.upload_room_thumb_image.return_value = make_room(
        thumb_image_url="https://cdn.test/thumb.png"
    )

    response = auth_client.patch("/rooms/upload/thumb/1", files=image_file())

    assert response.status_code == 200
    assert response.json()["thumb_image_url"] == "https://cdn.test/thumb.png"


def test_upload_thumb_returns_403_for_player(auth_client, services):
    services.read_role_room_user.return_value = make_room_user(role="player")

    response = auth_client.patch("/rooms/upload/thumb/1", files=image_file())

    assert response.status_code == 403
    services.upload_room_thumb_image.assert_not_awaited()


def test_upload_thumb_rejects_invalid_file_type(auth_client, services):
    response = auth_client.patch(
        "/rooms/upload/thumb/1",
        files=image_file(content_type="application/pdf")
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid file type"
    services.upload_room_thumb_image.assert_not_awaited()


def test_upload_thumb_returns_400_when_storage_exceeded(auth_client, services):
    services.upload_room_thumb_image.side_effect = ValueError(
        "The image exceeds its storage limit."
    )

    response = auth_client.patch("/rooms/upload/thumb/1", files=image_file())

    assert response.status_code == 400
    assert response.json()["detail"] == "The image exceeds its storage limit."


# PATCH /rooms/upload/asset/{room_id}

def test_create_asset_with_image(auth_client, services):
    services.create_asset.return_value = SimpleNamespace(id=7)
    services.upload_asset_image.return_value = make_asset(
        id=7,
        asset_image_url="https://cdn.test/token.png"
    )

    response = auth_client.patch("/rooms/upload/asset/10", files=image_file())

    assert response.status_code == 200
    assert response.json()["id"] == 7
    assert response.json()["asset_image_url"] == "https://cdn.test/token.png"

    asset_data = services.create_asset.call_args.kwargs["asset_data"]
    assert asset_data.room_id == 10
    assert asset_data.user_id == USER_ID
    assert services.upload_asset_image.call_args.kwargs["asset_id"] == 7


def test_create_asset_with_image_rejects_invalid_file_type(
    auth_client,
    services
):
    response = auth_client.patch(
        "/rooms/upload/asset/10",
        files={"file": ("notes.txt", b"text", "text/plain")}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid file type"
    services.create_asset.assert_not_awaited()


def test_create_asset_with_image_rejects_file_over_10mb(auth_client, services):
    response = auth_client.patch(
        "/rooms/upload/asset/10",
        files=image_file(content=b"0" * (MAX_FILE_SIZE + 1))
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "File exceeds maximum size: 10MB"
    services.create_asset.assert_not_awaited()


def test_create_asset_with_image_accepts_file_of_exactly_10mb(
    auth_client,
    services
):
    services.create_asset.return_value = SimpleNamespace(id=7)
    services.upload_asset_image.return_value = make_asset(id=7)

    response = auth_client.patch(
        "/rooms/upload/asset/10",
        files=image_file(content=b"0" * MAX_FILE_SIZE)
    )

    assert response.status_code == 200


def test_create_asset_with_image_returns_400_when_storage_exceeded(
    auth_client,
    services
):
    services.create_asset.return_value = SimpleNamespace(id=7)
    services.upload_asset_image.side_effect = ValueError(
        "The image exceeds its storage limit."
    )

    response = auth_client.patch("/rooms/upload/asset/10", files=image_file())

    assert response.status_code == 400
    assert response.json()["detail"] == "The image exceeds its storage limit."


def test_create_asset_with_image_returns_404_when_upload_returns_none(
    auth_client,
    services
):
    services.create_asset.return_value = SimpleNamespace(id=7)
    services.upload_asset_image.return_value = None

    response = auth_client.patch("/rooms/upload/asset/10", files=image_file())

    assert response.status_code == 404


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Segurança (IDOR): a rota não verifica se o usuário participa da "
        "sala antes de criar o asset nela"
    ),
)
def test_create_asset_with_image_returns_403_when_user_not_in_room(
    auth_client,
    services
):
    services.read_role_room_user.return_value = None
    services.create_asset.return_value = SimpleNamespace(id=7)
    services.upload_asset_image.return_value = make_asset(id=7)

    response = auth_client.patch("/rooms/upload/asset/10", files=image_file())

    assert response.status_code == 403


# GET /rooms/assets/{room_id}

def test_read_all_assets(auth_client, services):
    services.read_role_room_user.return_value = make_room_user(role="player")
    services.get_all_assets_from_user_in_room.return_value = [
        make_asset(id=1),
        make_asset(id=2, position_x="10", position_y="20",
                   layer=TabletopLayer.map),
    ]

    response = auth_client.get("/rooms/assets/10")

    assert response.status_code == 200
    assert [asset["id"] for asset in response.json()] == [1, 2]
    assert response.json()[1]["layer"] == "map"
    user_id, room_id = (
        services.get_all_assets_from_user_in_room.call_args.args[1:]
    )
    assert (user_id, room_id) == (USER_ID, 10)


def test_read_all_assets_returns_404_when_room_missing(auth_client, services):
    services.get_room.return_value = None

    response = auth_client.get("/rooms/assets/999")

    assert response.status_code == 404
    services.get_all_assets_from_user_in_room.assert_not_awaited()


def test_read_all_assets_returns_403_when_user_not_in_room(
    auth_client,
    services
):
    services.read_role_room_user.return_value = None

    response = auth_client.get("/rooms/assets/10")

    assert response.status_code == 403
    services.get_all_assets_from_user_in_room.assert_not_awaited()
