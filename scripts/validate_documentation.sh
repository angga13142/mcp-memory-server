#!/bin/bash
# Documentation validation wrapper script

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DOCS_DIR="$SCRIPT_DIR/../docs/monitoring"

echo "🔍 Documentation Validation Suite"
echo "=================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

run_check() {
    local name=$1
    local command=$2
    
    ((TOTAL_CHECKS++))
    
    echo "Running:  $name"
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASSED${NC}:  $name"
        ((PASSED_CHECKS++))
    else
        echo -e "${RED}❌ FAILED${NC}: $name"
        ((FAILED_CHECKS++))
    fi
    
    echo ""
}

# Check 1: Required files exist
echo "📄 CHECKING FILE EXISTENCE"
echo "-------------------------"

run_check "INDEX.md exists" "test -f $DOCS_DIR/INDEX.md"
run_check "README.md exists" "test -f $DOCS_DIR/README. md"
run_check "operator-guide.md exists" "test -f $DOCS_DIR/operator-guide.md"
run_check "developer-guide.md exists" "test -f $DOCS_DIR/developer-guide. md"
run_check "runbook.md exists" "test -f $DOCS_DIR/runbook.md"
run_check "troubleshooting.md exists" "test -f $DOCS_DIR/troubleshooting.md"
run_check "api-reference. md exists" "test -f $DOCS_DIR/api-reference.md"
run_check "architecture.md exists" "test -f $DOCS_DIR/architecture.md"

# Check 2: Markdown syntax
echo "📝 CHECKING MARKDOWN SYNTAX"
echo "-------------------------"

if command -v markdownlint &> /dev/null; then
    run_check "Markdown lint" "markdownlint $DOCS_DIR/*. md --config $SCRIPT_DIR/. markdownlint.json"
else
    echo -e "${YELLOW}⚠️  SKIPPED${NC}: markdownlint not installed"
    echo ""
fi

# Check 3: Broken links
echo "🔗 CHECKING LINKS"
echo "----------------"

if command -v markdown-link-check &> /dev/null; then
    for file in $DOCS_DIR/*. md; do
        filename=$(basename "$file")
        run_check "Links in $filename" "markdown-link-check $file --quiet"
    done
else
    echo -e "${YELLOW}⚠️  SKIPPED${NC}: markdown-link-check not installed"
    echo ""
fi

# Check 4: Spelling
echo "📖 CHECKING SPELLING"
echo "-------------------"

if command -v aspell &> /dev/null; then
    # Create temporary file with common technical terms
    cat > /tmp/aspell_ignore.txt <<EOF
asyncio
Prometheus
Grafana
alertmanager
datasource
datasources
webhook
EOF
    
    for file in $DOCS_DIR/*. md; do
        filename=$(basename "$file")
        
        # Extract text content (remove code blocks)
        cat "$file" | \
            sed '/```/,/```/d' | \
            aspell list --ignore-case --personal=/tmp/aspell_ignore.txt > /tmp/misspelled.txt
        
        if [ -s /tmp/misspelled.txt ]; then
            echo -e "${YELLOW}⚠️  WARNINGS${NC}:  Possible misspellings in $filename"
            head -5 /tmp/misspelled.txt | sed 's/^/   - /'
            echo ""
        fi
    done
    
    rm -f /tmp/aspell_ignore.txt /tmp/misspelled.txt
else
    echo -e "${YELLOW}⚠️  SKIPPED${NC}: aspell not installed"
    echo ""
fi

# Check 5: Code blocks syntax
echo "💻 CHECKING CODE BLOCKS"
echo "----------------------"

# Python code blocks
for file in $DOCS_DIR/*. md; do
    filename=$(basename "$file")
    
    # Extract Python code blocks
    awk '/```python/,/```/ {if (!/```/) print}' "$file" > /tmp/code_check.py
    
    if [ -s /tmp/code_check.py ]; then
        run_check "Python syntax in $filename" "python3 -m py_compile /tmp/code_check.py"
    fi
done

rm -f /tmp/code_check.py

# Check 6: File sizes
echo "📏 CHECKING FILE SIZES"
echo "---------------------"

for file in $DOCS_DIR/*.md; do
    filename=$(basename "$file")
    size=$(wc -l < "$file")
    
    if [ $size -gt 2000 ]; then
        echo -e "${YELLOW}⚠️  WARNING${NC}: $filename is large ($size lines)"
        echo "   Consider splitting into smaller files"
        echo ""
    fi
done

# Check 7: Run Python validator
echo "🐍 RUNNING PYTHON VALIDATOR"
echo "---------------------------"

if [ -f "$SCRIPT_DIR/validate_documentation.py" ]; then
    python3 "$SCRIPT_DIR/validate_documentation.py"
else
    echo -e "${YELLOW}⚠️  SKIPPED${NC}: validate_documentation.py not found"
    echo ""
fi

# Summary
echo "=================================="
echo "📊 VALIDATION SUMMARY"
echo "=================================="
echo ""
echo "Total checks:  $TOTAL_CHECKS"
echo -e "Passed: ${GREEN}$PASSED_CHECKS${NC}"
echo -e "Failed: ${RED}$FAILED_CHECKS${NC}"
echo ""

if [ $FAILED_CHECKS -eq 0 ]; then
    echo -e "${GREEN}✅ ALL VALIDATIONS PASSED!${NC}"
    exit 0
else
    echo -e "${RED}❌ SOME VALIDATIONS FAILED${NC}"
    exit 1
fi
