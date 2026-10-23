import re
import shutil
import uuid
from pathlib import Path

from app.core.config import get_settings
from app.core.errors import AppError

SESSION_ID_PATTERN = re.compile(r"[0-9a-f]{32}")


def new_session_id() -> str:
    return uuid.uuid4().hex


def session_dir(session_id: str) -> Path:
    # Only accept IDs we generated, so a request can never point outside the storage folder.
    if not SESSION_ID_PATTERN.fullmatch(session_id):
        raise AppError("INVALID_SESSION_ID", "Session ID is not valid.", 400)
    return get_settings().storage_dir / session_id


def create_session() -> tuple[str, Path]:
    session_id = new_session_id()
    path = session_dir(session_id)
    path.mkdir(parents=True, exist_ok=False)
    return session_id, path


def get_existing_session(session_id: str) -> Path:
    path = session_dir(session_id)
    if not path.is_dir():
        raise AppError("SESSION_NOT_FOUND", "Session not found or expired.", 404)
    return path


def delete_session(session_id: str) -> None:
    shutil.rmtree(get_existing_session(session_id))
