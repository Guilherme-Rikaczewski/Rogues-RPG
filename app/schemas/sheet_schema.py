from pydantic import BaseModel, Field
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


class SheetRoomResponse(BaseModel):
    id: int
    room_name: str
    code: str

    model_config = {"from_attributes": True}


class ListModeSheetResponse(BaseModel):
    id: int
    game_system: GameSystem
    sheet_type: SheetType
    asset_image_url: str | None = None
    name: str
    owner: bool

    user_profilepics: list[str] = Field(default_factory=list)

    room: SheetRoomResponse | None = None

    model_config = {"from_attributes": True}


class RecentSheetsResponse(BaseModel):
    owned: list[ListModeSheetResponse]
    shared: list[ListModeSheetResponse]

    model_config = {'from_attributes': True}
