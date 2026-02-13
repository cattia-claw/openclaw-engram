#!/bin/bash
echo "🧠 OpenClaw Brain — Uninstaller"
echo "================================"
echo ""
echo "This will remove cron jobs but PRESERVE your memory files."
echo ""

BRAIN_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_DIR="$(dirname "$BRAIN_DIR")"

echo "⚠️  The following will NOT be deleted:"
echo "   - $WORKSPACE_DIR/memory/"
echo "   - $WORKSPACE_DIR/neurons/"
echo ""

read -p "Remove Brain cron jobs and QMD collections? [y/N] " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Remove QMD collections
if command -v qmd &> /dev/null; then
    echo "🔍 Removing QMD collections..."
    qmd collection remove neuron-memory 2>/dev/null && echo "   ✅ neuron-memory" || echo "   ⏭️  neuron-memory not found"
    qmd collection remove sessions-digest 2>/dev/null && echo "   ✅ sessions-digest" || echo "   ⏭️  sessions-digest not found"
fi

echo ""
echo "⚠️  Please tell your agent to remove Brain cron jobs:"
echo "   - Session Digest"
echo "   - Neural Consolidation"
echo "   - QMD Update Neuron Memory"
echo "   - Forgetting Curve"
echo ""
echo "✅ Uninstall complete. Memory files preserved."
echo "   To fully remove: rm -rf $BRAIN_DIR $WORKSPACE_DIR/neurons"
