"""
metrics.py
----------
Reusable metrics for the depreciation hypothesis and the value-retention analysis.
No plotting here! Input is always the clean DataFrame from src.cleaning.clean().
"""

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

# The age range where electric and combustion cars overlap (95% of EVs are 6 years old or less)
OVERLAP_MAX_AGE = 6
COMPARED_FUELS = ["Petrol", "Diesel", "Electric", "Hybrid"]


# ---------------------------------------------------------------- 1. descriptive
def median_price_by_age(df, bin_width=1, max_age=None, min_n=30):
    """Median price per age bucket and fuel group (buckets with fewer than min_n cars are dropped)."""
    data = df if max_age is None else df[df["age_years"] <= max_age]
    bucket = (data["age_years"] // bin_width * bin_width + bin_width / 2).rename("age_bucket")
    table = (data.groupby([bucket, "fuel_group"])["price_in_euro"]
                 .agg(median_price="median", listings="size").reset_index())
    return table[table["listings"] >= min_n]


def simple_annual_depreciation(df, min_rows=50):
    """
    Annual price loss per fuel group from a plain fit log(price) = a + b * age.
    NOT controlled for mileage or brand: it is the quick number shown in the dashboard.
    """
    rows = []
    for fuel, group in df.groupby("fuel_group"):
        if len(group) < min_rows or group["age_years"].nunique() < 3:
            continue
        slope = np.polyfit(group["age_years"], np.log(group["price_in_euro"]), 1)[0]
        rows.append({"fuel_group": fuel, "annual_loss_pct": (1 - np.exp(slope)) * 100, "listings": len(group)})
    return pd.DataFrame(rows, columns=["fuel_group", "annual_loss_pct", "listings"])


# ---------------------------------------------------------------- 2. hypothesis model
def overlap_sample(df, max_age=OVERLAP_MAX_AGE, fuels=COMPARED_FUELS):
    """Only the cars where the groups can be compared, plus the model variables."""
    sample = df[df["age_years"].between(0, max_age) & df["fuel_group"].isin(fuels)].copy()
    sample["log_price"] = np.log(sample["price_in_euro"])
    sample["km_10k"] = sample["mileage_in_km"] / 10_000       # coefficient = effect of 10,000 km
    return sample


def fit_depreciation_model(sample, absorb="brand"):
    """
    log(price) = brand (or model) effect + fuel effect + [age and km slope for EACH fuel group].
    Robust (HC3) standard errors, because the spread of prices is not constant.
    """
    formula = (f"log_price ~ C({absorb}) + C(fuel_group)"
               " + C(fuel_group):age_years + C(fuel_group):km_10k")
    return smf.ols(formula, sample).fit(cov_type="HC3")


def _term(fuel, variable):
    return f"C(fuel_group)[{fuel}]:{variable}"


def slopes_table(result, variable="age_years"):
    """Slope of log(price) per fuel group, with 95% CI and the same numbers as % lost per year (or per 10,000 km)."""
    ci = result.conf_int()
    rows = []
    for name in result.params.index:
        if name.endswith(f":{variable}") and name.startswith("C(fuel_group)"):
            fuel = name.split("[")[1].split("]")[0]
            slope, low, high = result.params[name], ci.loc[name, 0], ci.loc[name, 1]
            rows.append({"fuel_group": fuel, "slope": slope,
                         "loss_pct": (1 - np.exp(slope)) * 100,
                         "loss_pct_low": (1 - np.exp(high)) * 100,     # the CI flips: a higher slope is a smaller loss
                         "loss_pct_high": (1 - np.exp(low)) * 100})
    return pd.DataFrame(rows).set_index("fuel_group")


def compare_slopes(result, fuel_a="Electric", fuel_b="Petrol", variable="age_years"):
    """Test H0: the slope of fuel_a equals the slope of fuel_b. Negative diff = fuel_a loses value faster."""
    names = list(result.params.index)
    contrast = np.zeros(len(names))
    contrast[names.index(_term(fuel_a, variable))] = 1
    contrast[names.index(_term(fuel_b, variable))] = -1
    test = result.t_test(contrast)
    diff = float(np.squeeze(test.effect))
    low, high = np.squeeze(test.conf_int())
    return {"comparison": f"{fuel_a} vs {fuel_b}", "slope_diff": diff,
            "ci_low": float(low), "ci_high": float(high), "p_value": float(np.squeeze(test.pvalue))}


def matched_models(df, max_age=OVERLAP_MAX_AGE, min_cars=20):
    """Car models sold both as Electric and as Petrol/Diesel (same model name, enough cars in each side)."""
    data = df[df["age_years"].between(0, max_age)]
    counts = data.assign(is_ev=data["fuel_group"].eq("Electric"),
                         is_ice=data["fuel_group"].isin(["Petrol", "Diesel"])
                         ).groupby("model")[["is_ev", "is_ice"]].sum()
    return counts.index[(counts["is_ev"] >= min_cars) & (counts["is_ice"] >= min_cars)].tolist()


# ---------------------------------------------------------------- 3. value retention
def value_retention(df, by=("brand", "fuel_group"), new_max_age=1.0, used_age=(3.0, 5.0), min_n=30):
    """
    Retention = median price of cars aged used_age / median price of 'almost new' cars (<= new_max_age),
    same group. 0.60 means a 4-year-old car sells for 60% of an almost-new one.
    Groups with fewer than min_n cars in either window are dropped (the median would be noise).
    """
    by = list(by)
    new = df[df["age_years"] <= new_max_age]
    used = df[df["age_years"].between(*used_age)]
    new_g = new.groupby(by)["price_in_euro"].agg(price_new="median", n_new="size")
    used_g = used.groupby(by)["price_in_euro"].agg(price_used="median", n_used="size")
    table = new_g.join(used_g, how="inner")
    table = table[(table["n_new"] >= min_n) & (table["n_used"] >= min_n)].copy()
    table["retention"] = table["price_used"] / table["price_new"]
    return table.reset_index()
