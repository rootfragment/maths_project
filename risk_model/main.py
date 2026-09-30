import argparse
import json

from .config import DEFAULT_TICKERS, DEFAULT_BENCHMARK, DEFAULT_PERIOD
from .config import DEFAULT_OUTPUT_JSON, DEFAULT_PLOTS_DIR, FACTOR_KEYS
from .data import fetch_all, normalize
from .config import CAPS
from .weights import derive_weights_regression, derive_weights_pca, blend_weights
from .predict import predict_next_volatility
from .plotting import plot_stock

def parse_args():
    p = argparse.ArgumentParser(description="Run the quantitative risk model pipeline.")
    p.add_argument("--tickers", nargs="+", default=DEFAULT_TICKERS,
                    help="Space-separated list of tickers to analyze.")
    p.add_argument("--benchmark", default=DEFAULT_BENCHMARK,
                    help="Benchmark ticker for beta/correlation (default: S&P 500).")
    p.add_argument("--period", default=DEFAULT_PERIOD,
                    help="yfinance history period, e.g. 3y, 5y (default: 3y).")
    p.add_argument("--output", default=DEFAULT_OUTPUT_JSON,
                    help="Path to write the output JSON.")
    p.add_argument("--plots-dir", default=DEFAULT_PLOTS_DIR,
                    help="Directory to save per-stock PNGs.")
    p.add_argument("--no-plots", action="store_true",
                    help="Skip generating matplotlib plots.")
    return p.parse_args()

def run(tickers, benchmark, period, output_path, plots_dir, make_plots=True):
    print("Fetching data...")
    all_data = fetch_all(tickers, benchmark, period)
    if len(all_data) < 5:
        raise RuntimeError(
            f"Only {len(all_data)} tickers returned usable data; "
            f"need at least 5 for stable weight derivation."
        )

    print("\nDeriving weights from data...")
    weights_regression = derive_weights_regression(all_data)
    weights_pca = derive_weights_pca(all_data)
    print("Regression-derived weights:", weights_regression)
    print("PCA-derived weights:", weights_pca)

    weights = blend_weights(weights_regression, weights_pca)
    print("Final blended weights:", weights)

    print("\nTraining volatility prediction model...")
    predicted_vols, mae = predict_next_volatility(all_data)

    output = {"weights": weights, "weights_pca": weights_pca, "stocks": {}}

    for d in all_data:
        ticker = d["ticker"]
        current_score = sum(weights[f] * d["scores"][f] for f in FACTOR_KEYS)

        pred_vol_score = normalize(predicted_vols[ticker], *CAPS["volatility"])
        pred_scores = dict(d["scores"])
        pred_scores["volatility"] = pred_vol_score
        predicted_score = sum(weights[f] * pred_scores[f] for f in FACTOR_KEYS)

        output["stocks"][ticker] = {
            "scores": {k: round(v, 1) for k, v in d["scores"].items()},
            "current_score": round(current_score, 1),
            "predicted_score": round(predicted_score, 1),
            "predicted_volatility_score": round(pred_vol_score, 1),
        }

        if make_plots:
            plot_stock(d, current_score, predicted_score, pred_vol_score, plots_dir)

    output["model_info"] = {
        "volatility_prediction_mae": round(mae, 4),
        "tickers_used": [d["ticker"] for d in all_data],
        "weight_method": (
            "Blend of two data-derived methods: (1) RidgeCV regression of 5 "
            "input factors, computed on the first 70% of the price window, "
            "against max drawdown realized in the remaining out-of-sample "
            "window; and (2) PCA loadings on the first principal component "
            "across all factors. Averaging both guards against either method "
            "being unstable due to a limited ticker sample."
        ),
        "weights_regression": weights_regression,
        "weights_pca": weights_pca,
    }

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved {output_path}")
    return output

def main():
    args = parse_args()
    run(
        tickers=args.tickers,
        benchmark=args.benchmark,
        period=args.period,
        output_path=args.output,
        plots_dir=args.plots_dir,
        make_plots=not args.no_plots,
    )

if __name__ == "__main__":
    main()
