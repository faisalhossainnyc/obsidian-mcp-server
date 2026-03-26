#!/bin/bash
#
# Run the full Obsidian MCP test suite.
#
# Usage:
#   ./run_tests.sh              # Run all tests
#   ./run_tests.sh -v           # Verbose output (see each test name)
#   ./run_tests.sh -k "search"  # Run only tests matching "search"
#   ./run_tests.sh --tb=short   # Shorter tracebacks on failure
#
# Tests use a temporary vault at /tmp/obsidian_test_vault
# and never touch your real Obsidian vault.
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment if present
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Install pytest if not present
python -c "import pytest" 2>/dev/null || pip install pytest -q

# Run tests from the project root so `src` imports work
PYTHONPATH="$SCRIPT_DIR" python -m pytest tests/ "$@"
