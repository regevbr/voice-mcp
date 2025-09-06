# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **BREAKING**: Reduced default silence threshold from 4.0s to 3.0s for faster STT response
  - Environment variable `VOICE_MCP_STT_SILENCE_THRESHOLD` defaults to `3.0` instead of `4.0`
  - Existing users may need to explicitly set `VOICE_MCP_STT_SILENCE_THRESHOLD=4.0` to maintain previous behavior

### Improved
- **Performance**: Enhanced tqdm patching for robust compatibility with RealtimeSTT/huggingface_hub
  - Comprehensive fix for tqdm locking issues with disabled_tqdm classes
  - Better performance and reduced memory overhead
  - Eliminates "NoneType object does not support the context manager protocol" errors
- **Resource Management**: Enhanced server cleanup and shutdown handling
  - Thread-safe cleanup with proper state tracking to prevent race conditions
  - Simplified signal handlers with reduced timeout complexity
  - More reliable graceful shutdown sequence

### Fixed
- **Compatibility**: Resolved tqdm locking issues in concurrent contexts
- **Stability**: Eliminated race conditions during server shutdown
- **CI/CD**: Fixed uv version inconsistencies between CI and local environments (0.5.13 → 0.8.13)

### Added
- **Security**: CodeQL security scanning in CI pipeline
- **Testing**: Comprehensive test coverage improvements (92% overall coverage achieved)
- **Documentation**: Enhanced configuration documentation with breaking change notes

## Migration Guide

### For users upgrading from versions with 4.0s silence threshold:

If you prefer the previous longer silence detection timeout:

```bash
# Set environment variable
export VOICE_MCP_STT_SILENCE_THRESHOLD=4.0

# Or in your configuration
VOICE_MCP_STT_SILENCE_THRESHOLD=4.0
```

### For developers extending the codebase:

- The server cleanup mechanism now uses thread-safe patterns
- Signal handlers have been simplified - custom cleanup should use the new `cleanup_operations` pattern
- tqdm patching is now minimal and targeted - avoid extensive monkey-patching in favor of upstream fixes
