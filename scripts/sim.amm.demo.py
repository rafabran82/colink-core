"""
Tiny AMM demo script for COLINK.

Runs a single COPX/COL pool, performs a swap, and writes NDJSON
under .artifacts/sim/amm-demo/ for graphing/testing.
"""

from pathlib import Path
import sys


def _ensure_repo_root_on_path() -> None:
    # scripts/ is one level below the repo root
    here = Path(__file__).resolve()
    repo_root = here.parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))


_ensure_repo_root_on_path()

from colink_core.sim.amm import AMMPool, MetricsEngine, NDJSONLogger  # noqa: E402


def main() -> None:
    base_dir = Path(".artifacts/sim/amm-demo")
    base_dir.mkdir(parents=True, exist_ok=True)

    pool = AMMPool("COPX", "COL", 1000, 7000, 0.003)
    metrics = MetricsEngine()
    logger = NDJSONLogger(str(base_dir))

    event = pool.swap_a_to_b(100.0)
    state = pool.state

    logger.append_event(
        "swaps",
        {
            "pair": event.pair,
            "side": event.side,
            "amount_in": event.amount_in,
            "amount_out": event.amount_out,
            "price": event.price,
            "slippage": event.slippage,
            "fee_charged": event.fee_charged,
            "timestamp": event.timestamp,
        },
    )

    m_state = metrics.compute_from_state(state)
    logger.append_event(
        "state",
        {
            "pair": state.pair,
            "reserve_a": state.reserve_a,
            "reserve_b": state.reserve_b,
            "lp_total": state.lp_total,
            "price": m_state["price"],
            "depth": m_state["depth"],
            "timestamp": state.timestamp,
        },
    )

    print("OK: sim.amm.demo completed; NDJSON written to", base_dir)


if __name__ == "__main__":
    main()
