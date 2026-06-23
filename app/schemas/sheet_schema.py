from pydantic import BaseModel
import enum


class SheetType(str, enum.Enum):
    master = "master"
    player = "player"


class GameSystem(str, enum.Enum):
    DND5e = "D&D5e"


class SheetCreate(BaseModel):
    game_system: GameSystem
    sheet_type: SheetType
    name: str
    token_image_url: str = ""
    token_image_public_id: str = ""
    content: dict

# lembra de validar com algo como 
# if data.game_system == "dnd5e":
#     validated = DndSheetSchema(**data.content)


class SheetUpdate(BaseModel):
    sheet_type: SheetType | None
    name: str | None
    token_image_url: str | None
    token_image_public_id: str | None
    content: dict | None


class SheetResponse(BaseModel):
    id: int
    game_system: GameSystem
    sheet_type: SheetType
    name: str
    token_image_url: str
    token_image_public_id: str
    content: dict

    model_config = {'from_attributes': True}


class ListModeSheetResponse(BaseModel):
    id: int
    game_system: GameSystem
    sheet_type: SheetType
    name: str
    token_image_url: str
    token_image_public_id: str
    owner: bool

    model_config = {'from_attributes': True}
