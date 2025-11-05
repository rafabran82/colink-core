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
- **CodeQL (required)**: [![CodeQL/CodeQL (pull_request)](https://github.com/rafabran82/colink-core/actions/workflows/codeql.yml/badge.svg)](https://github.com/rafabran82/colink-core/actions/workflows/codeql.yml)
