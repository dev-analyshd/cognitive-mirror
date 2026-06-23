#!/bin/bash
set -e

VERSION="1.0.0"
echo ""
echo "Cognitive Mirror v${VERSION} — Deploy"
echo "======================================="
echo ""

cd "$(dirname "$0")/.."

echo "Running test suite..."
python3 tests/test_coherence_engine.py
if [ $? -ne 0 ]; then
    echo "ERROR: Tests failed. Fix before deploying."
    exit 1
fi
echo "  OK  all tests passed"

echo ""
echo "Packaging UI bundle..."
mkdir -p dist
cd bundle
zip -r ../dist/cognitive-mirror-bundle-v${VERSION}.zip \
    index.html \
    style.css \
    app.js \
    icon.svg \
    2>/dev/null || (
    # If zip is not available, create a tar instead
    cd ..
    tar -czf dist/cognitive-mirror-bundle-v${VERSION}.tar.gz \
        -C bundle index.html style.css app.js icon.svg
    echo "  Created tar.gz (zip not available)"
    cd bundle
)
cd ..

echo "  OK  bundle packaged → dist/cognitive-mirror-bundle-v${VERSION}.zip"

echo ""
echo "Checking for CHANGEME placeholders..."
if grep -r "CHANGEME" manifest.json bundle/app.js executas/coherence-engine/pyproject.toml 2>/dev/null | grep -v "^Binary"; then
    echo ""
    echo "WARNING: CHANGEME placeholders found!"
    echo "  Run: python scripts/set-tool-id.py apply --tool YOUR_TOOL_ID --skill YOUR_SKILL_ID"
    echo "  Then re-run this script."
    echo ""
fi

echo ""
echo "======================================="
echo "Build complete!"
echo ""
echo "Artifacts:"
ls -lh dist/ 2>/dev/null || echo "  (none)"
echo ""
echo "Submit to Anna App Store:"
echo "  1. https://anna.partners/executa → My Apps"
echo "  2. Create App — fill from app.json"
echo "  3. Create version — paste manifest.json"
echo "  4. Upload bundle zip from dist/"
echo "  5. Submit for review"
echo ""
