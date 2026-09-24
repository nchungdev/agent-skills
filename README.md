# ⚡ Universal Agent Skills Catalog

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Agent Skills Standard](https://img.shields.io/badge/Standard-Agent%20Skills-brightgreen.svg)](https://agentskills.org)
[![Compatible With](https://img.shields.io/badge/Compatible%20With-Claude%20Code%20|%20Antigravity%20|%20Gemini%20|%20Codex%20|%20Cursor-orange.svg)](#-platform-compatibility)
[![Total Skills](https://img.shields.io/badge/Skills%20Catalog-14%20Production%20Skills-purple.svg)](#-skills-catalog)

> **A curated, production-grade monorepo of modular AI Agent Skills & Plugins crafted by [@nchungdev](https://github.com/nchungdev).**  
> Built strictly on the open **Agent Skills Standard (`SKILL.md`)**, ready to install, distribute, and execute across any AI coding assistant or autonomous runtime: **Claude Code, Google Antigravity / Gemini CLI, OpenAI Codex, Cursor, Windsurf**, and custom agent frameworks.

---

## 🌟 Core Principles

* 🔌 **Zero Vendor Lock-in (Universal Interoperability):** Fully adheres to the open `SKILL.md` specification (YAML frontmatter + step-by-step procedural guidelines + standalone executables). Write once, equip any LLM agent.
* ⚡ **Zero Runtime Bloat:** All core helper scripts are powered by the **Python 3 Standard Library**. Instant execution with zero startup latency and no third-party package dependencies (`pip install`).
* 🛡️ **Zero Secret Leakage (Built-in Redaction):** Hardened with automated pattern-based secret sanitization (`mask_sensitive_data`). Automatically redacts API keys, Bearer tokens, passwords, and private credentials in CLI transcripts, project reports, and shared state files.
* 📦 **1-Command Multi-Agent Installer:** Instant deployment via `./install.sh`. Generates dynamic symlinks into target skill directories across all major AI agent CLIs (`~/.gemini/skills`, `~/.agents/skills`, `~/.codex/skills`) or through the Claude Code Plugin Marketplace.
* 🧩 **Domain-Driven Modular Catalog:** Clear separation of concerns across multi-conversation orchestration, media automation, subtitle & localization studio, and distributed infrastructure.

---

## 🏛️ Skills Catalog

The catalog currently features **14 production-ready Agent Skills**, organized into four functional domains:

### 📊 1. Project Orchestration & Core Utilities

| Skill | Superpower & Description | Output / Protocol |
|---|---|---|
| **`project-reporter`** | Multi-conversation orchestrator & progress reporter. Eliminates context drift across concurrent chat sessions via a centralized ledger (`.agent/project_status.json`), enforces automated secret scrubbing, and provides high-level project visibility (`report`, `report all`). | Markdown Matrix, JSON Ledger |

### 🎬 2. Media Engineering & Automation

| Skill | Superpower & Description | Core Stack / Tooling |
|---|---|---|
| **`media-collector`** | Universal movie, anime, and TV show curator. Evaluates copyright censuses, discovers magnet/torrent sources, estimates disk footprints, and designs standardized library blueprints. | Torrent, Magnet, Web Search |
| **`media-downloader`** | High-performance multi-source downloader supporting Direct HTTP/HTTPS, BitTorrent via Aria2c P2P RPC client, and BitTorrent via TorBox Debrid Cloud API (with Cloudflare/anti-DDoS bypass). | Aria2c RPC, TorBox API |
| **`cloud-librarian`** | Remote library inspector (NAS via SSH, Google Drive). Traverses remote media storage and normalizes directory and file hierarchies according to strict Plex, Jellyfin, and TheTVDB conventions. | SSH/SFTP, Plex Naming |
| **`media-sync`** | High-throughput multi-target synchronization engine using Rclone and SSH/SFTP. Supports concurrent transfers to NAS and Google Drive with automatic post-sync local buffer purging. | Rclone, Rsync, SSH |
| **`tmdb-lookup`** | The Movie Database (TMDb v3) metadata enrichment tool. Fetches film/TV credits, downloads high-resolution posters/fanart, and generates Kodi/Plex-compliant `.nfo` files. | TMDb API v3, NFO Generator |
| **`franchise-classifier`** | Classifies and aggregates standalone films, series, OVAs, and live-actions into their overarching intellectual property (Franchise/IP) from TMDb/TheTVDB IDs using AI reasoning. | AI + Heuristic Classifier |
| **`media-hub-franchise`** | Queries and organizes video collections into franchises against the Media Hub database, enabling automated identifier mapping from CSV files. | Media Hub SQLite DB |

### 📝 3. Subtitle & Localization Studio

| Skill | Superpower & Description | Core Stack / Tooling |
|---|---|---|
| **`translate-subtitle`** | Two-stage deep neural subtitle translation engine tailored for cinema and anime. Preserves complex typography tags and precise timecodes while syncing with centralized glossaries. | Subtitle Glossary Hub |
| **`subtitle-extractor`** | Batch extractor for embedded subtitle streams (Muxed Subtitles) from video containers (MKV, MP4, M4V) into standalone `.srt` and `.ass` files formatted for Plex. | FFmpeg, FFprobe |
| **`subtitle-frame-aligner`** | Frame-perfect voice alignment engine matching subtitle cues to character speech using FFmpeg VAD with zero AI token consumption, preserving KFX/karaoke styling. | FFmpeg Silencedetect / VAD |
| **`sub-to-webvtt`** | Converts and sanitizes subtitle files (SRT, ASS, SSA) into W3C-standard WebVTT (`.vtt`) optimized for zero-latency in-browser web players. | W3C WebVTT Parser |

### 🖥️ 4. Infrastructure & Distributed Systems

| Skill | Superpower & Description | Core Stack / Tooling |
|---|---|---|
| **`omv-media-stack`** | Architecture blueprint, port matrix, media automation pipeline (Jellyseerr, Radarr, Sonarr, Prowlarr, Aria2c, Plex), and MergerFS storage runbooks for OpenMediaVault 7 NAS. | Docker Compose, MergerFS |
| **`tdarr-node`** | Distributed transcoding node operational guide for Tdarr on Apple Silicon (VideoToolbox), Linux (Intel QSV, NVIDIA NVENC), and Docker, including ENOENT-proof Path Translators. | Tdarr Node, Launchd, Systemd |

---

## 🌐 Platform Compatibility

| AI Agent Platform | Discovery Mechanism | Default Target Directory |
|---|---|---|
| **Claude Code** | Marketplace (`/plugin marketplace add`) or local plugin | `${CLAUDE_PLUGIN_ROOT}/skills/` |
| **Google Antigravity CLI** | Automated symlink script | `~/.agents/skills/` or `~/.gemini/antigravity-cli/skills/` |
| **Gemini CLI** | Automated symlink script | `~/.gemini/skills/` |
| **OpenAI Codex CLI** | Automated symlink script | `~/.codex/skills/` |
| **Cursor / Windsurf / Custom Agents** | Project workspace mount or global rules | `./.agents/skills/` or `~/.cursor/rules/` |

---

## 🚀 Installation

### Option 1: Multi-Agent CLI Installer (Recommended)

Clone the repository and run the automated installer to link all skills to your installed agent CLIs:

```bash
# 1. Clone the repository
git clone https://github.com/nchungdev/agent-skills.git ~/.agent-skills
cd ~/.agent-skills

# 2. Install all 14 skills across ALL supported CLIs (Gemini, Antigravity, Codex)
./install.sh all

# Or install for a specific agent:
./install.sh gemini       # Gemini CLI (~/.gemini/skills/)
./install.sh antigravity  # Antigravity CLI (~/.agents/skills/)
./install.sh codex        # OpenAI Codex CLI (~/.codex/skills/)

# Advanced flags:
./install.sh all --copy   # Copy files directly instead of creating symlinks
./install.sh all --force  # Overwrite pre-existing skills
```

> **💡 Pro Tip:** The installer creates **Symlinks** by default. Running `git pull` in this repository immediately updates all installed skills across all your AI agents without re-running the installer!

---

### Option 2: Claude Code Plugin Marketplace

```bash
# Register the marketplace in Claude Code
/plugin marketplace add nchungdev/agent-skills

# Install individual plugins or skills as needed
/plugin install project-reporter@antigravity-media
/plugin install media-downloader@antigravity-media
/plugin install translate-subtitle@antigravity-media
```

---

### Option 3: Per-Project / Workspace Embedding

To attach specific skills directly to a standalone project or Git repository:

```bash
mkdir -p .agent/skills
# Symlink or copy the required skill into your repository
ln -s ~/.agent-skills/plugins/project-reporter/skills/project-reporter .agent/skills/
```

---

## 📐 Monorepo Architecture

Each capability is encapsulated as a self-contained skill packaged both as a Claude Code Plugin and as a native Agent Skill:

```
agent-skills/
├── .claude-plugin/
│   └── marketplace.json            # Claude Code Marketplace Manifest
├── install.sh                      # Universal multi-agent installation script
├── plugins/
│   ├── project-reporter/
│   │   ├── .claude-plugin/plugin.json
│   │   └── skills/project-reporter/
│   │       ├── SKILL.md            # Agent instructions, procedural workflows & rules
│   │       └── scripts/            # Standalone executables (reporter.py)
│   ├── media-downloader/
│   │   ├── .claude-plugin/plugin.json
│   │   └── skills/media-downloader/
│   │       ├── SKILL.md
│   │       └── scripts/            # Providers: aria2, torbox, prowlarr, ddl
│   └── ... (additional plugins & skills)
└── README.md
```

---

## 🛠️ How to Author a New Skill

This repository is built to scale across any engineering domain (DevOps, Data Pipelines, Web Development, Mobile, Security, AI Research). To add a new skill:

1. Create the skill directory: `plugins/<plugin-name>/skills/<skill-name>/`
2. Create a standard `SKILL.md` file:
   ```yaml
   ---
   name: your-skill-name
   description: Concise description of the skill's capability and exact triggering conditions.
   ---
   # Skill Title
   ## 1. Overview & When to Activate
   ## 2. CLI Execution & Procedural Workflows
   ## 3. Mandatory Constraints & Rules
   ```
3. Place helper scripts into `scripts/` (relying on POSIX shell or standard library Python).
4. Register the new skill in `.claude-plugin/marketplace.json` and `./install.sh`.

---

## 🔗 Related Ecosystem

* 🪐 [**nchungdev/media-hub**](https://github.com/nchungdev/media-hub): Standalone Desktop Native & Web Dashboard orchestrator (powered by these agent skills under the hood).
* 📚 [**nchungdev/subtitle-glossary-hub**](https://github.com/nchungdev/subtitle-glossary-hub): Centralized knowledge base and persistent terminology dictionaries for subtitle translation workflows.

---

## 📄 License

Distributed under the [MIT License](LICENSE) — © 2026 **Chung Nguyen Hoai ([@nchungdev](https://github.com/nchungdev))**.  
Free to use, customize, and distribute for the entire AI developer and agentic engineering community.
