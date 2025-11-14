# Create "COLINK Dev Tools" shortcuts on Desktop

$devDir = Join-Path $HOME "Desktop\COLINK Dev Tools"
if (-not (Test-Path $devDir)) {
    New-Item -ItemType Directory -Path $devDir | Out-Null
}

$repoRoot   = "C:\Users\sk8br\Desktop\colink-core"
$iconFile   = Join-Path $repoRoot "assets\colink-icon.ico"

$useCustomIcon = Test-Path $iconFile
$iconLocation  = if ($useCustomIcon) { $iconFile } else { "powershell.exe,0" }

$WshShell = New-Object -ComObject WScript.Shell

function New-ColinkShortcut {
    param(
        [string]$Name,
        [string]$Target,
        [string]$Arguments,
        [string]$WorkingDir
    )

    $shortcutPath = Join-Path $devDir ($Name + ".lnk")
    $sc = $WshShell.CreateShortcut($shortcutPath)
    $sc.TargetPath       = $Target
    $sc.Arguments        = $Arguments
    $sc.WorkingDirectory = $WorkingDir
    $sc.IconLocation     = $iconLocation
    $sc.Save()

    Write-Host "✅ Created shortcut: $shortcutPath"
}

Write-Host "Creating COLINK Dev Tools shortcuts in: $devDir"
if ($useCustomIcon) {
    Write-Host "Using custom icon: $iconFile"
} else {
    Write-Host "Using default PowerShell icon (no custom .ico found)."
}

# 1) Guarded CI
New-ColinkShortcut `
    -Name "COLINK Guarded CI" `
    -Target "pwsh.exe" `
    -Arguments '-NoLogo -NoExit -File "C:\Users\sk8br\Desktop\colink-core\scripts\ci.desktop.launcher.ps1"' `
    -WorkingDir $repoRoot

# 2) Dashboard (index.html)
New-ColinkShortcut `
    -Name "COLINK Dashboard" `
    -Target "explorer.exe" `
    -Arguments '"C:\Users\sk8br\Desktop\colink-core\.artifacts\index.html"' `
    -WorkingDir $repoRoot

# 3) VS Code on repo
New-ColinkShortcut `
    -Name "COLINK VS Code" `
    -Target "pwsh.exe" `
    -Arguments '-NoLogo -NoExit -Command "Set-Location ''C:\Users\sk8br\Desktop\colink-core''; code ."' `
    -WorkingDir $repoRoot

# 4) API backend dev
New-ColinkShortcut `
    -Name "COLINK API Backend" `
    -Target "pwsh.exe" `
    -Arguments '-NoLogo -NoExit -File "C:\Users\sk8br\Desktop\colink-core\scripts\dev.api.launcher.ps1"' `
    -WorkingDir $repoRoot

# 5) Frontend dev
New-ColinkShortcut `
    -Name "COLINK Frontend" `
    -Target "pwsh.exe" `
    -Arguments '-NoLogo -NoExit -File "C:\Users\sk8br\Desktop\colink-core\scripts\dev.frontend.launcher.ps1"' `
    -WorkingDir $repoRoot

# 6) Start Everything launcher
New-ColinkShortcut `
    -Name "COLINK Start Everything" `
    -Target "pwsh.exe" `
    -Arguments '-NoLogo -NoExit -File "C:\Users\sk8br\Desktop\colink-core\scripts\dev.start-all.launcher.ps1"' `
    -WorkingDir $repoRoot

Write-Host ""
Write-Host "🎉 COLINK Dev Tools shortcuts ready on your Desktop."
