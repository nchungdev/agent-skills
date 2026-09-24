# ⚡ Universal Agent Skills Catalog

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Agent Skills Standard](https://img.shields.io/badge/Standard-Agent%20Skills-brightgreen.svg)](https://agentskills.org)
[![Compatible With](https://img.shields.io/badge/Compatible%20With-Claude%20Code%20|%20Antigravity%20|%20Gemini%20|%20Codex-orange.svg)](#-tương-thích--nền-tảng-hỗ-trợ)
[![Total Skills](https://img.shields.io/badge/Skills%20Catalog-14%20Production%20Skills-purple.svg)](#-danh-mục-agent-skills-skills-catalog)

> **Kho lưu trữ tập trung (Universal Catalog) chứa toàn bộ các Agent Skills & Plugins cao cấp do [@nchungdev](https://github.com/nchungdev) thiết kế.**  
> Thiết kế theo chuẩn mở **Agent Skills Standard (`SKILL.md`)**, sẵn sàng cài đặt, chia sẻ và tương thích đa nền tảng cho mọi AI Agent: **Claude Code, Google Antigravity / Gemini CLI, OpenAI Codex, Cursor, Windsurf**, hoặc bất kỳ Custom Agent runtime nào.

---

## 🌟 Triết Lý Thiết Kế (Core Principles)

* 🔌 **Zero Vendor Lock-in (Tính Phổ Quát Cao):** Tuân thủ tuyệt đối quy chuẩn mở `SKILL.md` (YAML frontmatter + workflow hướng dẫn chi tiết + standalone CLI script). Một skill viết ra dùng được cho tất cả các LLM Agents.
* ⚡ **Zero Runtime Bloat (Siêu Tinh Gọn):** Toàn bộ script helper lõi viết bằng **Python 3 Standard Library** thuần túy, không yêu cầu `pip install` cồng kềnh, chạy tức thì với độ trễ tối thiểu.
* 🛡️ **Zero Secret Leakage (Bảo Mật Tuyệt Đối):** Tích hợp sẵn cơ chế tự động che giấu (redaction) mọi token, API key, mật khẩu và thông tin nhạy cảm trong log, transcript và báo cáo trạng thái.
* 📦 **1-Command Install (Triển Khai Trong 1 Giây):** Tự động liên kết (symlink/copy) vào đúng thư mục cấu hình của từng Agent CLI (`~/.gemini/skills`, `~/.agents/skills`, `~/.codex/skills`) hoặc nạp qua Claude Plugin Marketplace.
* 🧩 **Domain-Driven Architecture (Phân Tách Theo Miền Nghiệp Vụ):** Quản trị dự án & điều phối đa phiên, tự động hóa hạ tầng P2P/Media, studio phụ đề và ngôn ngữ, triển khai cụm transcode phân tán,...

---

## 🏛️ Danh Mục Agent Skills (Skills Catalog)

Hiện repository cung cấp **14 Agent Skills** sẵn sàng thực chiến, được phân theo 4 nhóm chuyên biệt:

### 📊 1. Điều Phối & Quản Trị Dự Án (Project Orchestration & Core Utilities)

| Skill | Chức năng chính | Output / Giao thức |
|---|---|---|
| **`project-reporter`** | Điều phối tiến độ đa phiên (Multi-Conversation Orchestrator), đồng bộ ngữ cảnh (Context Synchronization) qua Sổ Cái `.agent/project_status.json`, tự động che giấu secret và tổng hợp báo cáo tiến độ (`report`, `report all`). | Markdown Matrix, JSON Ledger |

### 🎬 2. Kỹ Thuật & Tự Động Hóa Media (Media Engineering & Automation)

| Skill | Chức năng chính | Công cụ hỗ trợ |
|---|---|---|
| **`media-collector`** | Cố vấn & lập kế hoạch sưu tầm phim, anime, TV Series; tra cứu nguồn magnet/torrent, lập Census bản quyền và ước tính dung lượng lưu trữ. | Torrent, Magnet, Web Search |
| **`media-downloader`** | Tải dữ liệu đa nguồn hiệu năng cao: Direct HTTP/HTTPS, Torrent qua Aria2c P2P RPC client, hoặc Torrent qua TorBox Debrid Cloud API (chống DDoS & Cloudflare bypass). | Aria2c RPC, TorBox API |
| **`cloud-librarian`** | Chuẩn hóa kho media từ xa qua SSH (Synology, QNAP, TrueNAS, Linux) hoặc Google Drive theo định dạng chuẩn Plex/Jellyfin/TheTVDB. | SSH/SFTP, Plex Naming |
| **`media-sync`** | Đồng bộ dữ liệu đa đích tốc độ cao qua Rclone và SSH/SFTP (đẩy song song lên NAS & Google Drive) kèm cơ chế Auto-Purge dọn sạch cache ổ cứng. | Rclone, Rsync, SSH |
| **`tmdb-lookup`** | Tra cứu siêu dữ liệu điện ảnh & truyền hình qua TMDb API v3, tải Poster/Fanart chất lượng cao và tạo file `.nfo` chuẩn Plex/Kodi. | TMDb API v3, NFO Generator |
| **`franchise-classifier`** | Phân loại và gom nhóm phim lẻ, series, OVA, live-action vào một thương hiệu (Franchise/IP tổng thể) từ TMDb ID / TheTVDB ID. | AI + Heuristic Classifier |
| **`media-hub-franchise`** | Tra cứu và sắp xếp danh sách phim vào franchise tương ứng từ cơ sở dữ liệu Media Hub, hỗ trợ mapping mã định danh CSV. | Media Hub SQLite DB |

### 📝 3. Xử Lý Phụ Đề & Ngôn Ngữ (Subtitle & Localization Studio)

| Skill | Chức năng chính | Công cụ hỗ trợ |
|---|---|---|
| **`translate-subtitle`** | Động cơ dịch thuật phụ đề AI 2 tầng chuyên sâu cho phim và anime; bảo vệ mã định dạng typography, timecode và đồng bộ kho thuật ngữ tập trung. | Subtitle Glossary Hub |
| **`subtitle-extractor`** | Tự động phát hiện và bóc tách các track phụ đề nhúng (Muxed Subtitles) từ video container (MKV, MP4, M4V) ra file độc lập `.srt`, `.ass` theo chuẩn Plex. | FFmpeg, FFprobe |
| **`subtitle-frame-aligner`** | Căn chỉnh thời gian (Voice Alignment) từng dòng thoại khớp khẩu hình bằng FFmpeg VAD không tốn token AI, bảo vệ tuyệt đối KFX/karaoke. | FFmpeg Silencedetect / VAD |
| **`sub-to-webvtt`** | Chuyển đổi và làm sạch phụ đề (SRT, ASS, SSA) sang chuẩn WebVTT (`.vtt`) tối ưu hóa trình duyệt phát trực tuyến zero-latency. | W3C WebVTT Parser |

### 🖥️ 4. Hạ Tầng & Cụm Phân Tán (Infrastructure & Distributed Systems)

| Skill | Chức năng chính | Công cụ hỗ trợ |
|---|---|---|
| **`omv-media-stack`** | Thiết kế kiến trúc, ma trận cổng mạng, pipeline tự động hóa (Jellyseerr, Radarr, Sonarr, Prowlarr, Aria2c, Plex) và MergerFS trên OpenMediaVault 7 NAS. | Docker Compose, MergerFS |
| **`tdarr-node`** | Triển khai và vận hành Tdarr Distributed Transcode Node trên Apple Silicon (VideoToolbox), Linux (Intel QSV, NVIDIA NVENC) kèm Path Translators chống lỗi ENOENT. | Tdarr Node, Launchd, Systemd |

---

## 🌐 Tương Thích & Nền Tảng Hỗ Trợ

| Nền tảng AI Agent | Phương thức nhận diện | Thư mục nạp Skill mặc định |
|---|---|---|
| **Claude Code** | Marketplace (`/plugin marketplace add`) hoặc local | `${CLAUDE_PLUGIN_ROOT}/skills/` |
| **Google Antigravity CLI** | Script symlink tự động | `~/.agents/skills/` hoặc `~/.gemini/antigravity-cli/skills/` |
| **Gemini CLI** | Script symlink tự động | `~/.gemini/skills/` |
| **OpenAI Codex CLI** | Script symlink tự động | `~/.codex/skills/` |
| **Cursor / Windsurf / Custom Agent** | Mount trực tiếp vào workspace | `./.agents/skills/` hoặc `~/.cursor/rules/` |

---

## 🚀 Cài Đặt (Installation)

### Cách 1: Cài đặt tự động qua `install.sh` (Khuyên dùng cho mọi CLI)

Clone repository về máy và chạy script cài đặt một lần cho tất cả hoặc từng agent:

```bash
# 1. Clone repository về máy
git clone https://github.com/nchungdev/agent-skills.git ~/.agent-skills
cd ~/.agent-skills

# 2. Cài đặt toàn bộ 14 skills cho TẤT CẢ các Agent CLI (Gemini, Antigravity, Codex)
./install.sh all

# Hoặc chỉ định cài riêng cho từng Agent:
./install.sh gemini       # Chỉ cài cho Gemini CLI (~/.gemini/skills/)
./install.sh antigravity  # Chỉ cài cho Antigravity CLI (~/.agents/skills/)
./install.sh codex        # Chỉ cài cho OpenAI Codex CLI (~/.codex/skills/)

# Tùy chọn:
./install.sh all --copy   # Sao chép file trực tiếp thay vì tạo symlink
./install.sh all --force  # Ghi đè các skill cũ nếu đã tồn tại
```

> **💡 Lưu ý:** Mặc định script sử dụng cơ chế **Symlink**. Khi bạn chạy `git pull` cập nhật repository, mọi Agent sẽ tự động nhận phiên bản mới nhất ngay lập tức mà không cần cài đặt lại!

---

### Cách 2: Cài đặt trên Claude Code qua Plugin Marketplace

```bash
# Thêm marketplace vào Claude Code
/plugin marketplace add nchungdev/agent-skills

# Cài đặt toàn bộ hoặc từng plugin chuyên biệt
/plugin install project-reporter@antigravity-media
/plugin install media-downloader@antigravity-media
/plugin install translate-subtitle@antigravity-media
```

---

### Cách 3: Tích hợp vào một Workspace / Project bất kỳ

Nếu bạn muốn nhúng trực tiếp bộ kỹ năng vào thư mục dự án của riêng mình:

```bash
mkdir -p .agent/skills
# Tạo symlink hoặc copy skill bạn cần vào dự án
ln -s ~/.agent-skills/plugins/project-reporter/skills/project-reporter .agent/skills/
```

---

## 📐 Cấu Trúc Monorepo (Repository Structure)

Mỗi kỹ năng được đóng gói theo chuẩn độc lập, tự chứa (self-contained), vừa là Claude Code Plugin vừa là Native Agent Skill:

```
agent-skills/
├── .claude-plugin/
│   └── marketplace.json            # Manifest danh mục Marketplace cho Claude Code
├── install.sh                      # Shell script tự động cài đặt & liên kết đa nền tảng
├── plugins/
│   ├── project-reporter/
│   │   ├── .claude-plugin/plugin.json
│   │   └── skills/project-reporter/
│   │       ├── SKILL.md            # Chỉ dẫn, workflow & nguyên tắc cho Agent
│   │       └── scripts/            # Standalone CLI tools (reporter.py)
│   ├── media-downloader/
│   │   ├── .claude-plugin/plugin.json
│   │   └── skills/media-downloader/
│   │       ├── SKILL.md
│   │       └── scripts/            # Providers: aria2, torbox, prowlarr, ddl
│   └── ... (các plugin & skill khác)
└── README.md
```

---

## 🛠️ Quy Chuẩn Thêm Skill Mới (How to Add a New Skill)

Kho lưu trữ này được thiết kế để liên tục mở rộng cho mọi chủ đề (DevOps, Data, Web, Mobile, v.v.). Bất kỳ ai cũng có thể đóng góp skill mới bằng cách tuân thủ quy chuẩn sau:

1. Tạo thư mục: `plugins/<plugin-name>/skills/<skill-name>/`
2. Tạo file `SKILL.md` với định dạng chuẩn:
   ```yaml
   ---
   name: your-skill-name
   description: Mô tả ngắn gọn nhiệm vụ của skill và điều kiện Agent nên kích hoạt nó.
   ---
   # Tiêu Đề Skill
   ## 1. Mục đích & Khi nào sử dụng
   ## 2. Các lệnh CLI hoặc Workflow thực thi
   ## 3. Quy tắc bắt buộc (Rules)
   ```
3. Đặt các script thực thi (nếu có) vào thư mục con `scripts/` (ưu tiên Python standard library hoặc Bash POSIX chuẩn).
4. Khai báo plugin vào `.claude-plugin/marketplace.json` và cập nhật `./install.sh`.

---

## 🔗 Hệ Sinh Thái Liên Kết (Ecosystem)

* 🪐 [**nchungdev/media-hub**](https://github.com/nchungdev/media-hub): Ứng dụng Desktop Native & Web Dashboard điều phối tập trung đa nguồn (sử dụng các skill trong repo này làm nền tảng Agent).
* 📚 [**nchungdev/subtitle-glossary-hub**](https://github.com/nchungdev/subtitle-glossary-hub): Kho tri thức và từ điển thuật ngữ dịch thuật phụ đề phim & anime chuẩn hóa.

---

## 📄 Bản Quyền & Giấy Phép

Phát hành theo giấy phép mã nguồn mở [MIT License](LICENSE) — © 2026 **Chung Nguyen Hoai ([@nchungdev](https://github.com/nchungdev))**.  
Tự do sử dụng, tùy biến và chia sẻ cho cộng đồng lập trình viên & người dùng AI Agent.
