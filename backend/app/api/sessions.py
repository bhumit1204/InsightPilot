import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, Response, UploadFile, status

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.session import SessionCreated
from app.services import storage
from app.services.csv_reader import read_csv_bytes
from app.services.profile_service import get_profile

router = APIRouter(prefix="/sessions", tags=["sessions"])


def read_upload(file: UploadFile) -> bytes:
    filename = file.filename or ""
    if not filename.lower().endswith(".csv"):
        raise AppError("UNSUPPORTED_FILE", "Please upload a .csv file.", 415)

    limit = get_settings().max_upload_bytes
    raw = file.file.read(limit + 1)  # read one byte past the limit to detect oversize files
    if len(raw) > limit:
        raise AppError(
            "FILE_TOO_LARGE",
            f"The file is larger than {get_settings().max_upload_mb} MB.",
            413,
        )
    return raw


@router.post("", response_model=SessionCreated, status_code=status.HTTP_201_CREATED)
def create_session(file: Annotated[UploadFile, File()]) -> SessionCreated:
    raw = read_upload(file)
    result = read_csv_bytes(raw)  # raises a clear AppError for bad files

    session_id, path = storage.create_session()
    try:
        (path / storage.RAW_FILE).write_bytes(raw)
        storage.save_dataframe(result.df, path)

        summary = SessionCreated(
            session_id=session_id,
            filename=Path(file.filename or "data.csv").name,
            rows=len(result.df),
            columns=result.df.shape[1],
            column_names=list(result.df.columns),
            encoding=result.encoding,
            delimiter=result.delimiter,
        )
        metadata = summary.model_dump() | {"created_at": datetime.now(UTC).isoformat()}
        (path / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    except Exception:
        shutil.rmtree(path, ignore_errors=True)  # never leave half-written sessions behind
        raise

    return summary


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: str) -> Response:
    storage.delete_session(session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{session_id}/profile")
def read_profile(session_id: str, refresh: bool = False) -> dict:
    """Column types, roles, statistics and data-quality warnings. Cached after the first call."""
    return get_profile(session_id, refresh=refresh)
