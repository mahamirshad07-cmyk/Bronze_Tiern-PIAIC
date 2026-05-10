# AI Employee — Bronze Tier Setup Script (Windows PowerShell)
# Run this once to install all dependencies.

Write-Host "=== AI Employee Setup ===" -ForegroundColor Cyan

# Resolve Python — prefer py launcher, fall back to known install path
$python = $null
foreach ($candidate in @("python", "py", "C:\Users\Dell\AppData\Local\Programs\Python\Python313\python.exe")) {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) { $python = $candidate; break }
    if (Test-Path $candidate) { $python = $candidate; break }
}
if (-not $python) {
    Write-Host "[ERROR] Python not found. Install Python 3.13 from python.org first." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Python found: $python" -ForegroundColor Green
& $python --version

# Install core dependencies
Write-Host "`nInstalling dependencies..." -ForegroundColor Cyan
& $python -m pip install watchdog python-dotenv schedule --quiet
Write-Host "[OK] Core dependencies installed." -ForegroundColor Green

# Copy .env.example to .env if not present
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "`n[!] Created .env from template. Edit VAULT_PATH if needed." -ForegroundColor Yellow
} else {
    Write-Host "[OK] .env already exists." -ForegroundColor Green
}

# Confirm vault structure
$vault = "AI_Employee_Vault"
$folders = @("Inbox", "Needs_Action", "Done", "Plans", "Logs", "Pending_Approval", "Approved", "Rejected")
foreach ($f in $folders) {
    New-Item -ItemType Directory -Force -Path "$vault\$f" | Out-Null
}
Write-Host "[OK] Vault folder structure verified." -ForegroundColor Green

Write-Host "`n=== Setup Complete ===" -ForegroundColor Cyan
Write-Host "Next steps:"
Write-Host "  1. Start the watcher:  $python watchers/filesystem_watcher.py"
Write-Host "  2. Drop files into AI_Employee_Vault/Inbox to trigger processing"
Write-Host "  3. In Claude Code, run: /process-inbox"
