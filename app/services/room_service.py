from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from app.models.rooms import Room
from app.models.users import User
from app.models.room_users import RoomUser
from app.schemas.room_schema import (
    RoomCreate,
    RoomUpdate
)
from app.utils.code import generate_code
from app.utils.user_file_manager import (
    upload_image,
    delete_image
)
from fastapi import UploadFile
from sqlalchemy.orm import aliased


async def create_room(
    db: AsyncSession,
    room_data: RoomCreate
) -> Room:

    try:

        while True:

            room = Room(**room_data.model_dump())

            room.code = generate_code()

            try:

                db.add(room)

                await db.commit()
                await db.refresh(room)

                break

            except IntegrityError:

                await db.rollback()

            except Exception:

                await db.rollback()
                raise

        return room

    except Exception:
        raise


async def update_room(
    db: AsyncSession,
    room_id: int,
    room_data: RoomUpdate
) -> Room | None:

    try:

        result = await db.execute(
            select(Room).where(Room.id == room_id)
        )

        room = result.scalar_one_or_none()

        if not room:
            return None

        update_data = room_data.model_dump(
            exclude_unset=True,
            exclude_none=True
        )

        for k, v in update_data.items():

            if isinstance(v, str):
                v = v.strip()

            setattr(room, k, v)

        await db.commit()
        await db.refresh(room)

        return room

    except Exception:

        await db.rollback()
        raise


async def get_room(
    db: AsyncSession,
    room_id: int
) -> Room | None:

    try:

        room = await db.get(Room, room_id)

        return room

    except Exception:
        raise


async def get_all_rooms_from_user(
    db: AsyncSession,
    user_id: int
) -> list[dict]:

    try:

        room_user_owner = aliased(RoomUser)
        room_user_member = aliased(RoomUser)

        result_query = await db.execute(
            select(
                Room,
                room_user_owner.role.label("role"),
                User.profilepic_image_url
            )
            .join(
                room_user_owner,
                room_user_owner.room_id == Room.id
            )
            .join(
                room_user_member,
                room_user_member.room_id == Room.id
            )
            .join(
                User,
                User.id == room_user_member.user_id
            )
            .where(room_user_owner.user_id == user_id)
            .order_by(Room.room_name)
        )

        rows = result_query.all()

        if not rows:
            return []

        rooms_map = {}

        for room, role, profilepic in rows:

            if room.id not in rooms_map:

                rooms_map[room.id] = {
                    "id": room.id,
                    "room_name": room.room_name,
                    "code": room.code,
                    "role": role,
                    "thumb_image_url": room.thumb_image_url,
                    "created_at": room.created_at,
                    "updated_at": room.updated_at,
                    "members_profilepics": []
                }

            rooms_map[room.id]["members_profilepics"].append(
                profilepic
            )

        return list(rooms_map.values())

    except Exception:
        raise


async def get_recent_rooms_from_user(
    db: AsyncSession,
    user_id: int
) -> list[dict] | None:

    try:

        result_query = await db.execute(
            select(
                Room,
                RoomUser.role.label("role")
            )
            .join(
                RoomUser,
                RoomUser.room_id == Room.id
            )
            .where(RoomUser.user_id == user_id)
            .order_by(RoomUser.last_access.desc())
            .limit(9)
        )

        rooms = result_query.all()

        if not rooms:
            return None

        result = []

        for room, role in rooms:

            result.append({
                "id": room.id,
                "room_name": room.room_name,
                "code": room.code,
                "role": role,
                "thumb_image_url": room.thumb_image_url,
                "created_at": room.created_at,
                "updated_at": room.updated_at,
            })

        return result

    except Exception:
        raise


async def delete_room(
    db: AsyncSession,
    room_id: int
) -> bool:

    try:

        result = await db.execute(
            select(Room).where(Room.id == room_id)
        )

        room = result.scalar_one_or_none()

        if not room:
            return False

        if room.thumb_image_public_id != '':
            delete_image(room.thumb_image_public_id)

        await db.delete(room)

        await db.commit()

        return True

    except Exception:

        await db.rollback()
        raise


async def upload_room_thumb_image(
    db: AsyncSession,
    room_id: int,
    user_id: int,
    file: UploadFile,
) -> Room | None:

    try:

        room_result = await db.execute(
            select(Room).where(Room.id == room_id)
        )

        room = room_result.scalar_one_or_none()

        if not room:
            return None

        image = upload_image(
            file.file,
            user_id,
            img_id=f'thumb_room_{room_id}',
            extra_folder=f'/rooms/{room_id}'
        )

        MAX_ALLOWED_FOR_USER = 50 * 1024 * 1024

        user_result = await db.execute(
            select(User).where(User.id == user_id)
        )

        user = user_result.scalar_one_or_none()

        if not user:
            return None

        storage_without_thumb = max(
            0,
            user.storage_usage - room.thumb_image_size
        )

        future_storage_with_new_thumb = (
            storage_without_thumb + image['size']
        )

        if future_storage_with_new_thumb > MAX_ALLOWED_FOR_USER:

            delete_image(image['public_id'])

            raise ValueError(
                'The image exceeds its storage limit.'
            )

        room.thumb_image_url = image['url']
        room.thumb_image_size = image['size']
        room.thumb_image_public_id = image['public_id']

        user.storage_usage = future_storage_with_new_thumb

        await db.commit()
        await db.refresh(room)

        return room

    except Exception:

        await db.rollback()
        raise
