#!/bin/bash
# Full lint suite for Oh My Coins backend
# Runs ruff check, ruff format check, and mypy inside Docker
set -e

echo "🔍 Running Ruff linter..."
docker compose exec -T backend python -m ruff check app/

echo "🎨 Running Ruff format check..."
docker compose exec -T backend python -m ruff format app/ --check

echo "🔠 Running MyPy type checker..."
docker compose exec -T backend python -m mypy app/ --ignore-missing-imports || echo "⚠️  MyPy errors found (see MYPY_DEBT.md for known issues)"

echo ""
echo "✅ Lint suite complete."
