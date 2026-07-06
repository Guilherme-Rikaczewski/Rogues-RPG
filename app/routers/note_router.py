from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.note_schema import (
    NoteCreate,
    NoteUpdate,
    NoteResponse
)
import app.services.notes_service as ns
from app.services.auth_service import get_current_user_id


router = APIRouter(
    prefix="/notes",
    tags=["Notes"]
)


@router.post("/", response_model=NoteResponse)
async def create(
    note: NoteCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):

    try:
        return await ns.create_note(db, note, user_id)

    except Exception as error:
        raise HTTPException(
            500,
            detail=f'Internal server error {error}'
        )


@router.patch('/{note_id}', response_model=NoteResponse)
async def update(
    note_id: int,
    note: NoteUpdate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):

    try:
        updated_note = await ns.update_note(
            db,
            user_id,
            note_id,
            note
        )

        if not updated_note:
            raise HTTPException(
                404,
                detail='Note not found'
            )

        return updated_note

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            500,
            detail='Internal server error'
        )


@router.get('/{note_id}', response_model=NoteResponse)
async def read(
    note_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):

    try:
        note = await ns.get_note(
            db,
            user_id,
            note_id
        )

        if not note:
            raise HTTPException(
                404,
                detail='note not found'
            )

        return note

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            500,
            detail='Internal server error'
        )


@router.get('/all/{room_id}')
async def read_all(
    room_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    try:
        notes = await ns.get_all_notes_from_room(
            db,
            user_id,
            room_id
        )

        if not notes:
            raise HTTPException(
                404,
                detail='Notes not found'
            )

        return notes

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            500,
            detail=f'Internal server error: {error}'
        )


@router.delete('/{note_id}', status_code=204)
async def delete(
    note_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):

    try:
        success = await ns.delete_note(
            db,
            user_id,
            note_id
        )

        if not success:
            raise HTTPException(
                404,
                detail='User not found'
            )

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            500,
            detail='Internal server error'
        )
