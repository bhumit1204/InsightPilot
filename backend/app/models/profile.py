"""Response models for the data profile, so the frontend gets exact TypeScript types."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

ColumnTypeName = Literal["numeric", "datetime", "boolean", "text"]
ColumnRole = Literal["time", "metric", "category", "identifier", "free_text"]


class TopValue(BaseModel):
    value: str
    count: int


class ColumnStats(BaseModel):
    missing: int
    missing_pct: float
    unique: int
    # Numbers for numeric columns, ISO date strings for date columns.
    min: float | str | None = None
    max: float | str | None = None
    mean: float | None = None
    median: float | None = None
    std: float | None = None
    sum: float | None = None
    outliers: int | None = None
    top_values: list[TopValue] | None = None


class ColumnDetails(BaseModel):
    """Extra facts found while reading a column; most are only set for some types."""

    model_config = ConfigDict(extra="allow")

    currency: bool | None = None
    percent: bool | None = None
    format: str | None = None
    dayfirst_ambiguous: bool | None = None
    overridden: bool | None = None
    unparsed_values: int | None = None
    encoding: str | None = None


class ColumnProfile(BaseModel):
    name: str
    type: ColumnTypeName
    role: ColumnRole
    details: ColumnDetails
    stats: ColumnStats


class TimeGap(BaseModel):
    start: str
    end: str
    periods: int


class TimeProfile(BaseModel):
    column: str
    grain: str  # daily, weekly, monthly, quarterly, yearly, irregular or unknown
    regular: bool
    coverage_pct: float | None = None
    start: str | None = None
    end: str | None = None
    periods: int | None = None
    missing_periods: int
    gaps: list[TimeGap]
    suggested_grain: str | None = None


class Roles(BaseModel):
    time: list[str]
    metric: list[str]
    category: list[str]
    identifier: list[str]
    free_text: list[str]


class QualityWarning(BaseModel):
    code: str
    message: str
    column: str | None = None
    fix: str | None = None


class Profile(BaseModel):
    rows: int
    columns: int
    duplicate_rows: int
    missing_cells: int
    time: TimeProfile | None
    roles: Roles
    column_details: list[ColumnProfile]
    warnings: list[QualityWarning]
    generated_at: str
