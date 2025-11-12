param()

Write-Host "=== Running Bootstrap Self-Test ==="

# Run bootstrap with no execution (just modules)
python -u scripts/xrpl.testnet.bootstrap.py --network testnet --out .artifacts/data/bootstrap | Out-Null

# Now run the internal selftest
$code = python - << 'EOF'
from scripts.xrpl.testnet.bootstrap import _selftest
exit(_selftest())
EOF

if ($LASTEXITCODE -eq 0) {
    Write-Host "🟢 All bootstrap modules OK" -ForegroundColor Green
} else {
    Write-Host "🔴 Bootstrap module error detected" -ForegroundColor Red
}
