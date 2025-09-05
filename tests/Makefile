# Test Makefile for Voice MCP Server

.PHONY: test test-unit test-integration test-voice test-coverage test-watch clean

# Run all tests
test:
	pytest

# Run unit tests only
test-unit:
	pytest tests/unit tests/test_*.py -v

# Run integration tests only  
test-integration:
	pytest tests/integration -v

# Run voice-specific tests (requires audio hardware)
test-voice:
	pytest -m voice -v

# Run tests with coverage report
test-coverage:
	pytest --cov=voice_mcp --cov-report=html --cov-report=term

# Watch for changes and re-run tests
test-watch:
	pytest-watch

# Run tests in parallel (faster)
test-parallel:
	pytest -n auto

# Run only fast tests (exclude slow/voice tests)
test-fast:
	pytest -m "not slow and not voice" -v

# Clean test artifacts
clean:
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete