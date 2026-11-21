"""
kpis.py
-------
A tiny class that represents one KPI card (a big number with a label).
"""

import dash_bootstrap_components as dbc
from dash import html

from src.config import THEME
from src.metrics import value_retention


class KpiCard:
    """One KPI card: a title, a value and an optional unit."""

    def __init__(self, title, value, unit="", decimals=0):
        self.title = title
        self.value = value
        self.unit = unit
        self.decimals = decimals

    def formatted_value(self):
        """Nice text for the number: 19,690 or 6.2 (a dash when there is no data)."""
        if self.value is None:
            return "-"
        return f"{self.value:,.{self.decimals}f}"

    def render(self):
        """Turn the object into Dash components (what the browser shows)."""
        return dbc.Card(
            dbc.CardBody([
                html.Div(self.title, className="kpi-title"),
                html.Div([
                    html.Span(self.formatted_value(), style={"color": THEME.accent_color}),
                    html.Span(f" {self.unit}", className="kpi-unit"),
                ], className="kpi-value"),
            ]),
            className="kpi-card",
        )


def safe_median(series):
    """Median that returns None for an empty selection instead of NaN."""
    return None if series.dropna().empty else float(series.median())


def overall_retention(df):
    """Retention of the whole selection (median price at 3-5 years / median price up to 1 year), in %."""
    table = value_retention(df.assign(all_cars="all"), by=["all_cars"], min_n=30)
    return None if table.empty else float(table["retention"].iloc[0] * 100)


def build_kpis(df, df_all_ages):
    """KPI cards for the current selection. Retention needs all ages, so it uses df_all_ages."""
    return [
        KpiCard("Listings", len(df)),
        KpiCard("Median price", safe_median(df["price_in_euro"]), "EUR"),
        KpiCard("Median age", safe_median(df["age_years"]), "years", decimals=1),
        KpiCard("Value kept at 3-5 years", overall_retention(df_all_ages), "%"),
    ]


if __name__ == "__main__":
    # Quick test: python -m src.kpis
    card = KpiCard("Median price", 19690.0, "EUR")
    print(card.title, "->", card.formatted_value())
