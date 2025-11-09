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



