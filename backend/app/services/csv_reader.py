import csv
import io
from dataclasses import dataclass

import pandas as pd
from charset_normalizer import from_bytes

from app.core.errors import AppError

CANDIDATE_DELIMITERS = ",;\t|"
SNIFF_BYTES = 200_000


@dataclass
class ReadResult:
    df: pd.DataFrame
    encoding: str
    delimiter: str


def detect_encoding(raw: bytes) -> str:
    if raw.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    try:
        raw.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        pass
    best = from_bytes(raw[:SNIFF_BYTES]).best()
    return best.encoding if best else "latin-1"


def detect_delimiter(sample: str) -> str:
    lines = [line for line in sample.splitlines() if line.strip()][:20]
    try:
        return csv.Sniffer().sniff("\n".join(lines), delimiters=CANDIDATE_DELIMITERS).delimiter
    except csv.Error:
        return ","


def clean_column_names(columns) -> list[str]:
    names: list[str] = []
    seen: dict[str, int] = {}
    for i, col in enumerate(columns, start=1):
        name = str(col).strip()
        if not name:
            name = f"column_{i}"
        if name in seen:
            seen[name] += 1
            name = f"{name}_{seen[name]}"
        else:
            seen[name] = 1
        names.append(name)
    return names


def read_raw_header(text: str, delimiter: str) -> list[str]:
    for row in csv.reader(io.StringIO(text), delimiter=delimiter):
        if any(cell.strip() for cell in row):
            return [cell.strip() for cell in row]
    return []


def looks_like_header_missing(columns: list[str]) -> bool:
    # If every column name parses as a number, the first row was probably data.
    def is_number(value: str) -> bool:
        try:
            float(value.replace(",", ""))
            return True
        except ValueError:
            return False

    return all(is_number(c) for c in columns)


def read_csv_bytes(raw: bytes) -> ReadResult:
    if not raw.strip():
        raise AppError("EMPTY_FILE", "The file is empty.", 400)

    encoding = detect_encoding(raw)
    text = raw.decode(encoding, errors="replace")
    delimiter = detect_delimiter(text[:SNIFF_BYTES])

    try:
        df = pd.read_csv(io.StringIO(text), sep=delimiter, skip_blank_lines=True)
    except (pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        raise AppError("UNREADABLE_FILE", f"Could not read the CSV: {exc}", 400) from exc

    # Read the header ourselves: pandas renames duplicates to "name.1" and blanks to "Unnamed: 2".
    raw_header = read_raw_header(text, delimiter)
    if len(raw_header) != df.shape[1]:
        raw_header = [str(c) for c in df.columns]
    if looks_like_header_missing(raw_header):
        raise AppError("NO_HEADER", "The first row should contain column names, not data.", 400)

    # Excel exports sometimes repeat the header row inside the data.
    stripped = df.astype(str).apply(lambda col: col.str.strip())
    df = df[~(stripped == raw_header).all(axis=1)]
    df.columns = clean_column_names(raw_header)

    df = df.dropna(how="all")
    if df.empty:
        raise AppError("NO_ROWS", "The file has a header but no data rows.", 400)

    df = df.dropna(axis=1, how="all")
    if df.shape[1] < 2:
        raise AppError("TOO_FEW_COLUMNS", "The file needs at least 2 columns.", 400)

    return ReadResult(df=df.reset_index(drop=True), encoding=encoding, delimiter=delimiter)