from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.rooms import Room
from app.models.users import User
from app.models.room_users import RoomUser
from app.schemas.room_schema import RoomCreate, RoomUpdate
from app.utils.code import generate_code
from app.utils.user_file_manager import upload_image, delete_image
from fastapi import UploadFile


def create_room(db: Session, room_data: RoomCreate) -> Room:
    try:
        while True:
            room = Room(**room_data.model_dump())
            room.code = generate_code()

            try:
                db.add(room)
                db.commit()
                db.refresh(room)

                break
            except IntegrityError:
                db.rollback()
            except Exception:
                db.rollback()
                raise

        return room
    except Exception:
        raise


def update_room(
        db: Session,
        room_id: int,
        room_data: RoomUpdate
        ) -> Room | None:
    try:
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            return None

        update_data: dict[str, str] = room_data.model_dump(
            exclude_unset=True, exclude_none=True
        )

        for k, v in update_data.items():
            setattr(room, k, v.strip())

        db.commit()
        db.refresh(room)

        return room
    except Exception:
        db.rollback()
        raise


def get_room(db: Session, room_id: int) -> Room | None:
    try:
        room = db.get(Room, room_id)
        return room
    except Exception:
        raise


def get_all_rooms_from_user(db: Session, user_id: int) -> list[Room] | None:
    try:
        rooms = (
            db.query(
                Room,
                RoomUser.role.label("role")
            )
            .join(RoomUser, RoomUser.room_id == Room.id)
            .filter(RoomUser.user_id == user_id)
            .order_by(Room.room_name)
            .all()
        )
        if not rooms:
            return None

        result: list = []

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


def get_recent_rooms_from_user(db: Session, user_id: int) -> list[Room] | None:
    try:
        rooms = (
            db.query(
                Room,
                RoomUser.role.label("role")
            )
            .join(RoomUser, RoomUser.room_id == Room.id)
            .filter(RoomUser.user_id == user_id)
            .order_by(RoomUser.last_access.desc())
            .limit(9)
            .all()
        )
        if not rooms:
            return None

        result: list = []

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


def delete_room(db: Session, room_id: int) -> bool:
    try:
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            return False
        
        if room.thumb_image_public_id != '':
            delete_image(room.thumb_image_public_id)

        db.delete(room)
        db.commit()
        # db.refresh(room)

        return True
    except Exception:
        db.rollback()
        raise


def upload_room_thumb_image(
    db: Session,
    room_id: int,
    user_id: int,
    file: UploadFile,
) -> Room | None:
    try:
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            return None
        
        image = upload_image(
            file.file, user_id, img_id=f'thumb_room_{room_id}',
            extra_folder=f'/rooms/{room_id}'
        )
        
        MAX_ALLOWED_FOR_USER = 50 * 1024 * 1024
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        storage_without_thumb = max(0, (user.storage_usage - room.thumb_image_size))
        
        future_storage_with_new_thumb = storage_without_thumb + image['size']
        
        if future_storage_with_new_thumb > MAX_ALLOWED_FOR_USER:
            delete_image(image['public_id'])
            raise ValueError('The image exceeds its storage limit.')
        
        room.thumb_image_url = image['url']
        room.thumb_image_size = image['size']
        room.thumb_image_public_id = image['public_id']
        
        user.storage_usage = future_storage_with_new_thumb
        
        db.commit()
        db.refresh(room)
        
        return room
    except Exception:
        db.rollback()
        raise
