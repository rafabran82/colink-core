function cc-sim-sweep {
  param(
    [Parameter(Mandatory=$true)][string]$TradesCsv,  # e.g. "100,500,1000"
    [Parameter(Mandatory=$true)][string]$VolCsv,     # e.g. "0.01,0.03"
    [switch]$Show
  )
  $tr = $TradesCsv -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }
  $vo = $VolCsv   -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }

  $args = @('--trades') + $tr + @('--volatility') + $vo
  if ($Show) { $args += '--show' }

  python -m colink_core.sim.run_sweep @args
}
