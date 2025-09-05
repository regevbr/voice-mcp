#!/bin/bash
set -e

echo "🚀 Running all quality checks..."

# Change to project root directory
cd "$(dirname "$0")/.."

# Run all checks in sequence
echo "1/4 - Formatting..."
./scripts/format.sh

echo -e "\n2/4 - Linting..."
./scripts/lint.sh

echo -e "\n3/4 - Type checking..."
./scripts/typecheck.sh

echo -e "\n4/4 - Testing..."
./scripts/test.sh

echo -e "\n🎉 All quality checks passed!"
