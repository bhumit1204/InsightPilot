"""Build the data profile: column types, roles, statistics and a quality report."""

import re

import numpy as np
import pandas as pd

from app.services.type_inference import ColumnType, infer_types

ID_NAME_PATTERN = re.compile(r"(^id$|_id$|^id_|\bid\b|code$|_no$|number$)", re.IGNORECASE)
CATEGORY_MAX_UNIQUE = 50
CATEGORY_MAX_RATIO = 0.05
FREE_TEXT_MIN_LENGTH = 50
HIGH_MISSING_PCT = 20.0
TOP_VALUES = 5
MAX_GAPS_LISTED = 20

GRAINS = [  # (name, pandas frequency, typical days between periods)
    ("daily", "D", 1),
    ("weekly", "W", 7),
    ("monthly", "MS", 30.4),
    ("quarterly", "QS", 91.3),
    ("yearly", "YS", 365.25),
]


def _num(value) -> float | None:
    if value is None or pd.isna(value):
        return None
    return round(float(value), 4)


def assign_role(info: ColumnType, series: pd.Series) -> str:
    """time, metric, category, identifier or free_text."""
    non_null = series.dropna()
    n = len(non_null)
    n_unique = int(non_null.nunique())
    unique_ratio = n_unique / n if n else 0.0
    id_like_name = bool(ID_NAME_PATTERN.search(info.name))

    if info.inferred_type == "datetime":
        return "time"
    if info.inferred_type == "boolean":
        return "category"
    if info.inferred_type == "numeric":
        is_integer = n > 0 and bool((non_null % 1 == 0).all())
        if id_like_name and is_integer and unique_ratio > 0.95:
            return "identifier"
        return "metric"

    # Text columns.
    avg_length = float(non_null.astype(str).str.len().mean()) if n else 0.0
    if unique_ratio > 0.95 and (id_like_name or avg_length <= 20):
        return "identifier"
    if n_unique <= CATEGORY_MAX_UNIQUE or unique_ratio <= CATEGORY_MAX_RATIO:
        return "category"
    if avg_length >= FREE_TEXT_MIN_LENGTH:
        return "free_text"
    return "category" if unique_ratio < 0.5 else "free_text"


def column_stats(info: ColumnType, role: str, series: pd.Series) -> dict:
    total = len(series)
    missing = int(series.isna().sum())
    stats: dict = {
        "missing": missing,
        "missing_pct": round(100 * missing / total, 2) if total else 0.0,
        "unique": int(series.nunique(dropna=True)),
    }

    if info.inferred_type == "numeric":
        values = series.dropna().astype(float)
        if not values.empty:
            q1, q3 = values.quantile(0.25), values.quantile(0.75)
            iqr = q3 - q1
            outliers = int(((values < q1 - 1.5 * iqr) | (values > q3 + 1.5 * iqr)).sum())
            stats |= {
                "min": _num(values.min()),
                "max": _num(values.max()),
                "mean": _num(values.mean()),
                "median": _num(values.median()),
                "std": _num(values.std()),
                "sum": _num(values.sum()),
                "outliers": outliers,
            }
    elif info.inferred_type == "datetime":
        values = series.dropna()
        if not values.empty:
            stats |= {"min": values.min().isoformat(), "max": values.max().isoformat()}

    if role == "category":
        counts = series.dropna().astype(str).value_counts().head(TOP_VALUES)
        stats["top_values"] = [{"value": k, "count": int(v)} for k, v in counts.items()]
    return stats


def detect_grain(dates: pd.Series) -> dict:
    """Is the time column a regular series (daily, monthly...) and are any periods missing?"""
    unique = pd.Series(dates.dropna().dt.normalize().unique()).sort_values()
    if len(unique) < 3:
        return {"grain": "unknown", "regular": False, "gaps": [], "missing_periods": 0}

    median_days = float(unique.diff().dt.days.median())
    name, freq, _ = min(GRAINS, key=lambda g: abs(g[2] - median_days))

    expected = pd.date_range(unique.min(), unique.max(), freq=freq)
    present = set(unique.dt.to_period(freq[0]))
    expected_periods = pd.PeriodIndex(expected.to_period(freq[0])).unique()
    missing = [p for p in expected_periods if p not in present]
    coverage = 1 - len(missing) / len(expected_periods) if len(expected_periods) else 0.0

    span_days = (unique.max() - unique.min()).days
    result = {
        "grain": name,
        "regular": coverage >= 0.8,
        "coverage_pct": round(100 * coverage, 1),
        "start": unique.min().date().isoformat(),
        "end": unique.max().date().isoformat(),
        "periods": len(unique),
    }
    if not result["regular"]:
        # Transactions on random days: suggest a sensible grain for charts instead.
        result["grain"] = "irregular"
        result["suggested_grain"] = (
            "daily" if span_days <= 90 else "weekly" if span_days <= 730 else "monthly"
        )
        result |= {"gaps": [], "missing_periods": 0}
        return result

    result["missing_periods"] = len(missing)
    result["gaps"] = _group_gaps(missing)[:MAX_GAPS_LISTED]
    return result


def _group_gaps(missing: list) -> list[dict]:
    """Turn missing periods into ranges, e.g. 10 Aug, 11 Aug, 12 Aug -> one gap."""
    gaps: list[dict] = []
    for period in missing:
        if gaps and period - 1 == gaps[-1]["_last"]:
            gaps[-1]["_last"] = period
            gaps[-1]["periods"] += 1
        else:
            gaps.append({"_first": period, "_last": period, "periods": 1})
    return [
        {
            "start": g["_first"].start_time.date().isoformat(),
            "end": g["_last"].start_time.date().isoformat(),
            "periods": g["periods"],
        }
        for g in gaps
    ]


def build_warnings(columns: list[dict], duplicates: int, time: dict | None) -> list[dict]:
    warnings: list[dict] = []
    if duplicates:
        warnings.append(
            {
                "code": "DUPLICATE_ROWS",
                "message": f"{duplicates} duplicate rows found.",
                "fix": "drop_duplicates",
            }
        )
    for col in columns:
        name, stats = col["name"], col["stats"]
        if stats["missing_pct"] >= HIGH_MISSING_PCT:
            warnings.append(
                {
                    "code": "HIGH_MISSING",
                    "column": name,
                    "message": f"'{name}' is {stats['missing_pct']}% empty.",
                    "fix": "fill_or_drop_missing",
                }
            )
        if stats["unique"] == 1:
            warnings.append(
                {
                    "code": "CONSTANT_COLUMN",
                    "column": name,
                    "message": f"'{name}' has the same value in every row.",
                    "fix": "drop_column",
                }
            )
        if col["details"].get("unparsed_values"):
            warnings.append(
                {
                    "code": "CONVERSION_LOSS",
                    "column": name,
                    "message": (
                        f"{col['details']['unparsed_values']} values in '{name}' could not be "
                        f"read as {col['type']} and are treated as empty."
                    ),
                }
            )
        if col["details"].get("dayfirst_ambiguous"):
            warnings.append(
                {
                    "code": "AMBIGUOUS_DATES",
                    "column": name,
                    "message": f"Dates in '{name}' could be DD/MM or MM/DD; assumed DD/MM.",
                    "fix": "confirm_date_format",
                }
            )
    if time and time.get("missing_periods"):
        warnings.append(
            {
                "code": "TIME_GAPS",
                "column": time["column"],
                "message": f"{time['missing_periods']} {time['grain']} periods have no data.",
            }
        )
    return warnings


def build_profile(
    raw_df: pd.DataFrame, overrides: dict[str, dict] | None = None
) -> tuple[dict, pd.DataFrame]:
    """Return the profile and the data converted to its inferred types."""
    types, df = infer_types(raw_df, overrides)

    columns: list[dict] = []
    for info in types:
        series = df[info.name]
        role = assign_role(info, series)
        columns.append(
            {
                "name": info.name,
                "type": info.inferred_type,
                "role": role,
                "details": info.details,
                "stats": column_stats(info, role, series),
            }
        )

    time = None
    time_columns = [c for c in columns if c["role"] == "time"]
    if time_columns:
        primary = min(time_columns, key=lambda c: c["stats"]["missing"])
        time = {"column": primary["name"], **detect_grain(df[primary["name"]])}

    duplicates = int(raw_df.duplicated().sum())
    profile = {
        "rows": len(df),
        "columns": len(df.columns),
        "duplicate_rows": duplicates,
        "missing_cells": int(df.isna().sum().sum()),
        "time": time,
        "roles": {
            role: [c["name"] for c in columns if c["role"] == role]
            for role in ("time", "metric", "category", "identifier", "free_text")
        },
        "column_details": columns,
        "warnings": build_warnings(columns, duplicates, time),
    }
    return profile, df


def to_jsonable(value):
    """Convert numpy and pandas values so the profile can be saved as JSON."""
    if isinstance(value, dict):
        return {k: to_jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [to_jsonable(v) for v in value]
    if isinstance(value, np.generic):
        return value.item()
    return value
