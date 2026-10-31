import json
import logging
import shutil
from datetime import UTC, datetime

from app.core.config import get_settings
from app.models.session import SessionCreated
from app.services import storage
from app.services.csv_reader import read_csv_bytes

logger = logging.getLogger(__name__)


def create_session_from_bytes(raw: bytes, filename: str) -> SessionCreated:
    """Parse a CSV and store it as a new session. Used by uploads and by sample datasets."""
    result = read_csv_bytes(raw)  # raises a clear AppError for bad files

    session_id, path = storage.create_session()
    try:
        (path / storage.RAW_FILE).write_bytes(raw)
        storage.save_dataframe(result.df, path)

        summary = SessionCreated(
            session_id=session_id,
            filename=filename,
            rows=len(result.df),
            columns=result.df.shape[1],
            column_names=list(result.df.columns),
            encoding=result.encoding,
            delimiter=result.delimiter,
        )
        metadata = summary.model_dump() | {"created_at": datetime.now(UTC).isoformat()}
        (path / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    except Exception:
        shutil.rmtree(path, ignore_errors=True)  # never leave half-written sessions behind
        raise

    if get_settings().auto_clean:
        # Imported here: cleaning depends on profiling, which this module should not load early.
        from app.services.cleaning import auto_clean

        try:
            auto_clean(session_id)
        except Exception:  # a failed tidy-up must never block the upload itself
            logger.exception("Automatic cleaning failed for session %s", session_id)

    return summary
