from fastapi import APIRouter, status

from app.models.common import ErrorResponse
from app.models.sample import SampleDataset
from app.models.session import SessionCreated
from app.services import samples

router = APIRouter(prefix="/samples", tags=["samples"], responses={404: {"model": ErrorResponse}})


@router.get("", response_model=list[SampleDataset])
def list_samples() -> list[SampleDataset]:
    """Demo datasets available on this server."""
    return samples.list_samples()


@router.post("/{key}/sessions", response_model=SessionCreated, status_code=status.HTTP_201_CREATED)
def start_from_sample(key: str) -> SessionCreated:
    """Start a new session from a demo dataset, exactly as if it had been uploaded."""
    return samples.create_session_from_sample(key)
