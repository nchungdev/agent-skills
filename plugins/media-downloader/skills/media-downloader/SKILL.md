---
name: media-downloader
description: Bộ tải dữ liệu đa nguồn chuyên nghiệp. Hỗ trợ tải Direct Download Link (HTTP/HTTPS), tải Torrent/Magnet qua Aria2c RPC (đồng bộ Web GUI AriaNg), tải Torrent qua TorBox Debrid Cloud API, và tải Video/YouTube/Stream qua MeTube Web GUI (yt-dlp).
---

# Media Downloader Skill (Quản Lý Tải Xuống)

Kỹ năng quản trị và điều phối toàn bộ luồng kéo dữ liệu media về bộ đệm tạm thời (`Staging Buffer`) với **4 Provider cốt lõi đồng bộ Web GUI**:
1. 🔗 **`direct`**: Tải link trực tiếp HTTP/HTTPS/DDL qua multi-connection.
2. 🧲 **`aria2`**: Tải torrent/magnet/DDL đẩy thẳng vào **Aria2 RPC Daemon** (hiển thị trực tiếp và quản lý trên **AriaNg Web GUI** `http://192.168.1.37:6880`).
3. 📺 **`metube`**: Tải video/stream/YouTube/Playlist đẩy thẳng vào **MeTube REST API** (hiển thị trực tiếp và quản lý trên **MeTube Web GUI** `http://192.168.1.37:8081`).
4. ☁️ **`torbox`**: Tải torrent qua dịch vụ Debrid Cloud TorBox (`api.torbox.app`), lấy link DDL tốc độ cao.

---

## ⚠️ NGUYÊN TẮC BẮT BUỘC: ĐỒNG BỘ CLI VÀ WEB GUI

> [!IMPORTANT]
> **Mọi tiến trình tải khởi chạy từ CLI hoặc Script bắt buộc phải liên kết vào Web GUI tương ứng:**
> - **Video stream / YouTube / Playlist**: KHÔNG chạy `yt-dlp` detached trên terminal. PHẢI gửi qua `metube-dl` hoặc `downloader_cli.py --provider metube` để người dùng theo dõi được trên Web GUI MeTube (`:8081`).
> - **Torrent / Magnet / Direct Link**: KHÔNG chạy binary `aria2c` one-shot detached. PHẢI gửi qua Aria2 RPC (`aria2-add` hoặc `downloader_cli.py --provider aria2`) để người dùng theo dõi và quản lý trên AriaNg (`:6880`).

---

## 🚀 Cú Pháp Kích Hoạt CLI

```bash
# 1. Tải Video / YouTube / Playlist (Đồng bộ MeTube Web GUI :8081):
python3 <skill_dir>/scripts/downloader_cli.py download "https://www.youtube.com/watch?v=..." --provider metube --out-dir "TV Shows/ShowName"
# Hoặc dùng CLI shortcut:
metube-dl "https://www.youtube.com/watch?v=..." "TV Shows/ShowName" best

# 2. Tải Torrent / Magnet bằng Aria2c RPC (Đồng bộ AriaNg Web GUI :6880):
python3 <skill_dir>/scripts/downloader_cli.py download "magnet:?xt=urn:btih:..." --provider aria2 --out-dir "/srv/mergerfs/MainPool/downloads"
# Hoặc dùng CLI shortcut:
aria2-add "magnet:?xt=urn:btih:..." "/srv/mergerfs/MainPool/downloads"

# 3. Tải Torrent qua TorBox Debrid Cloud:
python3 <skill_dir>/scripts/downloader_cli.py download "magnet:?xt=urn:btih:..." --provider torbox --out-dir "/path/to/staging"

# 4. Tải bằng Direct Link (HTTP/DDL):
python3 <skill_dir>/scripts/downloader_cli.py download "https://example.com/video.mp4" --provider direct --out-dir "/path/to/staging"

# 5. Xem danh sách torrent trên TorBox hoặc Aria2:
python3 <skill_dir>/scripts/downloader_cli.py list --provider torbox
python3 <skill_dir>/scripts/downloader_cli.py list --provider aria2
```

---

## 🛠️ Các Tính Năng Chi Tiết

1. 📺 **MeTube Provider (Web GUI Video Stream Downloader):**
   * Đẩy job qua REST API (`http://127.0.0.1:8081/add`).
   * Tự động tạo thư mục con theo cấu trúc Plex/Jellyfin (`folder`).
   * Hiển thị đầy đủ tiến độ %, tốc độ, ETA, cho phép Pause/Cancel trực tiếp trên Web GUI.

2. 🧲 **Aria2 Provider (AriaNg Web GUI Integration):**
   * Kết nối Aria2 JSON-RPC (`http://127.0.0.1:6800/jsonrpc` với secret token `As123456`).
   * Xuất hiện ngay lập tức trên dashboard AriaNg (`http://192.168.1.37:6880`).
   * Tự động fallback sang binary cục bộ nếu RPC daemon không phản hồi.

3. ⚡ **Direct Download Provider:**
   * Tự động chia nhỏ nhiều luồng kết nối tải nhanh (Multi-threaded chunk download).
   * Tự động resume (tải tiếp) khi bị rớt mạng.

4. ☁️ **TorBox Provider (Cloud Debrid):**
   * Kế thừa trọn vẹn sức mạnh của TorBox API v2.
   * Chiến lược tải thông minh với ngưỡng 5GB (Zip trọn gói vs Single-file từng tập).
   * Cơ chế Jitter Backoff 5s-90s triệt tiêu rate-limit và dấu vết bot.
