#!/usr/bin/env python3
"""
Forgetting Curve — Monthly summary + automatic archival of old memories.

Brain analogy: Ebbinghaus forgetting curve — old memories fade,
important ones are strengthened through consolidation.

Usage:
  python3 forgetting_curve.py              # Full monthly run
  python3 forgetting_curve.py --summary YYYY-MM  # Generate specific month
"""

import json
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BRAIN_DIR = SCRIPT_DIR.parent
WORKSPACE_DIR = BRAIN_DIR.parent
MEMORY_DIR = WORKSPACE_DIR / "memory"
NEURONS_DIR = WORKSPACE_DIR / "neurons"
ARCHIVE_DIR = MEMORY_DIR / "archive"
MONTHLY_DIR = MEMORY_DIR / "monthly-summary"
DIGEST_DIR = MEMORY_DIR / "sessions-digest"

CONFIG_FILE = BRAIN_DIR / "config" / "categories.json"
SCHEDULE_FILE = BRAIN_DIR / "config" / "schedule.json"

_TZ_OFFSETS = {
    "Asia/Taipei": 8, "Asia/Tokyo": 9, "Asia/Shanghai": 8,
    "US/Eastern": -5, "US/Pacific": -8, "Europe/London": 0,
    "Europe/Berlin": 1, "UTC": 0,
}

# Load config
ARCHIVE_DAYS = 90
if SCHEDULE_FILE.exists():
    with SCHEDULE_FILE.open() as f:
        _sched = json.load(f)
    LOCAL_TZ = timezone(timedelta(hours=_TZ_OFFSETS.get(_sched.get("timezone", "UTC"), 0)))
    ARCHIVE_DAYS = _sched.get("archive_days", 90)
else:
    LOCAL_TZ = timezone.utc

# Load category names
CATEGORY_NAMES = []
if CONFIG_FILE.exists():
    with CONFIG_FILE.open() as f:
        _cats = json.load(f).get("categories", {})
    for v in _cats.values():
        CATEGORY_NAMES.append(v.get("display_name_zh") or v.get("display_name") or "")


def get_date_files(directory: Path, pattern: str = "*.md") -> list[tuple[str, Path]]:
    results = []
    for f in directory.glob(pattern):
        try:
            datetime.strptime(f.stem, "%Y-%m-%d")
            results.append((f.stem, f))
        except ValueError:
            continue
    return sorted(results)


def generate_monthly_summary(year: int, month: int):
    MONTHLY_DIR.mkdir(parents=True, exist_ok=True)
    month_str = f"{year}-{month:02d}"
    summary_file = MONTHLY_DIR / f"{month_str}.md"

    lines = [f"# Monthly Summary: {month_str}", ""]

    # Daily memories
    lines.append("## 📝 Daily Highlights")
    daily_count = 0
    for date_str, filepath in get_date_files(MEMORY_DIR):
        if date_str.startswith(month_str):
            content = filepath.read_text(encoding="utf-8")
            key_lines = [l.strip() for l in content.split("\n")
                        if l.strip().startswith("## ") or l.strip().startswith("- ⭐") or l.strip().startswith("- **")]
            if key_lines:
                lines.append(f"\n### {date_str}")
                lines.extend(key_lines[:10])
                daily_count += 1
    lines.append(f"\n*{daily_count} days*")

    # Neuron categories
    lines.append("\n## 🧠 Neuron Summary")
    for cat_name in CATEGORY_NAMES:
        cat_dir = NEURONS_DIR / cat_name
        if not cat_dir.exists():
            continue
        entries = []
        for date_str, filepath in get_date_files(cat_dir):
            if date_str.startswith(month_str):
                content = filepath.read_text(encoding="utf-8")
                entries.extend(l.strip() for l in content.split("\n")
                             if l.strip().startswith("- ") or l.strip().startswith("## "))
        if entries:
            lines.append(f"\n### {cat_name}")
            lines.extend(list(dict.fromkeys(entries))[:15])

    # Session highlights
    lines.append("\n## 💬 Chat Highlights")
    for date_str, filepath in get_date_files(DIGEST_DIR):
        if date_str.startswith(month_str):
            content = filepath.read_text(encoding="utf-8")
            for line in content.split("\n"):
                if line.startswith("### ") and "💬" in line:
                    lines.append(f"- {date_str}: {line.lstrip('# ')}")

    summary_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"📊 Monthly summary: {summary_file}")


def archive_old_files():
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(LOCAL_TZ)
    cutoff = now - timedelta(days=ARCHIVE_DAYS)
    count = 0

    for date_str, filepath in get_date_files(MEMORY_DIR):
        if datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=LOCAL_TZ) < cutoff:
            shutil.move(str(filepath), str(ARCHIVE_DIR / filepath.name))
            count += 1
            print(f"📦 Archived: {filepath.name}")

    for date_str, filepath in get_date_files(DIGEST_DIR):
        if datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=LOCAL_TZ) < cutoff:
            shutil.move(str(filepath), str(ARCHIVE_DIR / f"digest-{filepath.name}"))
            count += 1

    # Clean old neuron daily files
    for cat_name in CATEGORY_NAMES:
        cat_dir = NEURONS_DIR / cat_name
        if not cat_dir.exists():
            continue
        for date_str, filepath in get_date_files(cat_dir):
            if datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=LOCAL_TZ) < cutoff:
                filepath.unlink()
                count += 1

    print(f"{'✅ Archived ' + str(count) + ' files' if count else '📭 Nothing to archive'}")


def run_monthly():
    now = datetime.now(LOCAL_TZ)
    last_year = now.year - 1 if now.month == 1 else now.year
    last_month = 12 if now.month == 1 else now.month - 1

    print(f"🌙 Forgetting Curve — {now.strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)
    generate_monthly_summary(last_year, last_month)
    archive_old_files()
    print("=" * 50)
    print("✨ Done")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--summary":
        ym = sys.argv[2] if len(sys.argv) > 2 else datetime.now(LOCAL_TZ).strftime("%Y-%m")
        y, m = ym.split("-")
        generate_monthly_summary(int(y), int(m))
    else:
        run_monthly()


if __name__ == "__main__":
    main()
