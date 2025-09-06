#!/bin/bash

# Generate changelog using Claude Code CLI for commit analysis
# Usage: ./scripts/generate-changelog.sh [version] [since_ref]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output to stderr
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1" >&2
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1" >&2
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

print_header() {
    echo -e "${BLUE}[CHANGELOG]${NC} $1" >&2
}

# Check if Claude Code CLI is available
check_claude_cli() {
    if ! command -v claude &> /dev/null; then
        print_error "Claude Code CLI not found. Please install it first."
        print_error "Visit: https://github.com/anthropics/claude-code"
        exit 1
    fi
}

# Get the current version from pyproject.toml
get_current_version() {
    grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/'
}

# Get the latest git tag
get_latest_tag() {
    git describe --tags --abbrev=0 2>/dev/null || {
        # If no tags exist, use the first commit as reference
        git rev-list --max-parents=0 HEAD 2>/dev/null || echo "HEAD"
    }
}

# Generate changelog for a specific version
generate_changelog() {
    local version="$1"
    local since_ref="$2"
    local temp_file="/tmp/commits_for_changelog.txt"
    local changelog_file="/tmp/generated_changelog.md"

    print_header "Generating changelog for version $version"

    # Get commits since reference
    print_status "Analyzing commits since $since_ref..."
    git log --oneline --no-merges "${since_ref}..HEAD" > "$temp_file"

    if [ ! -s "$temp_file" ]; then
        print_warning "No commits found since $since_ref"
        echo "No changes in this release." > "$changelog_file"
        return 0
    fi

    print_status "Found $(wc -l < "$temp_file") commits to analyze"

    # Use Claude Code CLI to generate changelog
    print_status "Using Claude Code CLI to generate structured changelog..."

    local claude_prompt="Analyze these git commits and generate a structured changelog entry for version $version.

Format the output as a proper Keep a Changelog section with:
- ## [$version] - $(date +%Y-%m-%d)
- Use these sections only if relevant: Added, Changed, Fixed, Security, Performance, Documentation
- Each item should be a concise bullet point starting with a verb
- Focus on user-facing changes, not internal refactoring
- Combine related commits into single logical changes
- Use emojis sparingly for major features only

Here are the commits to analyze:"

    {
        echo "$claude_prompt"
        echo ""
        cat "$temp_file"
    } | claude > "$changelog_file"

    if [ ! -s "$changelog_file" ]; then
        print_error "Failed to generate changelog with Claude"
        exit 1
    fi

    print_status "Successfully generated changelog"

    # Clean up temp files
    rm -f "$temp_file"

    # Return only the file path
    echo "$changelog_file"
}

# Update CHANGELOG.md with new version
update_changelog_file() {
    local version="$1"
    local changelog_content="$2"
    local changelog_file="CHANGELOG.md"

    print_status "Updating $changelog_file..."

    # Create backup
    cp "$changelog_file" "${changelog_file}.backup"

    # Read the generated changelog content
    local new_content
    new_content=$(cat "$changelog_content")

    # Update the CHANGELOG.md file
    # Replace "## [Unreleased]" section with the new version and add new Unreleased section
    awk -v new_content="$new_content" '
    BEGIN { found_unreleased = 0; printed_new = 0 }
    /^## \[Unreleased\]/ {
        found_unreleased = 1
        print $0
        print ""
        next
    }
    found_unreleased && !printed_new && /^## \[/ {
        # We found the next version section, insert our new content before it
        print new_content
        print ""
        printed_new = 1
        print $0
        next
    }
    found_unreleased && !printed_new && /^$/ {
        # Empty line after Unreleased header, skip content until next version
        next
    }
    found_unreleased && !printed_new && /^[^#]/ {
        # Skip existing unreleased content
        next
    }
    {
        # Print everything else as-is
        print $0
    }
    END {
        # If we never found another version section, add our content at the end
        if (found_unreleased && !printed_new) {
            print ""
            print new_content
        }
    }
    ' "$changelog_file" > "${changelog_file}.tmp"

    mv "${changelog_file}.tmp" "$changelog_file"

    print_status "Updated $changelog_file successfully"
}

# Main execution
main() {
    local version="$1"
    local since_ref="$2"

    # Check prerequisites
    check_claude_cli

    # Determine version and reference point
    if [ -z "$version" ]; then
        version=$(get_current_version)
        print_status "Using current version from pyproject.toml: $version"
    fi

    if [ -z "$since_ref" ]; then
        since_ref=$(get_latest_tag)
        print_status "Using latest tag as reference: $since_ref"
    fi

    # Generate the changelog
    local changelog_file
    changelog_file=$(generate_changelog "$version" "$since_ref")

    # Update CHANGELOG.md
    update_changelog_file "$version" "$changelog_file"

    # Clean up
    rm -f "$changelog_file"
    rm -f "CHANGELOG.md.backup"

    print_header "Changelog generation complete!"
    print_status "Updated CHANGELOG.md with version $version"
    print_status "Review the changes and commit when ready"
}

# Handle script arguments
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [version] [since_ref]"
    echo ""
    echo "Generate changelog using Claude Code CLI"
    echo ""
    echo "Arguments:"
    echo "  version     Version to generate changelog for (default: current from pyproject.toml)"
    echo "  since_ref   Git reference to compare from (default: latest tag)"
    echo ""
    echo "Examples:"
    echo "  $0                          # Use current version, compare from latest tag"
    echo "  $0 0.2.0                    # Generate for v0.2.0, compare from latest tag"
    echo "  $0 0.2.0 v0.1.0             # Generate for v0.2.0, compare from v0.1.0"
    exit 0
fi

# Run main function
main "$@"
