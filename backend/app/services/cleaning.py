"""Cleaning fixes the user applies with one click. Every fix is logged and can be undone."""

from datetime import UTC, datetime

import pandas as pd

from app.core.errors import AppError
from app.models.cleaning import CleanRequest
from app.services import storage
from app.services.csv_reader import read_csv_bytes
from app.services.profile_service import get_profile, load_typed_data
from app.services.type_inference import convert_column


def _require_column(df: pd.DataFrame, column: str | None) -> str:
    if not column:
        raise AppError("INVALID_FIX", "This fix needs a column.", 400)
    if column not in df.columns:
        raise AppError("COLUMN_NOT_FOUND", f"Column '{column}' does not exist.", 404)
    return column


def _fill_value(session_id: str, df: pd.DataFrame, req: CleanRequest, column: str):
    strategy = req.strategy
    if strategy is None:
        raise AppError("INVALID_FIX", "fill_missing needs a strategy.", 400)
    if strategy == "value":
        if req.value is None:
            raise AppError("INVALID_FIX", "Strategy 'value' needs a value.", 400)
        return req.value
    if strategy == "zero":
        return 0
    if strategy == "mode":
        mode = df[column].dropna().mode()
        if mode.empty:
            raise AppError("INVALID_FIX", f"'{column}' has no values to take the mode from.", 400)
        return mode.iloc[0]

    # mean and median need real numbers, so use the typed data ("₹1,200" -> 1200).
    typed = load_typed_data(session_id)[column]
    if not pd.api.types.is_numeric_dtype(typed) or pd.api.types.is_bool_dtype(typed):
        raise AppError("NOT_NUMERIC", f"'{column}' is not numeric, so it has no {strategy}.", 400)
    value = typed.mean() if strategy == "mean" else typed.median()
    return round(float(value), 4)


def apply_fix(session_id: str, req: CleanRequest, auto: bool = False) -> dict:
    """Apply one fix. auto=True marks fixes InsightPilot made by itself, so the UI can say so."""
    df = storage.load_dataframe(session_id)
    rows_before, columns_before = df.shape
    overrides = storage.read_json(session_id, storage.TYPE_OVERRIDES_FILE) or {}
    entry: dict = {"action": req.action, "auto": auto}

    if req.action == "drop_duplicates":
        df = df.drop_duplicates().reset_index(drop=True)

    elif req.action == "drop_missing_rows":
        column = _require_column(df, req.column)
        df = df.dropna(subset=[column]).reset_index(drop=True)
        entry["column"] = column

    elif req.action == "fill_missing":
        column = _require_column(df, req.column)
        value = _fill_value(session_id, df, req, column)
        filled = int(df[column].isna().sum())
        is_text = df[column].dtype == "string" or df[column].dtype == object
        df[column] = df[column].fillna(str(value) if is_text else value)
        entry |= {"column": column, "strategy": req.strategy, "value": value, "cells": filled}

    elif req.action == "drop_column":
        column = _require_column(df, req.column)
        df = df.drop(columns=[column])
        overrides.pop(column, None)
        entry["column"] = column

    elif req.action == "set_type":
        column = _require_column(df, req.column)
        if req.type is None:
            raise AppError("INVALID_FIX", "set_type needs a type.", 400)
        override = {"type": req.type}
        if req.date_format:
            override["format"] = req.date_format
        # Try the conversion first so a wrong choice cannot wipe out a column.
        info, _ = convert_column(column, df[column], override)
        if df[column].notna().any() and info.parse_ratio == 0:
            raise AppError(
                "CANNOT_CONVERT", f"No values in '{column}' can be read as {req.type}.", 400
            )
        overrides[column] = override
        entry |= {"column": column, "type": req.type, "date_format": req.date_format}

    folder = storage.get_existing_session(session_id)
    storage.save_dataframe(df, folder)
    storage.write_json(session_id, storage.TYPE_OVERRIDES_FILE, overrides)

    entry |= {
        "rows_before": rows_before,
        "rows_after": len(df),
        "columns_before": columns_before,
        "columns_after": df.shape[1],
        "applied_at": datetime.now(UTC).isoformat(),
    }
    log = storage.read_json(session_id, storage.CLEANING_LOG_FILE) or {"fixes": []}
    log["fixes"].append(entry)
    storage.write_json(session_id, storage.CLEANING_LOG_FILE, log)

    storage.clear_derived(session_id)  # the profile must be rebuilt from the new data
    return entry


def get_log(session_id: str) -> dict:
    return storage.read_json(session_id, storage.CLEANING_LOG_FILE) or {"fixes": []}


def reset(session_id: str) -> dict:
    """Undo every fix: rebuild the working data from the original upload."""
    folder = storage.get_existing_session(session_id)
    raw = (folder / storage.RAW_FILE).read_bytes()
    storage.save_dataframe(read_csv_bytes(raw).df, folder)
    for name in (storage.TYPE_OVERRIDES_FILE, storage.CLEANING_LOG_FILE):
        (folder / name).unlink(missing_ok=True)
    storage.clear_derived(session_id)
    return get_profile(session_id)


def auto_clean(session_id: str) -> list[dict]:
    """Fixes that are safe to make without asking. Today: remove exact duplicate rows.

    Anything that would change a value (like filling empty cells) is left to the user.
    """
    df = storage.load_dataframe(session_id)
    applied = []
    if df.duplicated().any():
        applied.append(apply_fix(session_id, CleanRequest(action="drop_duplicates"), auto=True))
    return applied
