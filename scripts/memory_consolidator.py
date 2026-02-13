#!/usr/bin/env python3
"""
Neural Memory Consolidator — Classify daily memories into neuron categories.

Brain analogy: Hippocampal replay during sleep → long-term memory formation.

Usage:
  python3 memory_consolidator.py [YYYY-MM-DD]  # defaults to yesterday
"""

import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BRAIN_DIR = SCRIPT_DIR.parent
WORKSPACE_DIR = BRAIN_DIR.parent
MEMORY_DIR = WORKSPACE_DIR / "memory"
NEURONS_DIR = WORKSPACE_DIR / "neurons"

# Load categories from config
CONFIG_FILE = BRAIN_DIR / "config" / "categories.json"
SCHEDULE_FILE = BRAIN_DIR / "config" / "schedule.json"

_TZ_OFFSETS = {
    "Asia/Taipei": 8, "Asia/Tokyo": 9, "Asia/Shanghai": 8,
    "US/Eastern": -5, "US/Pacific": -8, "Europe/London": 0,
    "Europe/Berlin": 1, "UTC": 0,
}

if SCHEDULE_FILE.exists():
    with SCHEDULE_FILE.open() as f:
        _sched = json.load(f)
    LOCAL_TZ = timezone(timedelta(hours=_TZ_OFFSETS.get(_sched.get("timezone", "UTC"), 0)))
else:
    LOCAL_TZ = timezone.utc


def load_categories() -> dict:
    if CONFIG_FILE.exists():
        with CONFIG_FILE.open() as f:
            config = json.load(f)
        return config.get("categories", {}), config.get("default_category", "work")
    # Fallback defaults
    return {
        "work": {"patterns": ["project", "code", "deploy"], "indicators": ["task", "done"]},
    }, "work"


CATEGORIES, DEFAULT_CATEGORY = load_categories()


def parse_daily_memory(date_str: str) -> list[dict]:
    memory_file = MEMORY_DIR / f"{date_str}.md"
    if not memory_file.exists():
        return []

    content = memory_file.read_text(encoding="utf-8")
    entries = []
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("## ") or (line.startswith("- ") and len(line) > 5):
            entries.append({
                "content": line.lstrip("#- ").strip(),
                "raw": line,
            })
    return entries


def classify_entry(entry: dict) -> str:
    content = entry["content"].lower()
    scores = defaultdict(int)

    for cat_key, rules in CATEGORIES.items():
        for pattern in rules.get("patterns", []):
            if pattern.lower() in content:
                scores[cat_key] += 2
        for indicator in rules.get("indicators", []):
            if indicator.lower() in content:
                scores[cat_key] += 1

    if not scores:
        return DEFAULT_CATEGORY
    return max(scores, key=scores.get)


def consolidate(date_str: str):
    entries = parse_daily_memory(date_str)
    if not entries:
        print(f"📭 {date_str}: No memories to consolidate")
        return

    classified = defaultdict(list)
    for entry in entries:
        category = classify_entry(entry)
        classified[category].append(entry)

    for category, items in classified.items():
        # Use display name for folder if available
        display = CATEGORIES.get(category, {})
        folder_name = display.get("display_name_zh") or display.get("display_name") or category
        target_dir = NEURONS_DIR / folder_name
        target_dir.mkdir(parents=True, exist_ok=True)

        target_file = target_dir / f"{date_str}.md"
        existing = []
        if target_file.exists():
            existing = [l for l in target_file.read_text(encoding="utf-8").split("\n") if l.strip()]

        all_content = existing + [item["raw"] for item in items]
        unique = list(dict.fromkeys(all_content))

        header = f"# {date_str} Memory Consolidation\n\n"
        target_file.write_text(header + "\n".join(unique), encoding="utf-8")
        print(f"📝 {folder_name}: {len(items)} entries → {target_file.name}")

    print(f"✅ {date_str}: Consolidated {len(entries)} entries")


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else (datetime.now(LOCAL_TZ) - timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"🧠 Neural Memory Consolidator — {datetime.now(LOCAL_TZ).strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)
    consolidate(target)
    print("=" * 50)


if __name__ == "__main__":
    main()
