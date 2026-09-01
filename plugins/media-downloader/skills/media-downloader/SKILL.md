---
name: media-downloader
description: Bộ tải dữ liệu đa nguồn chuyên nghiệp. Hỗ trợ tải Direct Download Link (HTTP/HTTPS), tải Torrent/Magnet nội bộ qua Aria2c (P2P Client), hoặc tải Torrent qua TorBox Debrid Cloud API (kéo DDL tốc độ cao, quản lý hàng đợi, ngưỡng 5GB và jitter backoff chống chặn bot).
---

# Media Downloader Skill (Quản Lý Tải Xuống)

Kỹ năng quản trị và điều phối toàn bộ luồng kéo dữ liệu media về bộ đệm tạm thời (`Staging Buffer`) với **3 Provider cốt lõi**:
1. 🔗 **`direct`**: Tải link trực tiếp HTTP/HTTPS/DDL qua multi-connection.
2. 🧲 **`aria2`**: Tải torrent/magnet P2P trực tiếp trên máy client bằng daemon Aria2c.
3. ☁️ **`torbox`**: Tải torrent qua dịch vụ Debrid Cloud TorBox (`api.torbox.app`), lấy link DDL tốc độ cao.

---

## 🚀 Cú Pháp Kích Hoạt CLI

```bash
# 1. Tải bằng Direct Link (HTTP/DDL):
python3 <skill_dir>/scripts/downloader_cli.py download "https://example.com/video.mp4" --provider direct --out-dir "/path/to/staging"

# 2. Tải Torrent bằng Aria2c (P2P Client trên máy):
python3 <skill_dir>/scripts/downloader_cli.py download "magnet:?xt=urn:btih:..." --provider aria2 --out-dir "/path/to/staging"

# 3. Tải Torrent qua TorBox Debrid Cloud:
python3 <skill_dir>/scripts/downloader_cli.py download "magnet:?xt=urn:btih:..." --provider torbox --out-dir "/path/to/staging"

# 4. Xem danh sách torrent trên TorBox hoặc Aria2:
python3 <skill_dir>/scripts/downloader_cli.py list --provider torbox
python3 <skill_dir>/scripts/downloader_cli.py list --provider aria2
```

---

## 🛠️ Các Tính Năng Chi Tiết

1. ⚡ **Direct Download Provider:**
   * Tự động chia nhỏ nhiều luồng kết nối tải nhanh (Multi-threaded chunk download).
   * Tự động resume (tải tiếp) khi bị rớt mạng.

2. 🧲 **Aria2 Provider (Client-Side P2P):**
   * Kết nối với Aria2 RPC Daemon hoặc chạy trực tiếp binary `aria2c`.
   * Hỗ trợ DHT, PEX, cấu hình port và giới hạn băng thông.

3. ☁️ **TorBox Provider (Cloud Debrid):**
   * Kế thừa trọn vẹn sức mạnh của TorBox API v2.
   * Chiến lược tải thông minh với ngưỡng 5GB (Zip trọn gói vs Single-file từng tập).
   * Cơ chế Jitter Backoff 5s-90s triệt tiêu rate-limit và dấu vết bot.
