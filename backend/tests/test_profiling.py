from pathlib import Path

import pandas as pd
import pytest

from app.services.csv_reader import read_csv_bytes
from app.services.profiling import build_profile

SAMPLES_DIR = Path(__file__).resolve().parents[2] / "samples"


def load_sample(name: str) -> pd.DataFrame:
    path = SAMPLES_DIR / name
    if not path.exists():
        pytest.skip(f"{name} not generated")
    return read_csv_bytes(path.read_bytes()).df


def column(profile: dict, name: str) -> dict:
    return next(c for c in profile["column_details"] if c["name"] == name)


def test_roles_and_stats_on_small_frame():
    df = pd.DataFrame(
        {
            "order_id": [101, 102, 103, 104],
            "date": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"],
            "region": ["North", "South", "North", "East"],
            "revenue": ["₹100", "₹250", "₹175", "₹5,000"],
        }
    )
    profile, converted = build_profile(df)
    assert profile["roles"]["identifier"] == ["order_id"]
    assert profile["roles"]["time"] == ["date"]
    assert profile["roles"]["category"] == ["region"]
    assert profile["roles"]["metric"] == ["revenue"]
    revenue = column(profile, "revenue")["stats"]
    assert revenue["sum"] == 5525.0
    assert revenue["outliers"] == 1
    assert pd.api.types.is_numeric_dtype(converted["revenue"])


def test_constant_column_and_missing_warnings():
    df = pd.DataFrame(
        {
            "store": ["A"] * 5,
            "sales": [1, 2, None, None, None],
            "units": [3, 4, 5, 6, 7],
        }
    )
    codes = {w["code"] for w in build_profile(df)[0]["warnings"]}
    assert {"CONSTANT_COLUMN", "HIGH_MISSING"} <= codes


def test_retail_sample_profile():
    profile, _ = build_profile(load_sample("retail_sales.sample.csv"))
    assert profile["roles"]["identifier"] == ["order_line_id"]
    assert set(profile["roles"]["category"]) == {"region", "category", "product"}
    assert set(profile["roles"]["metric"]) == {"units_sold", "unit_price_inr", "revenue_inr"}

    time = profile["time"]
    assert time["column"] == "date"
    assert time["grain"] == "daily"
    assert time["gaps"] == [{"start": "2022-08-10", "end": "2022-08-12", "periods": 3}]
    assert "TIME_GAPS" in {w["code"] for w in profile["warnings"]}


def test_expenses_sample_profile():
    profile, _ = build_profile(load_sample("business_expenses.sample.csv"))
    assert profile["duplicate_rows"] == 4
    assert profile["time"]["grain"] == "irregular"
    assert profile["time"]["suggested_grain"] == "monthly"
    assert column(profile, "amount")["role"] == "metric"
    assert column(profile, "vendor")["role"] == "category"
    assert "DUPLICATE_ROWS" in {w["code"] for w in profile["warnings"]}


def test_hr_sample_profile():
    profile, _ = build_profile(load_sample("hr_employees.sample.csv"))
    assert profile["roles"]["identifier"] == ["employee_id"]
    assert profile["time"]["column"] == "hire_date"  # exit_date is mostly empty
    rating = column(profile, "performance_rating")["stats"]
    assert 2 <= rating["missing_pct"] <= 6
    exit_date = column(profile, "exit_date")["stats"]
    assert exit_date["missing_pct"] > 50


def test_constant_columns_are_ignored():
    df = pd.DataFrame({"store": ["A"] * 4, "sales": [1, 2, 3, 4], "region": list("NSNE")})
    profile, _ = build_profile(df)
    assert profile["roles"]["ignored"] == ["store"]
    assert column(profile, "store")["role"] == "ignored"
    assert "CONSTANT_COLUMN" in {w["code"] for w in profile["warnings"]}
