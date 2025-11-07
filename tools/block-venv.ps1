$ErrorActionPreference = "Stop"
# Block any staged path under .venv/
$staged = git diff --cached --name-only
if ($staged) {
  foreach ($p in $staged) {
    if ($p -like ".venv/*" -or $p -like ".venv\*") {
      Write-Error ".venv is not meant to be committed"
      exit 1
    }
  }
}
exit 0