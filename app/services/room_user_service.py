from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.room_users import RoomUser
from app.models.rooms import Room
from app.schemas.types import RoomCode
from fastapi import HTTPException


async def create_room_user(
    db: AsyncSession,
    room_id: int,
    user_id: int
) -> RoomUser:

    try:

        rule_data = {
            "user_id": user_id,
            "room_id": room_id,
            "role": "master",
        }

        room_user = RoomUser(**rule_data)

        db.add(room_user)

        await db.commit()
        await db.refresh(room_user)

        return room_user

    except Exception:

        await db.rollback()
        raise


async def read_role_room_user(
    db: AsyncSession,
    room_id: int,
    user_id: int
) -> RoomUser | None:

    try:

        result = await db.execute(
            select(RoomUser).where(
                RoomUser.room_id == room_id,
                RoomUser.user_id == user_id
            )
        )

        room_user = result.scalar_one_or_none()

        return room_user

    except Exception:

        await db.rollback()
        raise


async def join_room_by_code(
    db: AsyncSession,
    code: RoomCode,
    user_id: int
) -> RoomUser | None:

    try:

        room_result = await db.execute(
            select(Room).where(Room.code == code)
        )

        room = room_result.scalar_one_or_none()

        if not room:
            return None

        room_user = await read_role_room_user(
            db,
            room.id,
            user_id
        )

        user_already_joined = room_user is not None

        if user_already_joined:
            raise HTTPException(
                409,
                detail='User already joined'
            )

        rule_data = {
            "user_id": user_id,
            "room_id": room.id,
            "role": "player",
        }

        room_user = RoomUser(**rule_data)

        db.add(room_user)

        await db.commit()
        await db.refresh(room_user)

        return room_user

    except HTTPException:
        raise

    except Exception:

        await db.rollback()
        raise
