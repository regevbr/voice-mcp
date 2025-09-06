#!/bin/bash
set -e

echo "🎨 Running code formatting..."

echo "  🗂️  Running isort..."
uv run isort src/ tests/ examples/

echo "  ✨ Running ruff format..."
uv run ruff format src/ tests/ examples/

echo "✅ Code formatting complete!"
