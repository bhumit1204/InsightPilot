# InsightPilot

**Upload a CSV, get the story behind your data.**

InsightPilot is a data analyst assistant for small businesses and non-technical teams. Upload any CSV (sales, HR, expenses) and it profiles the data, builds charts, writes plain-language insights, answers your questions, and explains unusual jumps and dips using the data itself and news from that time.

> **Status:** early development. Phases 1–2 of 15 are complete: the backend accepts CSV uploads and stores them safely. See the [roadmap](#roadmap) for what works today.

---

## Why InsightPilot

Small teams have data but no analyst. Spreadsheets show numbers, not reasons. InsightPilot aims to answer three questions automatically:

1. **What is in my data?** Profile, quality checks, charts and key insights.
2. **What happened?** Ask questions and get exact answers with a chart.
3. **Why did it happen?** Break changes into their drivers, flag anomalies, and show news from around that time as possible context.

## How it works

InsightPilot is built in two versions.

- **v1: no AI required.** Every question becomes a structured *intent* (metric, grouping, time range, filters) built from smart dropdowns that read like a sentence. A deterministic engine runs it with Pandas. Answers are free, fast and exact.
- **v2: AI as a language layer.** An LLM translates plain English into the same intent and writes explanations. It only sees column names and computed summaries, never raw rows, and every number still comes from Pandas.

```json
{
  "action": "rank",
  "metric": "revenue",
  "aggregation": "sum",
  "group_by": "product",
  "time_range": "last_quarter",
  "limit": 5
}
```

## Features

| Feature | Version | Status |
| --- | --- | --- |
| CSV upload with encoding and delimiter detection | v1 | Done |
| Data profile: types, roles, missing values, quality report | v1 | Planned |
| Auto-generated charts and rule-based insights | v1 | Planned |
| Sentence-style question builder and suggested questions | v1 | Planned |
| "Why did this change?" driver breakdown | v1 | Planned |
| Anomaly detection with holiday and data-gap checks | v1 | Planned |
| News around each anomaly | v1 | Planned |
| PDF insights report | v1 | Planned |
| Plain-English questions | v2 | Planned |
| AI-written explanations with sources | v2 | Planned |
| Market radar: forecast plus news signals | v2 | Planned |

## Tech stack

- **Backend:** Python, FastAPI, Pydantic, Pandas, PyArrow (Parquet storage)
- **Analysis (planned):** statsmodels, ruptures, holidays
- **Frontend (planned):** Next.js, TypeScript, Tailwind CSS, shadcn/ui, ECharts
- **Tooling:** pytest, ruff, GitHub Actions

## Project structure

```
insightpilot/
├── backend/
│   ├── app/
│   │   ├── api/          # route handlers
│   │   ├── core/         # config, errors, logging
│   │   ├── models/       # request and response schemas
│   │   ├── services/     # storage, CSV reader, analysis logic
│   │   └── main.py       # app entry point
│   ├── sessions/         # uploaded data (git-ignored)
│   ├── tests/
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── pyproject.toml
├── frontend/             # coming in Phase 4
└── samples/              # demo datasets and their generator
```

## Getting started

### Prerequisites

- Python 3.11+
- Git

### Run the backend

```bash
git clone https://github.com/bhumit1204/InsightPilot.git
cd InsightPilot/backend

python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements-dev.txt
cp .env.example .env        # Windows: copy .env.example .env

uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for the interactive API docs. Try `POST /api/sessions` with a file from `samples/`.

### Sample datasets

Three demo datasets with known, planted events (COVID-19 lockdown, Diwali spikes, a price cut, a regional slump and more) live in `samples/`. Regenerate them from the repo root with:

```bash
python samples/generate_samples.py
```

See [samples/README.md](samples/README.md) for every planted event and the effect it should have.

### Run tests and lint

```bash
pytest -v
ruff check .
ruff format --check .
```

## API

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/health` | Health check |
| POST | `/api/sessions` | Upload a CSV (max 50 MB); returns a session ID, row and column counts, column names, detected encoding and delimiter |
| DELETE | `/api/sessions/{session_id}` | Delete a session and its data |

Example response from `POST /api/sessions`:

```json
{
  "session_id": "910178cb5bd24568bdf336f7bea6a813",
  "filename": "retail_sales.sample.csv",
  "rows": 54855,
  "columns": 8,
  "column_names": ["order_line_id", "date", "region", "category", "product",
                   "units_sold", "unit_price_inr", "revenue_inr"],
  "encoding": "utf-8",
  "delimiter": ","
}
```

Each upload is stored in its own folder as `raw.csv` (original), `data.parquet` (clean data) and `metadata.json`.

All errors use one format:

```json
{ "error": { "code": "NOT_FOUND", "message": "Not Found" } }
```

## Roadmap

| Phase | Name | Version | Status |
| --- | --- | --- | --- |
| 0 | Project scaffold | v1 | Done |
| 1 | Backend foundations | v1 | Done |
| 2 | Upload and storage | v1 | Done |
| 3 | Profiling, cleaning and rule-based context | v1 | Next |
| 4 | Frontend foundations | v1 | |
| 5 | Charts and template insights | v1 | |
| 6 | Intent engine and question builder | v1 | |
| 7 | "Why did this change?" analysis | v1 | |
| 8 | Anomaly detection and internal checks | v1 | |
| 9 | Keyword news around anomalies | v1 | |
| 10 | Report, deploy and v1 launch | v1 | |
| 11 | LLM adapter and context guess | v2 | |
| 12 | Plain-English intent parser | v2 | |
| 13 | LLM insights and news explanations | v2 | |
| 14 | Market radar | v2 | |
| 15 | Evaluation and v2 launch | v2 | |

## Design principles

- **Numbers come from code, not from AI.** Insights and answers are computed with Pandas; language models only interpret and phrase.
- **Your data stays private.** Raw rows are never sent to an AI provider, and uploaded data is deleted after 24 hours.
- **Context, not causation.** News is shown as possible context for a change, never as proof of its cause.

## License

MIT