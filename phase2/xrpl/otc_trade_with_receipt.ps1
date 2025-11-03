param(
  [Parameter(Mandatory=$true)][decimal]$QtyCOPX,
  [Parameter(Mandatory=$true)][decimal]$PriceXRP,
  [Parameter(Mandatory=$true)][decimal]$Slippage
)
param(
  [Parameter(Mandatory=$true)][decimal]$QtyCOPX,
  [Parameter(Mandatory=$true)][decimal]$PriceXRP,
  [Parameter(Mandatory=$true)][decimal]$Slippage
)

Import-Module xrpay -ErrorAction SilentlyContinue | Out-Null

$Worst    = $PriceXRP * (1+$Slippage)
$CapDrops = [int]([math]::Ceiling($QtyCOPX * $Worst * 1000000)) + 20
Write-Warning "Cap drops = $CapDrops at worst=$Worst XRP/COPX"

$before = python .\phase2\xrpl\tools\show_balances.py | Out-String

$env:OTC_XRP_DROPS = "$CapDrops"
$j1 = python .\phase2\xrpl\otc_step1_taker_pays_xrp.py | Out-String
try { $p1 = $j1 | ConvertFrom-Json -ErrorAction Stop } catch { throw "STEP1 not JSON: `n$j1" }
if (-not $p1.engine_result) { throw "STEP1 missing engine_result (hash=$($p1.hash))" }
if ($p1.engine_result -ne 'tesSUCCESS') { throw "STEP1 engine_result=$($p1.engine_result) hash=$($p1.hash)" }

$env:OTC_COPX_QTY = "$QtyCOPX"
$j2 = python .\phase2\xrpl\otc_step2_issuer_pays_copx.py | Out-String
try { $p2 = $j2 | ConvertFrom-Json -ErrorAction Stop } catch { throw "STEP2 not JSON: `n$j2" }
if (-not $p2.engine_result) { throw "STEP2 missing engine_result (hash=$($p2.hash))" }
if ($p2.engine_result -ne 'tesSUCCESS') { throw "STEP2 engine_result=$($p2.engine_result) hash=$($p2.hash)" }

$after = python .\phase2\xrpl\tools\show_balances.py | Out-String

$receipt = [ordered]@{
  timestamp    = (Get-Date).ToString("s")
  qty_copx     = "$QtyCOPX"
  price_xrp    = "$PriceXRP"
  slippage     = "$Slippage"
  cap_drops    = $CapDrops
  step1        = [ordered]@{
    engine_result = $p1.engine_result
    hash          = $p1.hash
    fee_drops     = $p1.fee_drops
    xrp_drops_sent= $p1.xrp_drops_sent
  }
  step2        = [ordered]@{
    engine_result = $p2.engine_result
    hash          = $p2.hash
    fee_drops     = $p2.fee_drops
    issuer_sent   = $p2.issuer_sent
  }
  balances     = [ordered]@{
    before = ($before | ConvertFrom-Json)
    after  = ($after  | ConvertFrom-Json)
  }
}

$dir = ".\phase2\xrpl\otc_receipts"
if (!(Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
$name = "otc-$((Get-Date).ToString('yyyyMMdd-HHmmss')).json"
$path = Join-Path $dir $name
$receipt | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 $path
Write-Host "Saved receipt:`n$path"

_oldWarnPref = $WarningPreference
try {
  $WarningPreference = 'SilentlyContinue'
  Import-Module xrpay -DisableNameChecking -ErrorAction SilentlyContinue
} finally {
  $WarningPreference = param(
  [Parameter(Mandatory=$true)][decimal]$QtyCOPX,
  [Parameter(Mandatory=$true)][decimal]$PriceXRP,
  [Parameter(Mandatory=$true)][decimal]$Slippage
)

Import-Module xrpay -ErrorAction SilentlyContinue | Out-Null

$Worst    = $PriceXRP * (1+$Slippage)
$CapDrops = [int]([math]::Ceiling($QtyCOPX * $Worst * 1000000)) + 20
Write-Warning "Cap drops = $CapDrops at worst=$Worst XRP/COPX"

$before = python .\phase2\xrpl\tools\show_balances.py | Out-String

$env:OTC_XRP_DROPS = "$CapDrops"
$j1 = python .\phase2\xrpl\otc_step1_taker_pays_xrp.py | Out-String
try { $p1 = $j1 | ConvertFrom-Json -ErrorAction Stop } catch { throw "STEP1 not JSON: `n$j1" }
if (-not $p1.engine_result) { throw "STEP1 missing engine_result (hash=$($p1.hash))" }
if ($p1.engine_result -ne 'tesSUCCESS') { throw "STEP1 engine_result=$($p1.engine_result) hash=$($p1.hash)" }

$env:OTC_COPX_QTY = "$QtyCOPX"
$j2 = python .\phase2\xrpl\otc_step2_issuer_pays_copx.py | Out-String
try { $p2 = $j2 | ConvertFrom-Json -ErrorAction Stop } catch { throw "STEP2 not JSON: `n$j2" }
if (-not $p2.engine_result) { throw "STEP2 missing engine_result (hash=$($p2.hash))" }
if ($p2.engine_result -ne 'tesSUCCESS') { throw "STEP2 engine_result=$($p2.engine_result) hash=$($p2.hash)" }

$after = python .\phase2\xrpl\tools\show_balances.py | Out-String

$receipt = [ordered]@{
  timestamp    = (Get-Date).ToString("s")
  qty_copx     = "$QtyCOPX"
  price_xrp    = "$PriceXRP"
  slippage     = "$Slippage"
  cap_drops    = $CapDrops
  step1        = [ordered]@{
    engine_result = $p1.engine_result
    hash          = $p1.hash
    fee_drops     = $p1.fee_drops
    xrp_drops_sent= $p1.xrp_drops_sent
  }
  step2        = [ordered]@{
    engine_result = $p2.engine_result
    hash          = $p2.hash
    fee_drops     = $p2.fee_drops
    issuer_sent   = $p2.issuer_sent
  }
  balances     = [ordered]@{
    before = ($before | ConvertFrom-Json)
    after  = ($after  | ConvertFrom-Json)
  }
}

$dir = ".\phase2\xrpl\otc_receipts"
if (!(Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
$name = "otc-$((Get-Date).ToString('yyyyMMdd-HHmmss')).json"
$path = Join-Path $dir $name
$receipt | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 $path
Write-Host "Saved receipt:`n$path"

_oldWarnPref
}

$Worst    = $PriceXRP * (1+$Slippage)
$CapDrops = [int]([math]::Ceiling($QtyCOPX * $Worst * 1000000)) + 20
Write-Warning "Cap drops = $CapDrops at worst=$Worst XRP/COPX"

$before = python .\phase2\xrpl\tools\show_balances.py | Out-String

$env:OTC_XRP_DROPS = "$CapDrops"
$j1 = python .\phase2\xrpl\otc_step1_taker_pays_xrp.py | Out-String
try { $p1 = $j1 | ConvertFrom-Json -ErrorAction Stop } catch { throw "STEP1 not JSON: `n$j1" }
if (-not $p1.engine_result) { throw "STEP1 missing engine_result (hash=$($p1.hash))" }
if ($p1.engine_result -ne 'tesSUCCESS') { throw "STEP1 engine_result=$($p1.engine_result) hash=$($p1.hash)" }

$env:OTC_COPX_QTY = "$QtyCOPX"
$j2 = python .\phase2\xrpl\otc_step2_issuer_pays_copx.py | Out-String
try { $p2 = $j2 | ConvertFrom-Json -ErrorAction Stop } catch { throw "STEP2 not JSON: `n$j2" }
if (-not $p2.engine_result) { throw "STEP2 missing engine_result (hash=$($p2.hash))" }
if ($p2.engine_result -ne 'tesSUCCESS') { throw "STEP2 engine_result=$($p2.engine_result) hash=$($p2.hash)" }

$after = python .\phase2\xrpl\tools\show_balances.py | Out-String

$receipt = [ordered]@{
  timestamp    = (Get-Date).ToString("s")
  qty_copx     = "$QtyCOPX"
  price_xrp    = "$PriceXRP"
  slippage     = "$Slippage"
  cap_drops    = $CapDrops
  step1        = [ordered]@{
    engine_result = $p1.engine_result
    hash          = $p1.hash
    fee_drops     = $p1.fee_drops
    xrp_drops_sent= $p1.xrp_drops_sent
  }
  step2        = [ordered]@{
    engine_result = $p2.engine_result
    hash          = $p2.hash
    fee_drops     = $p2.fee_drops
    issuer_sent   = $p2.issuer_sent
  }
  balances     = [ordered]@{
    before = ($before | ConvertFrom-Json)
    after  = ($after  | ConvertFrom-Json)
  }
}

$dir = ".\phase2\xrpl\otc_receipts"
if (!(Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
$name = "otc-$((Get-Date).ToString('yyyyMMdd-HHmmss')).json"
$path = Join-Path $dir $name
$receipt | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 $path
Write-Host "Saved receipt:`n$path"



