from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

from app import crud, models
from app.database import engine, get_db

# Creates the urls table on startup if it doesn't already exist.
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="URL Shortener",
    description="A small API that shortens URLs and tracks click counts.",
)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


class ShortenRequest(BaseModel):
    url: HttpUrl


class ShortenResponse(BaseModel):
    short_code: str
    short_url: str
    original_url: str


class StatsResponse(BaseModel):
    short_code: str
    original_url: str
    clicks: int
    created_at: str


@app.get("/health")
def health_check():
    """Used by uptime checks and, later, container health checks."""
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def serve_ui():
    """Serves the simple form-based frontend for shortening URLs."""
    return (STATIC_DIR / "index.html").read_text()


@app.post("/shorten", response_model=ShortenResponse)
def shorten_url(payload: ShortenRequest, db: Session = Depends(get_db)):
    url_entry = crud.create_short_url(db, str(payload.url))
    return ShortenResponse(
        short_code=url_entry.short_code,
        short_url=f"/{url_entry.short_code}",
        original_url=url_entry.original_url,
    )


@app.get("/stats/{short_code}", response_model=StatsResponse)
def get_stats(short_code: str, db: Session = Depends(get_db)):
    url_entry = crud.get_url_by_code(db, short_code)
    if not url_entry:
        raise HTTPException(status_code=404, detail="Short code not found")
    return StatsResponse(
        short_code=url_entry.short_code,
        original_url=url_entry.original_url,
        clicks=url_entry.clicks,
        created_at=url_entry.created_at.isoformat() if url_entry.created_at else "",
    )


@app.get("/{short_code}")
def redirect_to_original(short_code: str, db: Session = Depends(get_db)):
    """Kept last so it doesn't swallow /health, /shorten, /stats, /docs, etc."""
    url_entry = crud.get_url_by_code(db, short_code)
    if not url_entry:
        raise HTTPException(status_code=404, detail="Short code not found")
    crud.increment_clicks(db, url_entry)
    return RedirectResponse(url=url_entry.original_url)
