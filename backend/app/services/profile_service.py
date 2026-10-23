from datetime import UTC, datetime

import pandas as pd

from app.services import storage
from app.services.profiling import build_profile, to_jsonable


def get_profile(session_id: str, refresh: bool = False) -> dict:
    """Return the cached profile, building it (and the typed data) on first use."""
    if not refresh:
        cached = storage.read_json(session_id, storage.PROFILE_FILE)
        if cached is not None:
            return cached

    df = storage.load_dataframe(session_id)
    profile, typed = build_profile(df)
    profile = to_jsonable(profile) | {"generated_at": datetime.now(UTC).isoformat()}

    folder = storage.get_existing_session(session_id)
    storage.save_dataframe(typed, folder, storage.TYPED_FILE)
    storage.write_json(session_id, storage.PROFILE_FILE, profile)
    return profile


def load_typed_data(session_id: str) -> pd.DataFrame:
    """Data converted to its inferred types; later features (charts, queries) use this."""
    get_profile(session_id)  # makes sure typed.parquet exists
    return storage.load_dataframe(session_id, storage.TYPED_FILE)
