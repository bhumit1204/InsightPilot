from pydantic import BaseModel


class SampleDataset(BaseModel):
    key: str
    title: str
    description: str
    filename: str
    rows: int
    columns: int
    size_bytes: int
