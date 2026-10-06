"""Factories e mocks compartilhados entre os testes.

As factories retornam SimpleNamespace com os campos dos models; cada teste
sobrescreve só o que importa para ele via **overrides.
"""
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.tabletop_schema import TabletopLayer


USER_ID = 1


# Banco de dados

def make_db():
    # spec=AsyncSession: métodos async viram AsyncMock automaticamente
    # e métodos que não existem na sessão real levantam AttributeError
    return MagicMock(spec=AsyncSession)


def make_scalar_result(value):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


def make_scalars_result(items):
    result = MagicMock()
    result.scalars.return_value.all.return_value = items
    return result


def make_all_result(rows):
    result = MagicMock()
    result.all.return_value = rows
    return result


def make_db_with_scalar(value):
    db = make_db()
    db.execute.return_value = make_scalar_result(value)
    return db


def make_db_with_scalars(*values):
    """Cada chamada a db.execute retorna o próximo valor, na ordem."""
    db = make_db()
    db.execute.side_effect = [make_scalar_result(value) for value in values]
    return db


def make_upload_file(filename="image.png"):
    return SimpleNamespace(file=MagicMock(), filename=filename)


# Models

def make_user(**overrides):
    data = {
        "id": USER_ID,
        "username": "gui",
        "email": "gui@email.com",
        "password": "hashed-password",
        "storage_usage": 0,
        "seconds_played": 0,
        "last_room_enter_at": None,
        "profilepic_image_url": "",
        "profilepic_image_size": 0,
        "profilepic_image_public_id": "",
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def make_room(**overrides):
    now = datetime.now(timezone.utc)
    data = {
        "id": 1,
        "room_name": "Sala Teste",
        "code": "ABC123",
        "thumb_image_url": "",
        "thumb_image_size": 0,
        "thumb_image_public_id": "",
        "created_at": now,
        "updated_at": now,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def make_room_user(**overrides):
    data = {
        "id": 1,
        "room_id": 1,
        "user_id": USER_ID,
        "role": "master",
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def make_asset(**overrides):
    data = {
        "id": 1,
        "asset_image_url": "",
        "asset_image_public_id": "",
        "asset_image_file_name": "",
        "layer": TabletopLayer.players,
        "position_x": None,
        "position_y": None,
        "room_id": 1,
        "sheet_id": None,
        "user_id": USER_ID,
    }
    data.update(overrides)
    return SimpleNamespace(**data)
