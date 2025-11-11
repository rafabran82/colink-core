Param()

$ErrorActionPreference = "Stop"$allowed = @(
".artifacts/.gitkeep",
".artifacts/index.html",
".artifacts/ci/.gitkeep",
".artifacts/ci/ci_summary.json",
".artifacts/metrics/.gitkeep",
".artifacts/plots/.gitkeep",
".artifacts/data/.gitkeep",
".artifacts/bundles/.gitkeep"
)

$tracked = (git ls-files .artifacts) | ForEach-Object { $.Trim() } | Where-Object { $ }
$bad = $tracked | Where-Object { $_ -notin $allowed }

if ($bad) {
Write-Error ("Non-allowlisted tracked files under .artifacts/:n - " + ($bad -join "n - "))
exit 1
}
Write-Host "Artifact guard OK."
