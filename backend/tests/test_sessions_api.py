import json

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app

client = TestClient(app)

SAMPLE_CSV = b"date,product,revenue\n2026-01-01,Pen,120\n2026-01-02,Book,300\n"


@pytest.fixture(autouse=True)
def temp_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "storage_dir", tmp_path)
    return tmp_path


def upload(content: bytes, filename: str = "sales.csv"):
    return client.post("/api/sessions", files={"file": (filename, content, "text/csv")})


def test_upload_creates_session_files(temp_storage):
    response = upload(SAMPLE_CSV)
    assert response.status_code == 201
    body = response.json()
    assert body["rows"] == 2
    assert body["column_names"] == ["date", "product", "revenue"]

    folder = temp_storage / body["session_id"]
    assert (folder / "raw.csv").exists()
    assert json.loads((folder / "metadata.json").read_text())["filename"] == "sales.csv"
    assert len(pd.read_parquet(folder / "data.parquet")) == 2


def test_rejects_non_csv():
    response = upload(SAMPLE_CSV, filename="sales.xlsx")
    assert response.status_code == 415
    assert response.json()["error"]["code"] == "UNSUPPORTED_FILE"


def test_rejects_too_large_file(monkeypatch):
    monkeypatch.setattr(get_settings(), "max_upload_mb", 0)
    response = upload(SAMPLE_CSV)
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "FILE_TOO_LARGE"


def test_bad_csv_leaves_no_session_behind(temp_storage):
    response = upload(b"only_one_column\n1\n")
    assert response.status_code == 400
    assert list(temp_storage.iterdir()) == []


def test_delete_session(temp_storage):
    session_id = upload(SAMPLE_CSV).json()["session_id"]
    assert client.delete(f"/api/sessions/{session_id}").status_code == 204
    assert not (temp_storage / session_id).exists()
    assert client.delete(f"/api/sessions/{session_id}").status_code == 404
