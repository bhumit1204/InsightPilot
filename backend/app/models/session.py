from pydantic import BaseModel


class SessionCreated(BaseModel):
    session_id: str
    filename: str
    rows: int
    columns: int
    column_names: list[str]
    encoding: str
    delimiter: str


class SessionInfo(SessionCreated):
    """What was uploaded. rows and columns are as uploaded, before any cleaning."""

    created_at: str
