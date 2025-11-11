param(
  [Parameter(Mandatory)][string]$IndexPath,
  [Parameter(Mandatory)][string]$ChartRelPath,   # default img src (local)
  [string]$ExtraHtml = "",
  [string]$FooterHtml = "",
  [string]$TimeZoneLabel = "Local time (default)"
)

$tzOptions = @"
<option value="">Local time (default)</option>
<option value="Eastern">Eastern</option>
<option value="Central">Central</option>
<option value="Mountain">Mountain</option>
<option value="Pacific">Pacific</option>
<option value="UTC">UTC</option>
"@

$html = @"
<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<title>Local CI Summary</title>
<style>
 body{font-family:Segoe UI, sans-serif;margin:16px}
 .row{display:flex;gap:10px;align-items:center}
 .tz-table{margin-top:14px}
 .badge{padding:4px 8px;border:1px solid #ddd;border-radius:6px;background:#f6f6f6}
</style>
</head>
<body>
  <p>Generated: $(Get-Date)</p>

  <div class="row">
    <label><b>Timezone:</b></label>
    <select id="tzSelect">$tzOptions</select>
    <button id="tzBtn" class="badge">TZ: $TimeZoneLabel</button>
  </div>

  <h2>Local CI Run Trend</h2>
  <img id="ciChart" src="$ChartRelPath" width="800"/>

  <div id="tablesHost">
    $ExtraHtml
  </div>

  <div style="margin-top:10px;color:#888;font-size:12px">$FooterHtml</div>

<script>
(function(){
  function getParam(name){
    const u = new URL(window.location.href);
    return u.searchParams.get(name) || "";
  }
  function showTable(tz){
    document.querySelectorAll('.tz-table').forEach(div=>{
      div.style.display = (div.getAttribute('data-tz') === tz) ? 'block' : 'none';
    });
  }
  function applyTZ(tz){
    const chart = document.getElementById('ciChart');
    // compute image path from tz
    const stem = 'ci/runs/runs_trend_';
    chart.src = stem + (tz ? tz : 'local') + '.png';
    showTable(tz || '');
    const badge = document.getElementById('tzBtn');
    badge.textContent = 'TZ: ' + (tz || 'Local time (default)');
    const u = new URL(window.location.href);
    if (tz) { u.searchParams.set('tz', tz); } else { u.searchParams.delete('tz'); }
    history.replaceState(null, '', u.toString());
  }

  // init selection
  const initial = getParam('tz');               // "", "Eastern", ...
  const sel = document.getElementById('tzSelect');
  sel.value = initial;
  applyTZ(initial);

  sel.addEventListener('change', ()=>applyTZ(sel.value));
  document.getElementById('tzBtn').addEventListener('click', ()=>applyTZ(sel.value));
})();
</script>
</body>
</html>
"@

Set-Content -Path $IndexPath -Value $html -Encoding utf8
Write-Host "✅ Embedded TZ-enabled index into $IndexPath"
