"""
Render benchmark charts (PNG) from ga_benchmark.py --save artifacts.

Produces two slide-ready figures per case:
  1. <stem>_convergence.png  — GA basic vs memetic best-distance-per-generation curve
  2. <stem>_comparison.png   — mean route distance per algorithm (bars + std error)

Usage:
  python pipeline/benchmarks/plot_results.py --province "Siem Reap" --n 8
  python pipeline/benchmarks/plot_results.py --stem convergence_siem_reap_n8
"""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless — write files, no display
import matplotlib.pyplot as plt
import pandas as pd

RESULTS_DIR = Path(__file__).parent / "results"

# Brand palette (matches frontend: midnight / gold / teal)
COLOR_MEMETIC = "#102050"
COLOR_BASIC = "#E5A517"
BAR_COLORS = {
    "Random": "#c0392b",
    "Greedy NN": "#95a5a6",
    "2-opt": "#7f8c8d",
    "GA (basic)": "#E5A517",
    "GA (memetic)": "#102050",
}


def plot_convergence(stem: str) -> None:
    csv_path = RESULTS_DIR / f"{stem}.csv"
    if not csv_path.exists():
        print(f"[skip] convergence CSV not found: {csv_path}")
        return
    df = pd.read_csv(csv_path)

    fig, ax = plt.subplots(figsize=(8, 5))
    if "ga_basic_km" in df:
        ax.plot(df["generation"], df["ga_basic_km"], color=COLOR_BASIC,
                lw=2.2, label="GA (basic)")
    if "ga_memetic_km" in df:
        ax.plot(df["generation"], df["ga_memetic_km"], color=COLOR_MEMETIC,
                lw=2.2, ls="--", label="GA (memetic)")

    ax.set_xlabel("Generation")
    ax.set_ylabel("Best route distance (km)")
    ax.set_title("GA Convergence — best distance per generation")
    ax.grid(True, alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()

    out = RESULTS_DIR / f"{stem}_convergence.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"Convergence chart -> {out}")


def plot_comparison(stem: str) -> None:
    summary_path = RESULTS_DIR / f"{stem}_summary.json"
    if not summary_path.exists():
        print(f"[skip] summary JSON not found: {summary_path}")
        return
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    algos = summary["algorithms"]

    names = list(algos.keys())
    means = [algos[n]["mean_km"] for n in names]
    stds = [algos[n]["std_km"] for n in names]
    colors = [BAR_COLORS.get(n, "#34495e") for n in names]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(names, means, yerr=stds, capsize=5, color=colors,
                  edgecolor="white", linewidth=1)

    for bar, mean in zip(bars, means):
        ax.text(bar.get_x() + bar.get_width() / 2, mean,
                f"{mean:.1f}", ha="center", va="bottom",
                fontsize=9, fontweight="bold")

    prov = summary.get("province", "?")
    n = summary.get("n_places", "?")
    trials = summary.get("trials", "?")
    ax.set_ylabel("Mean route distance (km)")
    ax.set_title(f"Routing algorithms — {prov}, n={n} places, {trials} trials\n(lower is better)")
    ax.grid(True, axis="y", alpha=0.25)
    plt.xticks(rotation=15)
    fig.tight_layout()

    out = RESULTS_DIR / f"{stem}_comparison.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"Comparison chart -> {out}")


def main():
    parser = argparse.ArgumentParser(description="Plot GA benchmark results")
    parser.add_argument("--stem", default=None,
                        help="CSV stem, e.g. convergence_siem_reap_n8")
    parser.add_argument("--province", default="Siem Reap")
    parser.add_argument("--n", type=int, default=8)
    args = parser.parse_args()

    stem = args.stem or f"convergence_{args.province.replace(' ', '_').lower()}_n{args.n}"
    plot_convergence(stem)
    plot_comparison(stem)


if __name__ == "__main__":
    main()
