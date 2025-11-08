from __future__ import annotations

import math
import os
import random

from colink_core.telemetry.writer import NDJSONWriter, detect_run_metadata, event


def parse_pairs(s: str) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        base, quote = [x.strip() for x in part.split("/", 1)]
        pairs.append((base, quote))
    return pairs


def synth_series(n: int = 64, base: float = 100.0, amp: float = 3.0, seed: int = 42):
    rnd = random.Random(seed)
    out: list[tuple[int, float]] = []
    for i in range(n):
        val = base + amp * math.sin(i / 6.0) + rnd.uniform(-amp * 0.3, amp * 0.3)
        out.append((i, val))
    return out


def main() -> None:
    run_id = os.environ.get("GITHUB_RUN_ID") or os.environ.get("RUN_ID") or "local"
    out_dir = os.environ.get("SIM_OUT_DIR") or "out/smoke"
    nd_path = os.path.join(out_dir, f"sim_{run_id}.ndjson")

    pairs = parse_pairs(os.environ.get("SIM_PAIRS", "XRP/COL,COPX/COL"))
    seed = int(os.environ.get("SIM_SEED", "123"))

    meta: dict[str, object] = detect_run_metadata({"run_id": run_id, "pairs": pairs, "seed": seed})
    os.makedirs(out_dir, exist_ok=True)

    with NDJSONWriter(nd_path, mode="w") as w:
        w.write(event("sim_start", {"meta": meta}, run_id=run_id))

        for base, quote in pairs:
            series = synth_series(seed=seed)
            for t, v in series:
                w.write(
                    event(
                        "pair_tick",
                        {"pair": f"{base}/{quote}", "t": t, "v": v},
                        run_id=run_id,
                    )
                )

        # placeholder for future AI decisions
        w.write(
            event(
                "decision_log",
                {
                    "reason": "placeholder",
                    "policy": "none",
                    "inputs_ref": {"ndjson": os.path.basename(nd_path)},
                },
                run_id=run_id,
            )
        )

        w.write(event("sim_end", {"ok": True}, run_id=run_id))


if __name__ == "__main__":
    main()
