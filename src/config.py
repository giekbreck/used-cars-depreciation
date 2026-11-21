"""
config.py
---------
All the "look and feel" of the dashboard lives here.
Change the values below to customise the dashboard - no other file needs to change.
"""

from dataclasses import dataclass, field


@dataclass
class Theme:
    """A small container for every style choice of the app."""
    title: str = "Used Cars Germany 2023"
    subtitle: str = "Do electric cars lose value faster? AutoScout24 listings"
    bootstrap_theme: str = "CYBORG"        # dark themes: DARKLY, SLATE, VAPOR, SUPERHERO, CYBORG
    plotly_template: str = "plotly_dark"   # must match: dark bootstrap theme -> "plotly_dark"
    accent_color: str = "#00E5A8"          # main highlight colour (KPI values)
    font_family: str = "Inter, sans-serif"
    fuel_colors: dict = field(default_factory=lambda: {
        "Petrol": "#5B8DEF", "Diesel": "#9AA5B1", "Hybrid": "#FFB547", "Electric": "#00E5A8",
    })


# The one theme object the whole app imports
THEME = Theme()

# Fuel groups shown in the dashboard (the tiny "Other" group is left out)
FUELS = ["Petrol", "Diesel", "Hybrid", "Electric"]

# Slider limits for the age filter (years)
MAX_AGE = 30
