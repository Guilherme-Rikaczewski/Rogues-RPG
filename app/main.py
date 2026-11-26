from fastapi import FastAPI
from app.routers import user_router
from app.routers import room_router
from app.routers import auth_router
from app.routers import ai_router
from app.routers import sheet_router
from app.routers import note_router
from app.realtime.endpoints import tabletop
from app.db.session import engine
from app.db.base import Base
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.cache.client import connection
from sqlalchemy import text


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text(
            "ALTER TABLE rooms ADD COLUMN IF NOT EXISTS game_system "
            "VARCHAR(64) NOT NULL DEFAULT 'D&D5e'"
        ))
        await conn.execute(text(
            "ALTER TABLE rooms ADD COLUMN IF NOT EXISTS public_id VARCHAR(64)"
        ))
        await conn.execute(text(
            "UPDATE rooms SET public_id = gen_random_uuid()::text "
            "WHERE public_id IS NULL"
        ))
        await conn.execute(text(
            "ALTER TABLE rooms ALTER COLUMN public_id SET NOT NULL"
        ))
        await conn.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_rooms_public_id ON rooms (public_id)"
        ))
        await conn.execute(text(
            "ALTER TABLE notes ADD COLUMN IF NOT EXISTS page_id "
            "INTEGER REFERENCES tabletop_pages(id) ON DELETE CASCADE"
        ))
        await conn.execute(text(
            "ALTER TABLE notes ADD COLUMN IF NOT EXISTS width VARCHAR(256)"
        ))
        await conn.execute(text(
            "ALTER TABLE notes ADD COLUMN IF NOT EXISTS height VARCHAR(256)"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_notes_page_id ON notes (page_id)"
        ))
        await conn.execute(text(
            "ALTER TABLE tabletop_assets ADD COLUMN IF NOT EXISTS "
            "token_settings JSONB NOT NULL DEFAULT '{}'::jsonb"
        ))
        await conn.execute(text(
            "ALTER TABLE tabletop_page_assets ADD COLUMN IF NOT EXISTS "
            "owner_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL"
        ))
        await conn.execute(text(
            "ALTER TABLE tabletop_assets ADD COLUMN IF NOT EXISTS "
            "token_sheet_id INTEGER REFERENCES sheets(id) ON DELETE SET NULL"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_tabletop_assets_token_sheet_id "
            "ON tabletop_assets (token_sheet_id)"
        ))

    yield

    await connection.aclose()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # libera qualquer origem
    allow_credentials=True,
    allow_methods=["*"],  # libera todos os métodos (GET, POST, etc)
    allow_headers=["*"],  # libera todos os headers
)

# @app.on_event("startup")
# def startup():
#     Base.metadata.create_all(bind=engine)


app.include_router(user_router.router)
app.include_router(room_router.router)
app.include_router(auth_router.router)
app.include_router(ai_router.router)
app.include_router(tabletop.router)
app.include_router(sheet_router.router)
app.include_router(note_router.router)
