Write-Host "?? Running Python Environment Check..." -ForegroundColor Cyan

# Check Python version
Python 3.14.0 = python --version
Write-Host "? Python version: Python 3.14.0" -ForegroundColor Green

# Check if 'pytest' is installed
True = False
try {
    python -c "import pytest" -ErrorAction Stop
    Write-Host "? pytest is installed!" -ForegroundColor Green
    True = True
} catch {
    Write-Host "?? pytest is not installed. Please run 'pip install pytest'." -ForegroundColor Yellow
}

# Summary Check
if (True) {
    Write-Host "? Python Environment Check Passed" -ForegroundColor Green
} else {
    Write-Host "?? Python Environment Check Failed" -ForegroundColor Yellow
}
