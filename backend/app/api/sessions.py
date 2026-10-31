from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, Response, UploadFile, status

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.cleaning import CleanLog, CleanRequest, CleanResult
from app.models.common import ErrorResponse
from app.models.context import ContextResponse, ContextUpdate
from app.models.profile import Profile
from app.models.session import SessionCreated, SessionInfo
from app.services import cleaning, context_service, storage
from app.services.profile_service import get_profile
from app.services.session_service import create_session_from_bytes

# Every route can fail with the shared error format; listing it gives the frontend its type.
ERRORS = {
    400: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    413: {"model": ErrorResponse},
    415: {"model": ErrorResponse},
}

router = APIRouter(prefix="/sessions", tags=["sessions"], responses=ERRORS)


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
    return create_session_from_bytes(raw, Path(file.filename or "data.csv").name)


@router.get("/{session_id}", response_model=SessionInfo)
def read_session(session_id: str) -> SessionInfo:
    """File name, upload time and the original shape of the data."""
    storage.get_existing_session(session_id)
    metadata = storage.read_json(session_id, "metadata.json")
    if metadata is None:
        raise AppError("SESSION_NOT_FOUND", "Session not found or expired.", 404)
    return SessionInfo(**metadata)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: str) -> Response:
    storage.delete_session(session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{session_id}/profile", response_model=Profile)
def read_profile(session_id: str, refresh: bool = False) -> dict:
    """Column types, roles, statistics and data-quality warnings. Cached after the first call."""
    return get_profile(session_id, refresh=refresh)


@router.post("/{session_id}/clean", response_model=CleanResult)
def clean(session_id: str, request: CleanRequest) -> CleanResult:
    """Apply one cleaning fix, log it, and return the rebuilt profile."""
    applied = cleaning.apply_fix(session_id, request)
    return CleanResult(applied=applied, profile=get_profile(session_id))


@router.get("/{session_id}/clean/log", response_model=CleanLog)
def cleaning_log(session_id: str) -> dict:
    return cleaning.get_log(session_id)


@router.post("/{session_id}/clean/reset", response_model=Profile)
def reset_cleaning(session_id: str) -> dict:
    """Undo all fixes and return the profile of the original data."""
    return cleaning.reset(session_id)


@router.get("/{session_id}/context", response_model=ContextResponse)
def read_context(session_id: str) -> ContextResponse:
    """The guessed (or confirmed) context, plus the choices for each dropdown."""
    return ContextResponse(
        context=context_service.get_context(session_id),
        options=context_service.get_options(session_id),
    )


@router.put("/{session_id}/context", response_model=ContextResponse)
def confirm_context(session_id: str, update: ContextUpdate) -> ContextResponse:
    """Confirm the context, optionally changing some fields."""
    return ContextResponse(
        context=context_service.update_context(session_id, update),
        options=context_service.get_options(session_id),
    )
