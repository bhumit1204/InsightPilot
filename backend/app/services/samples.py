"""Demo datasets people can try without uploading their own file."""

from functools import lru_cache
from pathlib import Path

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.sample import SampleDataset
from app.models.session import SessionCreated
from app.services.session_service import create_session_from_bytes

SAMPLES = {
    # key: (title, description, shape as (rows, columns))
    "retail_sales": (
        "Retail sales, India",
        "Daily sales of six products across four regions, 2019 to 2025. Includes the 2020 "
        "lockdown, Diwali rushes and a regional slump to discover.",
        (54_855, 8),
    ),
    "hr_employees": (
        "Employee records",
        "1,200 employees with departments, cities, salaries, ratings, hire and exit dates.",
        (1_200, 10),
    ),
    "business_expenses": (
        "Business expenses",
        "Three years of small-business spending, exported messily: DD/MM dates, rupee "
        "amounts written as text, blank vendors and duplicate rows.",
        (438, 5),
    ),
}


def _path(key: str) -> Path:
    return get_settings().samples_dir / f"{key}.sample.csv"


@lru_cache
def list_samples() -> list[SampleDataset]:
    """Samples whose file exists. Run `python samples/generate_samples.py` to create them."""
    samples = []
    for key, (title, description, (rows, columns)) in SAMPLES.items():
        path = _path(key)
        if path.exists():
            samples.append(
                SampleDataset(
                    key=key,
                    title=title,
                    description=description,
                    filename=path.name,
                    rows=rows,
                    columns=columns,
                    size_bytes=path.stat().st_size,
                )
            )
    return samples


def create_session_from_sample(key: str) -> SessionCreated:
    if key not in SAMPLES or not _path(key).exists():
        raise AppError("SAMPLE_NOT_FOUND", f"There is no sample dataset called '{key}'.", 404)
    path = _path(key)
    return create_session_from_bytes(path.read_bytes(), path.name)
