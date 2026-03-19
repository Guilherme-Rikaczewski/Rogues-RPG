from sqlalchemy.orm import Session
from app.models.room_users import RoomUser


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
