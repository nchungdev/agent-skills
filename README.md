# 🪐 Antigravity Plugins & Skills Hub

Tập hợp các Plugin và Skill cao cấp dành cho **Google Antigravity**, tối ưu hóa tự động hóa đa phương tiện, xử lý phụ đề điện ảnh, tra cứu siêu dữ liệu TMDb và quản lý tải đám mây TorBox Debrid.

---

## 📦 Danh sách Plugins

### 1. ⚡ `torbox` (`torbox-manager`)
* **Mô tả:** Tích hợp trực tiếp với dịch vụ đám mây **TorBox Debrid** (`api.torbox.app`).
* **Tính năng chính:**
  * 🔐 Đăng nhập xác thực an toàn qua API Token hoặc mở trình duyệt web (`login --browser`).
  * 📋 Liệt kê trạng thái thời gian thực (`downloading`, `completed`, `cached`, `stalled`).
  * 🧲 Thêm nhanh bằng Magnet link hoặc file `.torrent`.
  * 🗑️ Xóa torrent và giải phóng slot tải trên Cloud.
  * 🚀 Tự động kéo file zip từ Cloudflare CDN qua `aria2c` 16 luồng và giải nén chuẩn hóa vào Plex.

### 2. 🎬 `tmdb-lookup`
* **Mô tả:** Tra cứu và phân tích siêu dữ liệu điện ảnh & truyền hình qua The Movie Database (TMDb) API v3.
* **Tính năng chính:**
  * 🔍 Tìm kiếm phim, anime, TV Shows theo tên, TMDb ID, TVDB ID, IMDb ID.
  * 👥 Trích xuất danh sách diễn viên, nhân vật, đạo diễn, studio sản xuất.
  * 🖼️ Tải poster, backdrop/fanart độ phân giải cao gốc.
  * 📄 Xuất file `tvshow.nfo` và `movie.nfo` chuẩn Plex / Jellyfin / Kodi.

### 3. 🎯 `media-collector`
* **Mô tả:** Pipeline tự động hóa thu thập và quản lý thư viện phim ảnh, anime, TV Shows đa thế hệ.
* **Tính năng chính:**
  * 🔍 Tự động tìm kiếm nguồn tải Nyaa, DDL, torrent với bộ lọc chất lượng nghiêm ngặt (tránh watermark, hardsub xấu).
  * 🏷️ Đổi tên và cấu trúc theo chuẩn quốc tế TVDB/Plex.
  * 🧹 Phát hiện và dọn dẹp file trùng lặp, tối ưu hóa bộ nhớ đĩa.

### 4. 📝 `translate-subtitle`
* **Mô tả:** Hệ thống dịch thuật phụ đề phim ảnh AI chuyên nghiệp 2 tầng (Two-Tier Architecture).
* **Tính năng chính:**
  * 🌐 Trích xuất và dịch thuật ngữ theo Master Glossary Hub.
  * 🎨 Định dạng phụ đề ASS/SRT với bộ style điện ảnh tùy biến (Mecha, Trinh thám, Cổ trang, Y khoa).

---

## 🛡️ Bảo mật & Secret Data
* Toàn bộ mã nguồn **không chứa bất kỳ API Key, Token hay thông tin cá nhân nhạy cảm nào**.
* API Key được quản lý cục bộ qua biến môi trường (`TORBOX_API_KEY`, `TMDB_API_KEY`) hoặc file cấu hình an toàn `~/.config/torbox/config.json` (chế độ bảo mật `0600`).
