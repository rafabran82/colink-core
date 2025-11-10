# --- Phase-25: Emit samples (optional, headless-safe) ---
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

$Root = if ($env:GITHUB_WORKSPACE) { $env:GITHUB_WORKSPACE } else { (git rev-parse --show-toplevel) }
$Out  = Join-Path $Root ".artifacts"
if (-not (Test-Path $Out)) { New-Item -ItemType Directory -Force -Path $Out | Out-Null }

# Prefer venv python
$Vpy = Join-Path $Root ".venv\Scripts\python.exe"
$python = if (Test-Path $Vpy) { $Vpy } else { (Get-Command python -ErrorAction SilentlyContinue)?.Source }
if (-not $python) {
  Write-Warning "python not found; skipping sample emission."
  exit 0
}

# Ensure matplotlib is present (no fail if install misses)
try {
  & $python -c "import importlib; importlib.import_module('matplotlib'); print('matplotlib OK')" 2>$null
} catch {
  Write-Host "Installing matplotlib for sample emission..."
  try { & $python -m pip install matplotlib | Out-Null } catch { Write-Warning "Could not install matplotlib; skipping."; exit 0 }
}

# Emit a PNG + JSON safely (Agg backend)
$py = @"
import os, json
os.environ['MPLBACKEND'] = 'Agg'
from pathlib import Path
from math import sin
import matplotlib.pyplot as plt

out = Path(r'$Out')
out.mkdir(parents=True, exist_ok=True)

# simple plot
x = [i/50 for i in range(0, 501)]
y = [sin(6.28318530718 * t) for t in x]
plt.figure()
plt.plot(x, y)
plt.title('CI sample')
plt.xlabel('t'); plt.ylabel('sin(2πt)')
plt.savefig(out / 'sample.png', dpi=120)
plt.close()

# simple metrics
m = {'points': len(x), 'min': min(y), 'max': max(y)}
(out / 'sample.json').write_text(json.dumps(m, indent=2))
print('Emitted:', (out / 'sample.png'), (out / 'sample.json'))
"@

$tmp = [IO.Path]::Combine([IO.Path]::GetTempPath(), "emit_{0}.py" -f ([guid]::NewGuid()))
[IO.File]::WriteAllText($tmp, $py, [Text.Encoding]::UTF8)

try {
  & $python $tmp
} catch {
  Write-Warning "Sample emission failed, but step is optional. Error: $($_.Exception.Message)"
  # do not fail
  exit 0
} finally {
  Remove-Item -Force $tmp -ErrorAction SilentlyContinue
}

Write-Host "Phase-25 complete."
exit 0
