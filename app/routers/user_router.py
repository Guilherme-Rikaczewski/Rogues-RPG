from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user_schema import UserCreate, UserUpdate, UserResponse
import app.services.user_service as us
from app.services.auth_service import get_current_user_id


router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=UserResponse)
def create(user: UserCreate, db: Session = Depends(get_db)):
    try:
        return us.create_user(db, user)
    except Exception as error:
        raise HTTPException(500, detail=f'Internal server error {error}')


@router.patch('/', response_model=UserResponse)
def update(
    user: UserUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
        ):
    try:
        return us.update_user(db, user_id, user)
    except Exception:
        raise HTTPException(500, detail='Internal server error')


@router.get('/', response_model=UserResponse)
def read(
    user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)
        ):
    try:
        return us.get_user(db, user_id)
    except Exception:
        raise HTTPException(500, detail='Internal server error')


@router.delete('/', status_code=204)
def delete(
    user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)
        ):
    try:
        success = us.delete_user(db, user_id)

        if not success:
            raise
    except Exception:
        raise HTTPException(500, detail='Internal server error')


@router.patch('/upload/profilepic', response_model=UserResponse)
def update_room_thumb_image(
           file: UploadFile = File(...),
           user_id: int = Depends(get_current_user_id), 
           db: Session = Depends(get_db)):
    try:
        MAX_SIZE = 10 * 1024 * 1024 

        file.file.seek(0, 2) 
        size = file.file.tell()
        file.file.seek(0)

        if size > MAX_SIZE:
            raise HTTPException(400, "File exceeds maximum size: 10MB")
        if file.content_type not in ["image/png", "image/jpeg", "image/webp"]:
            raise HTTPException(400, detail="Invalid file type")
        
        updated_user = us.upload_profile_pic_image(
            db, user_id, file,
        )
        if not updated_user:
            raise  HTTPException(404, detail="user not found")
        
        return updated_user
    except ValueError as error:
       raise HTTPException(400, detail=str(error))
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(500, detail=f'Internal server error {error}')