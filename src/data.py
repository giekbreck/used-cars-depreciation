"""
data.py
-------
Functions to load and filter the data for the dashboard. No plotting here!
"""

from src.cleaning import clean, load_raw
from src.config import FUELS


def load_data():
    """Clean data (same as the notebooks) restricted to the fuel groups of the dashboard."""
    df = clean(load_raw())
    return df[df["fuel_group"].isin(FUELS)].reset_index(drop=True)


def filter_data(df, brands=None, fuels=None, age_range=None):
    """Return only the rows that match the filters chosen in the dashboard (empty brands = all brands, no fuels = no cars)."""
    if brands:
        df = df[df["brand"].isin(brands)]
    if fuels is not None:                          # no fuel ticked = no cars (not 'all cars')
        df = df[df["fuel_group"].isin(fuels)]
    if age_range:
        df = df[df["age_years"].between(*age_range)]
    return df


if __name__ == "__main__":
    # Quick test: python -m src.data
    data = load_data()
    print(data.shape)
    print(filter_data(data, brands=["bmw"], fuels=["Electric"], age_range=(0, 3)).head())
