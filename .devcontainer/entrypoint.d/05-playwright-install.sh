#!/bin/bash
if command -v uv >/dev/null 2>&1; then
    uv run playwright install chromium --with-deps 2>/dev/null || true
fi
