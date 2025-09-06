#!/bin/bash

# Bump version with Claude Code CLI integration for intelligent version suggestions
# Usage: ./scripts/bump-version.sh [major|minor|patch|auto]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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
    echo -e "${BLUE}[VERSION]${NC} $1"
}

# Check if Claude Code CLI is available
check_claude_cli() {
    if ! command -v claude &> /dev/null; then
        print_warning "Claude Code CLI not found. Version bump will use manual input."
        return 1
    fi
    return 0
}

# Get the current version from pyproject.toml
get_current_version() {
    grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/'
}

# Parse semantic version into components
parse_version() {
    local version="$1"
    echo "$version" | sed -E 's/([0-9]+)\.([0-9]+)\.([0-9]+).*/\1 \2 \3/'
}

# Calculate new version based on bump type
calculate_new_version() {
    local current="$1"
    local bump_type="$2"

    read -r major minor patch <<< $(parse_version "$current")

    case "$bump_type" in
        "major")
            major=$((major + 1))
            minor=0
            patch=0
            ;;
        "minor")
            minor=$((minor + 1))
            patch=0
            ;;
        "patch")
            patch=$((patch + 1))
            ;;
        *)
            print_error "Invalid bump type: $bump_type"
            exit 1
            ;;
    esac

    echo "${major}.${minor}.${patch}"
}

# Use Claude to suggest version bump type
suggest_version_bump() {
    local since_ref="$1"
    local temp_file="/tmp/commits_for_version.txt"

    print_status "Using Claude Code CLI to analyze commits for version bump suggestion..."

    # Get commits since reference
    git log --oneline --no-merges "${since_ref}..HEAD" > "$temp_file"

    if [ ! -s "$temp_file" ]; then
        print_warning "No commits found since $since_ref"
        echo "patch"
        return 0
    fi

    local claude_prompt="Analyze these git commits and suggest the appropriate semantic version bump (major, minor, or patch).

Guidelines:
- MAJOR: Breaking changes, incompatible API changes, removed features
- MINOR: New features, backwards-compatible functionality additions
- PATCH: Bug fixes, small improvements, backwards-compatible changes

Look for keywords like:
- Breaking: BREAKING CHANGE, breaking, remove, drop support
- Features: feat, add, new, implement, support for
- Fixes: fix, bug, resolve, patch, correct

Respond with only one word: major, minor, or patch

Commits to analyze:"

    {
        echo "$claude_prompt"
        echo ""
        cat "$temp_file"
    } | claude | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]' | head -1

    rm -f "$temp_file"
}

# Update version in pyproject.toml
update_version_file() {
    local new_version="$1"

    print_status "Updating version in pyproject.toml to $new_version"

    # Create backup
    cp pyproject.toml pyproject.toml.backup

    # Update version
    sed -i "s/^version = .*/version = \"$new_version\"/" pyproject.toml

    # Verify the change
    local updated_version
    updated_version=$(get_current_version)

    if [ "$updated_version" != "$new_version" ]; then
        print_error "Failed to update version in pyproject.toml"
        mv pyproject.toml.backup pyproject.toml
        exit 1
    fi

    rm -f pyproject.toml.backup
    print_status "Successfully updated pyproject.toml"
}

# Get the latest git tag
get_latest_tag() {
    git describe --tags --abbrev=0 2>/dev/null || echo "HEAD~50"
}

# Create git tag and commit
create_git_tag() {
    local version="$1"
    local tag_name="v$version"

    print_status "Creating git commit and tag for version $version"

    # Stage the changes
    git add pyproject.toml CHANGELOG.md

    # Create commit
    git commit -m "chore: bump version to $version

- Updated pyproject.toml version to $version
- Updated CHANGELOG.md with release notes

🤖 Generated with Claude Code"

    # Create annotated tag
    git tag -a "$tag_name" -m "Release $version

$(grep -A 20 "## \[$version\]" CHANGELOG.md | sed '/## \[/,$d' | tail -n +2)

🤖 Generated with Claude Code"

    print_status "Created commit and tag $tag_name"
}

# Interactive confirmation
confirm_version_bump() {
    local current="$1"
    local new_version="$2"
    local bump_type="$3"

    print_header "Version Bump Summary"
    echo "  Current version: $current"
    echo "  New version:     $new_version"
    echo "  Bump type:       $bump_type"
    echo ""

    read -p "Continue with version bump? (y/N): " -n 1 -r
    echo

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Version bump cancelled"
        exit 0
    fi
}

# Display usage information
show_usage() {
    echo "Usage: $0 [major|minor|patch|auto]"
    echo ""
    echo "Bump project version with intelligent analysis"
    echo ""
    echo "Arguments:"
    echo "  major    Bump major version (breaking changes)"
    echo "  minor    Bump minor version (new features)"
    echo "  patch    Bump patch version (bug fixes)"
    echo "  auto     Let Claude analyze commits and suggest bump type"
    echo ""
    echo "Examples:"
    echo "  $0 patch        # Bump patch version"
    echo "  $0 minor        # Bump minor version"
    echo "  $0 auto         # Let Claude suggest version bump"
    echo ""
    echo "The script will:"
    echo "  1. Update version in pyproject.toml"
    echo "  2. Generate/update CHANGELOG.md using Claude"
    echo "  3. Create git commit and tag"
}

# Main execution
main() {
    local bump_type="$1"

    # Show help
    if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
        show_usage
        exit 0
    fi

    # Check if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_error "Not in a git repository"
        exit 1
    fi

    # Check for uncommitted changes
    if ! git diff-index --quiet HEAD --; then
        print_error "You have uncommitted changes. Please commit or stash them first."
        exit 1
    fi

    # Get current version
    local current_version
    current_version=$(get_current_version)
    print_status "Current version: $current_version"

    # Determine bump type
    if [ -z "$bump_type" ] || [ "$bump_type" = "auto" ]; then
        if check_claude_cli; then
            local since_ref
            since_ref=$(get_latest_tag)
            bump_type=$(suggest_version_bump "$since_ref")
            print_status "Claude suggests: $bump_type version bump"
        else
            print_warning "No bump type specified and Claude CLI not available"
            print_warning "Available options: major, minor, patch"
            read -p "Enter bump type: " bump_type
        fi
    fi

    # Validate bump type
    if [[ ! "$bump_type" =~ ^(major|minor|patch)$ ]]; then
        print_error "Invalid bump type: $bump_type"
        print_error "Must be one of: major, minor, patch"
        exit 1
    fi

    # Calculate new version
    local new_version
    new_version=$(calculate_new_version "$current_version" "$bump_type")

    # Confirm with user
    confirm_version_bump "$current_version" "$new_version" "$bump_type"

    # Update version in file
    update_version_file "$new_version"

    # Generate changelog for the new version
    print_status "Generating changelog for version $new_version..."
    ./scripts/generate-changelog.sh "$new_version"

    # Create git commit and tag
    create_git_tag "$new_version"

    print_header "Version bump complete!"
    print_status "Version updated from $current_version to $new_version"
    print_status "Created tag: v$new_version"
    print_status "Updated CHANGELOG.md"
    echo ""
    print_warning "Don't forget to push the changes:"
    echo "  git push origin main --tags"
}

# Run main function
main "$@"
