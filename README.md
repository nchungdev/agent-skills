# 🤖 Universal AI Agent Skills Hub

Tập hợp các **Skills & Plugins độc lập, chuẩn hóa quốc tế** dành cho mọi hệ thống AI Coding Assistant & Autonomous Agents:
* 🟣 **Claude Code** (Anthropic Claude CLI)
* 🟢 **OpenAI Codex / OpenCode**
* 🔵 **Google Antigravity** (DeepMind AGY)
* ⚡ **Nodeterm Canvas Multi-Agent Sessions**

---

## 🌟 Tính năng tương thích đa nền tảng (Cross-AI Compatibility)
* **Zero Dependency:** Toàn bộ công cụ được xây dựng dưới dạng các Standalone Python CLI Scripts có thể gọi trực tiếp từ Terminal của bất kỳ AI nào.
* **Auto-Discovery:** Tuân thủ cấu trúc `SKILL.md` (YAML Frontmatter + Markdown Instruction) giúp mọi mô hình LLM tự động nhận diện thời điểm và cách thức kích hoạt.
* **Bảo mật tuyệt đối:** Không chứa Secret Data/API Key. Quản lý xác thực an toàn qua `~/.config/` (phân quyền `0600`) hoặc biến môi trường.

---

## 📦 Danh mục Skills & Plugins

### 1. ⚡ `torbox-manager` (`plugins/torbox`)
* **Mô tả:** Tích hợp trực tiếp với dịch vụ đám mây **TorBox Debrid** (`api.torbox.app`).
* **Tính năng:**
  * 🔐 Đăng nhập tương tác an toàn (`login --browser`) & xác thực tài khoản.
  * 📋 Liệt kê trạng thái thời gian thực (`downloading`, `completed`, `cached`, `stalled`).
  * 🧲 Thêm nhanh bằng Magnet link hoặc file `.torrent`.
  * 🗑️ Xóa torrent và giải phóng slot tải trên Cloud.
  * 🚀 **Smart Download Strategy (Ngưỡng 5GB):**
    * `< 5 GB`: Tải nhanh dạng Zip trọn gói.
    * `>= 5 GB`: Tải Single-File cuốn chiếu từng tập (tối đa 2 luồng song song).
  * 🛡️ **JDownloader-2 Grade Anti-DDoS:** Đọc header `Retry-After`, áp dụng Exponential Backoff + Randomized Jitter `5s -> 90s`, giả lập Chrome Headers 128 đầy đủ.
  * ☁️ Tự động đồng bộ lũy tiến lên Google Drive.

### 2. 🎬 `tmdb-lookup` (`plugins/tmdb-lookup`)
* **Mô tả:** Tra cứu và phân tích siêu dữ liệu điện ảnh & truyền hình qua The Movie Database (TMDb) API v3.
* **Tính năng:**
  * 🔍 Tìm kiếm phim, anime, TV Shows theo tên, TMDb ID, TVDB ID, IMDb ID.
  * 👥 Trích xuất danh sách diễn viên, nhân vật, đạo diễn, studio sản xuất.
  * 🖼️ Tải poster, backdrop/fanart độ phân giải cao gốc.
  * 📄 Xuất file `tvshow.nfo` và `movie.nfo` chuẩn Plex / Jellyfin / Kodi.

### 3. 🎯 `media-collector` (`plugins/media-collector`)
* **Mô tả:** Pipeline tự động hóa thu thập và quản lý thư viện phim ảnh, anime đa thế hệ.
* **Tính năng:**
  * 🔍 Săn tìm nguồn tải Nyaa, DDL với bộ lọc chất lượng nghiêm ngặt (chặn logo fansub, chặn hardsub chết, chỉ lấy Master sạch).
  * 🏷️ Đổi tên và cấu trúc theo chuẩn quốc tế TVDB/Plex.
  * 🧹 Phát hiện và dọn dẹp file trùng lặp, tối ưu hóa bộ nhớ đĩa.

### 4. 📝 `translate-subtitle` (`plugins/translate-subtitle`)
* **Mô tả:** Hệ thống dịch thuật phụ đề phim ảnh AI chuyên nghiệp 2 tầng (Two-Tier Architecture).
* **Tính năng:**
  * 🌐 Trích xuất và dịch thuật ngữ theo Master Glossary Hub.
  * 🎨 Định dạng phụ đề ASS/SRT với bộ style điện ảnh tùy biến (Mecha, Trinh thám, Cổ trang, Y khoa).

---

## 🚀 Cách tích hợp vào Agent của bạn

### 🟣 Dành cho Claude Code:
Thêm vào `CLAUDE.md`:
```markdown
## Universal Skills:
- Quản lý TorBox: `python3 ~/.gemini/config/skills/torbox-manager/scripts/torbox_cli.py <command>`
- Tra cứu TMDb: `python3 ~/.gemini/config/skills/tmdb-lookup/scripts/tmdb_client.py <command>`
```

### 🔵 Dành cho Google Antigravity:
Đặt skill vào `~/.gemini/config/skills/` — Antigravity sẽ tự động kích hoạt khi có ngữ cảnh phù hợp.

### 🟢 Dành cho OpenAI Codex / OpenCode:
Khai báo trong `CODEX.md` hoặc `AGENTS.md` tương tự như trên.
