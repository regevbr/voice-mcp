#!/bin/bash
set -e

echo "📈 Analyzing coverage report..."

if [[ -f "coverage.json" ]]; then
  python << 'EOF'
import json
import sys

with open('coverage.json') as f:
    data = json.load(f)

print("## Coverage Analysis")
print(f"**Total Coverage:** {data['totals']['percent_covered']:.1f}%")
print(f"**Lines Covered:** {data['totals']['covered_lines']}/{data['totals']['num_statements']}")
print(f"**Missing Lines:** {data['totals']['missing_lines']}")
print(f"**Branch Coverage:** {data['totals']['percent_covered_display']}%")
print()

print("### File Coverage Breakdown")
print("| File | Coverage | Missing Lines |")
print("|------|----------|---------------|")

# Sort files by coverage percentage
files = [(f, d) for f, d in data['files'].items()]
files.sort(key=lambda x: x[1]['summary']['percent_covered'])

for filepath, file_data in files:
    filename = filepath.split('/')[-1]  # Just the filename
    coverage = file_data['summary']['percent_covered']
    missing = file_data['summary']['missing_lines']

    if coverage < 80:  # Highlight files with low coverage
        print(f"| **{filename}** | **{coverage:.1f}%** | **{missing}** |")
    else:
        print(f"| {filename} | {coverage:.1f}% | {missing} |")

print()
print("### Recommendations")

low_coverage_files = [
    (f.split('/')[-1], d['summary']['percent_covered'])
    for f, d in data['files'].items()
    if d['summary']['percent_covered'] < 80
]

if low_coverage_files:
    print("**Files needing attention (< 80% coverage):**")
    for filename, cov in low_coverage_files:
        print(f"- `{filename}`: {cov:.1f}% coverage")
else:
    print("✅ All files have good coverage (>= 80%)")

# Exit with error if overall coverage is too low
if data['totals']['percent_covered'] < 70:
    print(f"\n❌ Overall coverage {data['totals']['percent_covered']:.1f}% is below minimum threshold of 70%")
    sys.exit(1)
EOF
fi
