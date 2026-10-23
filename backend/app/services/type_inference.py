"""Work out what kind of data each column holds: number, date, yes/no or text.

Values are parsed, never guessed: a column counts as numeric or date only if
at least 95% of its non-empty values actually parse that way.
"""

import re
from dataclasses import asdict, dataclass, field

import pandas as pd

PARSE_THRESHOLD = 0.95
DATE_SAMPLE_SIZE = 2000

CURRENCY_PATTERN = re.compile(r"(?:₹|\$|€|£|¥|\bRs\.?|\bINR\b|\bUSD\b)", re.IGNORECASE)
TRUE_VALUES = {"true", "yes", "y", "t"}
FALSE_VALUES = {"false", "no", "n", "f"}

# Tried in order; for ambiguous dates like 03/04/2024 day-first wins (DD/MM is the norm in India).
DATE_FORMATS = [
    "%Y-%m-%d",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%d-%m-%Y",
    "%m-%d-%Y",
    "%d.%m.%Y",
    "%Y/%m/%d",
    "%d/%m/%Y %H:%M",
    "%m/%d/%Y %H:%M",
    "%d %b %Y",
    "%d-%b-%Y",
    "%b %d, %Y",
    "%b %Y",
    "%Y-%m",
]


@dataclass
class ColumnType:
    name: str
    inferred_type: str  # "numeric" | "datetime" | "boolean" | "text"
    original_dtype: str
    parse_ratio: float = 1.0
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def _non_empty_text(series: pd.Series) -> pd.Series:
    text = series.dropna().astype(str).str.strip()
    return text[text != ""]


def parse_numeric(series: pd.Series) -> tuple[pd.Series, float, dict]:
    """Parse numbers written like '₹1,23,456.00', '12.5%', '(1,200)' or '$ 99'."""
    if pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series):
        return series, 1.0, {}

    text = series.astype("string").str.strip()
    has_currency = bool(text.str.contains(CURRENCY_PATTERN, na=False).any())
    has_percent = bool(text.str.endswith("%", na=False).any())

    cleaned = (
        text.str.replace(CURRENCY_PATTERN, "", regex=True)
        .str.replace(",", "", regex=False)
        .str.replace("%", "", regex=False)
        .str.replace(r"^\((.*)\)$", r"-\1", regex=True)  # accounting negatives: (1200) -> -1200
        .str.strip()
    )
    parsed = pd.to_numeric(cleaned, errors="coerce")

    non_empty = int((text.fillna("") != "").sum())
    ratio = float(parsed.notna().sum() / non_empty) if non_empty else 0.0
    details = {"currency": has_currency, "percent": has_percent}
    return parsed, ratio, details


def parse_datetime(series: pd.Series) -> tuple[pd.Series, float, dict]:
    """Find the date format that parses the most values, then parse the whole column with it."""
    text = _non_empty_text(series)
    if text.empty or text.str.fullmatch(r"-?\d+(\.\d+)?").all():
        return series, 0.0, {}  # plain numbers are not dates

    sample = text.head(DATE_SAMPLE_SIZE)
    best_format, best_ratio = None, 0.0
    for fmt in DATE_FORMATS:
        ratio = float(pd.to_datetime(sample, format=fmt, errors="coerce").notna().mean())
        if ratio > best_ratio + 1e-9:
            best_format, best_ratio = fmt, ratio

    details: dict = {"format": best_format}
    if best_format is None or best_ratio < PARSE_THRESHOLD:
        mixed = pd.to_datetime(sample, format="mixed", dayfirst=True, errors="coerce")
        if float(mixed.notna().mean()) < PARSE_THRESHOLD:
            return series, best_ratio, {}
        best_format, details = None, {"format": "mixed"}

    full_text = series.astype("string").str.strip()
    if best_format:
        parsed = pd.to_datetime(full_text, format=best_format, errors="coerce")
    else:
        parsed = pd.to_datetime(full_text, format="mixed", dayfirst=True, errors="coerce")

    if best_format in ("%d/%m/%Y", "%d-%m-%Y", "%d/%m/%Y %H:%M"):
        # Ambiguous if no value proves the order (a day above 12 would).
        details["dayfirst_ambiguous"] = bool((parsed.dt.day <= 12).all())

    ratio = float(parsed.notna().sum() / len(text))
    return parsed, ratio, details


def parse_boolean(series: pd.Series) -> tuple[pd.Series, float]:
    if pd.api.types.is_bool_dtype(series):
        return series, 1.0
    text = _non_empty_text(series).str.lower()
    if text.empty or text.nunique() != 2 or not set(text) <= TRUE_VALUES | FALSE_VALUES:
        return series, 0.0
    mapping = {v: True for v in TRUE_VALUES} | {v: False for v in FALSE_VALUES}
    parsed = series.astype("string").str.strip().str.lower().map(mapping).astype("boolean")
    return parsed, 1.0


def infer_column(name: str, series: pd.Series) -> tuple[ColumnType, pd.Series]:
    original = str(series.dtype)

    if pd.api.types.is_datetime64_any_dtype(series):
        return ColumnType(name, "datetime", original), series

    parsed, ratio = parse_boolean(series)
    if ratio == 1.0:
        return ColumnType(name, "boolean", original), parsed

    parsed, ratio, details = parse_numeric(series)
    if ratio >= PARSE_THRESHOLD:
        values = parsed.dropna().unique()
        if len(values) == 2 and set(values) <= {0, 1}:
            return ColumnType(name, "boolean", original, ratio, {"encoding": "0/1"}), parsed
        return ColumnType(name, "numeric", original, round(ratio, 4), details), parsed

    parsed, ratio, details = parse_datetime(series)
    if ratio >= PARSE_THRESHOLD:
        return ColumnType(name, "datetime", original, round(ratio, 4), details), parsed

    return ColumnType(name, "text", original), series


def infer_types(df: pd.DataFrame) -> tuple[list[ColumnType], pd.DataFrame]:
    """Return the type of every column and a copy of the data converted to those types."""
    types: list[ColumnType] = []
    converted = {}
    for name in df.columns:
        info, parsed = infer_column(name, df[name])
        types.append(info)
        converted[name] = parsed
    return types, pd.DataFrame(converted, index=df.index)
