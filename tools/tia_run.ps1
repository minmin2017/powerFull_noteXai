# Elevated runner for tia_tool.py — avoids repeating the Start-Process/RunAs
# boilerplate every time. Captures output and prints it back to the caller.
#
# Usage: powershell -File tia_run.ps1 <tia_tool.py args...>
# Example: powershell -File tia_run.ps1 shot
#          powershell -File tia_run.ps1 focus
#          powershell -File tia_run.ps1 click 500 300 --double

param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ToolArgs
)

$toolPath = Join-Path $PSScriptRoot "tia_tool.py"
$outFile = Join-Path $env:TEMP "tia_run_out.txt"

$argsStr = ($ToolArgs | ForEach-Object { "`"$_`"" }) -join " "
$cmd = "python `"$toolPath`" $argsStr > `"$outFile`" 2>&1"

Start-Process powershell -Verb RunAs -WindowStyle Hidden `
    -ArgumentList "-NoProfile", "-Command", $cmd -Wait

Get-Content $outFile
