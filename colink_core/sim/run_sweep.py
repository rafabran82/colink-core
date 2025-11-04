from __future__ import annotations
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt


def simulate_gbm_paths(
    *,
    n_steps: int,
    n_paths: int,
    dt: float,
    mu: float,
    sigma: float,
    s0: float,
    seed: int | None = None,
):
    rng = np.random.default_rng(seed)
    dt_arr = dt
    drift = (mu - 0.5 * sigma * sigma) * dt_arr
    shock = sigma * np.sqrt(dt_arr) * rng.standard_normal(size=(n_steps, n_paths))
    increments = drift + shock
    log_paths = np.cumsum(increments, axis=0)
    s = s0 * np.exp(log_paths)
    s = np.vstack([np.full((1, n_paths), s0), s])  # prepend s0
    return s  # shape: (n_steps+1, n_paths)


def plot_paths(paths, outdir):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    out_path = outdir / "sweep_paths-0000.png"
    plt.figure(figsize=(8, 4.5))
    plt.plot(paths[:, : min(paths.shape[1], 20)])
    plt.title("GBM sample paths")
    plt.xlabel("step")
    plt.ylabel("price")
    plt.tight_layout()
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()
    return out_path


def plot_hist(paths, outdir):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    out_path = outdir / "sweep_hist-0000.png"
    terminal = paths[-1, :]
    plt.figure(figsize=(6, 4))
    plt.hist(terminal, bins=30)
    plt.title("Terminal price distribution")
    plt.xlabel("price")
    plt.ylabel("count")
    plt.tight_layout()
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()
    return out_path
