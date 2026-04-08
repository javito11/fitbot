#!/usr/bin/env sh
cd "$(dirname "$0")"
if command -v uv >/dev/null 2>&1; then
    uv run python ui/app.py
else
    python3 ui/app.py
fi
