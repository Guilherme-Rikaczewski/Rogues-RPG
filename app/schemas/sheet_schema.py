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
    content: dict

# lembra de validar com algo como 
# if data.game_system == "dnd5e":
#     validated = DndSheetSchema(**data.content)


class SheetUpdate(BaseModel):
    sheet_type: SheetType | None = None
    name: str | None = None
    content: dict | None = None


class SheetResponse(BaseModel):
    id: int
    game_system: GameSystem
    sheet_type: SheetType
    name: str
    asset_image_url: str | None = None
    content: dict

    model_config = {'from_attributes': True}


class ListModeSheetResponse(BaseModel):
    id: int
    game_system: GameSystem
    sheet_type: SheetType
    asset_image_url: str | None = None
    name: str
    owner: bool

    model_config = {'from_attributes': True}


class RecentSheetsResponse(BaseModel):
    owned: list[ListModeSheetResponse]
    shared: list[ListModeSheetResponse]

    model_config = {'from_attributes': True}
