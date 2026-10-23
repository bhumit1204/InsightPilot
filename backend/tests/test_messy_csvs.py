"""Real-world CSV quirks the reader must survive, plus the shipped sample datasets."""

from pathlib import Path

import pytest

from app.services.csv_reader import read_csv_bytes

SAMPLES_DIR = Path(__file__).resolve().parents[2] / "samples"


def test_tab_delimited():
    result = read_csv_bytes(b"name\tcity\tsales\nAsha\tPune\t10\nRavi\tDelhi\t20\n")
    assert result.delimiter == "\t"
    assert result.df.shape == (2, 3)


def test_pipe_delimited():
    result = read_csv_bytes(b"name|city|sales\nAsha|Pune|10\nRavi|Delhi|20\n")
    assert result.delimiter == "|"


def test_windows_line_endings():
    result = read_csv_bytes(b"name,sales\r\nAsha,10\r\nRavi,20\r\n")
    assert result.df["name"].tolist() == ["Asha", "Ravi"]


def test_quoted_fields_with_commas():
    raw = b'product,amount\n"Pen, blue","1,200"\n"Book","300"\n'
    result = read_csv_bytes(raw)
    assert result.df["product"].tolist() == ["Pen, blue", "Book"]
    assert result.df["amount"].tolist() == ["1,200", "300"]


def test_currency_strings_are_kept_for_profiling():
    raw = 'item,amount\nRent,"₹85,000.00"\nTea,₹120\n'.encode()
    result = read_csv_bytes(raw)
    assert result.df["amount"].tolist() == ["₹85,000.00", "₹120"]


def test_windows_1252_smart_quotes():
    raw = "note,value\n“Best” seller,5\nCafé order,7\n".encode("cp1252")
    result = read_csv_bytes(raw)
    assert result.df["note"].tolist() == ["“Best” seller", "Café order"]


def test_trailing_empty_columns_from_excel():
    result = read_csv_bytes(b"name,sales,,\nAsha,10,,\nRavi,20,,\n")
    assert list(result.df.columns) == ["name", "sales"]


def test_whitespace_around_column_names():
    result = read_csv_bytes(b" name , sales \nAsha,10\n")
    assert list(result.df.columns) == ["name", "sales"]


@pytest.mark.parametrize(
    ("filename", "rows", "columns"),
    [
        ("retail_sales.sample.csv", 54_855, 8),
        ("hr_employees.sample.csv", 1_200, 10),
        ("business_expenses.sample.csv", 438, 5),
    ],
)
def test_sample_datasets_load(filename, rows, columns):
    path = SAMPLES_DIR / filename
    if not path.exists():
        pytest.skip(f"{filename} not generated; run python samples/generate_samples.py")
    result = read_csv_bytes(path.read_bytes())
    assert result.df.shape == (rows, columns)
