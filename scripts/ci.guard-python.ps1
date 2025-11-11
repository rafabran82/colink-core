param(
  [string]$Root = "scripts",
  [string[]]$Include = @("*.py")
)
function Invoke-PythonSyntaxGuard {
  param([string]$Root = $Root, [string[]]$Include = $Include)

  $py = (Get-Command python -ErrorAction SilentlyContinue)?.Source
  if (-not $py) { throw "python not found on PATH" }

  $files = foreach ($pat in $Include) { Get-ChildItem -Path $Root -Recurse -Filter $pat -File }
  foreach ($f in $files) {
    & $py -m py_compile $f.FullName 2>$null
    if ($LASTEXITCODE -ne 0) { throw "Syntax error in $($f.FullName)" }
  }
}
Invoke-PythonSyntaxGuard -Root $Root -Include $Include
