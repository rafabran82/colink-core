param(
[Parameter(Mandatory=$true
    [ValidateSet("auto","TkAgg","Agg")]
    [string]$Backend = "auto",)][string]$TradesCsv,
  [Parameter(Mandatory=$true)][string]$VolCsv,
  [int]$Steps = 200,
  [int]$Seed,
  [string]$OutDir = "sim_results",
  [ValidateSet("price","k","both")][string]$Plot = "k",
  [switch]$Show,
  [switch]$Hold
)

$tr = $TradesCsv -split ',' | ForEach-Object { $_.Trim() }
$vo = $VolCsv   -split ',' | ForEach-Object { $_.Trim() }

$args = @(
    "--trades";  ($TradesCsv -split ",") | ForEach-Object { $_.Trim() }
    "--volatility"; ($VolCsv -split ",") | ForEach-Object { $_.Trim() }
)
if ($PSBoundParameters.ContainsKey("Steps"))  { $args += @("--steps",  $Steps) }
if ($PSBoundParameters.ContainsKey("Seed"))   { $args += @("--seed",   $Seed) }
if ($PSBoundParameters.ContainsKey("OutDir")) { $args += @("--outdir", $OutDir) }
if ($PSBoundParameters.ContainsKey("Plot"))   { $args += @("--plot",   $Plot)  }
if ($Show) { $args += "--show" }
if ($Hold) { $args += "--hold" }
if ($PSBoundParameters.ContainsKey("Backend") -and $Backend -ne "auto") {
    $args += @("--backend", $Backend)
}+ $tr +
        @("--volatility") + $vo +
        @("--steps", $Steps, "--outdir", $OutDir, "--plot", $Plot)

if ($PSBoundParameters.ContainsKey('Seed')) { $args += @("--seed", $Seed) }
if ($Show) { $args += "--show" }
if ($Hold) { $args += "--hold" }

python -m colink_core.sim.run_sweep @args

