import json
import re
import shutil
import uuid
from pathlib import Path

import pandas as pd

from app.core.config import get_settings
from app.core.errors import AppError

SESSION_ID_PATTERN = re.compile(r"[0-9a-f]{32}")

# Files inside each session folder.
RAW_FILE = "raw.csv"  # the original upload, never changed
DATA_FILE = "data.parquet"  # the working data (cleaning fixes are applied here)
TYPED_FILE = "typed.parquet"  # derived: data converted to the inferred types
PROFILE_FILE = "profile.json"  # derived: types, roles, stats, warnings
DERIVED_FILES = (TYPED_FILE, PROFILE_FILE)


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


def save_dataframe(df: pd.DataFrame, folder: Path, filename: str = DATA_FILE) -> None:
    # Parquet needs one type per column; mixed text columns are stored as strings.
    df = df.copy()
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype("string")
    df.to_parquet(folder / filename, index=False)


def load_dataframe(session_id: str, filename: str = DATA_FILE) -> pd.DataFrame:
    path = get_existing_session(session_id) / filename
    if not path.exists():
        raise AppError("DATA_NOT_FOUND", f"{filename} is missing for this session.", 404)
    return pd.read_parquet(path)


def read_json(session_id: str, filename: str) -> dict | None:
    path = get_existing_session(session_id) / filename
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(session_id: str, filename: str, data: dict) -> None:
    path = get_existing_session(session_id) / filename
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def clear_derived(session_id: str) -> None:
    """Delete cached results so they are rebuilt from the current data."""
    folder = get_existing_session(session_id)
    for name in DERIVED_FILES:
        (folder / name).unlink(missing_ok=True)
