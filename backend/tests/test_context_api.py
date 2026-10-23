from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app

client = TestClient(app)
SAMPLES_DIR = Path(__file__).resolve().parents[2] / "samples"


@pytest.fixture(autouse=True)
def temp_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "storage_dir", tmp_path)


def upload(content: bytes, filename: str) -> str:
    response = client.post("/api/sessions", files={"file": (filename, content, "text/csv")})
    return response.json()["session_id"]


def upload_sample(name: str) -> str:
    path = SAMPLES_DIR / f"{name}.sample.csv"
    if not path.exists():
        pytest.skip(f"{name} not generated")
    return upload(path.read_bytes(), f"{name}.csv")


def get_context(session_id: str) -> dict:
    return client.get(f"/api/sessions/{session_id}/context").json()["context"]


@pytest.mark.parametrize(
    ("sample", "domain", "metric", "time_column", "grain"),
    [
        ("retail_sales", "retail_sales", "revenue_inr", "date", "daily"),
        ("hr_employees", "hr", "annual_salary_inr", "hire_date", "monthly"),
        ("business_expenses", "expenses", "amount", "date", "monthly"),
    ],
)
def test_guess_on_samples(sample, domain, metric, time_column, grain):
    context = get_context(upload_sample(sample))
    assert context["domain"] == domain
    assert context["region"] == "India"
    assert context["currency"] == "INR"
    assert context["primary_metric"] == metric
    assert context["time_column"] == time_column
    assert context["time_grain"] == grain
    assert context["confirmed"] is False


def test_unknown_data_falls_back_to_general_and_global():
    session_id = upload(b"a,b,c\n1,x,2\n3,y,4\n5,x,6\n", "data.csv")
    context = get_context(session_id)
    assert context["domain"] == "general"
    assert context["region"] == "Global"


def test_options_list_choices_for_dropdowns():
    session_id = upload_sample("retail_sales")
    options = client.get(f"/api/sessions/{session_id}/context").json()["options"]
    assert set(options["metrics"]) == {"units_sold", "unit_price_inr", "revenue_inr"}
    assert options["time_columns"] == ["date"]
    assert "India" in options["regions"]


def test_confirm_and_edit_context():
    session_id = upload_sample("retail_sales")
    response = client.put(
        f"/api/sessions/{session_id}/context",
        json={"primary_metric": "units_sold", "time_grain": "weekly"},
    )
    assert response.status_code == 200
    context = response.json()["context"]
    assert context["primary_metric"] == "units_sold"
    assert context["time_grain"] == "weekly"
    assert context["confirmed"] is True
    assert get_context(session_id)["primary_metric"] == "units_sold"  # saved


def test_invalid_choice_is_rejected():
    session_id = upload_sample("retail_sales")
    response = client.put(f"/api/sessions/{session_id}/context", json={"primary_metric": "region"})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_CONTEXT"


def test_context_regenerates_after_metric_column_is_dropped():
    session_id = upload_sample("business_expenses")
    assert get_context(session_id)["primary_metric"] == "amount"
    client.post(
        f"/api/sessions/{session_id}/clean", json={"action": "drop_column", "column": "amount"}
    )
    assert get_context(session_id)["primary_metric"] is None
