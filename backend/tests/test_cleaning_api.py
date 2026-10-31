import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app

client = TestClient(app)

# Messy on purpose: a duplicate row, missing vendor and amount, a pincode stored as a number,
# and ambiguous DD/MM vs MM/DD dates.
MESSY_CSV = (
    "date,vendor,amount,pincode\n"
    '03/04/2026,Swiggy,"₹1,200",400001\n'
    '05/04/2026,,"₹800",400002\n'
    '03/04/2026,Swiggy,"₹1,200",400001\n'
    "07/04/2026,Uber,,411001\n"
    '08/04/2026,Uber,"₹400",560001\n'
).encode()


@pytest.fixture(autouse=True)
def temp_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "storage_dir", tmp_path)
    monkeypatch.setattr(get_settings(), "auto_clean", False)  # these tests apply fixes by hand


@pytest.fixture
def session_id() -> str:
    response = client.post("/api/sessions", files={"file": ("e.csv", MESSY_CSV, "text/csv")})
    return response.json()["session_id"]


def clean(session_id: str, **body):
    return client.post(f"/api/sessions/{session_id}/clean", json=body)


def column(profile: dict, name: str) -> dict:
    return next(c for c in profile["column_details"] if c["name"] == name)


def test_drop_duplicates(session_id):
    response = clean(session_id, action="drop_duplicates")
    assert response.status_code == 200
    body = response.json()
    assert body["applied"]["rows_before"] == 5
    assert body["applied"]["rows_after"] == 4
    assert body["profile"]["duplicate_rows"] == 0


def test_fill_missing_with_value_and_median(session_id):
    clean(session_id, action="fill_missing", column="vendor", strategy="value", value="Unknown")
    body = clean(session_id, action="fill_missing", column="amount", strategy="median").json()
    assert body["applied"]["value"] == 1000.0  # median of 1200, 800, 1200, 400
    profile = body["profile"]
    assert column(profile, "vendor")["stats"]["missing"] == 0
    assert column(profile, "amount")["stats"]["missing"] == 0
    assert column(profile, "amount")["stats"]["sum"] == 4600.0


def test_median_of_text_column_is_rejected(session_id):
    response = clean(session_id, action="fill_missing", column="vendor", strategy="median")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "NOT_NUMERIC"


def test_drop_missing_rows_and_drop_column(session_id):
    assert (
        clean(session_id, action="drop_missing_rows", column="amount").json()["applied"][
            "rows_after"
        ]
        == 4
    )
    profile = clean(session_id, action="drop_column", column="pincode").json()["profile"]
    assert "pincode" not in [c["name"] for c in profile["column_details"]]


def test_set_type_overrides_inference(session_id):
    profile = client.get(f"/api/sessions/{session_id}/profile").json()
    assert column(profile, "pincode")["type"] == "numeric"

    profile = clean(session_id, action="set_type", column="pincode", type="text").json()["profile"]
    assert column(profile, "pincode")["type"] == "text"
    assert column(profile, "pincode")["details"]["overridden"] is True


def test_confirm_month_first_dates(session_id):
    profile = client.get(f"/api/sessions/{session_id}/profile").json()
    assert "AMBIGUOUS_DATES" in {w["code"] for w in profile["warnings"]}

    body = clean(
        session_id, action="set_type", column="date", type="datetime", date_format="%m/%d/%Y"
    ).json()
    date = column(body["profile"], "date")
    assert date["stats"]["min"].startswith("2026-03-04")  # 03/04/2026 now reads as 4 March
    assert "AMBIGUOUS_DATES" not in {w["code"] for w in body["profile"]["warnings"]}


def test_impossible_conversion_is_rejected(session_id):
    response = clean(session_id, action="set_type", column="vendor", type="numeric")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "CANNOT_CONVERT"


def test_unknown_column(session_id):
    response = clean(session_id, action="drop_column", column="nope")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "COLUMN_NOT_FOUND"


def test_log_and_reset(session_id):
    clean(session_id, action="drop_duplicates")
    clean(session_id, action="drop_column", column="pincode")
    log = client.get(f"/api/sessions/{session_id}/clean/log").json()
    assert [f["action"] for f in log["fixes"]] == ["drop_duplicates", "drop_column"]

    profile = client.post(f"/api/sessions/{session_id}/clean/reset").json()
    assert profile["rows"] == 5
    assert "pincode" in [c["name"] for c in profile["column_details"]]
    assert client.get(f"/api/sessions/{session_id}/clean/log").json() == {"fixes": []}


def test_upload_removes_exact_duplicates_automatically(monkeypatch):
    monkeypatch.setattr(get_settings(), "auto_clean", True)
    response = client.post("/api/sessions", files={"file": ("e.csv", MESSY_CSV, "text/csv")})
    session_id = response.json()["session_id"]
    assert response.json()["rows"] == 5  # as uploaded

    profile = client.get(f"/api/sessions/{session_id}/profile").json()
    assert profile["rows"] == 4
    assert profile["duplicate_rows"] == 0
    log = client.get(f"/api/sessions/{session_id}/clean/log").json()
    assert log["fixes"][0]["action"] == "drop_duplicates"
    assert log["fixes"][0]["auto"] is True

    # Undo brings the duplicate back, and it is not removed again.
    restored = client.post(f"/api/sessions/{session_id}/clean/reset").json()
    assert restored["duplicate_rows"] == 1
