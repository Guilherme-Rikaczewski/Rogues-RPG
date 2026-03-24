from fastapi import FastAPI
from app.routers import user_router
from app.routers import room_router
from app.db.session import engine
from app.db.base import Base
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # libera qualquer origem
    allow_credentials=True,
    allow_methods=["*"],  # libera todos os métodos (GET, POST, etc)
    allow_headers=["*"],  # libera todos os headers
)

Base.metadata.create_all(bind=engine)

app.include_router(user_router.router)
app.include_router(room_router.router)
