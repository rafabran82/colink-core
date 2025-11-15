param (
    [string]$poolsData
)

# Convert the JSON string into PowerShell object
$pools = $poolsData | ConvertFrom-Json

# Output the pools data to a log file or console
$logPath = "C:\Users\sk8br\Desktop\colink-core\colink-dashboard\backend\pools_log.txt"

# Append data to a log file
$pools | Out-File -Append -FilePath $logPath

# Optionally print the data for debugging
Write-Host "Pools Data Logged: $pools"
