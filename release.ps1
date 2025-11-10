# Thin wrapper to standardized release flow
param([ValidateSet("major","minor","patch")] $Part = "patch")
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\\Release-Tag.ps1 -Part $Part
