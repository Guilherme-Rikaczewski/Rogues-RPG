from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user_schema import UserCreate, UserUpdate, UserResponse
import app.services.user_service as us

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=UserResponse)
def create(user: UserCreate, db: Session = Depends(get_db)):
    try:
        return us.create_user(db, user)
    except Exception:
        return HTTPException(500, detail='Internal server error')


@router.patch('/{id}', response_model=UserResponse)
def update(id: int, user: UserUpdate, db: Session = Depends(get_db)):
    try:
        return us.update_user(db, id, user)
    except Exception:
        return HTTPException(500, detail='Internal server error')


@router.get('/{id}', response_model=UserResponse)
def read(id: int, db: Session = Depends(get_db)):
    try:
        return us.get_user(db, id)
    except Exception:
        return HTTPException(500, detail='Internal server error')


@router.delete('/{id}', status_code=204)
def delete(id: int, db: Session = Depends(get_db)):
    try:
        success = us.delete_user(db, id)

        if not success:
            raise
    except Exception:
        return HTTPException(500, detail='Internal server error')
