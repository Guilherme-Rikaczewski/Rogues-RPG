from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user_schema import UserCreate, UserUpdate, UserResponse
from app.services.user_service import (create_user, update_user,
                                       get_user, delete_user)

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=UserResponse)
def create(user: UserCreate, db: Session = Depends(get_db)):
    try:
        return create_user(db, user)
    except Exception:
        return HTTPException(500, detail='Internal server error')


@router.patch('/{id}', response_model=UserResponse)
def update(id: int, user: UserUpdate, db: Session = Depends(get_db)):
    try:
        return update_user(db, id, user)
    except Exception:
        return HTTPException(500, detail='Internal server error')


@router.get('/{id}', response_model=UserResponse)
def read(id: int, db: Session = Depends(get_db)):
    try:
        return get_user(db, id)
    except Exception:
        return HTTPException(500, detail='Internal server error')


@router.delete('/{id}', status_code=204)
def delete(id: int, db: Session = Depends(get_db)):
    try:
        success = delete_user(db, id)

        if not success:
            raise
    except Exception:
        return HTTPException(500, detail='Internal server error')
