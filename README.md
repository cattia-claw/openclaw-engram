# 🧠 OpenClaw Brain — Neural Memory System

A human-brain-inspired memory architecture for [OpenClaw](https://github.com/openclaw/openclaw) AI agents.

Transform your agent from a goldfish (forgets everything each session) into a system with structured long-term memory, automatic consolidation, semantic search, and graceful forgetting.

## Architecture

```
╔═══════════════════════════════════════════════════════════════╗
║                    🧠 Brain Architecture                      ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  👁️ Sensory Buffer     Session JSONL (raw, never deleted)     ║
║         │                                                     ║
║         ▼ 04:00 daily                                         ║
║  🌙 Hippocampus        session_digest.py → markdown summaries ║
║         │                                                     ║
║         ▼ 04:30 daily                                         ║
║  🧬 Consolidation      memory_consolidator.py → categorized   ║
║         │                                                     ║
║         ├──► 📖 Episodic    memory/YYYY-MM-DD.md              ║
║         ├──► 🔬 Semantic    neurons/{category}/YYYY-MM-DD.md  ║
║         └──► 🔧 Procedural  skills/ + TOOLS.md                ║
║                                                               ║
║  🔍 Retrieval           QMD semantic search (local vectors)   ║
║         │                                                     ║
║         ▼                                                     ║
║  💭 Working Memory      Context window (~8K tokens auto-load) ║
║                                                               ║
║  ⏱️ Forgetting Curve    Monthly summary + 90-day archive      ║
╚═══════════════════════════════════════════════════════════════╝
```

## Features

- **Session Digest** — Automatically converts raw session JSONL into readable markdown summaries (filters out noise like heartbeats)
- **Neural Consolidation** — Classifies daily memories into semantic categories (customizable)
- **QMD Integration** — Semantic vector search across all memory layers
- **Forgetting Curve** — Monthly summaries, 90-day archival, graceful memory decay
- **Zero external dependencies** — Pure Python, local vector search, no cloud services needed
- **Minimal cost** — ~$0.03/day for 3 lightweight cron jobs (Haiku)

## Quick Start

```bash
# Clone into your OpenClaw workspace
cd ~/.openclaw/workspace
git clone https://github.com/cattia-claw/openclaw-brain.git brain

# Run the installer
cd brain
chmod +x install.sh
./install.sh
```

The installer will:
1. Create the neuron directory structure
2. Set up QMD collections (if QMD is installed)
3. Register cron jobs with OpenClaw
4. Run a test consolidation

## Directory Structure

After installation:

```
~/.openclaw/workspace/
├── brain/                    # This repo
│   ├── scripts/
│   │   ├── session_digest.py
│   │   ├── memory_consolidator.py
│   │   └── forgetting_curve.py
│   ├── config/
│   │   └── categories.json   # Customizable category rules
│   ├── install.sh
│   └── uninstall.sh
├── neurons/                  # Created by installer
│   ├── emotions/
│   ├── people/
│   ├── topics/
│   └── work/
└── memory/
    ├── YYYY-MM-DD.md         # Daily logs (your agent writes these)
    ├── sessions-digest/      # Auto-generated
    ├── monthly-summary/      # Auto-generated
    └── archive/              # 90+ day old files
```

## Configuration

Edit `config/categories.json` to customize memory categories:

```json
{
  "categories": {
    "emotions": {
      "display_name": "Emotions & Rapport",
      "patterns": ["like", "dislike", "feel", "mood", "prefer"],
      "indicators": ["think", "believe", "opinion"]
    },
    "people": {
      "display_name": "Important People",
      "patterns": ["family", "friend", "colleague", "doctor"],
      "indicators": ["who", "name", "relationship"]
    },
    "topics": {
      "display_name": "Interests & Discussions",
      "patterns": ["hobby", "travel", "game", "movie", "book"],
      "indicators": ["interest", "discuss", "topic"]
    },
    "work": {
      "display_name": "Projects & Tasks",
      "patterns": ["project", "website", "code", "API", "deploy"],
      "indicators": ["task", "TODO", "progress", "done"]
    }
  }
}
```

## Cron Schedule

| Time | Job | Description |
|------|-----|-------------|
| 04:00 | Session Digest | JSONL → markdown summaries |
| 04:30 | Neural Consolidation | Classify daily memories |
| 04:35 | QMD Update | Re-index + embed vectors |
| 1st of month 05:00 | Forgetting Curve | Monthly summary + archive |

All times are configurable in `config/schedule.json`.

## How It Works

### 1. Your Agent Writes Daily Logs

Your OpenClaw agent should write to `memory/YYYY-MM-DD.md` during conversations. Most agents already do this via AGENTS.md conventions.

### 2. Nightly Processing (Hippocampus)

At 4:00 AM, the system:
- Reads all session JSONL files from yesterday
- Filters noise (heartbeats, empty sessions)
- Generates a readable digest in `memory/sessions-digest/`

At 4:30 AM:
- Reads yesterday's daily memory file
- Classifies each entry by keyword matching
- Writes to appropriate neuron category folder

### 3. Semantic Search (Retrieval)

QMD provides local vector search:
```bash
qmd search neurons "what projects did we work on last week?"
```

### 4. Monthly Forgetting

On the 1st of each month:
- Generates a summary of last month across all categories
- Archives daily files older than 90 days
- Cleans up old neuron daily files

## Requirements

- **OpenClaw** v2026.2+ with cron support
- **Python 3.10+** (no pip packages needed)
- **QMD** (optional, for semantic search)

## Customization

### Adding Categories

Add new entries to `config/categories.json`. Categories map to folders under `neurons/`.

### Changing Archive Threshold

Edit `config/schedule.json`:
```json
{
  "archive_days": 90,
  "monthly_summary": true
}
```

### Multilingual Support

Category names and patterns support any language. The default config includes both English and Chinese examples.

## Uninstall

```bash
cd ~/.openclaw/workspace/brain
./uninstall.sh
```

This removes cron jobs but preserves your memory files.

## License

MIT

## Credits

Inspired by human memory architecture:
- **Sensory → Short-term → Long-term** memory model
- **Ebbinghaus forgetting curve**
- **Hippocampal consolidation** during sleep

Built for the [OpenClaw](https://github.com/openclaw/openclaw) ecosystem.
