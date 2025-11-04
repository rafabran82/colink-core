from __future__ import annotations
import math
from typing import List
import numpy as np

# Headless plotting
import matplotlib
matplotlib.use("Agg")  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402


def simulate_gbm_paths(
    n_paths: int,
    n_steps: int,
    s0: float = 1.0,
    mu: float = 0.0,
    sigma: float = 0.25,
    dt: float = 1.0 / 32.0,
) -> List[List[float]]:
    """
    Tiny GBM simulation returning a list-of-lists for stability and ease of JSON dumping.
    """
    # Precompute drift/vol
    drift = (mu - 0.5 * sigma * sigma) * dt
    vol = sigma * math.sqrt(dt)

    out: List[List[float]] = []
    rng = np.random.default_rng(42)  # stable seed for reproducible tests
    for _ in range(n_paths):
        s = s0
        path = [s]
        # n_steps values total; path length == n_steps
        for _ in range(1, n_steps):
            z = rng.standard_normal()
            s = s * math.exp(drift + vol * z)
            path.append(s)
        out.append(path)
    return out


def plot_paths(paths: List[List[float]], title: str, outfile: str) -> None:
    plt.figure()
    for p in paths:
        plt.plot(p)
    plt.title(title)
    plt.xlabel("step")
    plt.ylabel("price")
    plt.tight_layout()
    plt.savefig(outfile, dpi=120)
    plt.close()


def plot_hist(samples: List[float], title: str, outfile: str) -> None:
    plt.figure()
    plt.hist(samples, bins=20)
    plt.title(title)
    plt.xlabel("value")
    plt.ylabel("freq")
    plt.tight_layout()
    plt.savefig(outfile, dpi=120)
    plt.close()
