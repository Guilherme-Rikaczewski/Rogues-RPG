from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File
)
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.room_schema import (
    RoomCreate,
    RoomUpdate,
    RoomResponse,
    RoomRole
)
from app.schemas.types import RoomCode
import app.services.room_user_service as rus
import app.services.room_service as rs
from app.services.auth_service import (
    get_current_user_id
)


router = APIRouter(
    prefix="/rooms",
    tags=["Rooms"]
)


@router.post("/", response_model=RoomResponse)
async def create(
    room: RoomCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):

    try:

        new_room = await rs.create_room(
            db,
            room
        )

        room_user = await rus.create_room_user(
            db,
            new_room.id,
            user_id
        )

        setattr(
            new_room,
            'role',
            room_user.role
        )

        return new_room

    except Exception:

        raise HTTPException(
            500,
            detail='Internal server error'
        )


@router.patch('/{room_id}', response_model=RoomResponse)
async def update(
    room_id: int,
    room: RoomUpdate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):

    try:

        room_user = await rus.read_role_room_user(
            db,
            room_id,
            user_id
        )

        if not room_user:
            raise HTTPException(
                403,
                detail='Permission denied'
            )

        if room_user.role != RoomRole.master:
            raise HTTPException(
                403,
                detail='Permission denied'
            )

        updated_room = await rs.update_room(
            db,
            room_id,
            room
        )

        if not updated_room:
            raise HTTPException(
                404,
                detail='Room not found'
            )

        setattr(
            updated_room,
            'role',
            room_user.role
        )

        return updated_room

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            500,
            detail=f'Internal server error {error}'
        )


@router.get('/{room_id}', response_model=RoomResponse)
async def read(
    room_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):

    try:

        room = await rs.get_room(
            db,
            room_id
        )

        if not room:
            raise HTTPException(
                404,
                detail='Room not found'
            )

        room_user = await rus.read_role_room_user(
            db,
            room_id,
            user_id
        )

        if not room_user:
            raise HTTPException(
                403,
                detail='Permission denied'
            )

        setattr(
            room,
            'role',
            room_user.role
        )

        return room

    except HTTPException:
        raise

    except Exception:

        raise HTTPException(
            500,
            detail='Internal server error'
        )


@router.get('/all/')
async def read_all(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):

    try:

        return await rs.get_all_rooms_from_user(
            db,
            user_id
        )

    except Exception:

        raise HTTPException(
            500,
            detail='Internal server error'
        )


@router.get('/recent/')
async def read_recent(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):

    try:

        return await rs.get_recent_rooms_from_user(
            db,
            user_id
        )

    except Exception:

        raise HTTPException(
            500,
            detail='Internal server error'
        )


@router.delete('/{room_id}', status_code=204)
async def delete(
    room_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):

    try:

        room_user = await rus.read_role_room_user(
            db,
            room_id,
            user_id
        )

        if not room_user:
            raise HTTPException(
                403,
                detail='Permission denied'
            )

        if room_user.role != RoomRole.master:
            raise HTTPException(
                403,
                detail='Permission denied'
            )

        success = await rs.delete_room(
            db,
            room_id
        )

        if not success:
            raise HTTPException(
                404,
                detail='Room not found'
            )

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            500,
            detail=f'Internal server error {error}'
        )


@router.post(
    '/join/{room_code}',
    response_model=RoomResponse
)
async def join_room(
    room_code: RoomCode,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):

    try:

        room_user = await rus.join_room_by_code(
            db,
            room_code,
            user_id
        )

        if not room_user:
            raise HTTPException(
                404,
                detail='Room not found'
            )

        room = await rs.get_room(
            db,
            room_user.room_id
        )

        if not room:
            raise HTTPException(
                404,
                detail='Room not found'
            )

        setattr(
            room,
            'role',
            room_user.role
        )

        return room

    except HTTPException:
        raise

    except Exception:

        raise HTTPException(
            500,
            detail='Internal server error'
        )


@router.patch(
    '/upload/thumb/{room_id}',
    response_model=RoomResponse
)
async def update_room_thumb_image(
    room_id: int,
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):

    try:

        MAX_SIZE = 10 * 1024 * 1024

        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)

        if size > MAX_SIZE:
            raise HTTPException(
                400,
                "File exceeds maximum size: 10MB"
            )

        if file.content_type not in [
            "image/png",
            "image/jpeg",
            "image/webp"
        ]:
            raise HTTPException(
                400,
                detail="Invalid file type"
            )

        room_user = await rus.read_role_room_user(
            db,
            room_id,
            user_id
        )

        if not room_user:
            raise HTTPException(
                403,
                detail='Permission denied'
            )

        if room_user.role != RoomRole.master:
            raise HTTPException(
                403,
                detail='Permission denied'
            )

        updated_room = await rs.upload_room_thumb_image(
            db,
            room_id,
            user_id,
            file
        )

        if not updated_room:
            raise HTTPException(
                404,
                detail="Room not found"
            )

        setattr(
            updated_room,
            'role',
            room_user.role
        )

        return updated_room

    except ValueError as error:

        raise HTTPException(
            400,
            detail=str(error)
        )

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            500,
            detail=f'Internal server error {error}'
        )
