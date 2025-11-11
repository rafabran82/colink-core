<!-- CI BADGE BEGIN -->
[![PR CI](https://github.com/rafabran82/colink-core/actions/workflows/pr-ci.yml/badge.svg)](https://github.com/rafabran82/colink-core/actions/workflows/pr-ci.yml)
<!-- CI BADGE END -->
[![Windows Smoke (json_cli)](https://github.com/rafabran82/colink-core/actions/workflows/win-smoke.yml/badge.svg)](https://github.com/rafabran82/colink-core/actions/workflows/win-smoke.yml)

[![Sim Smoke](https://github.com/rafabran82/colink-core/actions/workflows/sim-smoke.yml/badge.svg)](https://github.com/rafabran82/colink-core/actions/workflows/sim-smoke.yml)
# colink-core

Core components and simulation CLI for COLINK.

## Quick Start

```powershell
pip install -e .
colink-json --version
colink-json quote --col-in 8000 --min-out-bps 150 --twap-guard
colink-json sweep --outdir charts
```

**Outputs**
- charts/sweep_paths-0000.png
- charts/sweep_hist-0000.png

## Dev notes

- Tests: `pytest -q`
- JSON CLI (module form): `python -m colink_core.sim.json_cli ...`
- API:
  - `GET  /sim/quote?col_in=8000&min_out_bps=150&twap_guard=true`
  - `POST /sim/sweep?outdir=charts`

## Quick start (dev)

```powershell
# install (with sim extras)
python -m pip install -e ".[sim]"

# run locally
uvicorn main:app --port 8000

# quick smoke
.\scripts\smoke.ps1

[![PR CI](https://github.com/rafabran82/colink-core/actions/workflows/pr-ci.yml/badge.svg)](https://github.com/rafabran82/colink-core/actions/workflows/pr-ci.yml)


## CI Status

- **Build & Tests (required)**: [![PR CI/build-test (pull_request)](https://github.com/rafabran82/colink-core/actions/workflows/pr-ci.yml/badge.svg)](https://github.com/rafabran82/colink-core/actions/workflows/pr-ci.yml)
- **CodeQL (required)**: [![CodeQL/CodeQL (pull_request)](https://github.com/rafabran82/colink-core/actions/workflows/codeql.yml/badge.svg)](https://github.com/rafabran82/colink-core/actions/workflows/codeql.yml)rnrn<!-- >>> sim-backend-docs begin >>> -->
## Simulation: backend & display options

The sweep CLI supports GUI/no-GUI rendering and explicit backend selection.

### Backends
- `auto` (default): uses **Agg** when headless and **TkAgg** when GUI is enabled.
- `TkAgg`: open a Tk window (when GUI is enabled).
- `Agg`: render offscreen (no window), still saves the summary overlay PNG.

### Examples

Headless (Agg auto):
```powershell
$env:SIM_NO_GUI = "1"
.\tools\cc-sim-sweep.ps1 -TradesCsv "100,500" -VolCsv "0.01,0.03" -Backend autornrn<!-- >>> sim-backend-docs begin >>> -->
## Simulation: backend & display options

The sweep CLI supports GUI/no-GUI rendering and explicit backend selection.

### Backends
- `auto` (default): uses **Agg** when headless and **TkAgg** when GUI is enabled.
- `TkAgg`: open a Tk window (when GUI is enabled).
- `Agg`: render offscreen (no window), still saves the summary overlay PNG.

### Examples

Headless (Agg auto):
```powershell
$env:SIM_NO_GUI = "1"
.\tools\cc-sim-sweep.ps1 -TradesCsv "100,500" -VolCsv "0.01,0.03" -Backend auto
**Slippage curve (headless Agg):**
```powershell
python -m colink_core.sim.run_sweep --steps 100 --slippage .sim_smoke/slippage.png --display Agg --no-show
**Slippage curve (headless Agg):**
```powershell
python -m colink_core.sim.run_sweep --steps 100 --slippage .sim_smoke/slippage.png --display Agg --no-show
**Spread over time (headless Agg):**
```powershell
python -m colink_core.sim.run_sweep --pairs XRP/COL --steps 100 --spread .sim_smoke/spread_{pair}.png --display Agg --no-show
**Deterministic run (fixed seed):**
```powershell
python -m colink_core.sim.run_sweep --pairs XRP/COL --steps 50 --seed 123 --out .sim_smoke/seeded.json --plot .sim_smoke/seeded.png --display Agg --no-show
**CSV-driven sweep (headless Agg):**
```powershell
python -m colink_core.sim.run_sweep `
  --pairs XRP/COL `
  --steps 200 `
  --seed 777 `
  --trades .sim_smoke/trades.csv `
  --volatility .sim_smoke/vol.csv `
  --out .sim_smoke/csv_metrics.json `
  --plot .sim_smoke/csv_timeseries.png `
  --display Agg --no-show
**Metrics-only (fast CI path):**
```powershell
python -m colink_core.sim.run_sweep `
  --pairs XRP/COL `
  --steps 100 `
  --seed 123 `
  --out .sim_smoke/metrics_only.json `
  --metrics-only `
  --display Agg --no-show


Test pre-commit CI badge seed

![pre-commit](https://github.com/rafabran82/colink-core/actions/workflows/pre-commit.yml/badge.svg)rnrn<!-- SIM QUICKSTART BEGIN -->
### Simulation quickstart

Headless demo (produces PNG + NDJSON + JSON metrics):

```bash
python -m colink_core.sim.run --demo --display Agg --out-prefix ./.artifacts/demornrnrn<!-- SIM QUICKSTART BEGIN -->
### Simulation quickstart

Headless demo (produces PNG + NDJSON + JSON metrics):

```bash
python -m colink_core.sim.run --demo --display Agg --out-prefix ./.artifacts/demo
<!-- SIM QUICKSTART END -->
rnrnrn<!-- SIM QUICKSTART BEGIN -->
### Simulation quickstart

Headless demo (produces PNG + NDJSON + JSON metrics):

```bash
python -m colink_core.sim.run --demo --display Agg --out-prefix ./.artifacts/demornrnrn<!-- BRIDGE QUICKSTART BEGIN -->
### Bridge (Phase 4) quickstart

Emit two-hop CP-AMM bridge artifacts (events NDJSON + metrics JSON):

```bash
python -m colink_core.bridge.run \
  --amount 1500 \
  --pairA COL/COPX \
  --pairM COPX/XRP \
  --out-prefix ./.artifacts/bridge_demo \
  --backend Agg \
  --sha $(git rev-parse HEAD)
<!-- BRIDGE QUICKSTART END -->




> chore/add-v2b-on-main: touch to trigger required checks ($(Get-Date -Format s))rnrn<!-- LOCAL-CI QUICKSTART BEGIN -->
### Local CI quickstart

```powershell
pwsh -NoLogo -NoProfile -File .\run_ci.ps1 -ProjectHook "& .\scripts\smoke.ps1" -OpenIndex
<!-- LOCAL-CI QUICKSTART END -->rnrn<!-- ARTIFACT_HOOKS_BEGIN -->
### Enable Git hooks (one time per clone)

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\EnableRepoHooks.ps1
<!-- ARTIFACT_HOOKS_END -->

<!-- CI HOOKS BEGIN -->
## CI hooks

The repo uses a tiny guard to ensure only **allowed** files are tracked under \.artifacts/\.
You can install a local **pre-commit** hook to catch this early:

\\\powershell
# one-time (Windows)
\#!/usr/bin/env bash
set -euo pipefail
# list staged files under .artifacts
bad=$(git diff --cached --name-only -- .artifacts/ \
  | grep -vE '^\.artifacts/($|\.gitkeep$|index\.html$|ci/($|\.gitkeep$|ci_summary\.json$)|metrics/\.gitkeep$|plots/\.gitkeep$|data/\.gitkeep$|bundles/\.gitkeep$)' || true)
if [ -n "$bad" ]; then
  echo "ERROR: You staged non-allowlisted files in .artifacts/:"
  echo "$bad" | sed 's/^/  - /'
  echo "Only index.html, ci/ci_summary.json, and .gitkeep files are allowed."
  exit 1
fi = @'
pwsh -NoProfile -File scripts/ci.guard-artifacts.ps1
if (\0 -ne 0) { exit \0 }
'@
Set-Content -Path .git/hooks/pre-commit -Value \#!/usr/bin/env bash
set -euo pipefail
# list staged files under .artifacts
bad=$(git diff --cached --name-only -- .artifacts/ \
  | grep -vE '^\.artifacts/($|\.gitkeep$|index\.html$|ci/($|\.gitkeep$|ci_summary\.json$)|metrics/\.gitkeep$|plots/\.gitkeep$|data/\.gitkeep$|bundles/\.gitkeep$)' || true)
if [ -n "$bad" ]; then
  echo "ERROR: You staged non-allowlisted files in .artifacts/:"
  echo "$bad" | sed 's/^/  - /'
  echo "Only index.html, ci/ci_summary.json, and .gitkeep files are allowed."
  exit 1
fi -Encoding ascii
\\\

- Guard script: \scripts/ci.guard-artifacts.ps1\ (tracked-allowlist enforcement)
- Optional: run your local CI script before pushing if you have one.

<!-- CI HOOKS END -->
### Managing allowed .artifacts files

If you intentionally want to keep a new tracked file under `.artifacts/`, update the guard’s allow-list:

```powershell
# Add one or more paths
$paths=@('.artifacts/reports/weekly.csv','.artifacts/reports/summary.json')
# Paste this block in PowerShell
$repo=(git rev-parse --show-toplevel); Set-Location $repo
$gp=Join-Path $repo 'scripts/ci.guard-artifacts.ps1'
$code=Get-Content -Raw $gp; $needle='$allowed = @('
foreach($p in $paths){ if($code -notmatch [regex]::Escape($p)){ $code=$code -replace [regex]::Escape($needle), "$needle`r`n  `"$p`"," } }
Set-Content $gp -Value $code -Encoding utf8
git add -- $gp
git commit -m ("ci(guard): allow {0}" -f ($paths -join ', '))
