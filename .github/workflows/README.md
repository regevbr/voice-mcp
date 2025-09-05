# GitHub Actions Workflows

This directory contains the CI/CD workflows for the Voice MCP Server project. These workflows provide comprehensive automation for code quality, testing, security, and deployment.

## 🔄 Available Workflows

### 1. CI Pipeline (`ci.yml`)
**Triggers:** Push to `main`/`develop`, Pull Requests
**Purpose:** Comprehensive continuous integration

**Features:**
- **Multi-Python Testing:** Tests on Python 3.12 and 3.13
- **Multi-OS Support:** Ubuntu, Windows, and macOS
- **Quality Checks:** Black, isort, Ruff, MyPy, Bandit security scanning
- **Fast Testing:** Excludes slow and hardware-dependent tests for quick feedback
- **Code Coverage:** Comprehensive coverage reporting with Codecov integration
- **Build Verification:** Ensures package builds correctly
- **Parallel Execution:** Jobs run in parallel for faster feedback

**Job Flow:**
1. `quality-checks` - Code formatting, linting, type checking, security scanning
2. `test` - Cross-platform testing with coverage
3. `integration-tests` - End-to-end testing (main branch only)
4. `build` - Package building and verification
5. `ci-summary` - Consolidated results

### 2. Release Pipeline (`release.yml`)
**Triggers:** Version tags (`v*.*.*`), Manual dispatch
**Purpose:** Automated release management

**Features:**
- **Version Validation:** Ensures proper semantic versioning
- **Quality Gate:** Full quality checks before release
- **Multi-Platform Testing:** Release candidate testing across platforms
- **GitHub Releases:** Automated release creation with notes
- **PyPI Publishing:** Automated package publishing with trusted publishing
- **Pre-release Support:** Handles alpha/beta/rc releases to Test PyPI

**Job Flow:**
1. `validate-release` - Version format and metadata validation
2. `quality-gate` - Comprehensive quality checks
3. `build-and-test` - Multi-platform testing
4. `build-package` - Final package building
5. `create-release` - GitHub release creation
6. `publish-pypi` - PyPI/Test PyPI publishing
7. `post-release` - Release notifications

### 3. Security & Dependencies (`security.yml`)
**Triggers:** Daily schedule, Manual dispatch, Dependency file changes
**Purpose:** Continuous security monitoring and dependency management

**Features:**
- **Security Scanning:** Bandit code security analysis
- **Vulnerability Scanning:** Safety dependency vulnerability checks
- **License Compliance:** License compatibility verification
- **Automated Updates:** Dependency update PRs with testing
- **Daily Monitoring:** Scheduled security scans

**Job Flow:**
1. `security-scan` - Code security analysis
2. `dependency-scan` - Vulnerability detection
3. `dependency-updates` - Automated dependency updates (scheduled)
4. `license-check` - License compliance verification

### 4. Documentation (`docs.yml`)
**Triggers:** Documentation changes, Main branch pushes
**Purpose:** Documentation building and deployment

**Features:**
- **Documentation Validation:** README, docstring coverage, link checking
- **MkDocs Integration:** Automatic documentation site generation
- **GitHub Pages Deployment:** Automated documentation publishing
- **Code Example Testing:** Validates code examples in documentation

### 5. Coverage Analysis (`coverage.yml`)
**Triggers:** Push, Pull Requests, Weekly schedule
**Purpose:** Comprehensive code coverage analysis

**Features:**
- **Coverage Reporting:** Detailed HTML and XML coverage reports
- **PR Comments:** Coverage summaries on pull requests
- **Coverage History:** Trend tracking over time
- **Mutation Testing:** Quality of test suite validation (scheduled)
- **Coverage Badges:** Automated coverage badge generation

## 🛠️ Configuration

### Environment Variables
These workflows use various environment variables for configuration:

```bash
# Testing Configuration
VOICE_MCP_DEBUG=false
VOICE_MCP_LOG_LEVEL=WARNING
VOICE_MCP_TTS_ENABLED=false    # Disable TTS in CI
VOICE_MCP_STT_ENABLED=false    # Disable STT in CI
VOICE_MCP_ENABLE_HOTKEY=false  # Disable hotkeys in CI
```

### Secrets Required
For full functionality, configure these repository secrets:

- `CODECOV_TOKEN` - For coverage reporting (optional)
- `PYPI_API_TOKEN` - For PyPI publishing (release workflow)

### GitHub Settings
Enable the following in your repository settings:

- **Pages:** Source = "GitHub Actions" for documentation deployment
- **Environments:** Create "release" environment with protection rules
- **Branch Protection:** Require CI checks for main/develop branches

## 📊 Workflow Status

You can monitor workflow status through:

- **GitHub Actions Tab:** Real-time workflow execution
- **README Badges:** Status indicators (if configured)
- **PR Checks:** Automatic status checks on pull requests
- **Branch Protection:** Required checks before merging

## 🔧 Local Development

### Running Quality Checks Locally
```bash
# Run all quality checks
./scripts/check-all.sh

# Individual checks
./scripts/format.sh      # Formatting
./scripts/lint.sh        # Linting
./scripts/typecheck.sh   # Type checking
./scripts/test.sh        # Testing
```

### Testing CI Changes
Before pushing workflow changes:

1. Test quality checks locally: `./scripts/check-all.sh`
2. Validate YAML syntax: Use GitHub's workflow validation
3. Test on a fork first for complex changes
4. Use `workflow_dispatch` for manual testing

## 📈 Performance Optimization

### Cache Strategy
Workflows use multiple cache layers:
- **uv dependencies:** `~/.cache/uv` and `.venv`
- **Python installations:** Managed by `astral-sh/setup-uv`
- **System packages:** OS package managers with caching

### Parallel Execution
Jobs are designed for maximum parallelization:
- Quality checks run independently
- Matrix builds execute in parallel
- Dependency scanning runs separately from main CI

### Resource Usage
- **Ubuntu runners:** Primary platform for comprehensive testing
- **Windows/macOS:** Limited matrix to reduce costs
- **Timeouts:** Appropriate timeouts to prevent hanging jobs

## 🐛 Troubleshooting

### Common Issues

**Test failures in CI but not locally:**
- Environment differences (audio hardware, display)
- Different dependency versions
- Timing issues in parallel tests

**Security scan failures:**
- Review Bandit results carefully
- Use `# nosec` comments for false positives
- Update vulnerable dependencies

**Documentation build failures:**
- Check MkDocs configuration
- Verify all documentation links
- Ensure docstring format compliance

### Debugging Workflows
1. Check workflow logs in GitHub Actions tab
2. Look for artifact uploads (coverage, security reports)
3. Use workflow summaries for quick issue identification
4. Enable debug logging with `ACTIONS_STEP_DEBUG=true`

## 🚀 Future Enhancements

Potential workflow improvements:
- **Performance Testing:** Automated performance benchmarks
- **Integration Testing:** Real hardware testing on self-hosted runners
- **Multi-Architecture:** ARM64 testing for broader compatibility
- **Staging Deployments:** Automated staging environment updates
- **Monitoring Integration:** Alerts for workflow failures

---

For questions about the CI/CD setup, please create an issue with the `ci` label.
