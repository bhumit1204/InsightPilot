import pytest

from app.core.config import get_settings
from app.core.errors import AppError
from app.services import storage


@pytest.fixture(autouse=True)
def temp_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "storage_dir", tmp_path)


def test_create_and_delete_session():
    session_id, path = storage.create_session()
    assert path.is_dir()
    storage.delete_session(session_id)
    assert not path.exists()


def test_rejects_path_traversal():
    with pytest.raises(AppError) as exc:
        storage.session_dir("../../etc")
    assert exc.value.code == "INVALID_SESSION_ID"


def test_missing_session_is_404():
    with pytest.raises(AppError) as exc:
        storage.get_existing_session("0" * 32)
    assert exc.value.status_code == 404
