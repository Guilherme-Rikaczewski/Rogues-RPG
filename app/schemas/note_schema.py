from pydantic import BaseModel
from app.schemas.types import ColorHexCode


class NoteCreate(BaseModel):
    color: ColorHexCode = "#48485B"
    tittle: str = ""
    content: str = ""
    room_id: int
    page_id: int
    position_x: str | None = None
    position_y: str | None = None
    width: str | None = None
    height: str | None = None


class NoteUpdate(BaseModel):
    color: ColorHexCode | None = None
    tittle: str | None = None
    content: str | None = None
    position_x: str | None = None
    position_y: str | None = None
    width: str | None = None
    height: str | None = None
    folder_id: int | None = None
    colors_hidden: bool | None = None
    colors_centered: bool | None = None


class NoteResponse(BaseModel):
    id: int
    page_id: int | None = None
    color: ColorHexCode
    tittle: str
    content: str | None = None
    position_x: str | None = None
    position_y: str | None = None
    width: str | None = None
    height: str | None = None
    folder_id: int | None = None
    colors_hidden: bool = False
    colors_centered: bool = False

    model_config = {'from_attributes': True}


class NoteFolderCreate(BaseModel):
    room_id: int


class NoteFolderRename(BaseModel):
    name: str


class NoteFolderResponse(BaseModel):
    id: int
    room_id: int
    name: str
    display_order: int = 0

    model_config = {'from_attributes': True}
