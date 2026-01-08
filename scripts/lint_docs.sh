#!/bin/bash
# Quick documentation linter

set -e

# Check for node modules (optional dynamic check)
if [ -f "docs/package.json" ]; then
    echo "Using docs/package.json"
fi

# Check for trailing whitespace
echo "Checking trailing whitespace..."
if grep -rn " $" $DOCS_DIR/*.md; then
    echo "❌ Found trailing whitespace (see above)"
    exit 1
else
    echo "✅ No trailing whitespace"
fi

# Check for tab characters
echo "Checking for tabs..."
if grep -rn $'\t' $DOCS_DIR/*.md; then
    echo "❌ Found tab characters (see above)"
    exit 1
else
    echo "✅ No tabs found"
fi

# Check for TODO/FIXME
echo "Checking for TODO/FIXME..."
if grep -rn -E "TODO|FIXME" $DOCS_DIR/*.md; then
    echo "⚠️  Found TODO/FIXME markers (see above)"
else
    echo "✅ No TODO/FIXME markers"
fi

# Check for placeholder text
echo "Checking for placeholders..."
if grep -rn -E "PLACEHOLDER|TBD|XXX" $DOCS_DIR/*. md; then
    echo "⚠️  Found placeholder text (see above)"
else
    echo "✅ No placeholders found"
fi

echo ""
echo "✅ Quick lint complete!"
