# risk_model
## config.py

Constants shared by every other module: the default ticker list,
benchmark, history period, output paths, and `CAPS`.

`CAPS` is the only place numbers are hand-picked in the whole pipeline —
it maps each raw factor (e.g. annualized volatility, beta) to a `(low,
high)` range used to rescale it onto 0-100. Everything downstream
(weights, predictions) is derived from data, not guessed.

`HISTORY_FRACTION` (0.7) splits each stock's price window in two: the
first 70% is used to compute the 5 input factors, the last 30% is held
out and used only as the regression target in `weights.py`. This split
exists so `track_record` (an input) can never leak into the outcome
being predicted.

## data.py

Pulls price/volume/fundamentals from yfinance and turns them into the 5
risk factors, both as raw values and as 0-100 normalized scores.

Key functions:
- `normalize(value, lo, hi, invert=False)` — rescales a raw value onto
  0-100 using the caps from `config.py`. Returns 50.0 (neutral) if the
  value is missing, so downstream code never has to check for `None`.
- `max_drawdown(prices)` — largest peak-to-trough decline in a price
  series, used both as the `track_record` input and as the out-of-sample
  regression target.
- `compute_factors(ticker, ...)` — the main per-stock function. Splits
  the price history per `HISTORY_FRACTION`, computes all 5 factors on
  the history split, and computes `future_mdd` (future max drawdown) on
  the held-out split.
- `fetch_all(tickers, ...)` — loops `compute_factors` over every ticker,
  skipping any with insufficient data.

## weights.py

Derives the model's factor weights from data instead of hand-picking
them. Two independent methods, then blended:

- `derive_weights_regression(all_data)` — RidgeCV regression of each
  stock's 5 factor scores against its `future_mdd` (out-of-sample, from
  `data.py`). Cross-validated alpha instead of a fixed guess, since a
  small ticker sample makes a single alpha choice unstable.
- `derive_weights_pca(all_data)` — PCA loadings on the first principal
  component of the normalized factor scores. Unsupervised, needs no
  target — a sanity check against the regression weights.
- `blend_weights(...)` — averages the two and renormalizes to sum to
  1.0. Guards against either method overreacting to the sample size.

## predict.py

Forecasts each stock's next-period volatility (not its price). A pooled
Ridge model is trained across all stocks: trailing 5/21/63-day realized
volatility predicts the volatility of the *next* 21 days. Time-ordered
train/test split, since this is sequential data and shuffling would leak
the future into training.

`predict_next_volatility(all_data)` returns per-ticker predictions plus
the test-set MAE, which `main.py` reports in `model_info`.

## plotting.py

`plot_stock(...)` saves one PNG per ticker: price history on top, a
current-vs-predicted risk score bar below. Colored red if predicted risk
is higher than current, green if lower.

This deliberately shows a **risk score** direction, not a price
forecast — the chart title always says "Risk trending UP/DOWN," never
anything implying the price itself will rise or fall.

## main.py

CLI entrypoint. `parse_args()` defines the flags (`--tickers`,
`--period`, `--output`, `--plots-dir`, `--no-plots`); `run(...)` wires
together `data.py` → `weights.py` → `predict.py` → `plotting.py` and
writes the final JSON. `main()` just parses args and calls `run`.
## Custom Universe & CLI Reference

By default the model scores a built-in universe of 20 tickers (`DEFAULT_TICKERS` in `risk_model/config.py`). You can point it at your own set of tickers instead. Weights, the volatility forecast, charts and the output JSON are then all computed on **your** universe.

### Choosing a universe

The universe is resolved in this order:

| Priority | Source | How |
|---|---|---|
| 1 | Universe file | `--universe my_universe.csv` |
| 2 | Inline list | `--tickers AAPL MSFT GOOG ...` |
| 3 | Built-in default | no flag needed |

If `--universe` is given but the file is missing or contains no tickers, the run **stops with an error** rather than silently falling back to the defaults, so you never get results for the wrong set of stocks.

### Universe file formats

| Format | Expected layout |
|---|---|
| `.csv` | A column named `ticker` or `symbol` (case-insensitive). If no such header exists, the first column is used. Extra columns are ignored. |
| `.json` | A list (`["AAPL", "MSFT"]`) or an object with a `tickers`, `universe` or `symbols` list. |
| `.txt` | Tickers separated by spaces, commas or newlines. `#` starts a comment. |

Symbols are uppercased and de-duplicated automatically.

Example `my_universe.csv`:

```csv
ticker,name,sector
AAPL,Apple,Technology
JPM,JPMorgan Chase,Financials
XOM,Exxon Mobil,Energy
```

### Command-line arguments

Run from the project root:

```bash
python -m risk_model.main [options]
```

| Argument | Default | Description |
|---|---|---|
| `--universe FILE` | none | Path to a `.csv`, `.json` or `.txt` universe file. Overrides `--tickers`. |
| `--tickers T1 T2 ...` | none | Space-separated tickers to analyze. Ignored if `--universe` is set. |
| `--benchmark TICKER` | `^GSPC` | Benchmark index for the correlation (beta) factor. |
| `--period P` | `3y` | yfinance history window, e.g. `2y`, `5y`, `10y`, `max`. |
| `--output FILE` | `risk_model_output.json` | Where to write the results JSON (the folder must already exist). |
| `--plots-dir DIR` | `plots` | Folder for the per-stock PNG charts (created if missing). |
| `--no-plots` | off | Skip chart generation. |
| `-h`, `--help` | | Show the argument list. |

### Examples

```bash
# Built-in 20-ticker universe
python -m risk_model.main

# Your own universe from a file
python -m risk_model.main --universe my_universe.csv

# Quick ad-hoc run on a handful of tickers
python -m risk_model.main --tickers AAPL MSFT GOOG JPM XOM KO

# Longer history, no charts
python -m risk_model.main --universe my_universe.csv --period 5y --no-plots

# Custom output locations
python -m risk_model.main --universe my_universe.csv \
    --output results/out.json --plots-dir results/charts

# Benchmark against the Nasdaq-100 instead of the S&P 500
python -m risk_model.main --benchmark QQQ
```

### Notes

- Tickers with fewer than ~100 trading days of history are skipped, and the run needs at least 5 usable tickers to derive weights.
- `risk_dashboard.html` embeds a static snapshot of the output JSON. After running on a new universe, paste the regenerated JSON into the dashboard's `DATA` constant to view it there.
Run as `python -m risk_model.main`.
