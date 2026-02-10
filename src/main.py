import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from database import async_session, engine, get_session
from models import Base, Wisdom, WisdomCreate, WisdomResponse
from seed import SEED_DATA

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        result = await session.execute(select(func.count(Wisdom.id)))
        count = result.scalar()
        if count == 0:
            for entry in SEED_DATA:
                session.add(Wisdom(**entry))
            await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await engine.dispose()


app = FastAPI(
    title="Sovereign Cloud Wisdom",
    description="Principles, facts, and proverbs about European digital sovereignty.",
    version="1.0.0",
    lifespan=lifespan,
)


def _parse_language(request: Request) -> str:
    accept = request.headers.get("accept-language", "")
    for part in accept.split(","):
        lang = part.split(";")[0].strip().lower()
        if lang.startswith("fr"):
            return "fr"
        if lang.startswith("en"):
            return "en"
    return "en"


async def _random_wisdom(session: AsyncSession, language: str) -> Wisdom | None:
    result = await session.execute(
        select(Wisdom).where(Wisdom.language == language).order_by(func.random()).limit(1)
    )
    return result.scalar_one_or_none()


# --- UI endpoints ---


@app.get("/", response_class=HTMLResponse)
async def ui_home(request: Request, session: AsyncSession = Depends(get_session)):
    language = _parse_language(request)
    wisdom = await _random_wisdom(session, language)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "wisdom": wisdom,
        "language": language,
    })


@app.get("/ui/wisdom", response_class=HTMLResponse)
async def ui_wisdom_fragment(
    request: Request,
    language: str = "en",
    session: AsyncSession = Depends(get_session),
):
    wisdom = await _random_wisdom(session, language)
    return templates.TemplateResponse("fragments/wisdom.html", {
        "request": request,
        "wisdom": wisdom,
    })


# --- API endpoints ---


@app.get("/api/random", response_model=WisdomResponse)
async def random_wisdom(session: AsyncSession = Depends(get_session)):
    """Get a random piece of sovereign cloud wisdom."""
    result = await session.execute(select(Wisdom).order_by(func.random()).limit(1))
    wisdom = result.scalar_one_or_none()
    if not wisdom:
        raise HTTPException(status_code=404, detail="No wisdom found. The database is empty.")
    return wisdom


@app.get("/api/wisdom", response_model=list[WisdomResponse])
async def list_wisdom(
    category: str | None = None,
    language: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    """List all wisdom entries, optionally filtered by category and/or language."""
    query = select(Wisdom).order_by(Wisdom.id)
    if category:
        query = query.where(Wisdom.category == category)
    if language:
        query = query.where(Wisdom.language == language)
    result = await session.execute(query)
    return result.scalars().all()


@app.get("/api/wisdom/{wisdom_id}", response_model=WisdomResponse)
async def get_wisdom(wisdom_id: int, session: AsyncSession = Depends(get_session)):
    """Get a specific wisdom entry by ID."""
    result = await session.execute(select(Wisdom).where(Wisdom.id == wisdom_id))
    wisdom = result.scalar_one_or_none()
    if not wisdom:
        raise HTTPException(status_code=404, detail="Wisdom not found.")
    return wisdom


@app.post("/api/wisdom", response_model=WisdomResponse, status_code=201)
async def create_wisdom(
    payload: WisdomCreate,
    session: AsyncSession = Depends(get_session),
):
    """Submit a new piece of sovereign cloud wisdom."""
    wisdom = Wisdom(
        text=payload.text,
        author=payload.author,
        category=payload.category.value,
        language=payload.language,
    )
    session.add(wisdom)
    await session.commit()
    await session.refresh(wisdom)
    return wisdom


@app.get("/health")
async def health_check():
    """Health check endpoint — verifies database connectivity."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={"status": "unhealthy", "database": str(e)},
        )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("APP_PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
