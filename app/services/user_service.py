from sqlalchemy.orm import Session
from app.models.users import User
from app.schemas.user_schema import UserCreate, UserUpdate


def create_user(db: Session, user_data: UserCreate) -> User:
    user = User(**user_data.model_dump())

    db.add(user)
    db.commit()
    db.refresh(user)

    return user
