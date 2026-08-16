$ErrorActionPreference = "Stop"
$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$distDir = Join-Path $rootDir "dist"
$nsis = "C:\Program Files (x86)\NSIS\makensis.exe"

Write-Host "=== AI QA Platform Build Script ===" -Foreground Cyan

function Step {
  param([string]$msg)
  Write-Host "`n>>> $msg" -Foreground Yellow
}

# --- Checks ---
if (-not (Test-Path -LiteralPath $nsis)) {
  Write-Host "ERROR: NSIS not found at $nsis" -Foreground Red; exit 1
}

# --- Clean ---
Step "Cleaning previous builds..."
foreach ($d in @($distDir, (Join-Path $rootDir "build"), (Join-Path $rootDir "dist-electron"))) {
  if (Test-Path -LiteralPath $d) { Remove-Item -Recurse -Force -LiteralPath $d }
}
$null = New-Item -ItemType Directory -Force -Path $distDir
$null = New-Item -ItemType Directory -Force -Path (Join-Path $rootDir "dist-electron")

# --- Step 1: Bundle Python desktop app ---
Step "1/2: Bundling AI QA Platform with PyInstaller..."
Push-Location $rootDir
try {
  pyinstaller --onefile --name "AI QA Platform" `
    --add-data "backend/agents/skills;backend/agents/skills" `
    --hidden-import uvicorn.logging `
    --hidden-import uvicorn.loops `
    --hidden-import uvicorn.loops.auto `
    --hidden-import uvicorn.protocols `
    --hidden-import uvicorn.protocols.http `
    --hidden-import uvicorn.protocols.http.auto `
    --hidden-import uvicorn.protocols.websockets `
    --hidden-import uvicorn.protocols.websockets.auto `
    --hidden-import uvicorn.lifespan `
    --hidden-import uvicorn.lifespan.on `
    --collect-all playwright `
    desktop_app.py
  if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }
} finally { Pop-Location }

# --- Step 2: Create NSIS installer ---
Step "2/2: Creating NSIS installer..."
$exePath = Join-Path $distDir "AI QA Platform.exe"
if (-not (Test-Path -LiteralPath $exePath)) {
  Write-Host "ERROR: PyInstaller did not produce $exePath" -Foreground Red; exit 1
}

$nsi = Join-Path $rootDir "dist-electron\installer.nsi"
@"
Unicode True
RequestExecutionLevel user

!define PRODUCT_NAME "AI QA Platform"
!define PRODUCT_VERSION "1.0.0"
!define PRODUCT_PUBLISHER "AI QA Team"

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "$rootDir\dist-electron\AI-QA-Platform-Setup.exe"
InstallDir "`$LOCALAPPDATA\${PRODUCT_NAME}"
InstallDirRegKey HKCU "Software\${PRODUCT_NAME}" ""

Section "Install"
  SetOutPath "`$INSTDIR"
  File "$exePath"
  WriteUninstaller "`$INSTDIR\uninstall.exe"
  CreateShortCut "`$DESKTOP\${PRODUCT_NAME}.lnk" "`$INSTDIR\AI QA Platform.exe"
  CreateDirectory "`$SMPROGRAMS\${PRODUCT_NAME}"
  CreateShortCut "`$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk" "`$INSTDIR\AI QA Platform.exe"
  CreateShortCut "`$SMPROGRAMS\${PRODUCT_NAME}\Uninstall.lnk" "`$INSTDIR\uninstall.exe"
  WriteRegStr HKCU "Software\${PRODUCT_NAME}" "" "`$INSTDIR"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayName" "${PRODUCT_NAME}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "UninstallString" "`$INSTDIR\uninstall.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "Publisher" "${PRODUCT_PUBLISHER}"
SectionEnd

Section "Uninstall"
  Delete "`$DESKTOP\${PRODUCT_NAME}.lnk"
  RMDir /r "`$SMPROGRAMS\${PRODUCT_NAME}"
  RMDir /r "`$INSTDIR"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
  DeleteRegKey HKCU "Software\${PRODUCT_NAME}"
SectionEnd
"@ | Set-Content -Path $nsi -Encoding ASCII

& $nsis $nsi
if ($LASTEXITCODE -ne 0) { throw "NSIS installer creation failed" }

$setup = Join-Path $rootDir "dist-electron\AI-QA-Platform-Setup.exe"
$size = (Get-Item -LiteralPath $setup).Length / 1MB
Write-Host "`n=== Build complete! ===" -Foreground Green
Write-Host "Standalone EXE: $exePath" -Foreground Green
Write-Host "Installer: $setup ($([math]::Round($size, 0)) MB)" -Foreground Green
