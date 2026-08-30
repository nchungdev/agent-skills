# 🤖 Universal AI Agent Skills Hub

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Cross-AI Compatible](https://img.shields.io/badge/agents-Claude%20%7C%20Codex%20%7C%20Antigravity%20%7C%20OpenCode-success.svg)](https://github.com/nchungdev/agent-skills)
[![Security Audited](https://img.shields.io/badge/security-Zero--Secrets%20Audited-green.svg)](https://github.com/nchungdev/agent-skills)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Kho lưu trữ chuẩn hóa các **Agent Skills & Plugins độc lập** được thiết kế theo tiêu chuẩn công cụ mở (*Universal Tooling Interface*), tương thích cắm-và-chạy (*plug-and-play*) trên mọi nền tảng AI Coding Assistant và Autonomous Multi-Agent Frameworks.

---

## 🧭 Ma Trận Tương Thích Đa Nền Tảng (Cross-AI Matrix)

| AI Agent Platform | Giao Thức Kích Hoạt | Cách Cấu Hình |
| :--- | :--- | :--- |
| 🟣 **Claude Code (Anthropic CLI)** | Native Terminal / `CLAUDE.md` | Thêm đường dẫn CLI vào `CLAUDE.md` |
| 🔵 **Google Antigravity (DeepMind AGY)** | Skills Engine / `SKILL.md` | Đặt thư mục vào `~/.gemini/config/skills/` |
| 🟢 **OpenAI Codex / OpenCode** | System Prompt / `AGENTS.md` | Tham chiếu lệnh trong `CODEX.md` hoặc `AGENTS.md` |
| ⚡ **Nodeterm Canvas Sessions** | Shared Terminal Workspace | Dùng chung Python environment và shared configs |

---

## 📦 Danh Mục Skills & Hướng Dẫn Sử Dụng

### 1. ⚡ `torbox-manager` (v1.2.0)
* **Vị trí:** `plugins/torbox/skills/torbox-manager/`
* **Mô tả:** Tự động hóa toàn diện quy trình quản lý đám mây **TorBox Debrid** (`api.torbox.app`), hỗ trợ tải siêu tốc qua `aria2c` đa luồng, chống DDoS chuẩn JDownloader-2 và tự động đồng bộ Google Drive.
* **Tính năng chủ lực:**
  * 🔐 **Xác thực an toàn (`login --browser`):** Hỗ trợ mở trình duyệt lấy Token, lưu cấu hình bảo mật `0600` tại `~/.config/torbox/config.json`.
  * 📋 **Quản lý chuyển khoản (`list`, `add`, `remove`):** Quản lý trạng thái downloading, cached, completed, stalled thời gian thực.
  * 📏 **Smart Download Strategy (Ngưỡng 5GB):**
    * Dung lượng `< 5.0 GB`: Tự động tải **Zip** trọn gói (phim ngắn, OVA, Movie).
    * Dung lượng `>= 5.0 GB`: Tự động chia nhỏ tải **Single-File từng tập** (tối đa 2 file song song).
  * 🛡️ **JDownloader-2 Engine:** Đọc header `Retry-After`, áp dụng thuật toán *Exponential Backoff + Randomized Jitter (5s - 90s)* và giả lập Headers Chrome 128 đầy đủ để tránh bị rate-limit / ban IP.
  * ☁️ **Incremental Cloud Sync:** Tải xong tập nào tự động đổi tên chuẩn Plex và đẩy ngay lên Google Drive tập đó.

```bash
# Đăng nhập xác thực:
python3 plugins/torbox/skills/torbox-manager/scripts/torbox_cli.py login --browser

# Xem danh sách torrents trên Cloud:
python3 plugins/torbox/skills/torbox-manager/scripts/torbox_cli.py list

# Tải thông minh về thư mục đích:
python3 plugins/torbox/skills/torbox-manager/scripts/torbox_cli.py download <TORRENT_ID> -o "/path/to/downloads"
```

---

### 2. 🎬 `tmdb-lookup` (v1.1.0)
* **Vị trí:** `plugins/tmdb-lookup/skills/tmdb-lookup/`
* **Mô tả:** Tra cứu, phân tích và trích xuất siêu dữ liệu điện ảnh & truyền hình qua **The Movie Database (TMDb) API v3**.
* **Tính năng chủ lực:**
  * 🔍 **Tìm kiếm đa năng (`search`):** Hỗ trợ tra cứu theo tên phim, Anime, TV Shows hoặc theo ID (TMDb, TVDB, IMDb).
  * 👥 **Phân tích nhân sự (`details`):** Trích xuất danh sách diễn viên, vai diễn (*Cast & Characters*), đạo diễn, hãng sản xuất.
  * 🖼️ **Tải Media Art (`download-images`):** Tự động tải poster, backdrop/fanart độ phân giải cao gốc.
  * 📄 **Xuất file NFO chuẩn (`export-nfo`):** Tạo file `tvshow.nfo` và `movie.nfo` chuẩn hóa cho Plex, Jellyfin, Kodi.

```bash
# Tìm kiếm phim:
python3 plugins/tmdb-lookup/skills/tmdb-lookup/scripts/tmdb_client.py search "Kingdom" --type tv

# Xuất thông tin chi tiết & dàn cast:
python3 plugins/tmdb-lookup/skills/tmdb-lookup/scripts/tmdb_client.py details 259259 --type tv

# Xuất file NFO chuẩn Plex/Kodi:
python3 plugins/tmdb-lookup/skills/tmdb-lookup/scripts/tmdb_client.py export-nfo 259259 --type tv -o "/path/to/series"
```

---

### 3. 🎯 `media-collector` (v1.0.0)
* **Vị trí:** `plugins/media-collector/skills/media-collector/`
* **Mô tả:** Pipeline tự động hóa thu thập, phân loại và chuẩn hóa thư viện media cá nhân.
* **Tính năng chủ lực:**
  * 🔍 **Bộ lọc chất lượng nghiêm ngặt (Strict Quality Gate):** Tự động loại bỏ các bản rip dính logo fansub/kênh truyền hình to bản, chặn hardsub chết, ưu tiên Master DVD 480p sạch hoặc BDRip 1080p 10-bit HEVC.
  * 🏷️ **Plex/TVDB Auto-Rename:** Tự động gom Season và đổi tên chuẩn mực `Series (Year) {tvdb-XXXXX}/Season XX/Series - SXXEXX.ext`.
  * 🧹 **Dọn dẹp trùng lặp (Deduplication):** Tự động phát hiện và loại bỏ các file trùng, tối ưu dung lượng đĩa.

---

### 4. 📝 `translate-subtitle` (v1.0.0)
* **Vị trí:** `plugins/translate-subtitle/skills/translate-subtitle/`
* **Mô tả:** Hệ thống dịch thuật phụ đề AI 2 tầng (*Two-Tier Translation Pipeline*) chuyên sâu cho phim ảnh và anime.
* **Tính năng chủ lực:**
  * 🌐 **Master Glossary Hub:** Đồng bộ và ánh xạ thuật ngữ nhân vật, chiêu thức, bối cảnh lịch sử / y khoa chính xác.
  * 🎨 **Cinematic ASS Styling:** Cung cấp bộ styles phụ đề ASS tùy biến chuyên nghiệp (Mecha Karaoke, Trinh thám, Y khoa, Phim rạp).

---

## 📜 Nhật Ký Phiên Bản (Skill Version Changelog)

### ⚡ `torbox-manager`
* **`v1.2.0` (2026-08-30):**
  * 🛡️ Tích hợp **JDownloader-2 Engine**: Tự động đọc header `Retry-After` từ server, áp dụng thuật toán *Exponential Backoff* kết hợp *Randomized Jitter (5s - 90s)*.
  * 🌐 Bổ sung bộ giả lập Headers trình duyệt Chrome 128 macOS đầy đủ chống Cloudflare WAF bot detection.
  * 📏 Cập nhật chiến lược tải thông minh với **Ngưỡng 5.0 GB** (< 5GB tải Zip, >= 5GB tải Single-File 2 luồng song song).
  * ☁️ Bổ sung Daemon tự động đồng bộ lũy tiến Google Drive (`auto_cloud_sync_watcher`).
* **`v1.1.0` (2026-08-30):**
  * 🔐 Bổ sung hệ thống xác thực tương tác (`login --browser`, `whoami`, `logout`) với cơ chế phân quyền bảo mật file cấu hình `0600`.
  * ⚡ Bổ sung cơ chế tải nối tiếp (`--continue=true`) chống đứt đoạn mạng cho file dung lượng lớn.
* **`v1.0.0` (2026-08-30):**
  * 🚀 Khởi tạo skill: Hỗ trợ kết nối REST API v1, liệt kê danh sách torrents, thêm magnet/torrent và lấy link DDL trực tiếp.

### 🎬 `tmdb-lookup`
* **`v1.1.0` (2026-08-29):**
  * 📄 Bổ sung tính năng xuất file metadata `.nfo` chuẩn cấu trúc XML cho Plex, Jellyfin và Kodi.
  * 🖼️ Tối ưu hóa tải ảnh poster/backdrop gốc với độ phân giải cao nhất từ máy chủ TMDb CDN.
* **`v1.0.0` (2026-08-28):**
  * 🚀 Khởi tạo skill: Tra cứu phim, anime, TV Shows đa CSDL qua TMDb API v3 độc lập.

### 🎯 `media-collector`
* **`v1.0.0` (2026-08-28):**
  * 🚀 Khởi tạo pipeline: Săn tìm torrent, lọc chất lượng video Master sạch và tự động cấu trúc thư viện Plex.

### 📝 `translate-subtitle`
* **`v1.0.0` (2026-08-28):**
  * 🚀 Khởi tạo hệ thống dịch thuật phụ đề AI 2 tầng với Master Glossary Hub.

---

## 🛡️ Chính Sách Bảo Mật & Quản Trị Bí Mật (Zero-Secrets Policy)

* 🔒 **Không lưu trữ Secret trong mã nguồn:** Toàn bộ repository tuyệt đối không chứa API Key, Token hay thông tin đăng nhập nhạy cảm.
* 📁 **Quản lý Token cục bộ:** API Keys được nạp tự động qua biến môi trường (`TORBOX_API_KEY`, `TMDB_API_KEY`) hoặc lưu trữ trong file cấu hình người dùng cục bộ `~/.config/torbox/config.json` với phân quyền nghiêm ngặt `0600` (chỉ user sở hữu có quyền đọc/ghi).

---

## 🤝 Hướng Dẫn Đóng Góp (Contributing)

Mọi đóng góp nâng cấp tính năng hoặc bổ sung Skill mới đều được hoan nghênh! Vui lòng tuân thủ các quy tắc:
1. Đảm bảo mỗi Skill có đầy đủ file `SKILL.md` và mã nguồn CLI độc lập trong thư mục `scripts/`.
2. Tuân thủ chính sách **Zero-Secrets** (không hardcode API key).
3. Cập nhật nhật ký thay đổi trong phần **Changelog**.
