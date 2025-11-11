@echo off
setlocal
pushd %~dp0

REM Rebuild charts/tables for Local/Eastern/Central/Mountain/Pacific/UTC, then embed and open index.
pwsh -NoProfile -Command ^
  "$log='.artifacts\ci\runs\runs_log.csv';$runs='.artifacts\ci\runs';$idx='.artifacts\index.html';" ^
  "$tz=@(@{Id=$null;Suffix='local';Sel='local'},@{Id='Eastern Standard Time';Suffix='Eastern';Sel='eastern'},@{Id='Central Standard Time';Suffix='Central';Sel='central'},@{Id='Mountain Standard Time';Suffix='Mountain';Sel='mountain'},@{Id='Pacific Standard Time';Suffix='Pacific';Sel='pacific'},@{Id='UTC';Suffix='UTC';Sel='utc'});" ^
  "$tables=@(); foreach($t in $tz){ $csv= if($t.Id){(& powershell -NoProfile -ExecutionPolicy Bypass -File 'scripts\ci.tz.convert.ps1' -InCsv $log -ToTz $t.Id 2>&1 | ?{ $_ -is [string] -and ($_ -match '\.csv$') } | select -Last 1).ToString().Trim()} else { $log };" ^
  "$png=Join-Path $runs ('runs_trend_{0}.png' -f $t.Suffix); python scripts/ci.plot.py --csv $csv --out $png | Out-Null;" ^
  "$tbl=& scripts\ci.table.ps1 -RunsLog $csv -Count 5; $tables += \"<div class='tz-table' data-tz='$($t.Sel)' style='display:none'>$tbl</div>\" };" ^
  "& scripts\ci.embed.ps1 -IndexPath $idx -ChartRelPath 'ci/runs/runs_trend_local.png' -ExtraHtml ($tables -join \"`r`n\") -TimeZoneLabel 'Local time (default)' -FooterHtml '<div style=''margin-top:10px;color:#888;font-size:12px''>Use rebuild_ci.cmd to refresh without adding a new run.</div>'" ^
  "; Start-Process $idx"

popd
endlocal
