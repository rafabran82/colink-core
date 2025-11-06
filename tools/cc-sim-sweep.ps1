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

# Build args for the Python module
$args = @()
$args += "--trades"
$args += ($TradesCsv -split "," | ForEach-Object { $_.Trim() })
$args += "--volatility"
$args += ($VolCsv -split "," | ForEach-Object { $_.Trim() })

if ($PSBoundParameters.ContainsKey("Steps"))  { $args += @("--steps",  $Steps) }
if ($PSBoundParameters.ContainsKey("Seed"))   { $args += @("--seed",   $Seed) }
if ($PSBoundParameters.ContainsKey("OutDir")) { $args += @("--outdir", $OutDir) }
if ($PSBoundParameters.ContainsKey("Plot"))   { $args += @("--plot",   $Plot)  }
if ($Show) { $args += "--show" }
if ($Hold) { $args += "--hold" }
if ($PSBoundParameters.ContainsKey("Backend") -and $Backend -ne "auto") {
    $args += @("--backend", $Backend)
}

python -m colink_core.sim.run_sweep @args
