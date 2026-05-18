#!/usr/bin/env pwsh
# cicd-cli 入口脚本 (Windows PowerShell)
# 用法: cicd-cli <service> [+shortcut|command] [flags]

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Set-Location $ProjectRoot

$VenvActivate = Join-Path $ProjectRoot ".venv" "Scripts" "Activate.ps1"
if (Test-Path $VenvActivate) {
    & $VenvActivate
}

python -m core.cli @args
