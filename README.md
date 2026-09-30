# Quantitative Risk Model

Converts volatility, liquidity, market correlation, leverage and track
record into a single 0-100 Risk Score, using weights derived from data,
plus a volatility forecast.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python -m risk_model.main
```

Options:

```bash
python -m risk_model.main --tickers AAPL MSFT GOOG --period 5y
python -m risk_model.main --output out.json --plots-dir charts
python -m risk_model.main --no-plots        # skip matplotlib PNGs
```

Produces:
- `risk_model_output.json` — the data contract for the UI/dashboard. See
  [`OUTPUT_SCHEMA.md`](./OUTPUT_SCHEMA.md) for the exact shape.
- `plots/<TICKER>_risk.png` — one chart per stock (price history + risk
  trend), unless `--no-plots` is passed.

## Project layout

```
risk_model/
  config.py     # tickers, caps, and other constants
  data.py       # yfinance pulls + the 5 risk-factor calculations
  weights.py    # weight derivation (RidgeCV regression + PCA, blended)
  predict.py    # next-period volatility forecast
  plotting.py   # matplotlib price + risk-trend charts
  main.py       # CLI entrypoint, wires everything together
  README.md     # module-by-module reference for this folder
risk_dashboard.html   # interactive slider dashboard (reads the JSON output)
OUTPUT_SCHEMA.md
requirements.txt
```

## Method summary

- **Five risk factors**, each normalized to 0-100 using fixed caps (the
  only hand-picked numbers in the pipeline): volatility, liquidity,
  correlation to the S&P 500, leverage (debt/equity), and track record
  (max drawdown, used as a reliability proxy).
- **Weights are derived, not guessed**: a RidgeCV regression of factor
  scores (computed on the first 70% of the price history) against future
  max drawdown (computed on the remaining out-of-sample window) — plus a
  PCA cross-check — averaged together for stability.
- **Prediction is scoped to risk, not price**: a small model forecasts
  next-period volatility; that swaps into the score to produce a
  "predicted" Risk Score. We do not predict whether the stock price
  itself will rise or fall.

## Known limitations

- Weights are only as stable as the ticker sample (currently ~20). More
  tickers would sharpen the regression.
- `track_record` is a max-drawdown proxy, not an official credit rating.
- Leverage data (`debtToEquity`) is occasionally missing for ETFs/some
  tickers and defaults to a neutral score of 50.
