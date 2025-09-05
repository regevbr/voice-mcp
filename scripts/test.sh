#!/bin/bash
set -e

echo "🧪 Running tests..."

# Default: Run fast tests only (exclude slow and hardware-dependent tests)
if [ $# -eq 0 ]; then
    TEST_ARGS='-m "not slow and not voice"'
else
    TEST_ARGS="$1"
fi

echo "  🏃 Running pytest with args: $TEST_ARGS"
uv run pytest ${TEST_ARGS} -v --tb=short

echo "✅ Tests complete!"
