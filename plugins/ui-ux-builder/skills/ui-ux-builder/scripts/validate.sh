#!/usr/bin/env bash
# Validate that the ui-ux-builder screenshot tool and its dependencies work correctly.
# Usage: ./validate.sh [url] [python_path]

set -euo pipefail

PASSED=0
FAILED=0
TMPFILES=()

cleanup() {
    for f in "${TMPFILES[@]}"; do
        rm -f "$f"
    done
}
trap cleanup EXIT

pass() { echo "  PASS: $1"; PASSED=$((PASSED + 1)); }
fail() { echo "  FAIL: $1"; FAILED=$((FAILED + 1)); }

# --- Resolve project root ---
find_project_root() {
    local dir
    dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    while [ "$dir" != "/" ]; do
        if [ -d "$dir/.claude" ] || [ -f "$dir/package.json" ] || [ -f "$dir/pyproject.toml" ] || [ -d "$dir/.git" ]; then
            echo "$dir"
            return
        fi
        dir="$(dirname "$dir")"
    done
    # Fallback: two levels up from scripts/
    echo "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
}

# --- Resolve python ---
find_python() {
    local root="$1"
    # 1. PYTHON env var
    if [ -n "${PYTHON:-}" ] && command -v "$PYTHON" &>/dev/null; then
        echo "$PYTHON"; return
    fi
    # 2. CLI argument
    if [ -n "${2:-}" ] && command -v "$2" &>/dev/null; then
        echo "$2"; return
    fi
    # 3. Project venvs
    for venv in "$root/venv" "$root/.venv" "$root"/venv_*; do
        if [ -x "$venv/bin/python" ]; then
            echo "$venv/bin/python"; return
        fi
    done
    # 4. System python3
    if command -v python3 &>/dev/null; then
        echo "python3"; return
    fi
    echo ""
}

PROJECT_ROOT="$(find_project_root)"
echo "Project root: $PROJECT_ROOT"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOL="$SCRIPT_DIR/screenshot.py"

URL="${1:-}"
PYTHON_ARG="${2:-}"
PYTHON_BIN="$(find_python "$PROJECT_ROOT" "$PYTHON_ARG")"

echo ""
echo "=== ui-ux-builder validation ==="
echo ""

# --- Check 1: Python binary ---
echo "1. Python binary"
if [ -n "$PYTHON_BIN" ] && command -v "$PYTHON_BIN" &>/dev/null; then
    pass "Found python at: $PYTHON_BIN ($($PYTHON_BIN --version 2>&1))"
else
    fail "No usable python found"
    echo "  Install Python 3.10+ or set PYTHON env var"
    exit 1
fi

# --- Check 2: Playwright importable ---
echo "2. Playwright import"
if $PYTHON_BIN -c "import playwright" 2>/dev/null; then
    pass "playwright is importable"
else
    fail "playwright is not installed"
    echo "  Run: $PYTHON_BIN -m pip install playwright && $PYTHON_BIN -m playwright install chromium"
fi

# --- Check 3: Chromium browser ---
echo "3. Chromium browser"
if $PYTHON_BIN -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    browser.close()
    print('ok')
" 2>/dev/null | grep -q "ok"; then
    pass "Chromium launches and closes"
else
    fail "Chromium browser failed to launch"
    echo "  Run: $PYTHON_BIN -m playwright install chromium"
fi

# --- Check 4: Screenshot capture ---
echo "4. Screenshot capture"
TMPSHOT=$(mktemp /tmp/validate_screenshot_XXXXXX.png)
TMPFILES+=("$TMPSHOT")

if [ -n "$URL" ]; then
    TEST_URL="$URL"
else
    # Use inline HTML via data URI
    TEST_URL="data:text/html,<html><head><title>Test</title></head><body><h1>Validation Test</h1><p>This is a test page.</p></body></html>"
fi

if $PYTHON_BIN "$TOOL" "$TEST_URL" -o "$TMPSHOT" --wait 1 2>/dev/null && [ -s "$TMPSHOT" ]; then
    pass "Screenshot captured ($(wc -c < "$TMPSHOT" | tr -d ' ') bytes)"
else
    fail "Screenshot capture failed"
fi

# --- Check 5: Structure output ---
echo "5. Page structure (--structure)"
TMPJSON=$(mktemp /tmp/validate_structure_XXXXXX.json)
TMPFILES+=("$TMPJSON")

if $PYTHON_BIN "$TOOL" "$TEST_URL" --structure --wait 1 > "$TMPJSON" 2>/dev/null; then
    if $PYTHON_BIN -c "
import json, sys
data = json.load(open('$TMPJSON'))
assert 'headings' in data, 'missing headings key'
print('ok')
" 2>/dev/null | grep -q "ok"; then
        pass "Structure JSON is valid with 'headings' key"
    else
        fail "Structure JSON missing 'headings' key"
    fi
else
    fail "Structure command failed"
fi

# --- Summary ---
echo ""
echo "Results: $PASSED passed, $FAILED failed"
if [ "$FAILED" -gt 0 ]; then
    exit 1
fi
echo "All checks passed!"
