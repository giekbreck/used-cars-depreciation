# Data quality report - AutoScout24 Germany Used Cars 2023

Source file: `data/raw/autoscout24_germany_2023.csv` (251,079 rows, 14 columns).
Evidence and code: `notebooks/01_data_quality.ipynb`. Final cleaning: `src/cleaning.py` (`clean()`).

## Summary

The file needs cleaning before any analysis: **2.7% of the rows are removed** (251,079 -> 244,255). The problems are
shifted columns from the scraper, duplicated listings and a few impossible values. Missing values are not a problem for the
hypothesis, except the fuel consumption columns, which we do not use.

## Problems found and decisions

| # | Problem | Rows | How we found it | Decision |
|---|---|---|---|---|
| 1 | Columns shifted by the scraper (`fuel_type = "01/2023"`, `price = "Automatik"`) | 199 | `year` and `price_in_euro` were text; `fuel_type.value_counts()` showed non-fuels | remove (the shift is irregular, cannot be repaired) |
| 2 | Exact duplicate listings (all columns equal) | 6,338 (2.5%) | `df.duplicated()` | remove |
| 3 | Price below 500 EUR | 103 | `nsmallest`: 120 EUR Polo, engine-damage cars | remove |
| 4 | Mileage above 500,000 km (max 3.8 million) | 131 | `describe()` and `nlargest` | remove |
| 5 | Missing mileage | 53 | `isna()` | remove (mileage is a control variable) |

Rows left after each step:

| Step | Rows left | Removed |
|---|---|---|
| raw file | 251,079 | 0 |
| remove shifted rows | 250,880 | 199 |
| remove exact duplicates | 244,542 | 6,338 |
| remove price < 500 EUR | 244,439 | 103 |
| remove mileage > 500,000 km | 244,308 | 131 |
| remove rows without mileage | 244,255 | 53 |

## Missing values

| Column | Missing | Mechanism | Decision |
|---|---|---|---|
| `fuel_consumption_l_100km` | 10.7% (92% for electric cars) | MAR: electric cars report kWh or range, not l/100 km; units are mixed | not used |
| `color`, `power_kw`, `power_ps`, `mileage_in_km` | under 0.2% | - | only mileage is needed (rows removed, see above) |

## Values that look wrong but are real (kept)

| Value | Rows | Why it stays |
|---|---|---|
| Price above 300,000 EUR | 591 | Ferrari, Lamborghini, Aston Martin. Handled with medians and log price. |
| Power above 600 kW | 53 | Real supercars. `PS / kW` is always about 1.36: the columns agree. |
| Mileage = 0 | 202 | Almost all 2022-2023 cars (new or pre-registered). |
| More than 60,000 km per year | 153 | Cannot be proven wrong; too few to move any result. |

## Checks that passed

- `year` equals the year of `registration_date` in every row.
- `PS / kW` is between 1.0 and 1.4 (median 1.36).
- Brands removed as shifted rows are spread over many brands (none above 0.5% of its own rows).
- Final `assert`s: price between 500 and 6 million, mileage between 0 and 500,000, valid fuel types, no duplicates, age not negative.

## What this means for the analysis

- Electric cars are **young**: median age 2.2 years and 95% are 6 years old or less (petrol 5.8, diesel 6.8). The hypothesis is therefore tested only on the
  age range 0-6 years, where electric and combustion cars overlap.
- The data was scraped around **November 2023** (newest registration is 11/2023): this is an **assumption** used to compute `age_years`.
- Prices are **asking prices**, not sale prices.

## Columns created

`age_years`, `fuel_group` (Petrol, Diesel, Hybrid, Electric, Other) and `km_per_year`. Definitions in the README.
