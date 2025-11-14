from colink_core.sim.run import parse_args

args = parse_args([
    "--sim",
    "--display","Agg",
    "--out-prefix",".artifacts/test_args",
    "--xrpl-bootstrap-dir",".artifacts/data/bootstrap",
    "--swap-direction","CPX->COL",
    "--swap-amount","10000",
])

print(args)
