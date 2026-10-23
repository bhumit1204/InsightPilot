import pytest

from app.core.errors import AppError
from app.services.csv_reader import read_csv_bytes


def test_reads_simple_utf8_csv():
    result = read_csv_bytes(b"date,product,revenue\n2026-01-01,Pen,120\n2026-01-02,Book,300\n")
    assert result.delimiter == ","
    assert list(result.df.columns) == ["date", "product", "revenue"]
    assert len(result.df) == 2


def test_detects_semicolon_and_latin1():
    raw = "ville;montant\nMontréal;10\nQuébec;20\n".encode("latin-1")
    result = read_csv_bytes(raw)
    assert result.delimiter == ";"
    assert result.df["ville"].tolist() == ["Montréal", "Québec"]


def test_handles_utf8_bom():
    result = read_csv_bytes(b"\xef\xbb\xbfname,score\nA,1\nB,2\n")
    assert result.df.columns[0] == "name"


def test_drops_blank_rows_and_repeated_headers():
    raw = b"name,score\nA,1\n,\nname,score\nB,2\n\n"
    result = read_csv_bytes(raw)
    assert result.df["name"].tolist() == ["A", "B"]


def test_cleans_duplicate_and_empty_column_names():
    raw = b"name,name,,score\nA,B,C,1\n"
    result = read_csv_bytes(raw)
    assert list(result.df.columns) == ["name", "name_2", "column_3", "score"]


@pytest.mark.parametrize(
    ("raw", "code"),
    [
        (b"", "EMPTY_FILE"),
        (b"only_one_column\n1\n2\n", "TOO_FEW_COLUMNS"),
        (b"name,score\n", "NO_ROWS"),
        (b"1,2,3\n4,5,6\n", "NO_HEADER"),
    ],
)
def test_rejects_bad_files(raw, code):
    with pytest.raises(AppError) as exc:
        read_csv_bytes(raw)
    assert exc.value.code == code