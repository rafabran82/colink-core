from __future__ import annotations

import math
import os
import random

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def plot_pair(out_dir: str, pair: str, seed: int = 123) -> str:
    os.makedirs(out_dir, exist_ok=True)
    rnd = random.Random(seed)

    xs = list(range(64))
    ys = [100 + 3 * math.sin(i / 6.0) + rnd.uniform(-0.9, 0.9) for i in xs]

    fig = plt.figure(figsize=(6, 3.2), dpi=150)
    plt.plot(xs, ys, linewidth=2)
    plt.title(pair)
    plt.xlabel("t")
    plt.ylabel("price (synth)")

    path = os.path.join(out_dir, f"{pair.replace('/', '_')}.png")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path
