from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.note_schema import (
    NoteCreate,
    NoteUpdate,
    NoteResponse,
    NoteFolderCreate,
    NoteFolderRename,
    NoteFolderResponse,
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
        created_note = await ns.create_note(db, note, user_id)
        if not created_note:
            raise HTTPException(status_code=403, detail="Room membership required")
        return created_note

    except HTTPException:
        raise

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
    page_id: int = Query(...),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    try:
        notes = await ns.get_all_notes_from_room(
            db,
            user_id,
            room_id,
            page_id,
        )

        return notes

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            500,
            detail=f'Internal server error: {error}'
        )


@router.get('/folders/{room_id}', response_model=list[NoteFolderResponse])
async def read_folders(
    room_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await ns.get_note_folders(db, user_id, room_id)


@router.post('/folders', response_model=NoteFolderResponse)
async def create_folder(
    folder: NoteFolderCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    created = await ns.create_note_folder(db, folder.room_id, user_id)
    if not created:
        raise HTTPException(status_code=403, detail="Room membership required")
    return created


@router.patch('/folders/{folder_id}', response_model=NoteFolderResponse)
async def rename_folder(
    folder_id: int,
    folder: NoteFolderRename,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    updated = await ns.rename_note_folder(db, folder_id, user_id, folder.name)
    if not updated:
        raise HTTPException(status_code=404, detail="Folder not found")
    return updated


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
