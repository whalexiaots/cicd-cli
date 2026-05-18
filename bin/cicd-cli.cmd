@echo off
REM cicd-cli 入口脚本 (Windows CMD)
REM 用法: cicd-cli <service> [+shortcut|command] [flags]

setlocal

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

cd /d "%PROJECT_ROOT%"

if exist "%PROJECT_ROOT%\.venv\Scripts\activate.bat" (
    call "%PROJECT_ROOT%\.venv\Scripts\activate.bat"
)

python -m core.cli %*
