import csv
import json
import os

from .config import DEFAULT_TICKERS

TICKER_COLUMN_NAMES = {"ticker", "tickers", "symbol", "symbols"}


def _clean(values):
    seen, out = set(), []
    for v in values:
        t = str(v).strip().upper()
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _read_txt(path):
    with open(path, newline="") as f:
        lines = [ln.split("#", 1)[0] for ln in f]
    tokens = []
    for ln in lines:
        tokens.extend(ln.replace(",", " ").split())
    return tokens


def _read_csv(path):
    with open(path, newline="") as f:
        rows = [r for r in csv.reader(f) if r and any(c.strip() for c in r)]
    if not rows:
        return []
    header = [c.strip().lower() for c in rows[0]]
    for i, name in enumerate(header):
        if name in TICKER_COLUMN_NAMES:
            return [r[i] for r in rows[1:] if len(r) > i]
    return [r[0] for r in rows]


def _read_json(path):
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, dict):
        for key in ("tickers", "universe", "symbols"):
            if key in data:
                data = data[key]
                break
    if not isinstance(data, list):
        raise ValueError(
            f"{path}: expected a JSON list of tickers, or an object with a "
            f"'tickers' / 'universe' / 'symbols' list."
        )
    return data


def load_universe_file(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Universe file not found: {path}")
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        raw = _read_csv(path)
    elif ext == ".json":
        raw = _read_json(path)
    else:
        raw = _read_txt(path)
    tickers = _clean(raw)
    if not tickers:
        raise ValueError(f"Universe file {path} contained no tickers.")
    return tickers


def resolve_universe(universe_path=None, cli_tickers=None):
    """Priority: --universe file > --tickers > hardcoded DEFAULT_TICKERS."""
    if universe_path:
        tickers = load_universe_file(universe_path)
        return tickers, f"custom universe file ({universe_path})"
    if cli_tickers:
        return _clean(cli_tickers), "--tickers"
    return list(DEFAULT_TICKERS), "default hardcoded universe"
