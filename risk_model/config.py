DEFAULT_TICKERS = [
    "AAPL", "TSLA", "JNJ", "SPY", "NVDA", "KO", "GME", "XOM",
    "MSFT", "AMZN", "META", "PFE", "WMT", "DIS", "AMD", "BA",
    "INTC", "NFLX", "COST", "T",
]
DEFAULT_BENCHMARK = "^GSPC"
DEFAULT_PERIOD = "3y"
DEFAULT_OUTPUT_JSON = "risk_model_output.json"
DEFAULT_PLOTS_DIR = "plots"

HISTORY_FRACTION = 0.7

CAPS = {
    "volatility": (0.10, 0.80),
    "liquidity": (6, 11),
    "correlation": (0.0, 2.0),
    "leverage": (0, 300),
    "track_record": (0.0, 0.6),
}

FACTOR_KEYS = list(CAPS.keys())
