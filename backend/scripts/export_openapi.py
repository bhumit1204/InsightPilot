"""Write the API schema to frontend/openapi.json so the frontend can generate its types.

Run from the backend folder after changing any endpoint or model:
    python -m scripts.export_openapi
"""

import json
from pathlib import Path

from app.main import app

OUTPUT = Path(__file__).resolve().parents[2] / "frontend" / "openapi.json"


def render_schema() -> str:
    return json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    OUTPUT.write_text(render_schema(), encoding="utf-8")
    print(f"Wrote {OUTPUT}")