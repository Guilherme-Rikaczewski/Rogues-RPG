from app.realtime.connection.manager import manager
from app.services.tabletop_service import (
    roll_dices
)


async def handle_dice_roll(
    _,
    data,
    room_code,
    user_id,
) -> bool:

    dices_result = roll_dices(data.quantity, data.sides)

    total = sum(dices_result) + data.bonus

    data.result["dices"] = dices_result
    data.result["total"] = total

    if data.only_for_user_id is not None:
        await manager.send_to_user(
            room_code,
            data.only_for_user_id,
            message={
                'event': 'message',
                'user_id': user_id,
                'payload': data.model_dump()
            }
        )
        return False

    return True
