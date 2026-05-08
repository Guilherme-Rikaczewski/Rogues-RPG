from sqlalchemy.orm import Session
from app.models.users import User
from app.schemas.user_schema import UserCreate, UserUpdate
from app.utils.crypt import get_password_hash
from app.utils.user_file_manager import upload_image, delete_image
from fastapi import UploadFile


def create_user(db: Session, user_data: UserCreate) -> User:
    user = User(**user_data.model_dump())

    user.password = get_password_hash(user.password)
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def update_user(
        db: Session,
        user_id: int,
        user_data: UserUpdate
        ) -> User | None:
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        update_data: dict[str, str] = user_data.model_dump(
            exclude_unset=True, exclude_none=True
        )

        if 'password' in update_data:
            update_data['password'] = get_password_hash(
                update_data['password']
            )

        for k, v in update_data.items():
            setattr(user, k, v.strip())

        db.commit()
        db.refresh(user)

        return user
    except Exception:
        db.rollback()
        raise
    

def upload_profile_pic_image(
    db: Session,
    user_id: int,
    file: UploadFile,
) -> User | None:
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        image = upload_image(
            file.file, user_id, img_id=f'profilepic_user_{user_id}',
            max_width=512, max_height=512
        )
        
        MAX_ALLOWED_FOR_USER = 50 * 1024 * 1024
        
        storage_without_profile_pic = max(0, (user.storage_usage - user.profilepic_image_size))
        
        future_storage_with_new_profile_pic = storage_without_profile_pic + image['size']
        
        if future_storage_with_new_profile_pic > MAX_ALLOWED_FOR_USER:
            delete_image(image['public_id'])
            raise ValueError('The image exceeds its storage limit.')
        
        user.profilepic_image_url = image['url']
        user.profilepic_image_size = image['size']
        user.profilepic_image_public_id = image['public_id']
        
        user.storage_usage = future_storage_with_new_profile_pic
        
        db.commit()
        db.refresh(user)
        
        return user
    except Exception:
        db.rollback()
        raise


def get_user(db: Session, user_id: int) -> User | None:
    try:
        # user = db.query(User).filter(User.id == user_id).first()
        user = db.get(User, user_id)
        if not user:
            return None

        return user
    except Exception:
        raise


def delete_user(db: Session, user_id: int) -> bool:
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        db.delete(user)
        db.commit()
        # db.refresh(user)

        return True
    except Exception:
        db.rollback()
        raise
