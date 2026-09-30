import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def plot_stock(d, current_score, predicted_score, predicted_vol_score, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    ticker = d["ticker"]
    close = d["close"]

    rising = predicted_score > current_score
    trend_color = "#c0392b" if rising else "#27ae60"
    trend_label = "Risk trending UP" if rising else "Risk trending DOWN"
    delta = predicted_score - current_score

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(9, 6), gridspec_kw={"height_ratios": [3, 1]}
    )

    ax1.plot(close.index, close.values, color="#1a2744", linewidth=1.3)
    ax1.set_title(f"{ticker} — Price History", fontsize=12, fontweight="bold")
    ax1.set_ylabel("Price")
    ax1.grid(alpha=0.25)

    bars = ax2.barh(
        ["Current", "Predicted"],
        [current_score, predicted_score],
        color=["#1a2744", trend_color],
    )
    ax2.set_xlim(0, 100)
    ax2.set_xlabel("Risk Score (0-100)")
    ax2.axvline(33, color="#bbb", linestyle="--", linewidth=0.8)
    ax2.axvline(66, color="#bbb", linestyle="--", linewidth=0.8)
    for bar, val in zip(bars, [current_score, predicted_score]):
        ax2.text(val + 1.5, bar.get_y() + bar.get_height() / 2, f"{val:.1f}",
                  va="center", fontsize=9)

    fig.suptitle(
        f"{trend_label}  ({delta:+.1f} pts)  —  driven by predicted volatility "
        f"score of {predicted_vol_score:.1f}",
        fontsize=10, color=trend_color, y=0.98
    )
    plt.tight_layout(rect=[0, 0, 1, 0.94])

    path = os.path.join(out_dir, f"{ticker}_risk.png")
    fig.savefig(path, dpi=130)
    plt.close(fig)
    print(f"  saved {path}")
