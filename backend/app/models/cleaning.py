from typing import Any, Literal

from pydantic import BaseModel

from app.models.profile import Profile

CleanAction = Literal[
    "drop_duplicates",
    "drop_missing_rows",
    "fill_missing",
    "drop_column",
    "set_type",
]
FillStrategy = Literal["value", "mean", "median", "mode", "zero"]
ColumnTypeName = Literal["numeric", "datetime", "boolean", "text"]


class CleanRequest(BaseModel):
    action: CleanAction
    column: str | None = None
    strategy: FillStrategy | None = None  # fill_missing
    value: Any = None  # fill_missing with strategy "value"
    type: ColumnTypeName | None = None  # set_type
    date_format: str | None = None  # set_type with type "datetime", e.g. "%m/%d/%Y"

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"action": "drop_duplicates"},
                {
                    "action": "fill_missing",
                    "column": "vendor",
                    "strategy": "value",
                    "value": "Unknown",
                },
                {
                    "action": "set_type",
                    "column": "date",
                    "type": "datetime",
                    "date_format": "%m/%d/%Y",
                },
            ]
        }
    }


class CleanResult(BaseModel):
    applied: dict[str, Any]
    profile: Profile


class CleanLog(BaseModel):
    fixes: list[dict[str, Any]]