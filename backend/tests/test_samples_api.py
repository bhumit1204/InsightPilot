import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.services import samples

client = TestClient(app)


@pytest.fixture(autouse=True)
def temp_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "storage_dir", tmp_path)
    samples.list_samples.cache_clear()
    yield
    samples.list_samples.cache_clear()


def require_samples():
    if not (get_settings().samples_dir / "retail_sales.sample.csv").exists():
        pytest.skip("samples not generated")


def test_lists_available_samples():
    require_samples()
    response = client.get("/api/samples")
    assert response.status_code == 200
    keys = [s["key"] for s in response.json()]
    assert keys == ["retail_sales", "hr_employees", "business_expenses"]
    assert response.json()[0]["rows"] == 54_855


def test_start_session_from_sample():
    require_samples()
    response = client.post("/api/samples/business_expenses/sessions")
    assert response.status_code == 201
    body = response.json()
    assert body["rows"] == 438
    assert body["filename"] == "business_expenses.sample.csv"
    profile = client.get(f"/api/sessions/{body['session_id']}/profile").json()
    assert profile["duplicate_rows"] == 0  # removed automatically after upload
    assert profile["rows"] == 434


def test_listed_shapes_match_the_files():
    require_samples()
    for sample in client.get("/api/samples").json():
        body = client.post(f"/api/samples/{sample['key']}/sessions").json()
        assert (body["rows"], body["columns"]) == (sample["rows"], sample["columns"])  # as uploaded


def test_unknown_sample_is_404():
    response = client.post("/api/samples/nope/sessions")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SAMPLE_NOT_FOUND"


def test_missing_samples_folder_lists_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "samples_dir", tmp_path / "none")
    assert client.get("/api/samples").json() == []
