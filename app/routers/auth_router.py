from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.auth_schema import LoginResponse, TokenData
from datetime import timedelta
from app.utils.refresh import create_opaque_token
from app.cache.client import connection
import app.services.auth_service as aus
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm


router = APIRouter(prefix="/auth", tags=["Auth"])
ACCESS_TOKEN_EXPIRE_MINUTES = 60


@router.post('/login', response_model=LoginResponse)
async def login(response: Response,
                form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                db: Session = Depends(get_db)):
    try:
        authenticated_user = aus.authenticate_user(
            db, form_data.username, form_data.password
        )
        if not authenticated_user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token_data = TokenData(id=authenticated_user.id)
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = aus.create_access_token(
            {'id': token_data.id},
            access_token_expires
        )

        refresh_token = create_opaque_token()
        await aus.save_refresh_token(
            token_data.id, refresh_token, connection
        )

        response.headers['Authorization'] = f'Bearer {access_token}'

        response.set_cookie(
            key='refreshToken',
            value=refresh_token,
            httponly=True,
            secure=False,
            samesite='strict',
            max_age=60*60*24*7
        )

        return LoginResponse(
            access_token=access_token,
            token_type='Bearer'
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(500, detail='Internal server error')
