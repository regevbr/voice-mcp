#!/bin/bash
set -e

echo "🔍 Running linting checks..."

echo "  📋 Running ruff check..."
uv run ruff check src/ tests/ examples/

echo "  🔒 Running bandit security check..."
uv run bandit -r src/ -f txt

echo "✅ Linting checks complete!"
