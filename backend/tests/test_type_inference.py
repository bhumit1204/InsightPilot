from pathlib import Path

import pandas as pd
import pytest

from app.services.csv_reader import read_csv_bytes
from app.services.type_inference import infer_column, infer_types

SAMPLES_DIR = Path(__file__).resolve().parents[2] / "samples"


def kind(values) -> str:
    info, _ = infer_column("col", pd.Series(values))
    return info.inferred_type


def test_plain_numbers():
    assert kind([1, 2, 3.5]) == "numeric"


def test_indian_currency_strings():
    info, parsed = infer_column("amount", pd.Series(["₹1,23,456.00", "₹85,000", "Rs. 120"]))
    assert info.inferred_type == "numeric"
    assert info.details["currency"] is True
    assert parsed.tolist() == [123456.0, 85000.0, 120.0]


def test_percent_and_accounting_negatives():
    _, parsed = infer_column("x", pd.Series(["12.5%", "(1,200)", "-3"]))
    assert parsed.tolist() == [12.5, -1200.0, -3.0]


def test_mostly_text_stays_text():
    assert kind(["10", "20", "abc", "def", "xyz"]) == "text"


def test_iso_dates():
    info, parsed = infer_column("d", pd.Series(["2024-01-05", "2024-02-10", None]))
    assert info.inferred_type == "datetime"
    assert info.details["format"] == "%Y-%m-%d"
    assert parsed.iloc[1] == pd.Timestamp("2024-02-10")


def test_day_first_dates_detected_from_day_above_12():
    info, parsed = infer_column("d", pd.Series(["25/03/2024", "01/04/2024"]))
    assert info.details["format"] == "%d/%m/%Y"
    assert info.details["dayfirst_ambiguous"] is False
    assert parsed.iloc[1] == pd.Timestamp("2024-04-01")


def test_month_first_dates():
    info, _ = infer_column("d", pd.Series(["03/25/2024", "04/01/2024"]))
    assert info.details["format"] == "%m/%d/%Y"


def test_ambiguous_dates_default_to_day_first_and_are_flagged():
    info, _ = infer_column("d", pd.Series(["03/04/2024", "05/06/2024"]))
    assert info.details["format"] == "%d/%m/%Y"
    assert info.details["dayfirst_ambiguous"] is True


def test_numbers_are_not_dates():
    assert kind(["2024", "2025", "2026"]) == "numeric"


@pytest.mark.parametrize("values", [["Yes", "No", "yes"], ["TRUE", "false"], [0, 1, 1, 0]])
def test_booleans(values):
    assert kind(values) == "boolean"


def test_categories_stay_text():
    assert kind(["North", "South", "East"]) == "text"


def load_sample(name: str) -> pd.DataFrame:
    path = SAMPLES_DIR / name
    if not path.exists():
        pytest.skip(f"{name} not generated")
    return read_csv_bytes(path.read_bytes()).df


def test_expenses_sample_types():
    types, df = infer_types(load_sample("business_expenses.sample.csv"))
    by_name = {t.name: t for t in types}
    assert by_name["date"].inferred_type == "datetime"
    assert by_name["date"].details["format"] == "%d/%m/%Y"
    assert by_name["amount"].inferred_type == "numeric"
    assert by_name["amount"].details["currency"] is True
    assert by_name["vendor"].inferred_type == "text"
    assert 245000.0 in df["amount"].tolist()  # the one-off equipment purchase


def test_retail_and_hr_sample_types():
    retail, _ = infer_types(load_sample("retail_sales.sample.csv"))
    assert {t.name: t.inferred_type for t in retail} == {
        "order_line_id": "text",
        "date": "datetime",
        "region": "text",
        "category": "text",
        "product": "text",
        "units_sold": "numeric",
        "unit_price_inr": "numeric",
        "revenue_inr": "numeric",
    }
    hr, _ = infer_types(load_sample("hr_employees.sample.csv"))
    hr_types = {t.name: t.inferred_type for t in hr}
    assert hr_types["hire_date"] == "datetime"
    assert hr_types["exit_date"] == "datetime"
    assert hr_types["annual_salary_inr"] == "numeric"
