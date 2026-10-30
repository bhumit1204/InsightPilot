import pytest

from scripts.export_openapi import OUTPUT, render_schema


def test_frontend_schema_is_up_to_date():
    """Fails when an endpoint changed but frontend/openapi.json was not regenerated."""
    if not OUTPUT.exists():
        pytest.skip("frontend/openapi.json not generated yet")
    assert OUTPUT.read_text(encoding="utf-8") == render_schema(), (
        "API changed: run `python -m scripts.export_openapi` in backend, "
        "then `npm run api:types` in frontend"
    )