from pydantic import BaseModel


class HealthStatus(BaseModel):
    status: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list | dict | None = None


class ErrorResponse(BaseModel):
    """The shape of every error the API returns."""

    error: ErrorBody