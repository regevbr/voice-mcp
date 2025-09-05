#!/bin/bash
set -e

echo "🔍 Running type checking..."

echo "  📝 Running MyPy..."
uv run mypy src/ --config-file=pyproject.toml

echo "✅ Type checking complete!"
