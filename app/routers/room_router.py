from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.room_schema import RoomCreate, RoomUpdate, RoomResponse
from app.services.room_user_service import create_room_user
import app.services.room_service as rs

router = APIRouter(prefix="/rooms", tags=["Rooms"])


@router.post("/{id}", response_model=RoomResponse)
def create(id: int, room: RoomCreate, db: Session = Depends(get_db)):
    try:
        new_room = rs.create_room(db, room)
        create_room_user(db, new_room.id, id)
        return new_room
    except Exception:
        return HTTPException(500, detail='Internal server error')


@router.patch('/{id}', response_model=RoomResponse)
def update(id: int, room: RoomUpdate, db: Session = Depends(get_db)):
    try:
        return rs.update_room(db, id, room)
    except Exception:
        return HTTPException(500, detail='Internal server error')


@router.get('/{id}', response_model=RoomResponse)
def read(id: int, db: Session = Depends(get_db)):
    try:
        return rs.get_room(db, id)
    except Exception:
        return HTTPException(500, detail='Internal server error')


@router.get('/all/{id}')
def read_all(id: int, db: Session = Depends(get_db)):
    try:
        return rs.get_all_rooms_from_user(db, id)
    except Exception:
        return HTTPException(500, detail='Internal server error')


@router.get('/recent/{id}')
def read_recent(id: int, db: Session = Depends(get_db)):
    try:
        return rs.get_recent_rooms_from_user(db, id)
    except Exception:
        return HTTPException(500, detail='Internal server error')


@router.delete('/{id}', status_code=204)
def delete(id: int, db: Session = Depends(get_db)):
    try:
        success = rs.delete_room(db, id)

        if not success:
            raise
    except Exception:
        return HTTPException(500, detail='Internal server error')
