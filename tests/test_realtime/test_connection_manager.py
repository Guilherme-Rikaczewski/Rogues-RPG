from unittest.mock import AsyncMock, MagicMock

from app.realtime.connection.manager import ConnectionManager


ROOM_CODE = "ABC123"


def make_websocket():
    websocket = MagicMock()
    websocket.accept = AsyncMock()
    websocket.close = AsyncMock()
    websocket.send_json = AsyncMock()
    return websocket


async def test_connect_accepts_and_registers_websocket():
    manager = ConnectionManager()
    websocket = make_websocket()

    await manager.connect(ROOM_CODE, 1, websocket)

    websocket.accept.assert_awaited_once()
    assert manager.active_connections == {ROOM_CODE: {1: websocket}}


async def test_connect_closes_previous_session_of_same_user():
    manager = ConnectionManager()
    old_websocket = make_websocket()
    new_websocket = make_websocket()

    await manager.connect(ROOM_CODE, 1, old_websocket)
    await manager.connect(ROOM_CODE, 1, new_websocket)

    old_websocket.close.assert_awaited_once_with(
        code=4001,
        reason="Another session connected"
    )
    assert manager.active_connections[ROOM_CODE][1] is new_websocket


async def test_disconnect_removes_user_and_empty_room():
    manager = ConnectionManager()
    await manager.connect(ROOM_CODE, 1, make_websocket())

    manager.disconnect(ROOM_CODE, 1, active_websocket=True)

    assert ROOM_CODE not in manager.active_connections


async def test_disconnect_keeps_room_with_other_users():
    manager = ConnectionManager()
    other_websocket = make_websocket()
    await manager.connect(ROOM_CODE, 1, make_websocket())
    await manager.connect(ROOM_CODE, 2, other_websocket)

    manager.disconnect(ROOM_CODE, 1, active_websocket=True)

    assert manager.active_connections == {ROOM_CODE: {2: other_websocket}}


async def test_disconnect_inactive_websocket_keeps_user_registered():
    manager = ConnectionManager()
    websocket = make_websocket()
    await manager.connect(ROOM_CODE, 1, websocket)

    manager.disconnect(ROOM_CODE, 1, active_websocket=False)

    assert manager.active_connections[ROOM_CODE][1] is websocket


def test_disconnect_unknown_room_does_nothing():
    manager = ConnectionManager()

    manager.disconnect("ZZZ999", 1, active_websocket=True)

    assert manager.active_connections == {}


async def test_send_to_user_sends_only_to_target():
    manager = ConnectionManager()
    target = make_websocket()
    other = make_websocket()
    await manager.connect(ROOM_CODE, 1, target)
    await manager.connect(ROOM_CODE, 2, other)

    await manager.send_to_user(ROOM_CODE, 1, {"event": "ping"})

    target.send_json.assert_awaited_once_with({"event": "ping"})
    other.send_json.assert_not_awaited()


async def test_send_to_user_ignores_unknown_room_or_user():
    manager = ConnectionManager()
    websocket = make_websocket()
    await manager.connect(ROOM_CODE, 1, websocket)

    await manager.send_to_user("ZZZ999", 1, {"event": "ping"})
    await manager.send_to_user(ROOM_CODE, 999, {"event": "ping"})

    websocket.send_json.assert_not_awaited()


async def test_broadcast_sends_to_everyone_in_room():
    manager = ConnectionManager()
    first = make_websocket()
    second = make_websocket()
    other_room = make_websocket()
    await manager.connect(ROOM_CODE, 1, first)
    await manager.connect(ROOM_CODE, 2, second)
    await manager.connect("XYZ789", 3, other_room)

    await manager.broadcast(ROOM_CODE, {"event": "ping"})

    first.send_json.assert_awaited_once_with({"event": "ping"})
    second.send_json.assert_awaited_once_with({"event": "ping"})
    other_room.send_json.assert_not_awaited()


async def test_broadcast_to_unknown_room_does_nothing():
    manager = ConnectionManager()

    await manager.broadcast("ZZZ999", {"event": "ping"})

    assert manager.active_connections == {}


async def test_broadcast_removes_users_whose_socket_fails(capsys):
    manager = ConnectionManager()
    broken = make_websocket()
    broken.send_json.side_effect = RuntimeError("connection lost")
    healthy = make_websocket()
    await manager.connect(ROOM_CODE, 1, broken)
    await manager.connect(ROOM_CODE, 2, healthy)

    await manager.broadcast(ROOM_CODE, {"event": "ping"})

    healthy.send_json.assert_awaited_once_with({"event": "ping"})
    assert manager.active_connections == {ROOM_CODE: {2: healthy}}
