param(
  [Parameter(Mandatory)]
  [string]$IndexPath,
  [Parameter(Mandatory)]
  [string]$ChartRelPath,
  [string]$ExtraHtml = "",
  [string]$FooterHtml = "",
  [string]$TimeZoneLabel = "Local time (default)"
)

# Build HTML with a TZ dropdown that reloads index.html using ?tz=<zone>
$html = @"
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Local CI Summary</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body { font-family: Segoe UI, system-ui, -apple-system, Roboto, sans-serif; margin: 16px; }
    h1 { margin: 6px 0 12px; }
    h3 { margin: 18px 0 8px; }
    .row { display: flex; gap: 14px; align-items: center; flex-wrap: wrap; }
    .tz { font-size: 14px; }
    .badge { background:#f3f4f6; border:1px solid #e5e7eb; border-radius:8px; padding:6px 10px; }
    select { padding:6px 8px; border-radius:6px; border:1px solid #d1d5db; }
    .chart { margin-top:12px; }
    .foot { margin-top:18px; color:#6b7280; font-size:13px; }
  </style>
</head>
<body>
  <h1>Local CI Summary</h1>
  <p>Generated: $(Get-Date)</p>

  <div class="row tz">
    <label for="tzSelect"><strong>Timezone:</strong></label>
    <select id="tzSelect" aria-label="Timezone">
      <option value="">Local time (default)</option>
      <option value="Eastern">Eastern</option>
      <option value="Central">Central</option>
      <option value="Mountain">Mountain</option>
      <option value="Pacific">Pacific</option>
      <option value="UTC">UTC</option>
    </select>
    <span id="tzBadge" class="badge">TZ: $TimeZoneLabel</span>
  </div>

  <h3>Local CI Run Trend</h3>
  <div class="chart">
    <img src="$ChartRelPath" width="600" />
  </div>

  <div id="extra" style="margin-top:18px;">$ExtraHtml</div>
  <div class="foot">$FooterHtml</div>

  <script>
    // Read ?tz= param
    const params = new URLSearchParams(location.search);
    const tz = (params.get("tz") || "").trim();

    const sel = document.getElementById("tzSelect");
    const badge = document.getElementById("tzBadge");

    // Preselect dropdown
    Array.from(sel.options).forEach(opt => {
      if ((opt.value || "") === tz) opt.selected = true;
    });

    // Human label map for badge
    const labelMap = {
      "": "Local time (default)",
      "Eastern": "Eastern",
      "Central": "Central",
      "Mountain": "Mountain",
      "Pacific": "Pacific",
      "UTC": "UTC"
    };
    badge.textContent = "TZ: " + (labelMap[tz] ?? "Local time (default)");

    // On change → reload with ?tz=<zone>
    sel.addEventListener("change", () => {
      const v = sel.value;
      const url = new URL(location.href);
      if (v) { url.searchParams.set("tz", v); }
      else   { url.searchParams.delete("tz"); }
      location.href = url.toString();
    });
  </script>
</body>
</html>
"@

Set-Content -Path $IndexPath -Value $html -Encoding utf8
Write-Host "✅ Embedded trend chart into $IndexPath"
