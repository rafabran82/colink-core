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
