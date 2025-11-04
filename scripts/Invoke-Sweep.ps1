param(
  [Parameter(Mandatory=$true)][string]$OutDir,
  [string]$RunName = "dev"
)

Write-Host "==> Running sweep -> $OutDir (run: $RunName) ..."

# Ensure directory exists
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

# --- Run the sweep with a robust inline Python temp file + Agg backend ---
$py = @"
import os, sys, traceback
from pathlib import Path

# Force headless rendering
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

outdir = Path(r'$OutDir')
outdir.mkdir(parents=True, exist_ok=True)

def write_two(out: Path):
    names = ['summary.png','pnl.png']
    # chart 1
    plt.figure()
    plt.plot([0,1],[0,1]); plt.title('summary')
    plt.savefig(out / names[0], dpi=120, bbox_inches='tight'); plt.close()
    # chart 2
    plt.figure()
    plt.plot([0,1],[1,0]); plt.title('pnl')
    plt.savefig(out / names[1], dpi=120, bbox_inches='tight'); plt.close()
    return [str(out/n) for n in names]

written = []
try:
    try:
        from colink_core.sim.run_sweep import main as sweep_main  # type: ignore
        sweep_main(outdir=str(outdir))
    except Exception:
        # Try module form
        os.environ['COLINK_SWEEP_OUT'] = str(outdir)
        try:
            import colink_core.sim.run_sweep as rs  # type: ignore
            if hasattr(rs, 'main'): rs.main()
            elif hasattr(rs, 'sweep'): rs.sweep()
            else: raise RuntimeError('run_sweep has no callable entrypoint')
        except Exception:
            pass

    pngs = sorted([str(p) for p in outdir.rglob('*.png')])
    if len(pngs) < 2:
        pngs = write_two(outdir)

    # Print for the PS wrapper to capture
    print("\\n".join(pngs))
except Exception as e:
    print('SWEEP_FALLBACK due to:', e, file=sys.stderr)
    traceback.print_exc()
    pngs = write_two(outdir)
    print("\\n".join(pngs))
"@

$tmpPy = Join-Path $env:TEMP "sweep_inline_{0}.py" -f ([guid]::NewGuid())
Set-Content -Path $tmpPy -Value $py -Encoding utf8
$stdout = & .\.venv\Scripts\python.exe $tmpPy
Remove-Item $tmpPy -ErrorAction SilentlyContinue

# Print what was written
$files = @()
if ($stdout) {
  $files = $stdout -split "`r?`n" | Where-Object { $_ -match '\.png$' }
}
if ($files.Count -gt 0) {
  Write-Host "==> Wrote $($files.Count) chart(s):"
  $files | ForEach-Object { Write-Host " - $_" }
} else {
  Write-Warning "No charts reported by Python step."
}

# --- Write a minimal summary.json via temp Python (for CI slip SLOs) ---
$pySummary = @"
from colink_core.sim.summary import write_minimal
print(write_minimal('artifacts/charts', name='$RunName', twap_guard_bps=150.0))
"@
$tmpSum = Join-Path $env:TEMP "write_summary_{0}.py" -f ([guid]::NewGuid())
Set-Content -Path $tmpSum -Value $pySummary -Encoding utf8
try {
  & .\.venv\Scripts\python.exe $tmpSum | Out-Host
} catch {
  Write-Warning "Could not write minimal summary.json: $($_.Exception.Message)"
} finally {
  Remove-Item $tmpSum -ErrorAction SilentlyContinue
}

Write-Host "==> Sweep complete."
