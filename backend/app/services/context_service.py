"""Guess what a dataset is about (domain, region, main metric) using rules, no AI.

The guess is always shown to the user to confirm or edit; the confirmed context
later steers insight wording and news searches.
"""

import re

import pandas as pd

from app.core.errors import AppError
from app.models.context import ContextOptions, ContextUpdate, DataContext
from app.services import storage
from app.services.profile_service import get_profile

DOMAINS = {
    # key: (label, keywords matched against column names, file name and category values)
    "retail_sales": (
        "Retail sales",
        [
            "revenue",
            "sales",
            "sold",
            "units",
            "order",
            "product",
            "sku",
            "price",
            "customer",
            "store",
            "quantity",
            "discount",
        ],
    ),
    "hr": (
        "HR and people",
        [
            "employee",
            "salary",
            "hire",
            "department",
            "attrition",
            "exit",
            "designation",
            "gender",
            "performance",
            "manager",
            "tenure",
        ],
    ),
    "expenses": (
        "Business expenses",
        [
            "expense",
            "vendor",
            "amount",
            "payment",
            "invoice",
            "bill",
            "spend",
            "reimbursement",
            "cost",
        ],
    ),
    "finance": (
        "Finance and accounting",
        [
            "profit",
            "loss",
            "balance",
            "debit",
            "credit",
            "account",
            "transaction",
            "interest",
            "loan",
            "ledger",
        ],
    ),
    "marketing": (
        "Marketing",
        [
            "campaign",
            "clicks",
            "impressions",
            "ctr",
            "conversion",
            "leads",
            "cpc",
            "channel",
            "ad_spend",
        ],
    ),
    "saas": (
        "SaaS and subscriptions",
        ["mrr", "arr", "churn", "subscription", "plan", "signup", "trial", "active_users"],
    ),
    "inventory": (
        "Inventory and logistics",
        ["stock", "inventory", "warehouse", "shipment", "delivery", "supplier", "reorder"],
    ),
    "general": ("General", []),
}

REGIONS = [
    "India",
    "United States",
    "United Kingdom",
    "Canada",
    "Australia",
    "Singapore",
    "United Arab Emirates",
    "Germany",
    "France",
    "Global",
]
TIME_GRAINS = ["daily", "weekly", "monthly", "quarterly", "yearly"]

CURRENCY_HINTS = [
    # (pattern in values or column names, currency, region)
    (re.compile(r"₹|\bRs\.?\s?\d|\bINR\b|_inr\b", re.IGNORECASE), "INR", "India"),
    (re.compile(r"£|\bGBP\b|_gbp\b", re.IGNORECASE), "GBP", "United Kingdom"),
    (re.compile(r"€|\bEUR\b|_eur\b", re.IGNORECASE), "EUR", None),
    (re.compile(r"\bAED\b|_aed\b", re.IGNORECASE), "AED", "United Arab Emirates"),
    (re.compile(r"\bSGD\b|_sgd\b", re.IGNORECASE), "SGD", "Singapore"),
    (re.compile(r"\$|\bUSD\b|_usd\b", re.IGNORECASE), "USD", None),  # $ is used by many countries
]

PLACES = {
    "India": [
        "mumbai",
        "delhi",
        "new delhi",
        "bengaluru",
        "bangalore",
        "pune",
        "chennai",
        "hyderabad",
        "kolkata",
        "ahmedabad",
        "jaipur",
        "lucknow",
        "surat",
        "noida",
        "gurugram",
        "gurgaon",
        "maharashtra",
        "karnataka",
        "tamil nadu",
        "gujarat",
        "kerala",
        "telangana",
        "uttar pradesh",
        "west bengal",
        "rajasthan",
    ],
    "United States": [
        "new york",
        "california",
        "texas",
        "san francisco",
        "los angeles",
        "chicago",
        "seattle",
        "boston",
        "florida",
        "washington",
    ],
    "United Kingdom": [
        "london",
        "manchester",
        "birmingham",
        "edinburgh",
        "glasgow",
        "england",
        "scotland",
    ],
    "Canada": ["toronto", "vancouver", "montreal", "ontario", "quebec", "alberta"],
    "Australia": ["sydney", "melbourne", "brisbane", "perth", "queensland", "victoria"],
    "Singapore": ["singapore"],
    "United Arab Emirates": ["dubai", "abu dhabi", "sharjah"],
    "Germany": ["berlin", "munich", "hamburg", "frankfurt"],
    "France": ["paris", "lyon", "marseille"],
}

MONEY_WORDS = [
    "revenue",
    "sales",
    "amount",
    "salary",
    "cost",
    "spend",
    "profit",
    "value",
    "total",
    "price",
    "income",
]


def _normalise(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(text).lower()).strip("_")


def guess_domain(
    column_names: list[str], filename: str, values: list[str]
) -> tuple[str, float, list[str]]:
    names = [_normalise(c) for c in column_names]
    file_words = _normalise(filename)
    value_text = " ".join(_normalise(v) for v in values)

    scores: dict[str, float] = {}
    hits: dict[str, list[str]] = {}
    for key, (_, keywords) in DOMAINS.items():
        score, found = 0.0, []
        for word in keywords:
            if any(word in name for name in names):
                score += 2
                found.append(word)
            if word in file_words:
                score += 3
            if word in value_text:
                score += 0.5
        scores[key], hits[key] = score, found

    best = max(scores, key=scores.get)
    total = sum(scores.values())
    if scores[best] < 2:
        return "general", 0.2, ["No column names matched a known domain."]

    confidence = round(min(0.95, scores[best] / total + 0.2), 2)
    reason = f"Columns mention {', '.join(hits[best][:4])}." if hits[best] else ""
    return best, confidence, [reason] if reason else []


def guess_region(raw: pd.DataFrame, column_names: list[str]) -> tuple[str, str | None, list[str]]:
    sample_text = " ".join(
        raw[col].dropna().astype(str).head(300).str.cat(sep=" ")
        for col in raw.columns
        if pd.api.types.is_string_dtype(raw[col]) or raw[col].dtype == object
    )
    names_text = " ".join(_normalise(c) for c in column_names)

    currency, region, reasons = None, None, []
    for pattern, code, place in CURRENCY_HINTS:
        if pattern.search(sample_text) or pattern.search(names_text):
            currency, region = code, place
            reasons.append(f"Amounts use {code}.")
            break

    lowered = sample_text.lower()
    place_hits = {
        country: [p for p in places if re.search(rf"\b{re.escape(p)}\b", lowered)]
        for country, places in PLACES.items()
    }
    best_country = max(place_hits, key=lambda c: len(place_hits[c]))
    if place_hits[best_country]:
        if region is None or region == best_country:
            region = best_country
            reasons.append(f"Places mentioned: {', '.join(place_hits[best_country][:3])}.")

    return region or "Global", currency, reasons


def guess_primary_metric(profile: dict) -> str | None:
    metrics = [c for c in profile["column_details"] if c["role"] == "metric"]
    if not metrics:
        return None

    def rank(col: dict) -> tuple[int, float]:
        name = _normalise(col["name"])
        is_money = any(word in name for word in MONEY_WORDS) and "unit_price" not in name
        return (1 if is_money else 0, abs(col["stats"].get("sum") or 0))

    return max(metrics, key=rank)["name"]


def guess_entities(profile: dict) -> list[str]:
    """Top values of the main category columns; later used in news searches."""
    entities: list[str] = []
    for col in profile["column_details"]:
        if col["role"] == "category" and 1 < col["stats"]["unique"] <= 20:
            entities += [v["value"] for v in col["stats"].get("top_values", [])[:3]]
    return entities[:8]


def build_guess(session_id: str) -> DataContext:
    profile = get_profile(session_id)
    raw = storage.load_dataframe(session_id)
    metadata = storage.read_json(session_id, "metadata.json") or {}
    names = [c["name"] for c in profile["column_details"]]
    category_values = [
        v["value"]
        for c in profile["column_details"]
        if c["role"] == "category"
        for v in c["stats"].get("top_values", [])
    ]

    domain, confidence, reasons = guess_domain(names, metadata.get("filename", ""), category_values)
    region, currency, region_reasons = guess_region(raw, names)
    time = profile.get("time") or {}
    grain = time.get("grain")
    if grain in ("irregular", "unknown"):
        grain = time.get("suggested_grain")

    return DataContext(
        domain=domain,
        domain_label=DOMAINS[domain][0],
        region=region,
        currency=currency,
        primary_metric=guess_primary_metric(profile),
        time_column=time.get("column"),
        time_grain=grain,
        entities=guess_entities(profile),
        keywords=DOMAINS[domain][1][:5],
        confidence=confidence if region != "Global" else round(confidence * 0.8, 2),
        reasons=reasons + region_reasons,
        confirmed=False,
    )


def get_options(session_id: str) -> ContextOptions:
    profile = get_profile(session_id)
    return ContextOptions(
        domains=[{"key": k, "label": v[0]} for k, v in DOMAINS.items()],
        regions=REGIONS,
        metrics=profile["roles"]["metric"],
        time_columns=profile["roles"]["time"],
        time_grains=TIME_GRAINS,
    )


def _is_still_valid(context: DataContext, options: ContextOptions) -> bool:
    # A cleaning fix (say, dropping a column) can make a saved context point at nothing.
    return (context.primary_metric is None or context.primary_metric in options.metrics) and (
        context.time_column is None or context.time_column in options.time_columns
    )


def get_context(session_id: str) -> DataContext:
    saved = storage.read_json(session_id, storage.CONTEXT_FILE)
    if saved is not None:
        context = DataContext(**saved)
        if _is_still_valid(context, get_options(session_id)):
            return context

    context = build_guess(session_id)
    storage.write_json(session_id, storage.CONTEXT_FILE, context.model_dump())
    return context


def update_context(session_id: str, update: ContextUpdate) -> DataContext:
    context = get_context(session_id)
    options = get_options(session_id)
    changes = update.model_dump(exclude_none=True)

    checks = {
        "domain": [d.key for d in options.domains],
        "region": options.regions,
        "primary_metric": options.metrics,
        "time_column": options.time_columns,
        "time_grain": options.time_grains,
    }
    for field, value in changes.items():
        if value not in checks[field]:
            raise AppError(
                "INVALID_CONTEXT",
                f"'{value}' is not a valid {field.replace('_', ' ')}.",
                400,
            )

    data = context.model_dump() | changes | {"confirmed": True}
    if "domain" in changes:
        data["domain_label"] = DOMAINS[changes["domain"]][0]
        data["keywords"] = DOMAINS[changes["domain"]][1][:5]
    updated = DataContext(**data)
    storage.write_json(session_id, storage.CONTEXT_FILE, updated.model_dump())
    return updated
