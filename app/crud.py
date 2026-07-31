import secrets
import string

from sqlalchemy.orm import Session

from app import models

ALPHABET = string.ascii_letters + string.digits
CODE_LENGTH = 6
MAX_GENERATION_ATTEMPTS = 5


def generate_short_code(length: int = CODE_LENGTH) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def create_short_url(db: Session, original_url: str) -> models.URL:
    """Generate a unique short code and store the mapping to original_url."""
    code = None
    for _ in range(MAX_GENERATION_ATTEMPTS):
        candidate = generate_short_code()
        if not get_url_by_code(db, candidate):
            code = candidate
            break

    if code is None:
        # Extremely unlikely at 62^6 possible codes, but fail loudly if it happens.
        raise RuntimeError("Could not generate a unique short code, please retry")

    url_entry = models.URL(short_code=code, original_url=original_url)
    db.add(url_entry)
    db.commit()
    db.refresh(url_entry)
    return url_entry


def get_url_by_code(db: Session, short_code: str) -> models.URL | None:
    return db.query(models.URL).filter(models.URL.short_code == short_code).first()


def increment_clicks(db: Session, url_entry: models.URL) -> models.URL:
    url_entry.clicks += 1
    db.commit()
    db.refresh(url_entry)
    return url_entry
