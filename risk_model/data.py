import numpy as np
import pandas as pd
import yfinance as yf

from .config import CAPS, HISTORY_FRACTION

def normalize(value, lo, hi, invert=False):

    if value is None or (isinstance(value, float) and np.isnan(value)):
        return 50.0
    score = (value - lo) / (hi - lo) * 100
    score = float(np.clip(score, 0, 100))
    return 100 - score if invert else score

def max_drawdown(prices):

    cum_max = prices.cummax()
    drawdown = (prices - cum_max) / cum_max
    return abs(drawdown.min())

def fetch_benchmark_returns(benchmark, period):
    hist = yf.Ticker(benchmark).history(period=period)
    return hist["Close"].pct_change().dropna()

def compute_factors(ticker, bench_returns, period, history_fraction=HISTORY_FRACTION):

    tk = yf.Ticker(ticker)
    hist = tk.history(period=period)
    if hist.empty or len(hist) < 100:
        return None

    close_full = hist["Close"]
    volume_full = hist["Volume"]

    split_idx = int(len(close_full) * history_fraction)
    close = close_full.iloc[:split_idx]
    volume = volume_full.iloc[:split_idx]
    close_future = close_full.iloc[split_idx:]

    returns = close.pct_change().dropna()
    returns_full = close_full.pct_change().dropna()

    vol_annual = returns.std() * np.sqrt(252)

    dollar_vol = (close * volume).mean()
    log_dollar_vol = np.log10(dollar_vol) if dollar_vol > 0 else 6

    aligned = pd.concat([returns, bench_returns], axis=1, join="inner").dropna()
    aligned.columns = ["stock", "bench"]
    if len(aligned) > 30 and aligned["bench"].var() > 0:
        beta = np.cov(aligned["stock"], aligned["bench"])[0, 1] / aligned["bench"].var()
    else:
        beta = 1.0

    try:
        debt_equity = tk.info.get("debtToEquity", None)
    except Exception:
        debt_equity = None

    mdd = max_drawdown(close)

    future_mdd = max_drawdown(close_future) if len(close_future) > 20 else np.nan

    raw = {
        "volatility": vol_annual,
        "liquidity": log_dollar_vol,
        "correlation": beta,
        "leverage": debt_equity,
        "track_record": mdd,
    }

    scores = {
        "volatility": normalize(vol_annual, *CAPS["volatility"]),
        "liquidity": normalize(log_dollar_vol, *CAPS["liquidity"], invert=True),
        "correlation": normalize(beta, *CAPS["correlation"]),
        "leverage": normalize(debt_equity, *CAPS["leverage"]),
        "track_record": normalize(mdd, *CAPS["track_record"]),
    }

    return {
        "ticker": ticker,
        "raw": raw,
        "scores": scores,
        "future_mdd": future_mdd,
        "returns": returns_full,
        "close": close_full,
    }

def fetch_all(tickers, benchmark, period):

    bench_returns = fetch_benchmark_returns(benchmark, period)
    all_data = []
    for t in tickers:
        print(f"Processing {t}...")
        result = compute_factors(t, bench_returns, period)
        if result is None:
            print(f"  skipped (no data)")
        else:
            all_data.append(result)
    return all_data
