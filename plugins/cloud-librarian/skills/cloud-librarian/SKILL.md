---
name: cloud-librarian
description: Nhìn các kho lưu trữ từ xa như một thư viện media kiểu Plex. Tự động dò tìm thư mục thư viện Plex/Jellyfin trên NAS (Synology, QNAP, TrueNAS, Unraid, Linux server) qua SSH để lấy đường dẫn đích cho media-sync, và sinh đường dẫn đặt tên chuẩn Plex/TheTVDB cho TV Series sau khi làm sạch tag rác của torrent. Phần duyệt thư viện Google Drive do media-hub đảm nhiệm.
---

# Cloud Librarian Skill (Thư Viện Media Trên Kho Lưu Trữ Từ Xa)

Kỹ năng nhìn các kho lưu trữ từ xa — trước hết là **NAS** qua SSH/SFTP — như một thư viện media duy nhất theo quy chuẩn tổ chức của **Plex Media Server & Jellyfin**: dò đúng thư mục thư viện, và sinh đường dẫn đặt tên chuẩn trước khi `media-sync` đẩy file lên.

---

## 🚀 Cú Pháp Kích Hoạt CLI

```bash
# 1. Dò tìm thư mục thư viện Plex/Jellyfin trên NAS qua SSH:
python3 <skill_dir>/scripts/librarian_cli.py scan-nas --host "192.168.1.50" --user "admin" [--port 22] [--key ~/.ssh/id_ed25519]

# 2. Sinh đường dẫn đặt tên chuẩn Plex cho một tập phim:
python3 <skill_dir>/scripts/librarian_cli.py format-name --title "Monster" --year 2004 --tvdb 74599 --season 1 --episode 1
```

---

## 🛠️ Các Tính Năng Cốt Lõi

1. 🔍 **Dò Tìm Thư Mục Thư Viện Trên NAS (SSH Auto-Detection)** — lệnh `scan-nas`
   * Kết nối SSH (`BatchMode`, timeout 5 giây) tới NAS Synology, QNAP, TrueNAS, Unraid hoặc Linux server.
   * Kiểm tra danh sách đường dẫn thư viện phổ biến: `/volume1/video`, `/volume1/Media`, `/volume1/Plex`, `/volume2/video`, `/share/Multimedia`, `/share/CACHEDEV1_DATA/Multimedia`, `/mnt/user/Media`, `/srv/media`, `/var/media`.
   * Trả về JSON các thư mục thực sự tồn tại, để `media-sync` dùng làm đích mà người dùng không phải gõ tay đường dẫn.

2. 🏷️ **Sinh Đường Dẫn Chuẩn Plex / TheTVDB** — lệnh `format-name`
   * Làm sạch tag rác của torrent trong tên: `[EMBER]`, `x264-RARBG`, `1080p BluRay`, `WEB-DL`, `HEVC`, `AAC`, `DUAL`...
   * Xuất đường dẫn: `TV Shows/{Show} ({Year}) {tvdb-XXXXX}/Season XX/{Show} - SXXEXX - [{Quality}].{ext}`.

---

## ⚠️ Phạm Vi Hiện Tại

* `format-name` mới sinh layout **TV Shows**; phim lẻ (Movies) chưa hỗ trợ.
* Duyệt và ánh xạ thư viện **Google Drive** do `media-hub` đảm nhiệm (qua Rclone); skill này chưa có lệnh riêng cho Drive.
* Ghép phụ đề đúng tên tập do `subtitle-extractor` và `sub-to-webvtt` xử lý.

---

## 🔗 Vị Trí Trong Pipeline

`media-downloader` (tải về staging) ➔ **`cloud-librarian`** (dò thư mục đích + đặt tên chuẩn) ➔ `media-sync` (đẩy lên NAS / Google Drive).
