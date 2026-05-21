from sqlalchemy.orm import Session
from app.models.room_users import RoomUser
from app.models.rooms import Room
from app.schemas.types import RoomCode
from fastapi import HTTPException


def create_room_user(db: Session, room_id: int, user_id: int) -> RoomUser:
    try:
        rule_data = {
            "user_id": user_id,
            "room_id": room_id,
            "role": "master",
        }
        room_user = RoomUser(**rule_data)

        db.add(room_user)
        db.commit()
        db.refresh(room_user)

        return room_user
    except Exception:
        db.rollback()
        raise


def read_role_room_user(db: Session, room_id: int, user_id: int) -> RoomUser | None:
    try:
        room_user = db.query(RoomUser).filter(
            RoomUser.room_id == room_id,
            RoomUser.user_id == user_id
        ).first()
        return room_user
    except Exception:
        db.rollback()
        raise


def join_room_by_code(db: Session, code: RoomCode, user_id: int
                      ) -> RoomUser | None:
    try:
        room = db.query(Room).filter(Room.code == code).first()

        if not room:
            return None

        room_user = read_role_room_user(db, room.id, user_id)
        user_already_joined = room_user is not None
        if user_already_joined:
            raise HTTPException(409, detail='User already joined')

        rule_data = {
            "user_id": user_id,
            "room_id": room.id,
            "role": "player",
        }
        room_user = RoomUser(**rule_data)

        db.add(room_user)
        db.commit()
        db.refresh(room_user)

        return room_user
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise
