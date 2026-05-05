from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.schemas.types import Username, Password


class UserCreate(BaseModel):
    email: EmailStr
    username: Username
    password: Password
    storage_usage: int = 0
    hours_played: int = 0
    profilepic_image_url: str = ''
    profilepic_image_size: int = 0
    profilepic_image_public_id: str = ''


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: Username | None = None
    password: Password | None = None


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    username: Username
    storage_usage: int
    hours_played: int
    profilepic_image_url: str
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}
