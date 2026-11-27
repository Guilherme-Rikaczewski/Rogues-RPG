from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tabletop_drawings import TabletopDrawing
from app.models.tabletop_page_assets import TabletopPageAsset
from app.models.tabletop_pages import TabletopPage
from app.models.tabletop_texts import TabletopText
from app.schemas.tabletop_schema import TabletopLayer


async def next_page_layer_order(
    db: AsyncSession, page_id: int, layer: TabletopLayer
) -> int | None:
    """Allocate a shared stacking order for every object type on a page layer."""
    page_result = await db.execute(
        select(TabletopPage.id)
        .where(TabletopPage.id == page_id)
        .with_for_update()
    )
    if page_result.scalar_one_or_none() is None:
        return None

    max_orders = []
    for model in (TabletopPageAsset, TabletopText, TabletopDrawing):
        result = await db.execute(
            select(func.max(model.layer_order)).where(
                model.page_id == page_id,
                model.layer == layer,
            )
        )
        max_orders.append(result.scalar_one())

    return max((order for order in max_orders if order is not None), default=-1) + 1
