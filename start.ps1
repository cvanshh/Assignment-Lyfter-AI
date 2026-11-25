$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not (Test-Path "$root\.env")) {
    Copy-Item "$root\.env.example" "$root\.env"
}

$backendProc = Start-Process -FilePath "$root\backend\.venv\Scripts\python.exe" `
    -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000" `
    -WorkingDirectory "$root\backend" -PassThru

$npm = Get-Command npm -ErrorAction SilentlyContinue
if ($npm) {
    $frontendProc = Start-Process -FilePath $npm.Source `
        -ArgumentList "run", "dev", "--", "--port", "3000" `
        -WorkingDirectory "$root\frontend" -PassThru
} else {
    Write-Host "Node/npm not found in PATH; serving prebuilt frontend/dist via Python HTTP server..."
    $frontendProc = Start-Process -FilePath "$root\backend\.venv\Scripts\python.exe" `
        -ArgumentList "-m", "http.server", "3000", "--bind", "127.0.0.1", "--directory", "$root\frontend\dist" `
        -WorkingDirectory "$root" -PassThru
}

Write-Host "Backend running on  http://localhost:8000/health (PID $($backendProc.Id))"
Write-Host "Frontend running on http://localhost:3000        (PID $($frontendProc.Id))"
Write-Host "Press Ctrl+C to stop (or close the spawned windows)."
try {
    Wait-Process -Id $backendProc.Id, $frontendProc.Id
} finally {
    Stop-Process -Id $backendProc.Id, $frontendProc.Id -ErrorAction SilentlyContinue
}
