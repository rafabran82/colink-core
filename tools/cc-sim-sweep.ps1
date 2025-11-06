param(
  [Parameter(Mandatory=$true)][string]$TradesCsv,    # e.g. "100,500,1000"
  [Parameter(Mandatory=$true)][string]$VolCsv,       # e.g. "0.01,0.03"
  [int]$Steps = 200,
  [int]$Seed,
  [string]$OutDir = "sim_results",
  [ValidateSet("price","k","both")][string]$Plot = "k",
  [switch]$Show
)

$tr = $TradesCsv -split ',' | ForEach-Object { $_.Trim() }
$vo = $VolCsv   -split ',' | ForEach-Object { $_.Trim() }

$args = @("--trades") + $tr + @("--volatility") + $vo + @("--steps", $Steps, "--outdir", $OutDir, "--plot", $Plot)
if ($PSBoundParameters.ContainsKey("Seed")) { $args += @("--seed", $Seed) }
if ($Show) { $args += "--show" }

python -m colink_core.sim.run_sweep @args
