# 🪐 Antigravity Agent Skills & Media Ecosystem

Kho lưu trữ chuẩn hóa bộ **8 Agent Skills & Plugins** chuyên biệt cho hệ sinh thái **AI Agent & Media Automation**.

> 🚀 **Media Hub Standalone App**: Ứng dụng Desktop & Web Dashboard điều phối trung tâm đã được tách thành repository riêng biệt tại [**nchungdev/media-hub**](https://github.com/nchungdev/media-hub). Bộ kỹ năng trong repository này cung cấp toàn bộ năng lực AI Agent xử lý ngầm cho Media Hub.

---

## 🏛️ Danh Sách 8 Agent Skills

### 🚀 1. TẦNG QUY TRÌNH CHÍNH (CORE PIPELINE)
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

### 📦 3. HỆ SINH THÁI LIÊN KẾT (RELATED REPOSITORIES)
* 🪐 [**nchungdev/media-hub**](https://github.com/nchungdev/media-hub): Ứng dụng Desktop Native Electron & Web Dashboard điều phối tập trung, quản lý hàng đợi, Subtitle Studio và giám sát CLI Console realtime.
* 📚 [**nchungdev/subtitle-glossary-hub**](https://github.com/nchungdev/subtitle-glossary-hub): Kho tri thức tập trung của `translate-subtitle` — glossary, workflow và quy chuẩn thuật ngữ phim/anime tái sử dụng vĩnh viễn.

---

## 📥 Cài Đặt

### Claude Code — cài qua marketplace

```bash
/plugin marketplace add nchungdev/agent-skills
/plugin install translate-subtitle@antigravity-media
```

Cài từng plugin theo nhu cầu (`media-downloader@antigravity-media`, `cloud-librarian@antigravity-media`, ...), hoặc mở `/plugin` để duyệt toàn bộ 8 plugin trong marketplace `antigravity-media`.

### Gemini CLI / Antigravity CLI / Codex CLI — cài qua `install.sh`

Ba CLI này nạp **Agent Skills** từ thư mục phẳng, script sẽ symlink 8 skill vào đúng vị trí:

```bash
git clone https://github.com/nchungdev/agent-skills.git
cd agent-skills
./install.sh all          # cả ba CLI
./install.sh antigravity  # hoặc chỉ một: gemini | antigravity | codex
./install.sh all --copy   # sao chép thay vì symlink
```

| CLI | Thư mục đích |
|---|---|
| Gemini CLI | `~/.gemini/skills/` |
| Antigravity CLI | `~/.agents/skills/` |
| Codex CLI | `~/.codex/skills/` |

Mặc định script tạo **symlink**, nên `git pull` trong repo là mọi CLI nhận bản mới ngay. Dùng `--force` để ghi đè skill trùng tên đã có.

### Quy ước `<skill_dir>` trong các SKILL.md

Lệnh CLI trong tài liệu skill viết dưới dạng `python3 <skill_dir>/scripts/...`. Thay `<skill_dir>` bằng đường dẫn thật của skill sau khi cài:

| Môi trường | `<skill_dir>` |
|---|---|
| Claude Code | `${CLAUDE_PLUGIN_ROOT}/skills/<tên-skill>` |
| Gemini / Antigravity / Codex | `~/.gemini/skills/<tên-skill>` (hoặc `~/.agents/skills/`, `~/.codex/skills/`) |
| Chạy trực tiếp từ repo | `plugins/<tên-plugin>/skills/<tên-skill>` |

### Yêu cầu hệ thống

Toàn bộ script chỉ dùng **Python 3 standard library** (không cần `pip install`). Một số skill gọi công cụ ngoài khi thực thi: `ffmpeg`/`ffprobe` (subtitle-extractor), `aria2c` (media-downloader), `rclone` (media-sync, media-collector), `rsync`/`ssh` (media-sync, cloud-librarian, media-collector).

---

## 📄 Giấy Phép

Phát hành theo giấy phép [MIT](LICENSE) — © 2026 Chung Nguyen Hoai (nchungdev).
