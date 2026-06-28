from sqlalchemy.ext.asyncio import AsyncSession
from app.models.sheet_user import SheetUser
from sqlalchemy import select, update, func


async def create_sheet_user(
    db: AsyncSession,
    sheet_id: int,
    user_id: int,
    owner: bool
) -> SheetUser:
    try:

        sheet_user_data = {
            "user_id": user_id,
            "sheet_id": sheet_id,
            "owner": owner,
        }

        sheet_user = SheetUser(**sheet_user_data)

        db.add(sheet_user)

        await db.commit()
        await db.refresh(sheet_user)

        return sheet_user

    except Exception:

        await db.rollback()
        raise


async def check_user_acces_for_sheet(
    db: AsyncSession,
    user_id: int,
    sheet_id: int,
) -> bool:
    try:
        result = await db.execute(
            select(SheetUser).where(
                SheetUser.sheet_id == sheet_id,
                SheetUser.user_id == user_id
            )
        )

        sheet_user = result.scalar_one_or_none()

        return sheet_user is not None

    except Exception:

        await db.rollback()
        raise


async def update_sheet_last_access(
    db: AsyncSession,
    user_id: int,
    sheet_id: int,
) -> None:
    try:
        await db.execute(
            update(SheetUser)
            .where(
                SheetUser.user_id == user_id,
                SheetUser.sheet_id == sheet_id
            )
            .values(last_access=func.now())
        )

        await db.commit()

    except Exception:

        await db.rollback()
        raise
