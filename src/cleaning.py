"""
cleaning.py
-----------
Reusable cleaning functions for the AutoScout24 Germany 2023 dataset.
No plotting here! Every decision is documented in notebooks/01_data_quality.ipynb.
"""

from pathlib import Path

import numpy as np
import pandas as pd

RAW_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "autoscout24_germany_2023.csv"

# The newest registration in the file is 11/2023 -> we treat the scrape as taken on that date
REFERENCE_DATE = pd.Timestamp("2023-11-01")

VALID_FUELS = {"Petrol", "Diesel", "Hybrid", "Diesel Hybrid", "Electric",
               "LPG", "CNG", "Ethanol", "Hydrogen", "Other", "Unknown"}
NUMERIC_COLS = ["year", "price_in_euro", "power_kw", "power_ps"]

# Plausibility limits (see the notebook for the evidence behind each number)
MIN_PRICE = 500
MAX_MILEAGE = 500_000

# 5 raw fuel labels -> the groups we compare in the hypothesis
FUEL_GROUPS = {
    "Petrol": "Petrol", "Diesel": "Diesel", "Electric": "Electric",
    "Hybrid": "Hybrid", "Diesel Hybrid": "Hybrid",
}


def load_raw(path=RAW_PATH):
    """Read the CSV exactly as it is (the first unnamed column is just the old index)."""
    return pd.read_csv(path, index_col=0)


def find_shifted_rows(df):
    """True for rows where the scraper shifted the columns (e.g. fuel_type = '01/2023')."""
    bad_fuel = ~df["fuel_type"].isin(VALID_FUELS)
    bad_numbers = pd.concat(
        [pd.to_numeric(df[c], errors="coerce").isna() for c in ["year", "price_in_euro"]], axis=1
    ).any(axis=1)
    return bad_fuel | bad_numbers


def parse_types(df):
    """Text -> numbers and dates. Call it only after the shifted rows are removed."""
    df = df.copy()
    for col in NUMERIC_COLS:
        df[col] = pd.to_numeric(df[col])
    df["registration_date"] = pd.to_datetime(df["registration_date"], format="%m/%Y")
    return df


def add_features(df):
    """Columns we need for the hypothesis: age, fuel group, km per year."""
    df = df.copy()
    df["age_years"] = ((REFERENCE_DATE - df["registration_date"]).dt.days / 365.25).round(2)
    df["fuel_group"] = df["fuel_type"].map(FUEL_GROUPS).fillna("Other")
    df["km_per_year"] = df["mileage_in_km"] / df["age_years"].clip(lower=0.5)
    return df


def clean(raw, return_log=False):
    """
    Every cleaning decision in one place. Returns the clean DataFrame
    (and, if return_log=True, a table with the rows removed at each step).
    """
    log = [("raw file", len(raw))]

    df = raw[~find_shifted_rows(raw)]
    log.append(("remove shifted rows", len(df)))

    df = parse_types(df)
    df = df.drop_duplicates()
    log.append(("remove exact duplicates", len(df)))

    df = df[df["price_in_euro"] >= MIN_PRICE]
    log.append((f"remove price < {MIN_PRICE} EUR", len(df)))

    df = df[df["mileage_in_km"].isna() | (df["mileage_in_km"] <= MAX_MILEAGE)]
    log.append((f"remove mileage > {MAX_MILEAGE:,} km", len(df)))

    df = df.dropna(subset=["mileage_in_km"])
    log.append(("remove rows without mileage", len(df)))

    df = add_features(df).reset_index(drop=True)

    if return_log:
        log = pd.DataFrame(log, columns=["step", "rows_left"])
        log["rows_removed"] = (-log["rows_left"].diff()).fillna(0).astype(int)
        return df, log
    return df


if __name__ == "__main__":
    # Quick test: python -m src.cleaning
    clean_df, log = clean(load_raw(), return_log=True)
    print(log)
    print(clean_df.shape)
