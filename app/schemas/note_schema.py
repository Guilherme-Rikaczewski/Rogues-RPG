from pydantic import BaseModel
from app.schemas.types import ColorHexCode


class NoteCreate(BaseModel):
    color: ColorHexCode
    tittle: str
    content: str | None = None
    room_id: int
    position_x: str | None = None
    position_y: str | None = None


class NoteUpdate(BaseModel):
    color: ColorHexCode | None = None
    tittle: str | None = None
    content: str | None = None
    position_x: str | None = None
    position_y: str | None = None


class NoteResponse(BaseModel):
    id: int
    color: ColorHexCode
    tittle: str
    content: str | None = None
    position_x: str | None = None
    position_y: str | None = None

    model_config = {'from_attributes': True}
