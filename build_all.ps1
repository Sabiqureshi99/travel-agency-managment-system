$ErrorActionPreference = "Stop"

Write-Host "Stopping any running TAMS_ERP processes..."
try {
    Get-Process TAMS_ERP -ErrorAction SilentlyContinue | Stop-Process -Force
} catch {}

Write-Host "Running PyInstaller..."
.\venv\Scripts\pyinstaller.exe TAMS_ERP.spec --clean -y

Write-Host "Copying .env..."
Copy-Item -Path ".env" -Destination "dist\TAMS_ERP\.env" -Force

Write-Host "Re-running create_fresh_db.py..."
.\venv\Scripts\python.exe create_fresh_db.py

Write-Host "Ensuring backups and logs directories exist..."
New-Item -ItemType Directory -Force -Path "dist\TAMS_ERP\backups"
New-Item -ItemType Directory -Force -Path "dist\TAMS_ERP\logs"

Write-Host "Running Inno Setup Compiler..."
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" "e:\Customized Travel Agency System\TAMS_ERP_Installer.iss"

Write-Host "All done!"
