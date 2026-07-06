from pydantic import BaseModel
from app.schemas.types import ColorHexCode


class NoteCreate(BaseModel):
    color: ColorHexCode
    tittle: str
    content: str | None = None
    room_id: int


class NoteUpdate(BaseModel):
    color: ColorHexCode | None = None
    tittle: str | None = None
    content: str | None = None


class NoteResponse(BaseModel):
    color: ColorHexCode
    tittle: str
    content: str | None = None

    model_config = {'from_attributes': True}
