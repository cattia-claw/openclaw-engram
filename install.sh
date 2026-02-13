#!/bin/bash
set -e

echo "🧠 OpenClaw Brain — Neural Memory System Installer"
echo "=================================================="
echo ""

# Resolve paths
BRAIN_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_DIR="$(dirname "$BRAIN_DIR")"
NEURONS_DIR="$WORKSPACE_DIR/neurons"

# Load config
SCHEDULE_FILE="$BRAIN_DIR/config/schedule.json"
CATEGORIES_FILE="$BRAIN_DIR/config/categories.json"

if [ ! -f "$SCHEDULE_FILE" ]; then
    echo "❌ Missing config/schedule.json"
    exit 1
fi

TZ=$(python3 -c "import json; print(json.load(open('$SCHEDULE_FILE')).get('timezone','UTC'))")
MODEL=$(python3 -c "import json; print(json.load(open('$SCHEDULE_FILE')).get('model','anthropic/claude-haiku-4-5'))")

echo "📍 Workspace: $WORKSPACE_DIR"
echo "🕐 Timezone: $TZ"
echo "🤖 Model: $MODEL"
echo ""

# Step 1: Create neuron directories
echo "📁 Creating neuron directories..."
CATEGORIES=$(python3 -c "
import json
cats = json.load(open('$CATEGORIES_FILE')).get('categories', {})
for v in cats.values():
    name = v.get('display_name_zh') or v.get('display_name') or 'misc'
    print(name)
")

while IFS= read -r cat; do
    mkdir -p "$NEURONS_DIR/$cat"
    echo "   ✅ neurons/$cat/"
done <<< "$CATEGORIES"

# Step 2: Create memory subdirectories
echo ""
echo "📁 Creating memory directories..."
mkdir -p "$WORKSPACE_DIR/memory/sessions-digest"
mkdir -p "$WORKSPACE_DIR/memory/monthly-summary"
mkdir -p "$WORKSPACE_DIR/memory/archive"
echo "   ✅ memory/sessions-digest/"
echo "   ✅ memory/monthly-summary/"
echo "   ✅ memory/archive/"

# Step 3: Make scripts executable
echo ""
echo "🔧 Making scripts executable..."
chmod +x "$BRAIN_DIR/scripts/"*.py
echo "   ✅ Done"

# Step 4: Set up QMD collections (if QMD is available)
echo ""
if command -v qmd &> /dev/null; then
    echo "🔍 Setting up QMD collections..."

    # Neurons collection
    if ! qmd collection list 2>/dev/null | grep -q "neuron-memory"; then
        qmd collection add "$NEURONS_DIR" --name neuron-memory --mask "**/*.md" 2>/dev/null || true
        echo "   ✅ neuron-memory collection"
    else
        echo "   ⏭️  neuron-memory already exists"
    fi

    # Sessions digest collection
    if ! qmd collection list 2>/dev/null | grep -q "sessions-digest"; then
        qmd collection add "$WORKSPACE_DIR/memory/sessions-digest" --name sessions-digest --mask "**/*.md" 2>/dev/null || true
        echo "   ✅ sessions-digest collection"
    else
        echo "   ⏭️  sessions-digest already exists"
    fi

    echo "   🔄 Running initial embed..."
    qmd embed 2>/dev/null || echo "   ⚠️  Embed skipped (run 'qmd embed' manually)"
else
    echo "⚠️  QMD not found. Semantic search will not be available."
    echo "   Install QMD: npm install -g qmd"
fi

# Step 5: Register cron jobs with OpenClaw
echo ""
echo "⏰ Registering cron jobs..."
echo "   (Requires OpenClaw gateway to be running)"
echo ""

# Check if openclaw is available
if command -v openclaw &> /dev/null; then
    echo "   📋 Cron jobs to register:"
    echo "   1. Session Digest        — 04:00 daily"
    echo "   2. Neural Consolidation  — 04:30 daily"
    echo "   3. QMD Update            — 04:35 daily"
    echo "   4. Forgetting Curve      — 05:00 1st of month"
    echo ""
    echo "   ⚠️  Auto-registration requires OpenClaw cron API."
    echo "   Please tell your agent:"
    echo ""
    echo "   \"Set up Brain cron jobs from $BRAIN_DIR/config/schedule.json\""
    echo ""
else
    echo "   ⚠️  OpenClaw CLI not found."
    echo "   Install: npm install -g openclaw"
fi

# Step 6: Run test consolidation
echo ""
echo "🧪 Running test consolidation..."
YESTERDAY=$(date -v-1d +%Y-%m-%d 2>/dev/null || date -d "yesterday" +%Y-%m-%d 2>/dev/null || echo "")
if [ -n "$YESTERDAY" ]; then
    python3 "$BRAIN_DIR/scripts/session_digest.py" "$YESTERDAY" 2>&1 || echo "   ⚠️  Session digest test skipped"
    python3 "$BRAIN_DIR/scripts/memory_consolidator.py" "$YESTERDAY" 2>&1 || echo "   ⚠️  Consolidator test skipped"
else
    echo "   ⏭️  Skipped (could not determine yesterday's date)"
fi

echo ""
echo "=================================================="
echo "✅ OpenClaw Brain installed successfully!"
echo ""
echo "Next steps:"
echo "  1. Tell your agent to set up cron jobs"
echo "  2. Edit config/categories.json to customize categories"
echo "  3. Your agent should write to memory/YYYY-MM-DD.md daily"
echo ""
echo "🧠 Your agent now has long-term memory!"
