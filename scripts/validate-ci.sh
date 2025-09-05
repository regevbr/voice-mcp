#!/bin/bash
set -e

echo "🔍 Validating CI/CD Configuration..."

# Change to project root directory
cd "$(dirname "$0")/.."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

error_count=0

# Function to report errors
report_error() {
    echo -e "${RED}❌ $1${NC}"
    ((error_count++))
}

# Function to report success
report_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to report warning
report_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo "1️⃣  Checking GitHub Actions workflow files..."

# Check if .github directory exists
if [[ ! -d ".github" ]]; then
    report_error ".github directory not found"
else
    report_success ".github directory exists"
fi

# Check if workflows directory exists
if [[ ! -d ".github/workflows" ]]; then
    report_error ".github/workflows directory not found"
else
    report_success ".github/workflows directory exists"
fi

# Check for required workflow files
REQUIRED_WORKFLOWS=(
    "ci.yml"
    "release.yml"
    "security.yml"
    "docs.yml"
    "coverage.yml"
)

for workflow in "${REQUIRED_WORKFLOWS[@]}"; do
    if [[ ! -f ".github/workflows/$workflow" ]]; then
        report_error "Missing workflow: .github/workflows/$workflow"
    else
        report_success "Found workflow: $workflow"
    fi
done

echo -e "\n2️⃣  Validating YAML syntax..."

# Check if yq or python yaml is available for validation
if command -v yq > /dev/null 2>&1; then
    YAML_VALIDATOR="yq"
elif python3 -c "import yaml" > /dev/null 2>&1; then
    YAML_VALIDATOR="python"
else
    report_warning "No YAML validator found (yq or python yaml module). Skipping syntax validation."
    YAML_VALIDATOR=""
fi

if [[ -n "$YAML_VALIDATOR" ]]; then
    for workflow_file in .github/workflows/*.yml; do
        if [[ -f "$workflow_file" ]]; then
            if [[ "$YAML_VALIDATOR" == "yq" ]]; then
                if yq eval . "$workflow_file" > /dev/null 2>&1; then
                    report_success "YAML syntax valid: $(basename "$workflow_file")"
                else
                    report_error "YAML syntax error in: $(basename "$workflow_file")"
                fi
            else
                if python3 -c "import yaml; yaml.safe_load(open('$workflow_file'))" > /dev/null 2>&1; then
                    report_success "YAML syntax valid: $(basename "$workflow_file")"
                else
                    report_error "YAML syntax error in: $(basename "$workflow_file")"
                fi
            fi
        fi
    done
fi

echo -e "\n3️⃣  Checking supporting files..."

# Check for supporting files
SUPPORTING_FILES=(
    ".github/dependabot.yml"
    ".github/CODEOWNERS"
    ".github/pull_request_template.md"
    ".github/ISSUE_TEMPLATE/bug_report.yml"
    ".github/ISSUE_TEMPLATE/feature_request.yml"
)

for file in "${SUPPORTING_FILES[@]}"; do
    if [[ ! -f "$file" ]]; then
        report_warning "Missing supporting file: $file"
    else
        report_success "Found supporting file: $(basename "$file")"
    fi
done

echo -e "\n4️⃣  Checking script dependencies..."

# Check for required scripts
REQUIRED_SCRIPTS=(
    "scripts/check-all.sh"
    "scripts/format.sh"
    "scripts/lint.sh"
    "scripts/typecheck.sh"
    "scripts/test.sh"
)

for script in "${REQUIRED_SCRIPTS[@]}"; do
    if [[ ! -f "$script" ]]; then
        report_error "Missing script: $script"
    elif [[ ! -x "$script" ]]; then
        report_warning "Script not executable: $script"
    else
        report_success "Found executable script: $(basename "$script")"
    fi
done

echo -e "\n5️⃣  Checking project configuration..."

# Check pyproject.toml
if [[ ! -f "pyproject.toml" ]]; then
    report_error "pyproject.toml not found"
else
    report_success "pyproject.toml exists"

    # Check for required sections
    REQUIRED_SECTIONS=(
        "\[project\]"
        "\[tool\.pytest\.ini_options\]"
        "\[tool\.black\]"
        "\[tool\.ruff\]"
        "\[tool\.mypy\]"
        "\[tool\.coverage"
    )

    for section in "${REQUIRED_SECTIONS[@]}"; do
        if grep -q "$section" pyproject.toml; then
            report_success "Found configuration section: $section"
        else
            report_warning "Missing configuration section: $section"
        fi
    done
fi

echo -e "\n6️⃣  Testing local quality checks..."

# Test if quality checks can run
if ./scripts/check-all.sh > /dev/null 2>&1; then
    report_success "Quality checks run successfully"
else
    report_warning "Quality checks failed - this may cause CI failures"
fi

echo -e "\n7️⃣  Checking dependencies..."

# Check if uv is available
if command -v uv > /dev/null 2>&1; then
    report_success "uv package manager available"

    # Check if dependencies can be resolved
    if uv sync --dry-run > /dev/null 2>&1; then
        report_success "Dependencies can be resolved"
    else
        report_warning "Dependency resolution issues detected"
    fi
else
    report_error "uv package manager not found - required for CI"
fi

echo -e "\n8️⃣  Validation Summary"
echo "========================"

if [[ $error_count -eq 0 ]]; then
    echo -e "${GREEN}🎉 All critical checks passed! CI/CD setup looks good.${NC}"
    echo ""
    echo "✅ Your workflows are ready for:"
    echo "   • Continuous Integration testing"
    echo "   • Automated releases"
    echo "   • Security monitoring"
    echo "   • Documentation deployment"
    echo "   • Code coverage analysis"
    echo ""
    echo "💡 Next steps:"
    echo "   1. Push to trigger CI workflows"
    echo "   2. Configure repository settings (branch protection, environments)"
    echo "   3. Set up PyPI trusted publishing for releases"
    echo "   4. Enable GitHub Pages for documentation"
else
    echo -e "${RED}❌ Found $error_count critical issues that need to be fixed.${NC}"
    echo ""
    echo "🔧 Please address the errors above before using CI/CD workflows."
    exit 1
fi

echo -e "\n📚 For more information, see .github/workflows/README.md"
