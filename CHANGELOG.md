## v3.0.0-ci-stable — 2025-11-12

- ci.daily.ps1: rebuilt from scratch for PS5 compatibility, single-run simulation, single-owner dashboard open
- sim.run.py: stable demo output, Windows-safe prints (no emoji); explicit --out default pinned
- ci.embed-latest.ps1: safe helpers, JSON→CSV fallback, stable metrics badge insertion
- Deduped/neutralized all non-canonical openers (.githooks, rebuild_ci.cmd, run_sim.cmd)
- Added robust resolver to open .artifacts\index.html once (absolute path + explorer fallback)


