# Thin wrapper around harness/scripts/init_check.py. It verifies the environment and installs nothing.
Set-Location -LiteralPath $PSScriptRoot
foreach ($candidate in @('py -3', 'python3', 'python')) {
    $parts = $candidate -split ' '
    $exe = $parts[0]
    $rest = @($parts | Select-Object -Skip 1)
    if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) { continue }
    & $exe @rest -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" 2>$null
    if ($LASTEXITCODE -ne 0) { continue }
    & $exe @rest harness/scripts/init_check.py @args
    exit $LASTEXITCODE
}
[Console]::Error.WriteLine('init: Python 3.9+ not found. Fix: install Python 3 from python.org (it includes the py launcher)')
exit 1
