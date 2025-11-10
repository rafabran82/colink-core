param(
    [Parameter(Mandatory=$true)][string]$TradesCsv,
    [Parameter(Mandatory=$true)][string]$VolCsv,
    [int]$Steps = 200,
    [int]$Seed,
    [string]$OutDir = "sim_results",
    [ValidateSet("price","k","both")][string]$Plot = "k",
    [ValidateSet("auto","TkAgg","Agg")][string]$Backend = "auto",
    [switch]$Show,
    [switch]$Hold
)

$ErrorActionPreference = "Stop"

# Build CLI args for the Python module (do NOT pass --backend; we use SIM_BACKEND env)
$args = @(
    "--trades";     ($TradesCsv -split ",") | ForEach-Object { $_.Trim() }
    "--volatility"; ($VolCsv   -split ",") | ForEach-Object { $_.Trim() }
)

if ($PSBoundParameters.ContainsKey("Steps"))  { $args += @("--steps",  $Steps) }
if ($PSBoundParameters.ContainsKey("Seed"))   { $args += @("--seed",   $Seed) }
if ($PSBoundParameters.ContainsKey("OutDir")) { $args += @("--outdir", $OutDir) }
if ($PSBoundParameters.ContainsKey("Plot"))   { $args += @("--plot",   $Plot)  }
if ($Show) { $args += "--show" }
if ($Hold) { $args += "--hold" }

# Temporarily set SIM_BACKEND so _get_pyplot() can honor it
$prevSimBackend = $env:SIM_BACKEND
try {
    if ($PSBoundParameters.ContainsKey("Backend") -and $Backend -ne "auto") {
        $env:SIM_BACKEND = $Backend
    } else {
        # Remove to allow auto-select (TkAgg when GUI, Agg when headless)
        Remove-Item Env:SIM_BACKEND -ErrorAction SilentlyContinue
    }

    python -m colink_core.sim.run_sweep @args
}
finally {
    # Restore original env state
    if ($null -ne $prevSimBackend -and $prevSimBackend -ne "") {
        $env:SIM_BACKEND = $prevSimBackend
    } else {
        Remove-Item Env:SIM_BACKEND -ErrorAction SilentlyContinue
    }
}
