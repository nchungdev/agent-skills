# 🪐 Antigravity Agent Skills & Media Ecosystem

Kho lưu trữ chuẩn hóa các bộ kỹ năng (**Agent Skills & Plugins**) chuyên biệt cho hệ sinh thái **Antigravity Media Hub & AI Agent**.

---

## 🏛️ Kiến Trúc Hệ Sinh Thái (Two-Tier Standard)

### 🚀 1. TẦNG QUY TRÌNH CHÍNH (CORE PIPELINE)
* **`media-hub`**: Trung tâm điều phối & Quản trị cấu hình/tài khoản tập trung (Centralized Credential Hub), đồng thời là Dashboard Web UI thời gian thực cổng 8888 kết nối AI Command Center.
* **`media-downloader`**: Bộ tải dữ liệu đa nguồn (Direct HTTP/DDL, Torrent qua Aria2c Client P2P, hoặc Torrent qua TorBox Debrid Cloud API).
* **`plex-librarian`**: Quản lý & chuẩn hóa cấu trúc thư viện Plex/Jellyfin, tự động nhận diện thư mục lưu trữ qua SSH NAS và Google Drive.
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
* **`expense-tracker`**: Quản lý chi tiêu và tự động đồng bộ hóa đơn Shopee.
