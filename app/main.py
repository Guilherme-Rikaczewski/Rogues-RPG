from fastapi import FastAPI
from app.routers import user_router
from app.db.session import engine
from app.db.base import Base

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(user_router.router)
