param(
  [string]$Pair = "XRP/COL",
  [int]$Steps = 60,
  [int]$Seed = 42
)

$ErrorActionPreference = "Stop"

# Resolve repo root from this script's folder
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

# Pick Python
$py = Join-Path $repo ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

Write-Host "== Phase-3 MVP Sim =="
Write-Host "Pair=$Pair  Steps=$Steps  Seed=$Seed"

# Ensure imports resolve from repo
$oldPath = $env:PYTHONPATH
$env:PYTHONPATH = if ($oldPath) { "$repo;$oldPath" } else { $repo }

# Python launcher: try real sim; if missing, write stub artifacts
$code = @"
import os, sys, json, random, time, csv

PAIR  = sys.argv[1] if len(sys.argv) > 1 else "XRP/COL"
STEPS = int(sys.argv[2]) if len(sys.argv) > 2 else 60
SEED  = int(sys.argv[3]) if len(sys.argv) > 3 else 42

art = os.path.join(os.getcwd(), ".artifacts")
os.makedirs(art, exist_ok=True)

def run_real():
    try:
        from colink_core.sim.mvp.run import main
        return ("REAL", main(pair=PAIR, steps=STEPS, seed=SEED))
    except Exception as e:
        return ("FALLBACK", e)

mode, res = run_real()
if mode == "FALLBACK":
    random.seed(SEED)
    rows, price = [], 1.0
    for t in range(STEPS):
        price *= (1.0 + random.uniform(-0.01, 0.01))
        rows.append({"t": t, "pair": PAIR, "price": round(price, 6)})

    with open(os.path.join(art, "sim.events.ndjson"), "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps({"ts": time.time(), **r}) + "\n")

    metrics = {
        "pair": PAIR, "steps": STEPS, "seed": SEED, "mode": "stub",
        "p_start": rows[0]["price"], "p_end": rows[-1]["price"], "ts": time.time(),
    }
    with open(os.path.join(art, "sim.metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    with open(os.path.join(art, "sim.summary.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["t","pair","price"])
        w.writeheader(); w.writerows(rows)

    print("Sim fallback wrote: sim.events.ndjson, sim.metrics.json, sim.summary.csv")
else:
    print("Real sim completed:", res)
"@

$tmp = Join-Path $env:TEMP ("run_sim_{0}.py" -f ([guid]::NewGuid()))
Set-Content -Path $tmp -Value $code -Encoding utf8

try {
  & $py $tmp $Pair $Steps $Seed
} finally {
  Remove-Item $tmp -Force -ErrorAction SilentlyContinue
  $env:PYTHONPATH = $oldPath
}
