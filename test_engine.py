import pathlib, json
from colink_core.sim.run import SimContext, load_bootstrap_snapshot
from colink_core.sim.engine import run_sim

snap = load_bootstrap_snapshot('.artifacts/data/bootstrap')

ctx = SimContext(
    out_prefix=pathlib.Path('.'),
    display=None,
    xrpl_snapshot=snap,
    swap_direction='CPX->COL',
    swap_amount=10000,
)

res = run_sim(ctx)
print(res)
