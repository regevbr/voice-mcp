# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]


Looking at the commit history, I'll generate a structured changelog entry for version 0.1.1:

## [0.1.1] - 2025-09-06

### Added
- 📝 Comprehensive GitHub Actions CI/CD pipeline with Windows and Linux support
- Pre-commit hooks and automated code quality tools
- Optional audio dependencies for CI environments
- Test coverage expansion from 56% to 81% across core modules
- Reproducible builds with uv.lock file

### Fixed
- Redirect print functions to stderr to prevent output capture issues
- Clean up changelog output to prevent filename issues
- Improve git tag fallback logic for first release
- Security CI configuration
- Virtual environment creation issues in CI
- Windows CI cache and virtual environment compatibility
- STT timeout context cross-platform compatibility
- FastMCP, STT, and text output mocking issues in tests
- GitHub Actions PR creation permission issues
- Windows PowerShell parsing in CI workflows
- Lazy pynput imports to prevent CI failures in headless environments
- Python 3.11 compatibility with librosa and llvmlite dependencies

### Changed
- Smoother release cycle with Claude Code CLI integration
- Updated project configuration and documentation
- Enhanced error handling and documentation
- Dependency updates for better compatibility

### Performance
- Make audio dependencies optional to reduce installation overhead in CI environments

This changelog captures the major improvements in CI/CD infrastructure, test coverage expansion, cross-platform compatibility fixes, and the transition to optional audio dependencies for better CI performance.
