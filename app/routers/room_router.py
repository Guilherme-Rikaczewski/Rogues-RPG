from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.room_schema import RoomCreate, RoomUpdate, RoomResponse
import app.services.room_user_service as rus
import app.services.room_service as rs

router = APIRouter(prefix="/rooms", tags=["Rooms"])


@router.post("/{id}", response_model=RoomResponse)
def create(id: int, room: RoomCreate, db: Session = Depends(get_db)):
    try:
        new_room = rs.create_room(db, room)
        room_user = rus.create_room_user(db, new_room.id, id)
        setattr(new_room, 'role', room_user.role)
        return new_room
    except Exception:
        return HTTPException(500, detail='Internal server error')


@router.patch('/{id}', response_model=RoomResponse)
def update(id: int, room: RoomUpdate, db: Session = Depends(get_db)):
    try:
        updated_room = rs.update_room(db, id, room)
        setattr(updated_room, 'role', 'master')
        return updated_room
    except Exception:
        return HTTPException(500, detail='Internal server error')


@router.get('/{room_id}/user/{user_id}', response_model=RoomResponse)
def read(room_id: int, user_id: int, db: Session = Depends(get_db)):
    try:
        get_room = rs.get_room(db, room_id)
        if not get_room:
            raise HTTPException(500, detail='Internal server error')

        room_user = rus.read_role_room_user(db, room_id, user_id)
        setattr(get_room, 'role', room_user.role)
        return get_room
    except Exception:
        raise HTTPException(500, detail='Internal server error')


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
