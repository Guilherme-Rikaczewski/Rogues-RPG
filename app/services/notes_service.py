from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.note_folders import NoteFolder
from app.models.note_display_preferences import NoteDisplayPreferences
from app.models.note_metadata import NoteMetadata
from app.models.notes import Note
from app.models.room_users import RoomUser
from app.models.tabletop_pages import TabletopPage
from app.schemas.note_schema import (
    NoteCreate, NoteFolderResponse, NoteResponse, NoteUpdate,
)


async def _is_room_member(db: AsyncSession, room_id: int, user_id: int) -> bool:
    result = await db.execute(select(RoomUser.id).where(
        RoomUser.room_id == room_id,
        RoomUser.user_id == user_id,
    ))
    return result.scalar_one_or_none() is not None


async def _serialize_note(db: AsyncSession, note: Note) -> NoteResponse:
    result = await db.execute(select(NoteMetadata).where(NoteMetadata.note_id == note.id))
    metadata = result.scalar_one_or_none()
    preferences_result = await db.execute(select(NoteDisplayPreferences).where(NoteDisplayPreferences.note_id == note.id))
    preferences = preferences_result.scalar_one_or_none()
    return NoteResponse(
        id=note.id,
        page_id=note.page_id,
        color=note.color,
        tittle=note.tittle,
        content=note.content,
        position_x=note.position_x,
        position_y=note.position_y,
        width=note.width,
        height=note.height,
        folder_id=metadata.folder_id if metadata else None,
        colors_hidden=metadata.colors_hidden if metadata else False,
        colors_centered=preferences.colors_centered if preferences else False,
    )


async def get_note(db: AsyncSession, user_id: int, note_id: int) -> NoteResponse | None:
    result = await db.execute(select(Note).where(Note.id == note_id, Note.user_id == user_id))
    note = result.scalar_one_or_none()
    if not note or not await _is_room_member(db, note.room_id, user_id):
        return None
    return await _serialize_note(db, note)


async def create_note(db: AsyncSession, note_data: NoteCreate, user_id: int) -> NoteResponse | None:
    if not await _is_room_member(db, note_data.room_id, user_id):
        return None
    page_result = await db.execute(select(TabletopPage).where(
        TabletopPage.id == note_data.page_id,
        TabletopPage.room_id == note_data.room_id,
    ))
    if not page_result.scalar_one_or_none():
        return None
    note = Note(
        color=note_data.color,
        tittle=note_data.tittle,
        content=note_data.content,
        user_id=user_id,
        room_id=note_data.room_id,
        page_id=note_data.page_id,
        position_x=note_data.position_x,
        position_y=note_data.position_y,
        width=note_data.width,
        height=note_data.height,
    )
    try:
        db.add(note)
        await db.flush()
        db.add(NoteMetadata(note_id=note.id))
        db.add(NoteDisplayPreferences(note_id=note.id))
        await db.commit()
        await db.refresh(note)
        return await _serialize_note(db, note)
    except Exception:
        await db.rollback()
        raise


async def update_note(
    db: AsyncSession, user_id: int, note_id: int, note_data: NoteUpdate
) -> NoteResponse | None:
    result = await db.execute(select(Note).where(Note.id == note_id, Note.user_id == user_id))
    note = result.scalar_one_or_none()
    if not note or not await _is_room_member(db, note.room_id, user_id):
        return None

    values = note_data.model_dump(exclude_unset=True)
    folder_id = values.pop("folder_id", ...)
    colors_hidden = values.pop("colors_hidden", ...)
    colors_centered = values.pop("colors_centered", ...)
    if folder_id is not ... and folder_id is not None:
        folder_result = await db.execute(select(NoteFolder).where(
            NoteFolder.id == folder_id,
            NoteFolder.room_id == note.room_id,
            NoteFolder.user_id == user_id,
        ))
        if not folder_result.scalar_one_or_none():
            return None

    for field, value in values.items():
        if value is not None:
            setattr(note, field, value)

    metadata_result = await db.execute(select(NoteMetadata).where(NoteMetadata.note_id == note.id))
    metadata = metadata_result.scalar_one_or_none()
    if metadata is None:
        metadata = NoteMetadata(note_id=note.id)
        db.add(metadata)
        await db.flush()
    if folder_id is not ...:
        metadata.folder_id = folder_id
    if colors_hidden is not ... and colors_hidden is not None:
        metadata.colors_hidden = colors_hidden
    if colors_centered is not ... and colors_centered is not None:
        preferences_result = await db.execute(select(NoteDisplayPreferences).where(NoteDisplayPreferences.note_id == note.id))
        preferences = preferences_result.scalar_one_or_none()
        if preferences is None:
            preferences = NoteDisplayPreferences(note_id=note.id)
            db.add(preferences)
            await db.flush()
        preferences.colors_centered = colors_centered

    await db.commit()
    await db.refresh(note)
    return await _serialize_note(db, note)


async def get_all_notes_from_room(
    db: AsyncSession, user_id: int, room_id: int, page_id: int
) -> list[NoteResponse]:
    if not await _is_room_member(db, room_id, user_id):
        return []
    result = await db.execute(
        select(Note, NoteMetadata, NoteDisplayPreferences)
        .outerjoin(NoteMetadata, NoteMetadata.note_id == Note.id)
        .outerjoin(NoteDisplayPreferences, NoteDisplayPreferences.note_id == Note.id)
        .where(Note.room_id == room_id, Note.page_id == page_id, Note.user_id == user_id)
        .order_by(Note.id)
    )
    return [NoteResponse(
        id=note.id,
        page_id=note.page_id,
        color=note.color,
        tittle=note.tittle,
        content=note.content,
        position_x=note.position_x,
        position_y=note.position_y,
        width=note.width,
        height=note.height,
        folder_id=metadata.folder_id if metadata else None,
        colors_hidden=metadata.colors_hidden if metadata else False,
        colors_centered=preferences.colors_centered if preferences else False,
    ) for note, metadata, preferences in result.all()]


async def assign_legacy_notes_to_page(
    db: AsyncSession, room_id: int, page_id: int
) -> None:
    """Attach pre-page notes to the room's selected page on first load."""
    await db.execute(
        update(Note)
        .where(Note.room_id == room_id, Note.page_id.is_(None))
        .values(page_id=page_id)
    )
    await db.commit()


async def delete_note(db: AsyncSession, user_id: int, note_id: int) -> bool:
    result = await db.execute(select(Note).where(Note.id == note_id, Note.user_id == user_id))
    note = result.scalar_one_or_none()
    if not note or not await _is_room_member(db, note.room_id, user_id):
        return False
    await db.delete(note)
    await db.commit()
    return True


async def get_note_folders(
    db: AsyncSession, user_id: int, room_id: int
) -> list[NoteFolderResponse]:
    if not await _is_room_member(db, room_id, user_id):
        return []
    result = await db.execute(select(NoteFolder).where(
        NoteFolder.room_id == room_id,
        NoteFolder.user_id == user_id,
    ).order_by(NoteFolder.display_order, NoteFolder.id))
    return [NoteFolderResponse.model_validate(folder) for folder in result.scalars().all()]


async def create_note_folder(
    db: AsyncSession, room_id: int, user_id: int
) -> NoteFolderResponse | None:
    if not await _is_room_member(db, room_id, user_id):
        return None
    result = await db.execute(select(NoteFolder).where(
        NoteFolder.room_id == room_id,
        NoteFolder.user_id == user_id,
    ))
    folders = result.scalars().all()
    folder = NoteFolder(
        room_id=room_id,
        user_id=user_id,
        name=f"Folder {len(folders) + 1}",
        display_order=len(folders),
    )
    db.add(folder)
    await db.commit()
    await db.refresh(folder)
    return NoteFolderResponse.model_validate(folder)


async def rename_note_folder(
    db: AsyncSession, folder_id: int, user_id: int, name: str
) -> NoteFolderResponse | None:
    clean_name = name.strip()
    if not clean_name or len(clean_name) > 120:
        return None
    result = await db.execute(select(NoteFolder).where(
        NoteFolder.id == folder_id,
        NoteFolder.user_id == user_id,
    ))
    folder = result.scalar_one_or_none()
    if not folder or not await _is_room_member(db, folder.room_id, user_id):
        return None
    folder.name = clean_name
    await db.commit()
    await db.refresh(folder)
    return NoteFolderResponse.model_validate(folder)
