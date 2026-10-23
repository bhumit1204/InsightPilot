"""Generate InsightPilot's demo datasets with known, planted events.

Run from the repo root:  python samples/generate_samples.py
Every event planted here is listed in samples/README.md, so later phases
(anomalies, "why did this change?", profiling) can be tested against a known answer.
"""

from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).parent
rng = np.random.default_rng(42)  # fixed seed: same files every run


# ---------------------------------------------------------------- retail sales
def retail_sales() -> pd.DataFrame:
    dates = pd.date_range("2019-01-01", "2025-12-31", freq="D")
    products = {
        # product: (category, base daily units per region, unit price in INR)
        "Wireless Earbuds": ("Electronics", 40, 1999),
        "Smartphone": ("Electronics", 12, 15999),
        "Cotton Kurta": ("Apparel", 35, 899),
        "Running Shoes": ("Apparel", 18, 2499),
        "Pressure Cooker": ("Home & Kitchen", 15, 1799),
        "Smartwatch": ("Electronics", 20, 3499),
    }
    regions = {"North": 1.0, "South": 1.15, "East": 0.8, "West": 1.1}
    diwali = pd.to_datetime(
        [
            "2019-10-27",
            "2020-11-14",
            "2021-11-04",
            "2022-10-24",
            "2023-11-12",
            "2024-10-31",
            "2025-10-20",
        ]
    )

    t = np.arange(len(dates)) / 365.0
    base = 1 + 0.08 * t  # 8% yearly growth
    base *= np.where(dates.day_of_week >= 5, 1.25, 1.0)  # weekends busier
    base *= 1 + 0.10 * np.sin(2 * np.pi * (dates.day_of_year - 60) / 365)  # seasonality

    # Diwali: sales build in the 10 days before the festival.
    days_to_diwali = np.full(len(dates), 999)
    for d in diwali:
        delta = (d - dates).days
        days_to_diwali = np.where((delta >= 0) & (delta < days_to_diwali), delta, days_to_diwali)
    base *= np.where(days_to_diwali <= 10, 1.6, 1.0)

    # COVID-19 lockdown in India (from 25 Mar 2020), then gradual recovery.
    lockdown = (dates >= "2020-03-25") & (dates <= "2020-05-31")
    recovery = (dates > "2020-05-31") & (dates <= "2020-08-31")
    base *= np.where(lockdown, 0.3, 1.0)
    rec_progress = np.clip((dates - pd.Timestamp("2020-05-31")).days / 92, 0, 1)
    base *= np.where(recovery, 0.3 + 0.7 * rec_progress, 1.0)
    # Second wave (Apr-May 2021).
    base *= np.where((dates >= "2021-04-15") & (dates <= "2021-05-31"), 0.65, 1.0)

    rows = []
    for product, (category, units, price) in products.items():
        for region, region_factor in regions.items():
            factor = base * region_factor
            if product == "Smartwatch":  # launched 1 Jun 2023
                factor = np.where(dates >= "2023-06-01", factor, 0)
            unit_price = np.full(len(dates), float(price))
            if product == "Smartphone":  # price cut 1 Feb 2024
                after = dates >= "2024-02-01"
                unit_price = np.where(after, price * 0.85, unit_price)
                factor = np.where(after, factor * 1.3, factor)
            if category == "Electronics" and region == "West":  # West electronics slump
                factor = np.where(
                    (dates >= "2025-03-01") & (dates <= "2025-04-30"), factor * 0.45, factor
                )
            qty = rng.poisson(np.maximum(units * factor, 0))
            frame = pd.DataFrame(
                {
                    "date": dates,
                    "region": region,
                    "category": category,
                    "product": product,
                    "units_sold": qty,
                    "unit_price_inr": unit_price.round(2),
                }
            )
            rows.append(frame[frame["units_sold"] > 0])

    df = pd.concat(rows, ignore_index=True)
    df["revenue_inr"] = (df["units_sold"] * df["unit_price_inr"]).round(2)
    # Data issue: three days missing from the export (10-12 Aug 2022).
    df = df[~df["date"].between("2022-08-10", "2022-08-12")]
    df = df.sort_values(["date", "region", "product"]).reset_index(drop=True)
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    df.insert(0, "order_line_id", [f"OL{i:06d}" for i in range(1, len(df) + 1)])
    return df


# ---------------------------------------------------------------- HR employees
def hr_employees() -> pd.DataFrame:
    n = 1200
    departments = ["Engineering", "Sales", "Operations", "HR", "Finance", "Marketing"]
    dept = rng.choice(departments, n, p=[0.32, 0.24, 0.18, 0.06, 0.08, 0.12])
    city = rng.choice(["Mumbai", "Bengaluru", "Pune", "Delhi"], n, p=[0.3, 0.35, 0.2, 0.15])

    hire = pd.Timestamp("2018-01-01") + pd.to_timedelta(rng.integers(0, 2900, n), unit="D")
    # Hiring push in 2022: extra engineers.
    push = rng.random(n) < 0.15
    hire = pd.DatetimeIndex(
        np.where(
            push,
            pd.Timestamp("2022-01-01") + pd.to_timedelta(rng.integers(0, 365, n), unit="D"),
            hire,
        )
    )
    dept = np.where(push, "Engineering", dept)

    base_salary = {
        "Engineering": 1_400_000,
        "Sales": 800_000,
        "Operations": 650_000,
        "HR": 700_000,
        "Finance": 950_000,
        "Marketing": 850_000,
    }
    salary = np.array([base_salary[d] for d in dept]) * rng.normal(1, 0.18, n)

    # Attrition: about 12% normally, much higher for Sales in Bengaluru during 2024.
    leave_prob = np.where((dept == "Sales") & (city == "Bengaluru"), 0.55, 0.12)
    left = rng.random(n) < leave_prob
    exit_offset = pd.to_timedelta(rng.integers(120, 1500, n), unit="D")
    exit_date = hire + exit_offset
    hot = (dept == "Sales") & (city == "Bengaluru") & left
    exit_date = pd.DatetimeIndex(
        np.where(
            hot,
            pd.Timestamp("2024-01-01") + pd.to_timedelta(rng.integers(0, 366, n), unit="D"),
            exit_date,
        )
    )
    left &= exit_date <= pd.Timestamp("2025-12-31")
    left &= exit_date > hire

    df = pd.DataFrame(
        {
            "employee_id": [f"E{i:05d}" for i in range(1, n + 1)],
            "department": dept,
            "city": city,
            "gender": rng.choice(["Female", "Male", "Non-binary"], n, p=[0.42, 0.56, 0.02]),
            "age": rng.integers(22, 58, n),
            "hire_date": hire.strftime("%Y-%m-%d"),
            "exit_date": np.where(left, exit_date.strftime("%Y-%m-%d"), ""),
            "annual_salary_inr": salary.round(-3).astype(int),
            "performance_rating": rng.choice([1, 2, 3, 4, 5], n, p=[0.04, 0.12, 0.45, 0.29, 0.10]),
            "status": np.where(left, "Exited", "Active"),
        }
    )
    # Some missing ratings, as in real HR exports.
    df.loc[rng.random(n) < 0.04, "performance_rating"] = np.nan
    return df


# ---------------------------------------------------------------- business expenses
def business_expenses() -> pd.DataFrame:
    rows = []
    for month in pd.date_range("2023-01-01", "2025-12-01", freq="MS"):
        rent = 85_000 if month < pd.Timestamp("2024-04-01") else 110_000  # rent hike Apr 2024
        rows.append(
            (month + pd.Timedelta(days=4), "Rent", "Shree Properties", rent, "Bank transfer")
        )
        rows.append(
            (
                month + pd.Timedelta(days=9),
                "Salaries",
                "Payroll",
                420_000 + 4_000 * ((month.year - 2023) * 12 + month.month),
                "Bank transfer",
            )
        )
        electricity = 9_000 * (1.35 if month.month in (4, 5, 6) else 1.0)  # summer AC load
        rows.append(
            (
                month + pd.Timedelta(days=14),
                "Utilities",
                "MSEDCL",
                electricity * rng.normal(1, 0.08),
                "UPI",
            )
        )
        rows.append(
            (
                month + pd.Timedelta(days=16),
                "Software",
                "Cloud subscriptions",
                12_500,
                "Credit card",
            )
        )
        for _ in range(rng.integers(6, 12)):  # small day-to-day spends
            day = month + pd.Timedelta(days=int(rng.integers(0, 27)))
            cat, vendor, amount = [
                ("Travel", "Uber", rng.uniform(250, 1800)),
                ("Office Supplies", "Amazon Business", rng.uniform(400, 6000)),
                ("Meals", "Swiggy", rng.uniform(300, 2500)),
                ("Marketing", "Meta Ads", rng.uniform(5000, 25000)),
            ][int(rng.integers(0, 4))]
            rows.append((day, cat, vendor, amount, rng.choice(["UPI", "Credit card", "Cash"])))
    # One-off equipment purchase.
    rows.append((pd.Timestamp("2024-09-18"), "Equipment", "Croma", 245_000, "Credit card"))

    df = pd.DataFrame(rows, columns=["date", "category", "vendor", "amount", "payment_method"])
    df = df.sort_values("date").reset_index(drop=True)
    # Deliberately messy, like a real export: DD/MM/YYYY dates and "₹1,23,456.00" amounts.
    df["date"] = df["date"].dt.strftime("%d/%m/%Y")
    df["amount"] = df["amount"].map(lambda v: f"₹{v:,.2f}")
    df.loc[rng.random(len(df)) < 0.03, "vendor"] = ""  # missing vendors
    df = pd.concat([df, df.sample(4, random_state=1)]).sort_index()  # duplicate rows
    return df


if __name__ == "__main__":
    for name, build in [
        ("retail_sales", retail_sales),
        ("hr_employees", hr_employees),
        ("business_expenses", business_expenses),
    ]:
        data = build()
        path = OUT / f"{name}.sample.csv"
        data.to_csv(path, index=False, encoding="utf-8")
        print(f"{path.name}: {len(data):,} rows, {path.stat().st_size / 1e6:.1f} MB")