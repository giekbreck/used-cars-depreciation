"""
app.py
------
The Dash application: layout (what we see) + callback (what happens when we click).

Run locally:
    uv run python app.py
Then open http://127.0.0.1:8050 in your browser.
"""

import dash_bootstrap_components as dbc
from dash import Dash, Input, Output, dcc, html

from src import charts
from src.config import FUELS, MAX_AGE, THEME
from src.data import filter_data, load_data
from src.kpis import build_kpis

# ---------------------------------------------------------------- 1. data
df = load_data()
BRANDS = sorted(df["brand"].unique())

# ---------------------------------------------------------------- 2. app
app = Dash(
    __name__,
    external_stylesheets=[
        getattr(dbc.themes, THEME.bootstrap_theme),
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap",
    ],
    title=THEME.title,
)
server = app.server

# ---------------------------------------------------------------- 3. layout
header = html.Div([
    html.H1(THEME.title, className="app-title"),
    html.P(f"{THEME.subtitle} - {len(df):,} cars", className="app-subtitle"),
], className="app-header")

filters = dbc.Card(dbc.CardBody([
    html.H5("Filters", className="mb-3"),

    html.Label("Brands (empty = all)"),
    dcc.Dropdown(id="brand-filter", options=BRANDS, value=[], multi=True,
                 placeholder="All brands", className="mb-3"),

    html.Label("Fuel"),
    dbc.Checklist(id="fuel-filter", options=FUELS, value=FUELS, switch=True, className="mb-3"),

    html.Label("Age (years)"),
    dcc.RangeSlider(id="age-filter", min=0, max=MAX_AGE, step=1, value=[0, MAX_AGE],
                    marks={0: "0", 5: "5", 10: "10", 20: "20", 30: "30"},
                    tooltip={"placement": "bottom"}, className="mb-3"),

    html.Hr(),
    html.Small("The age filter does not change the retention card and the retention chart: "
               "they always compare cars of 3-5 years with nearly-new ones.", className="text-muted"),
]), className="filter-card")


def graph_card(graph_id):
    """A card that holds one graph (a function, so we don't repeat ourselves)."""
    return dbc.Card(dcc.Graph(id=graph_id, config={"displayModeBar": False}), className="graph-card")


app.layout = dbc.Container([
    header,
    dbc.Row([
        dbc.Col(filters, lg=3, className="mb-4"),
        dbc.Col([
            dbc.Row(id="kpi-row", className="g-3 mb-3"),
            dbc.Row([dbc.Col(graph_card("age-graph"), lg=6),
                     dbc.Col(graph_card("loss-graph"), lg=6)], className="g-3 mb-3"),
            dbc.Row([dbc.Col(graph_card("retention-graph"), lg=6),
                     dbc.Col(graph_card("mileage-graph"), lg=6)], className="g-3"),
        ], lg=9),
    ]),
    html.Footer("Built with Plotly Dash - Ironhack DSML", className="app-footer"),
], fluid=True)


# ---------------------------------------------------------------- 4. callback
@app.callback(
    Output("kpi-row", "children"),
    Output("age-graph", "figure"),
    Output("loss-graph", "figure"),
    Output("retention-graph", "figure"),
    Output("mileage-graph", "figure"),
    Input("brand-filter", "value"),
    Input("fuel-filter", "value"),
    Input("age-filter", "value"),
)
def update_dashboard(brands, fuels, age_range):
    """Runs every time a filter changes: filter the data, rebuild KPIs and figures."""
    selected = filter_data(df, brands, fuels, age_range)
    all_ages = filter_data(df, brands, fuels)      # retention needs every age

    if selected.empty:
        empty = charts.empty_figure()
        return [], empty, empty, empty, empty

    kpi_cards = [dbc.Col(card.render(), md=3) for card in build_kpis(selected, all_ages)]
    return (
        kpi_cards,
        charts.price_by_age(selected),
        charts.annual_loss(selected),
        charts.retention_by_brand(all_ages),
        charts.price_vs_mileage(selected),
    )


# ---------------------------------------------------------------- 5. run
if __name__ == "__main__":
    app.run(debug=True)
