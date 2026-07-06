from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.notes import Note
from app.schemas.note_schema import NoteCreate, NoteUpdate, NoteResponse


async def create_note(
    db: AsyncSession,
    note_data: NoteCreate,
    user_id: int
) -> Note:

    note = Note(
        color=note_data.color,
        tittle=note_data.tittle,
        content=note_data.content,
        user_id=user_id,
        room_id=note_data.room_id
    )

    db.add(note)

    await db.commit()
    await db.refresh(note)

    return note


async def update_note(
    db: AsyncSession,
    user_id: int,
    note_id: int,
    note_data: NoteUpdate
) -> Note | None:

    try:
        result = await db.execute(
            select(Note).where(
                Note.id == note_id,
                Note.user_id == user_id
            )
        )

        note = result.scalar_one_or_none()

        if not note:
            return None

        update_data = note_data.model_dump(
            exclude_unset=True,
            exclude_none=True
        )

        for k, v in update_data.items():

            if isinstance(v, str):
                v = v.strip()

            setattr(note, k, v)

        await db.commit()
        await db.refresh(note)

        return note

    except Exception:
        await db.rollback()
        raise


async def get_note(
    db: AsyncSession,
    user_id: int,
    note_id: int
) -> Note | None:

    try:
        result = await db.execute(
            select(Note).where(
                Note.id == note_id,
                Note.user_id == user_id
            )
        )

        note = result.scalar_one_or_none()

        if not note:
            return None

        return note

    except Exception:
        raise


async def get_all_notes_from_room(
    db: AsyncSession,
    user_id: int,
    room_id: int
) -> list[NoteResponse]:

    try:
        result = await db.execute(
            select(Note).where(
                Note.room_id == room_id,
                Note.user_id == user_id
            )
        )

        rows = result.all()

        return [
            NoteResponse(
                id=row.id,
                color=row.color,
                tittle=row.tittle,
                content=row.content
            )
            for row in rows
        ]

    except Exception:
        raise


async def delete_note(
    db: AsyncSession,
    user_id: int,
    note_id: int
) -> bool:

    try:
        result = await db.execute(
            select(Note).where(
                Note.id == note_id,
                Note.user_id == user_id
            )
        )

        note = result.scalar_one_or_none()

        if not note:
            return False

        await db.delete(note)
        await db.commit()

        return True

    except Exception:
        await db.rollback()
        raise
