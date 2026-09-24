---
name: media-downloader
description: Universal media curation and high-performance multi-source ingestion pipeline. Evaluates copyright censuses, estimates disk footprints, searches torrent/magnet sources via Prowlarr/Nyaa, and executes accelerated downloads via Aria2c RPC, TorBox Debrid Cloud API (with Cloudflare bypass), and direct HTTP/HTTPS. Supports local download and remote dispatch directly to NAS storage, with built-in real-time queue reporting (`media-downloader report`).
---

# Media Downloader & Ingestion Pipeline Skill

Bộ kỹ năng toàn diện cho quy trình sưu tầm, thẩm định dung lượng và kéo dữ liệu media đa nguồn. Hợp nhất năng lực lập kế hoạch (Curation/Census) và các động cơ tải hiệu năng cao (Aria2c RPC, TorBox Debrid, Prowlarr, MeTube).

---

## 🚀 Các Lệnh CLI Cốt Lõi

```bash
# 1. Báo cáo tiến độ tải về (Realtime Queue Report):
python3 <skill_dir>/scripts/downloader_cli.py report
# Hoặc xem danh sách theo từng provider:
python3 <skill_dir>/scripts/downloader_cli.py list --provider aria2
python3 <skill_dir>/scripts/downloader_cli.py list --provider torbox

# 2. Tải Torrent / Magnet bằng Aria2c RPC (Đồng bộ AriaNg Web GUI :6880):
python3 <skill_dir>/scripts/downloader_cli.py download "magnet:?xt=urn:btih:..." --provider aria2 --out-dir "/srv/mergerfs/MainPool/Phim/..."

# 3. Tải Torrent qua TorBox Debrid Cloud API (Cloudflare/anti-DDoS bypass):
python3 <skill_dir>/scripts/downloader_cli.py download "magnet:?xt=urn:btih:..." --provider torbox --out-dir "/path/to/staging"

# 4. Tìm kiếm nguồn torrent qua Prowlarr Indexer:
python3 <skill_dir>/scripts/providers/prowlarr_provider.py search "The Westward Season 5"

# 5. Tải bằng Direct Link (HTTP/HTTPS):
python3 <skill_dir>/scripts/downloader_cli.py download "https://example.com/file.mp4" --provider direct --out-dir "/path/to/staging"
```

---

## 💾 Ước Tính Dung Lượng (Disk Space Estimation)

> [!IMPORTANT]
> Agent **bắt buộc phải tính toán dung lượng ước tính và kiểm tra ổ đĩa còn trống (`df -h`) TRƯỚC KHI bắt đầu tải**.

| Chuẩn Video & Codec | ~Mỗi Tập Anime (24p) | ~Mỗi Tập TV Show (45p) | ~Mỗi Phim Lẻ (90-120p) |
|---|:---:|:---:|:---:|
| **720p BDRip (x264)** | ~300 MB | ~600 MB | ~1.5 – 3 GB |
| **1080p BDRip (x264/H.264)** | ~500 MB – 1 GB | ~1 – 2 GB | ~3 – 8 GB |
| **1080p HEVC (x265)** | ~300 – 600 MB | ~600 MB – 1.2 GB | ~2 – 5 GB |
| **1080p BD Remux (Lossless)** | ~2 – 4 GB | ~4 – 8 GB | ~15 – 35 GB |
| **4K UHD (HEVC / HDR)** | ~3 – 6 GB | ~5 – 10 GB | ~20 – 60 GB |

---

## 🎮 Hai Chế Độ Tải (Local vs Remote Dispatch)

1. **Local Mode (Tải về máy cá nhân)**:
   - Dùng khi người dùng muốn lưu phim trên laptop/PC cá nhân để xem offline.
   - File tải về thư mục staging cục bộ.
2. **Remote Dispatch Mode (Bắn lệnh sang NAS tải ngầm)**:
   - Dùng khi người dùng yêu cầu: *"Tải trực tiếp trên NAS"*.
   - Agent gửi lệnh vào **Aria2 JSON-RPC của NAS** (`http://<nas-ip>:6800/jsonrpc`).
   - NAS tự kết nối tải thẳng vào pool `/srv/mergerfs/MainPool/Phim/...`. Laptop có thể tắt máy mà không ảnh hưởng tới tiến độ.

---

## 📊 Định Dạng Báo Cáo: `media-downloader report`

Khi được yêu cầu báo cáo tiến độ tải, Agent truy vấn Aria2 và TorBox để render bảng thời gian thực:

```markdown
### 📊 Báo Cáo Tiến Độ Tải Về (Media Downloader Dashboard)
> **Engine**: Aria2c RPC | **Đích lưu**: `/srv/mergerfs/MainPool/Phim/...`
> **Tốc độ**: ⬇️ `18.5 MB/s` | ⬆️ `2.1 MB/s` | **Ổ đĩa còn trống**: `1.4 TB`

| # | Tập / Tên Tệp | Kích Thước | Tiến Độ (%) | Tốc Độ | Nguồn / Client | Trạng Thái |
|:---:|---|:---:|:---:|:---:|:---:|:---:|
| 1 | `The Westward - S05E01.mkv` | 450 MB | 100% | — | Aria2c NAS | ✅ Hoàn tất |
| 2 | `The Westward - S05E02.mkv` | 465 MB | 78% | 6.2 MB/s | Aria2c NAS | ⏳ Đang tải (ETA 1m) |
```
