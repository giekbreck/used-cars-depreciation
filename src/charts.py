"""
charts.py
---------
One function per figure. Each function receives a DataFrame and returns a Plotly figure.
These are the same plots we made in the notebooks - just wrapped in functions.
"""

import pandas as pd
import plotly.express as px

from src.config import FUELS, THEME
from src.metrics import median_price_by_age, simple_annual_depreciation, value_retention


def style_figure(fig):
    """Apply the same look to every figure (template, font, transparent background)."""
    fig.update_layout(
        template=THEME.plotly_template,
        font_family=THEME.font_family,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=50, b=20),
        legend_title_text="",
        hovermode="closest",
    )
    return fig


def empty_figure(message="No data for this selection"):
    """Shown when the filters remove all rows (or a group is too small)."""
    fig = px.scatter()
    fig.add_annotation(text=message, showarrow=False, font_size=16)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return style_figure(fig)


def price_by_age(df):
    """Median price by year of age, one line per fuel (log scale, buckets with at least 30 cars)."""
    curve = median_price_by_age(df, bin_width=1)
    if curve.empty:
        return empty_figure("Not enough cars to draw the curves")
    fig = px.line(curve.sort_values(["fuel_group", "age_bucket"]), x="age_bucket", y="median_price",
                  color="fuel_group", markers=True, log_y=True,
                  color_discrete_map=THEME.fuel_colors, category_orders={"fuel_group": FUELS},
                  title="Median price by age",
                  labels={"age_bucket": "age (years)", "median_price": "median price (EUR)"})
    return style_figure(fig)


def annual_loss(df):
    """Bar chart: % of price lost per year of age, one bar per fuel (simple fit, no controls)."""
    loss = simple_annual_depreciation(df)
    if loss.empty:
        return empty_figure("Not enough cars to estimate the loss")
    fig = px.bar(loss, x="fuel_group", y="annual_loss_pct", color="fuel_group",
                 color_discrete_map=THEME.fuel_colors, category_orders={"fuel_group": FUELS},
                 text=loss["annual_loss_pct"].round(1).astype(str) + "%",
                 title="Price lost per year of age (simple fit)",
                 labels={"annual_loss_pct": "% lost per year", "fuel_group": ""})
    fig.update_layout(showlegend=False)
    return style_figure(fig)


def retention_by_brand(df, top_brands=15):
    """Value retention at 3-5 years by brand and fuel (the brands with most listings in the selection)."""
    table = value_retention(df)
    if table.empty:
        return empty_figure("Not enough cars per brand and fuel (30 needed in each age window)")
    biggest = df["brand"].value_counts().head(top_brands).index
    table = table[table["brand"].isin(biggest)].copy()
    if table.empty:
        return empty_figure("Not enough cars per brand and fuel (30 needed in each age window)")
    table["retention_pct"] = table["retention"] * 100
    order = table.groupby("brand")["retention_pct"].mean().sort_values().index.tolist()
    fig = px.bar(table, x="retention_pct", y="brand", color="fuel_group", barmode="group", orientation="h",
                 color_discrete_map=THEME.fuel_colors, category_orders={"fuel_group": FUELS, "brand": order},
                 title="Value kept at 3-5 years, by brand (all ages, % of nearly-new price)",
                 labels={"retention_pct": "% of price kept", "brand": ""})
    return style_figure(fig)


def price_vs_mileage(df, sample_size=4000):
    """One dot per car (random sample, so the browser stays fast): price vs mileage."""
    if df.empty:
        return empty_figure()
    sample = df.sample(min(sample_size, len(df)), random_state=42)
    fig = px.scatter(sample, x="mileage_in_km", y="price_in_euro", color="fuel_group", log_y=True, opacity=0.5,
                     color_discrete_map=THEME.fuel_colors, category_orders={"fuel_group": FUELS},
                     hover_data=["brand", "model", "age_years"],
                     title=f"Price vs mileage (sample of {len(sample):,} cars)",
                     labels={"mileage_in_km": "mileage (km)", "price_in_euro": "price (EUR)"})
    return style_figure(fig)


if __name__ == "__main__":
    # Quick test: python -m src.charts  -> opens a figure in your browser
    from src.data import load_data
    fig = price_by_age(load_data())
    if "dark" in THEME.plotly_template:
        fig.update_layout(paper_bgcolor="#111111", plot_bgcolor="#111111")
    fig.show()
