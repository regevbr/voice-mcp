#!/bin/bash

# Comprehensive release preparation script with Claude Code CLI integration
# Usage: ./scripts/prepare-release.sh [version_type]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[RELEASE]${NC} $1"
}

print_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

print_success() {
    echo -e "${CYAN}[SUCCESS]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_step "Checking prerequisites..."

    # Check if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_error "Not in a git repository"
        exit 1
    fi

    # Check for uncommitted changes
    if ! git diff-index --quiet HEAD --; then
        print_error "You have uncommitted changes. Please commit or stash them first."
        git status --short
        exit 1
    fi

    # Check if we're on the main branch
    local current_branch
    current_branch=$(git branch --show-current)
    if [ "$current_branch" != "main" ] && [ "$current_branch" != "master" ]; then
        print_warning "You're on branch '$current_branch', not 'main/master'"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_warning "Release preparation cancelled"
            exit 0
        fi
    fi

    # Check if required scripts exist
    if [ ! -f "scripts/bump-version.sh" ]; then
        print_error "scripts/bump-version.sh not found"
        exit 1
    fi

    if [ ! -f "scripts/check-all.sh" ]; then
        print_error "scripts/check-all.sh not found"
        exit 1
    fi

    print_success "Prerequisites check passed"
}

# Run quality checks
run_quality_checks() {
    print_step "Running quality checks..."

    if ! ./scripts/check-all.sh; then
        print_error "Quality checks failed. Please fix issues before releasing."
        exit 1
    fi

    print_success "Quality checks passed"
}

# Get current project status
get_project_status() {
    local current_version
    current_version=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')

    local latest_tag
    latest_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "none")

    local commits_since_tag
    if [ "$latest_tag" != "none" ]; then
        commits_since_tag=$(git rev-list --count "${latest_tag}..HEAD")
    else
        commits_since_tag=$(git rev-list --count HEAD)
    fi

    echo "current_version:$current_version"
    echo "latest_tag:$latest_tag"
    echo "commits_since_tag:$commits_since_tag"
}

# Show release preview
show_release_preview() {
    local version_type="$1"

    print_step "Generating release preview..."

    # Get project status
    local status
    status=$(get_project_status)
    local current_version=$(echo "$status" | grep "current_version:" | cut -d: -f2)
    local latest_tag=$(echo "$status" | grep "latest_tag:" | cut -d: -f2)
    local commits_count=$(echo "$status" | grep "commits_since_tag:" | cut -d: -f2)

    print_header "Release Preview"
    echo "  📋 Current version: $current_version"
    echo "  🏷️  Latest tag: $latest_tag"
    echo "  📝 Commits since last release: $commits_count"
    echo "  🎯 Requested bump type: ${version_type:-auto}"
    echo ""

    if [ "$commits_count" -eq 0 ]; then
        print_warning "No commits since last release. Nothing to release."
        return 1
    fi

    # Show recent commits
    print_header "Recent Commits"
    if [ "$latest_tag" != "none" ]; then
        git log --oneline --no-merges "${latest_tag}..HEAD" | head -10
    else
        git log --oneline --no-merges HEAD | head -10
    fi
    echo ""

    return 0
}

# Interactive version selection
select_version_type() {
    local suggested_type="$1"

    print_header "Version Bump Selection"

    if [ -n "$suggested_type" ]; then
        echo "  🤖 Claude suggests: $suggested_type"
        echo ""
    fi

    echo "Version bump types:"
    echo "  1) patch  - Bug fixes and small improvements"
    echo "  2) minor  - New features (backwards compatible)"
    echo "  3) major  - Breaking changes"
    echo "  4) auto   - Let Claude analyze and decide"
    echo ""

    while true; do
        read -p "Select version bump type (1-4): " -n 1 -r
        echo

        case $REPLY in
            1)
                echo "patch"
                return 0
                ;;
            2)
                echo "minor"
                return 0
                ;;
            3)
                echo "major"
                return 0
                ;;
            4)
                echo "auto"
                return 0
                ;;
            *)
                print_warning "Invalid selection. Please choose 1-4."
                ;;
        esac
    done
}

# Create release PR
create_release_pr() {
    local version="$1"

    print_step "Creating release PR..."

    # Check if gh CLI is available
    if ! command -v gh &> /dev/null; then
        print_warning "GitHub CLI (gh) not found. Skipping PR creation."
        print_warning "You can create a PR manually or install gh CLI."
        return 0
    fi

    # Check if we have changes to create PR with
    if git diff-index --quiet HEAD --; then
        print_warning "No changes to create PR with"
        return 0
    fi

    local branch_name="release/v$version"
    local current_branch
    current_branch=$(git branch --show-current)

    # Create release branch
    git checkout -b "$branch_name" 2>/dev/null || {
        print_warning "Branch $branch_name already exists, using it"
        git checkout "$branch_name"
    }

    # Push the branch
    git push -u origin "$branch_name"

    # Create PR
    local pr_title="🚀 Release v$version"
    local pr_body="## Release Preparation

This PR prepares the release of version $version.

### Changes
- Updated version to $version in pyproject.toml
- Generated changelog for v$version
- Ready for release workflow

### Checklist
- [x] Version bumped
- [x] Changelog updated
- [x] Quality checks passed
- [ ] PR reviewed and approved
- [ ] Ready to merge and trigger release

### Next Steps
1. Review the changes
2. Merge this PR to trigger the release workflow
3. Monitor the release pipeline

🤖 Generated with Claude Code"

    gh pr create \
        --title "$pr_title" \
        --body "$pr_body" \
        --base "$current_branch" \
        --head "$branch_name"

    print_success "Release PR created: $branch_name → $current_branch"
}

# Main execution
main() {
    local version_type="$1"

    print_header "🚀 Voice MCP Release Preparation"
    echo "This script will prepare a new release with quality checks and changelog generation."
    echo ""

    # Check prerequisites
    check_prerequisites

    # Run quality checks first
    run_quality_checks

    # Show release preview
    if ! show_release_preview "$version_type"; then
        exit 0
    fi

    # Interactive version selection if not specified
    if [ -z "$version_type" ]; then
        version_type=$(select_version_type)
    fi

    print_header "Release Confirmation"
    echo "  📦 Preparing release with version bump: $version_type"
    echo ""
    read -p "Continue with release preparation? (Y/n): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Nn]$ ]]; then
        print_warning "Release preparation cancelled"
        exit 0
    fi

    # Run the version bump (this will update version and generate changelog)
    print_step "Running version bump..."
    if ! ./scripts/bump-version.sh "$version_type"; then
        print_error "Version bump failed"
        exit 1
    fi

    # Get the new version
    local new_version
    new_version=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')

    # Final verification
    print_step "Running final quality checks..."
    if ! ./scripts/check-all.sh; then
        print_error "Final quality checks failed"
        exit 1
    fi

    # Create release PR
    create_release_pr "$new_version"

    print_header "🎉 Release Preparation Complete!"
    print_success "Version $new_version is ready for release"
    print_success "Changelog has been generated and updated"
    print_success "Git tag v$new_version has been created"
    echo ""
    print_warning "Next steps:"
    echo "  1. Push the changes: git push origin main --tags"
    echo "  2. Create a GitHub release to trigger the release workflow"
    echo "  3. Or merge the release PR if one was created"
    echo ""
    print_warning "The release workflow will handle:"
    echo "  • Building and testing the package"
    echo "  • Creating the GitHub release"
    echo "  • Publishing to PyPI"
}

# Show usage information
show_usage() {
    echo "Usage: $0 [version_type]"
    echo ""
    echo "Prepare a new release with comprehensive checks and automation"
    echo ""
    echo "Arguments:"
    echo "  version_type    Type of version bump: major, minor, patch, or auto"
    echo ""
    echo "Examples:"
    echo "  $0              # Interactive mode"
    echo "  $0 patch        # Prepare patch release"
    echo "  $0 auto         # Let Claude analyze commits"
    echo ""
    echo "The script will:"
    echo "  1. Run quality checks"
    echo "  2. Show release preview"
    echo "  3. Bump version and generate changelog"
    echo "  4. Create git tag and commit"
    echo "  5. Optionally create release PR"
}

# Handle script arguments
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_usage
    exit 0
fi

# Run main function
main "$@"
