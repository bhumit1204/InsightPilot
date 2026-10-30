from pydantic import BaseModel


class DataContext(BaseModel):
    domain: str
    domain_label: str
    region: str
    currency: str | None
    primary_metric: str | None
    time_column: str | None
    time_grain: str | None
    entities: list[str]
    keywords: list[str]
    confidence: float
    reasons: list[str]
    confirmed: bool = False


class ContextUpdate(BaseModel):
    """Fields the user can change on the confirmation card. Anything left out stays as is."""

    domain: str | None = None
    region: str | None = None
    primary_metric: str | None = None
    time_column: str | None = None
    time_grain: str | None = None


class DomainOption(BaseModel):
    key: str
    label: str


class ContextOptions(BaseModel):
    domains: list[DomainOption]
    regions: list[str]
    metrics: list[str]
    time_columns: list[str]
    time_grains: list[str]


class ContextResponse(BaseModel):
    context: DataContext
    options: ContextOptions