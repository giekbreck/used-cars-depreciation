# Do electric cars lose value faster? - Germany Used Cars 2023

Personal Data Science project, built on the Kaggle dataset *Germany Used Cars Dataset 2023* (AutoScout24 listings): https://www.kaggle.com/datasets/wspirat/germany-used-cars-dataset-2023?resource=download

## Question, hypothesis, result

- **Question:** do electric cars depreciate faster than combustion cars?
- **Hypothesis:** yes, **at the same age and mileage**.
- **Extra metric:** value retention by brand and fuel type.
- **Result: the hypothesis is supported.** At the same age, mileage and brand, electric cars lose about **19% of their price per year**,
  against about **8% for petrol**, 10% for diesel and 8% for hybrid. After 4 years an electric car keeps about 44% of its price and a petrol car about 71%.
  The result holds in four different model specifications (see below).

| Fuel | Price lost per year (95% CI) | Price kept after 4 years |
|---|---|---|
| Electric | 18.7% (18.0 - 19.4) | 44% |
| Diesel | 10.3% (10.0 - 10.6) | 65% |
| Petrol | 8.3% (8.1 - 8.5) | 71% |
| Hybrid | 8.1% (7.6 - 8.6) | 71% |

Same age, mileage and brand; cars aged 0-6 years; 126,249 cars. The difference electric vs petrol is highly significant (p-value below 1e-100) and, more important, **large**.

| Robustness check | Electric | Petrol | Diesel |
|---|---|---|---|
| A. Main model (brand effect, age 0-6) | 18.7% | 8.3% | 10.3% |
| B. Only cars up to 4 years | 19.7% | 9.7% | 12.4% |
| C. Only models sold as both electric and petrol/diesel, with model effect (19 models, e.g. Fiat 500, Kia Niro) | 14.0% | 8.1% | 8.9% |
| D. Without the top 1% of prices | 18.9% | 8.4% | 10.3% |

In every check electric cars lose more per year. The gap is smaller for the *same car model* (14% vs 8%), which means part of the faster loss in the main model
comes from which electric models exist, but a solid core remains.

**Value retention** (median price at 3-5 years / median price up to 1 year, same group): electric 50%, diesel 56%, petrol 73%, hybrid 86%.
Inside the same brand, electric retains less than petrol for 7 of 9 brands (Volkswagen 34% vs 71%, Renault 38% vs 62%); the exceptions are Opel and Mercedes-Benz.

## Limits of the result

1. **Asking prices**, not final sale prices.
2. **Cross-section:** we compare cars of different ages on sale today; we do not follow one car. Older electric cars were different (and launched at other prices), so part of the
   measured depreciation is a generation effect.
3. The 2022-2023 **price cuts** on new electric cars lower used prices at every age. It is a real cause of the faster loss in this market, but it may not repeat.
4. Only **0-6 years** are compared (95% of electric cars are in this range).
5. Battery condition, equipment and trim level are not in the data.
6. `Hybrid` mixes plug-in and mild hybrids.
7. The scraping date (November 2023) is an assumption.

## Project structure

```
used_cars_depreciation/
|-- app.py                                  # Dash dashboard
|-- assets/style.css                        # dashboard style
|-- data/raw/                               # put the downloaded CSV here (the CSV is git-ignored, the folder is kept)
|   `-- autoscout24_germany_2023.csv        # original file, never modified
|-- notebooks/
|   |-- 01_data_quality.ipynb               # problems found and every cleaning decision
|   |-- 02_eda.ipynb                        # exploration and confounders
|   `-- 03_hypothesis.ipynb                 # the test, robustness, retention, limits
|-- reports/data_quality.md                 # short data quality report
|-- src/
|   |-- cleaning.py                         # load_raw, clean, ...
|   |-- metrics.py                          # depreciation model, tests, retention
|   `-- config.py, data.py, charts.py, kpis.py   # the dashboard, one job per file
|-- pyproject.toml                          # dependencies (uv)
|-- uv.lock                                 # exact pinned versions (commit it)
`-- README.md
```

## How to run

**1. Get the data.** The CSV is not in the repository (it is git-ignored). Download it from the [Kaggle dataset](https://www.kaggle.com/datasets/wspirat/germany-used-cars-dataset-2023)
and save it **inside `data/raw/`** with this exact name:

```
data/raw/autoscout24_germany_2023.csv
```

Without this file, `load_raw()`, the notebooks and the dashboard stop with a "file not found" error.

**2. Set up the environment.** The project uses [uv](https://docs.astral.sh/uv/). Dependencies are declared in `pyproject.toml` and pinned in `uv.lock`, so everyone gets the exact same versions.

```bash
uv sync                          # creates .venv with the exact packages of uv.lock
source .venv/bin/activate        # or skip this and prefix commands with "uv run"

jupyter lab                      # open the notebooks in order (01, 02, 03), select the .venv kernel
python app.py                    # start the dashboard, then open http://127.0.0.1:8050
python -m src.cleaning           # quick test: prints the cleaning log
```

Without activating the environment, the same commands work as `uv run jupyter lab`, `uv run python app.py`, and so on.
To add a package: `uv add <package>` (updates `pyproject.toml` and `uv.lock`). Never use `pip install` in this project.

Use the code in any notebook or script:

```python
from src.cleaning import load_raw, clean
from src.metrics import overlap_sample, fit_depreciation_model, slopes_table

df = clean(load_raw())                    # clean data with age_years, fuel_group, km_per_year
model = fit_depreciation_model(overlap_sample(df))
slopes_table(model)                       # % of price lost per year, by fuel
```

## The data

251,079 listings, 14 columns (the task said ~200k: always check `shape`).
Key columns: `brand`, `model`, `registration_date` (`MM/YYYY`), `price_in_euro`, `mileage_in_km`, `fuel_type`, `power_kw`, `transmission_type`.

## Cleaning steps

All steps live in `clean()` in [src/cleaning.py](src/cleaning.py) and run in this order. The evidence for each one is in `notebooks/01_data_quality.ipynb`
and the summary in [reports/data_quality.md](reports/data_quality.md).

| # | Step | Rows removed | Why |
|---|---|---|---|
| 1 | Remove **shifted rows** | 199 | The scraper moved values to the wrong columns (e.g. `fuel_type = "01/2023"`, `price = "Automatik"`). The shift is irregular, so the rows cannot be repaired safely. They are 0.08% of the file and spread over many brands. |
| 2 | Remove **exact duplicates** | 6,338 | There is no listing id, so the key is all columns. Same price, date, km and description to the exact value means the same listing scraped twice. |
| 3 | Remove **price < 500 EUR** | 103 | Not realistic sale prices (placeholders, engine damage, deposits). |
| 4 | Remove **mileage > 500,000 km** | 131 | Typing errors (max was 3.8 million km); they would distort the mileage control. |
| 5 | Remove **rows without mileage** | 53 | Mileage is a control variable of the hypothesis. |

**Result: 251,079 -> 244,255 rows (2.7% removed).** The order matters: types are converted only after the shifted rows are gone, otherwise `to_numeric` fails.

**Kept on purpose:** prices above 300,000 EUR (real Ferrari, Lamborghini...), power above 600 kW (real supercars), mileage = 0 (new cars).
**Not used:** `fuel_consumption_*` (92% missing for electric cars, mixed units).

## Transformations

| Column | How it is built | Why |
|---|---|---|
| `year`, `price_in_euro`, `power_kw`, `power_ps` | `pd.to_numeric` | They were text because of the shifted rows. |
| `registration_date` | `pd.to_datetime(..., format="%m/%Y")` | Real date. `year` always equals its year, so `registration_date` is kept (it has the month). |
| `age_years` | `(2023-11-01 - registration_date) / 365.25` | The newest registration is 11/2023, so we **assume** the data was scraped in November 2023 (`REFERENCE_DATE`). |
| `fuel_group` | `Petrol`, `Diesel`, `Electric` kept; `Hybrid` + `Diesel Hybrid` -> `Hybrid`; LPG, CNG, Ethanol, Hydrogen, Other, Unknown -> `Other` | The small groups are too tiny to compare one by one. |
| `km_per_year` | `mileage_in_km / age_years` (age floored at 0.5 years) | The floor avoids huge values for brand-new cars. |
| `log_price`, `km_10k` | `log(price)`, `mileage / 10,000` (in `overlap_sample`, only for the model) | The log turns "% lost per year" into a straight line; `km_10k` makes the coefficient "per 10,000 km". |

| Fuel group | Listings | Median price | Median age | Median km |
|---|---|---|---|---|
| Petrol | 139,421 | 17,990 EUR | 5.8 | 57,000 |
| Diesel | 84,738 | 19,900 EUR | 6.8 | 109,498 |
| Electric | 5,870 | 29,990 EUR | 2.2 | 12,391 |
| Hybrid | 12,214 | 30,990 EUR | 2.2 | 16,769 |
| Other | 2,012 | 16,800 EUR | 5.0 | 58,000 |

## What the EDA found (and what we did about it)

| Finding | What we did in the test |
|---|---|
| Prices are right-skewed | log of the price and medians |
| Electric cars are young (95% up to 6 years) | compare only the age range 0-6 years |
| Age and mileage are correlated (0.83) | both in the model |
| Electric cars start at a higher price (about 46,000 vs 30,000 EUR under 1 year) | measure the loss in % per year, not in euros |
| Electric cars are driven less (6,600 km/year vs 8,900 petrol, 15,200 diesel) | a mileage slope for each fuel |
| Different brand mix | brand effects, and a check inside the same model |

## How the hypothesis is tested

`log(price) = brand effect + fuel effect + slope_age[fuel] * age + slope_km[fuel] * km`, fitted by least squares with robust (HC3) standard errors.
A slope of -0.09 on the log scale means the price is multiplied by exp(-0.09) = 0.914 each year, a loss of 8.6%. H0: the age slope of electric cars equals the one of petrol cars.
The functions are in [src/metrics.py](src/metrics.py); the step-by-step explanation is in `notebooks/03_hypothesis.ipynb`.

## How to use the dashboard

Start it with `uv run python app.py` and open **http://127.0.0.1:8050**. Stop it with Ctrl+C in the terminal. Loading takes a few seconds, because the data is cleaned at start.

**Filters (left column)** - every chart and card updates when you change one:

| Filter | What it does |
|---|---|
| Brands | Choose one or more brands. Empty = all brands. |
| Fuel | Switch on or off Petrol, Diesel, Hybrid, Electric. If you switch off all of them, no cars are left. |
| Age (years) | Keep only cars in an age range (0-30). Drag the two ends of the slider. |

**Cards (top)**

| Card | Meaning |
|---|---|
| Listings | Number of cars in the selection. |
| Median price | Median asking price, in EUR. |
| Median age | Median age in years. |
| Value kept at 3-5 years | Median price of 3-5 year old cars as % of the median price of cars up to 1 year, in the selected brands and fuels. It ignores the age slider (it needs both age windows) and shows "-" when there are fewer than 30 cars in a window. |

**Charts**

| Chart | How to read it |
|---|---|
| Median price by age | One line per fuel, log scale: a steeper line = a faster % loss. Points appear only where there are at least 30 cars. |
| Price lost per year of age | The % of price lost per year of age, one bar per fuel, from a simple fit. **It does not control for mileage and brand**, so it is a quick view; the controlled numbers are in notebook 03 (electric 18.7%, petrol 8.3%). |
| Value kept at 3-5 years, by brand | Grouped bars by brand and fuel, for the 15 biggest brands of the selection. A brand/fuel pair appears only with 30+ cars in both age windows. |
| Price vs mileage | One dot per car (random sample of 4,000). Hover to see brand, model and age. |

**Things to try**
- Leave everything on, then look at "Price lost per year of age": electric is the highest bar.
- Pick `volkswagen` and `renault`: in the retention chart the electric bars are far lower than the petrol ones.
- Set the age slider to 0-3 and look at the price-vs-mileage dots: electric cars sit at low mileage.
- Select only `Electric` and a brand with few cars (e.g. `daihatsu`): the message "No data for this selection" or "Not enough cars" shows up. This is intended: small groups give noisy numbers.

**Where the dashboard code is** (one job per file): `app.py` (layout + callback), `src/config.py` (theme and options), `src/data.py` (loading and filtering),
`src/charts.py` (one function per figure), `src/kpis.py` (the cards), `assets/style.css` (look).

## Status

| Deliverable | Status |
|---|---|
| `notebooks/01_data_quality.ipynb` | done |
| `notebooks/02_eda.ipynb` | done |
| `notebooks/03_hypothesis.ipynb` | done |
| `src/cleaning.py`, `src/metrics.py` | done |
| `app.py` Dash dashboard | done |
| `reports/data_quality.md` | done |
