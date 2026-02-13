#!/usr/bin/env python3
"""
Session Digest — Convert JSONL session files into readable markdown summaries.

Brain analogy: Sensory buffer → Episodic memory consolidation

Usage:
  python3 session_digest.py [YYYY-MM-DD]  # defaults to yesterday
"""

import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Resolve paths relative to this script's location
SCRIPT_DIR = Path(__file__).resolve().parent
BRAIN_DIR = SCRIPT_DIR.parent
WORKSPACE_DIR = BRAIN_DIR.parent

# OpenClaw sessions directory (standard location)
SESSIONS_DIR = Path.home() / ".openclaw" / "agents" / "main" / "sessions"
DIGEST_DIR = WORKSPACE_DIR / "memory" / "sessions-digest"

# Load timezone from config
CONFIG_FILE = BRAIN_DIR / "config" / "schedule.json"
if CONFIG_FILE.exists():
    with CONFIG_FILE.open() as f:
        _config = json.load(f)
    _tz_name = _config.get("timezone", "UTC")
    # Simple offset mapping for common timezones
    _TZ_OFFSETS = {
        "Asia/Taipei": 8, "Asia/Tokyo": 9, "Asia/Shanghai": 8,
        "US/Eastern": -5, "US/Pacific": -8, "Europe/London": 0,
        "Europe/Berlin": 1, "UTC": 0,
    }
    _offset = _TZ_OFFSETS.get(_tz_name, 0)
    LOCAL_TZ = timezone(timedelta(hours=_offset))
else:
    LOCAL_TZ = timezone.utc


def parse_session(jsonl_path: Path) -> dict:
    """Parse a single JSONL session file."""
    session = {
        "id": "", "start_time": None, "end_time": None,
        "model": "", "messages": [], "tools_used": [],
        "is_cron": False, "cron_name": "",
    }

    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            obj_type = obj.get("type", "")
            timestamp = obj.get("timestamp", "")

            if timestamp:
                try:
                    ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    if session["start_time"] is None:
                        session["start_time"] = ts
                    session["end_time"] = ts
                except ValueError:
                    pass

            if obj_type == "session":
                session["id"] = obj.get("id", "")
            elif obj_type == "model_change":
                session["model"] = obj.get("modelId", "")
            elif obj_type == "message":
                msg = obj.get("message", {})
                role = msg.get("role", "")
                text = _extract_text(msg.get("content", ""))
                if text:
                    if role == "user" and "[cron:" in text:
                        session["is_cron"] = True
                        m = re.search(r"\[cron:\S+\s+(.+?)\]", text)
                        if m:
                            session["cron_name"] = m.group(1)
                    session["messages"].append({
                        "role": role, "text": text, "timestamp": timestamp,
                    })
            elif obj_type == "tool_use":
                name = obj.get("name", "")
                if name and name not in session["tools_used"]:
                    session["tools_used"].append(name)

    return session


def _extract_text(content) -> str:
    if isinstance(content, str):
        return content.strip()
    elif isinstance(content, list):
        return " ".join(
            c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"
        ).strip()
    return ""


def generate_digest(session: dict) -> str:
    lines = []
    start = session["start_time"]
    time_str = start.astimezone(LOCAL_TZ).strftime("%H:%M") if start else "??:??"
    kind = "🤖 Cron" if session["is_cron"] else "💬 Chat"
    title = session.get("cron_name", "") if session["is_cron"] else "Session"

    lines.append(f"### {time_str} {kind}: {title}")
    lines.append(f"- **Model**: {session['model']}")
    if session["tools_used"]:
        lines.append(f"- **Tools**: {', '.join(session['tools_used'][:10])}")
    lines.append("")

    for msg in session["messages"]:
        text = msg["text"]
        if len(text) > 500:
            text = text[:500] + "…"
        text = re.sub(r"\[cron:\S+\s+.+?\]\s*", "", text)

        if msg["role"] == "user":
            lines.append(f"**👤 User**: {text}")
        elif msg["role"] == "assistant" and text and not text.startswith("<"):
            lines.append(f"**🤖 Assistant**: {text}")
        lines.append("")

    return "\n".join(lines)


def process_date(target_date: str):
    target = datetime.strptime(target_date, "%Y-%m-%d").replace(tzinfo=LOCAL_TZ)
    target_start_utc = target.replace(hour=0, minute=0, second=0).astimezone(timezone.utc)
    target_end_utc = target.replace(hour=23, minute=59, second=59).astimezone(timezone.utc)

    sessions = []
    for f in SESSIONS_DIR.glob("*.jsonl"):
        mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
        if mtime < target_start_utc - timedelta(days=1) or mtime > target_end_utc + timedelta(days=1):
            continue

        s = parse_session(f)
        if s["start_time"] is None:
            continue
        if s["start_time"].astimezone(LOCAL_TZ).date() != target.date():
            continue
        if len(s["messages"]) < 2:
            continue

        # Filter heartbeat noise
        is_hb = s["is_cron"] and "heartbeat" in s.get("cron_name", "").lower()
        has_substance = any(
            m["role"] == "assistant" and m["text"]
            and m["text"] not in ("HEARTBEAT_OK", "NO_REPLY", "")
            and not m["text"].startswith("<")
            for m in s["messages"]
        )
        if is_hb and not has_substance:
            continue

        sessions.append(s)

    sessions.sort(key=lambda s: s["start_time"] or datetime.min.replace(tzinfo=timezone.utc))

    if not sessions:
        print(f"📭 {target_date}: No sessions to digest")
        return

    DIGEST_DIR.mkdir(parents=True, exist_ok=True)
    digest_file = DIGEST_DIR / f"{target_date}.md"

    total_msgs = sum(len(s["messages"]) for s in sessions)
    cron_count = sum(1 for s in sessions if s["is_cron"])
    chat_count = len(sessions) - cron_count
    all_tools = set()
    for s in sessions:
        all_tools.update(s["tools_used"])

    lines = [
        f"# Session Digest: {target_date}", "",
        f"{len(sessions)} sessions", "",
        "## 📊 Stats",
        f"- Chat: {chat_count} | Cron: {cron_count}",
        f"- Messages: {total_msgs}",
    ]
    if all_tools:
        lines.append(f"- Tools: {', '.join(sorted(all_tools))}")
    lines.extend(["", "## 📝 Sessions", ""])

    for s in sessions:
        lines.append(generate_digest(s))
        lines.extend(["---", ""])

    digest_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ {target_date}: Digested {len(sessions)} sessions → {digest_file}")


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else (datetime.now(LOCAL_TZ) - timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"📖 Session Digest — {datetime.now(LOCAL_TZ).strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)
    process_date(target)
    print("=" * 50)


if __name__ == "__main__":
    main()
