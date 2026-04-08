@echo off
where uv >nul 2>&1
if %errorlevel% == 0 (
    uv run python ui/app.py
) else (
    python ui/app.py
)
