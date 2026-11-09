$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$VenvDir = if ($env:AQUA3_VENV) { $env:AQUA3_VENV } else { Join-Path $RootDir ".venv" }
$Python = if ($env:AQUA3_PYTHON) { $env:AQUA3_PYTHON } else { "py" }

if ($Python -eq "py") {
    & py -3.11 -c "import sys; assert sys.version_info >= (3, 10)"
    $PythonArgs = @("-3.11")
} else {
    & $Python -c "import sys; assert sys.version_info >= (3, 10)"
    $PythonArgs = @()
}

Write-Host "Creating AQuA3 environment at $VenvDir"
& $Python @PythonArgs -m venv $VenvDir
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -e "$RootDir[dev]"
& $VenvPython -m aqua3 --check

Write-Host ""
Write-Host "AQuA3 is ready."
Write-Host "Activate it with:"
Write-Host "  $VenvDir\Scripts\Activate.ps1"
Write-Host "Then launch the GUI with: aqua3"
