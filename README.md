# 🪐 Antigravity Agent Skills & Media Ecosystem

Kho lưu trữ chuẩn hóa các bộ kỹ năng (**Agent Skills & Plugins**) chuyên biệt cho hệ sinh thái **Antigravity Media Hub & AI Agent**.

---

## 🏛️ Kiến Trúc Hệ Sinh Thái (Two-Tier Standard)

### 🚀 1. TẦNG QUY TRÌNH CHÍNH (CORE PIPELINE)
* **`media-hub`**: Trung tâm điều phối & Quản trị cấu hình/tài khoản tập trung (Centralized Credential Hub), đồng thời là Dashboard Web UI thời gian thực cổng 8888 kết nối AI Command Center.
* **`media-downloader`**: Bộ tải dữ liệu đa nguồn (Direct HTTP/DDL, Torrent qua Aria2c Client P2P, hoặc Torrent qua TorBox Debrid Cloud API).
* **`cloud-librarian`**: Nhìn các kho lưu trữ từ xa (NAS qua SSH, Google Drive) như một thư viện kiểu Plex — dò tìm thư mục thư viện đích và sinh tên file chuẩn Plex/Jellyfin.
* **`media-sync`**: Đồng bộ đa đích chuyên nghiệp qua Rclone và SSH/SFTP (hỗ trợ đẩy đồng thời lên NAS & Google Drive, kèm cơ chế Auto-Purge giải phóng 100% bộ đệm sau khi hoàn tất).

---

### 🧰 2. TẦNG HỘP CÔNG CỤ (MEDIA TOOLBOX & UTILITIES)
* **`media-collector`**: Sưu tầm, tìm nguồn torrent/magnet, lập Census bản quyền và ước tính dung lượng.
* **`tmdb-lookup`**: Tra cứu siêu dữ liệu The Movie Database (TMDb v3), tải Poster/Fanart HD và tạo file NFO chuẩn.
* **`translate-subtitle`**: Động cơ dịch thuật phụ đề 2 tầng chuyên sâu cho phim và anime (kèm `subtitle-glossary-hub`).
* **`subtitle-extractor`**: Bóc tách phụ đề nhúng (Muxed Subtitles) từ video container (MKV, MP4, M4V) ra file `.srt`, `.ass`.
* **`sub-to-webvtt`**: Chuyển đổi và làm sạch phụ đề sang chuẩn WebVTT (`.vtt`) tối ưu phát trực tuyến trên trình duyệt.

---

### 📦 3. TIỆN ÍCH MỞ RỘNG KHÁC
* **`subtitle-glossary-hub`** ([nchungdev/subtitle-glossary-hub](https://github.com/nchungdev/subtitle-glossary-hub)): Kho tri thức tập trung của `translate-subtitle` — glossary, workflow và pitfalls tái sử dụng vĩnh viễn. Skill tự kéo về khi cần, không cần cài riêng.

---

## 📥 Cài Đặt

### Claude Code — cài qua marketplace

```bash
/plugin marketplace add nchungdev/agent-skills
/plugin install media-hub@antigravity-media
```

Cài từng plugin theo nhu cầu (`media-downloader@antigravity-media`, `cloud-librarian@antigravity-media`, ...), hoặc mở `/plugin` để duyệt toàn bộ 9 plugin trong marketplace `antigravity-media`.

### Gemini CLI / Antigravity CLI / Codex CLI — cài qua `install.sh`

Ba CLI này nạp **Agent Skills** từ thư mục phẳng, nên script sẽ symlink 9 skill vào đúng vị trí:

```bash
git clone https://github.com/nchungdev/agent-skills.git
cd agent-skills
./install.sh all          # cả ba CLI
./install.sh codex        # hoặc chỉ một: gemini | antigravity | codex
./install.sh all --copy   # sao chép thay vì symlink
```

| CLI | Thư mục đích |
|---|---|
| Gemini CLI | `~/.gemini/skills/` |
| Antigravity CLI | `~/.agents/skills/` |
| Codex CLI | `~/.codex/skills/` |

Mặc định script tạo **symlink**, nên `git pull` trong repo là mọi CLI nhận bản mới ngay. Dùng `--force` để ghi đè skill trùng tên đã có.

> **Lưu ý:** Codex CLI cũng tự đọc thư mục skill của Claude Code, nên nếu đã cài qua marketplace ở trên thì có thể bỏ qua bước này cho Codex.

### Quy ước `<skill_dir>` trong các SKILL.md

Lệnh CLI trong tài liệu skill viết dưới dạng `python3 <skill_dir>/scripts/...`. Thay `<skill_dir>` bằng đường dẫn thật của skill sau khi cài:

| Môi trường | `<skill_dir>` |
|---|---|
| Claude Code | `${CLAUDE_PLUGIN_ROOT}/skills/<tên-skill>` |
| Gemini / Antigravity / Codex | `~/.gemini/skills/<tên-skill>` (hoặc `~/.agents/skills/`, `~/.codex/skills/`) |
| Chạy trực tiếp từ repo | `plugins/<tên-plugin>/skills/<tên-skill>` |

### Yêu cầu hệ thống

Toàn bộ script chỉ dùng **Python 3 standard library** (không cần `pip install`). Một số skill gọi công cụ ngoài khi thực thi: `ffmpeg`/`ffprobe` (subtitle-extractor, media-hub), `aria2c` (media-downloader, media-hub), `rclone` (media-sync, media-collector, media-hub), `rsync`/`ssh` (media-sync, cloud-librarian, media-collector, media-hub) và `yt-dlp` (media-hub).

---

## 📄 Giấy Phép

Phát hành theo giấy phép [MIT](LICENSE) — © 2026 Chung Nguyen Hoai (nchungdev).
