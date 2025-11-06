param(
  [Parameter(Mandatory=$true)][string]$TradesCsv,
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

$args = @("--trades") + $tr +
        @("--volatility") + $vo +
        @("--steps", $Steps, "--outdir", $OutDir, "--plot", $Plot)

if ($PSBoundParameters.ContainsKey('Seed')) { $args += @("--seed", $Seed) }
if ($Show) { $args += "--show" }
if ($Hold) { $args += "--hold" }

python -m colink_core.sim.run_sweep @args
