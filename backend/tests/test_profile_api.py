import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.services import profile_service

client = TestClient(app)

SAMPLE_CSV = (
    b"order_id,date,region,revenue\n"
    b'1,2026-01-01,North,"\xe2\x82\xb9100"\n'
    b'2,2026-01-02,South,"\xe2\x82\xb9250"\n'
    b'3,2026-01-03,North,"\xe2\x82\xb91,175"\n'
)


@pytest.fixture(autouse=True)
def temp_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "storage_dir", tmp_path)
    return tmp_path


def upload() -> str:
    response = client.post("/api/sessions", files={"file": ("sales.csv", SAMPLE_CSV, "text/csv")})
    return response.json()["session_id"]


def test_profile_endpoint_returns_roles_and_saves_files(temp_storage):
    session_id = upload()
    response = client.get(f"/api/sessions/{session_id}/profile")
    assert response.status_code == 200

    profile = response.json()
    assert profile["roles"]["metric"] == ["revenue"]
    assert profile["roles"]["time"] == ["date"]
    assert profile["time"]["grain"] == "daily"

    folder = temp_storage / session_id
    assert (folder / "profile.json").exists()
    typed = pd.read_parquet(folder / "typed.parquet")
    assert typed["revenue"].sum() == 1525
    assert pd.api.types.is_datetime64_any_dtype(typed["date"])


def test_profile_is_cached(monkeypatch):
    session_id = upload()
    first = client.get(f"/api/sessions/{session_id}/profile").json()

    def fail(*args, **kwargs):
        raise AssertionError("profile should come from cache")

    monkeypatch.setattr(profile_service, "build_profile", fail)
    assert client.get(f"/api/sessions/{session_id}/profile").json() == first


def test_refresh_rebuilds_profile():
    session_id = upload()
    first = client.get(f"/api/sessions/{session_id}/profile").json()
    second = client.get(f"/api/sessions/{session_id}/profile?refresh=true").json()
    assert second["generated_at"] != first["generated_at"]


def test_profile_for_unknown_session_is_404():
    response = client.get(f"/api/sessions/{'0' * 32}/profile")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SESSION_NOT_FOUND"
