---
name: plex-librarian
description: Quản lý và chuẩn hóa cấu trúc thư viện Plex & Jellyfin. Tự động nhận diện (auto-detect) thư mục lưu trữ phim trên NAS qua kết nối SSH/SFTP, tự động ánh xạ cấu trúc phân loại Movies và TV Shows trên Google Drive, chuẩn hóa tên file theo chuẩn TheTVDB/TMDb, tích hợp phụ đề WebVTT và hỗ trợ quét duyệt thư viện.
---

# Plex Librarian Skill (Quản Lý & Ánh Xạ Thư Viện Plex/Jellyfin)

Kỹ năng chuyên trách chuẩn hóa, phân loại và nhận diện vị trí lưu trữ phim trên **NAS Storage** và **Google Drive** theo 100% quy chuẩn tổ chức của **Plex Media Server & Jellyfin**.

---

## 🚀 Cú Pháp Kích Hoạt CLI

```bash
# 1. Tự động quét và nhận diện các thư mục Plex/Jellyfin trên NAS qua SSH:
python3 <skill_dir>/scripts/librarian_cli.py scan-nas --host "192.168.1.50" --user "admin" [--port 22]

# 2. Chuẩn hóa tên file và thư mục một bộ phim trước khi đưa vào thư viện:
python3 <skill_dir>/scripts/librarian_cli.py rename "/path/to/raw_files" --title "Monster" --year 2004 --tvdb 74599

# 3. Quét kiểm tra cấu trúc thư viện Google Drive:
python3 <skill_dir>/scripts/librarian_cli.py inspect-drive --remote "gdrive" --root "Phim"
```

---

## 🛠️ Các Tính Năng Cốt Lõi

1. 🔍 **Tự Động Nhận Diện Thư Mục NAS (SSH Auto-Detection):**
   * Kết nối SSH an toàn tới NAS Synology, QNAP, TrueNAS hoặc Linux Server.
   * Tự động dò tìm các đường dẫn chứa phim phổ biến:
     * `/volume1/video/Movies`, `/volume1/video/TV Shows`
     * `/share/CACHEDEV1_DATA/Multimedia/Plex`
     * `/srv/dev-disk-by-label/Media`
   * Báo cáo chính xác thư mục đích cho `media-sync` mà người dùng không cần nhập tay đường dẫn phức tạp.

2. 🏷️ **Chuẩn Hóa Đặt Tên 100% Chuẩn Plex / Jellyfin:**
   * **TV Series:** `{Show Name} ({Year}) {tvdb-XXXXX}/Season XX/{Show Name} - SXXEXX - {Title} [{Quality}].ext`
   * **Movies:** `Movies/{Movie Name} ({Year})/{Movie Name} ({Year}) [{Quality}].ext`
   * Tự động loại bỏ các tag rác của torrent (`[EMBER]`, `x264-RARBG`, `YIFY`).

3. 🎬 **Tích Hợp Phụ Đề Chuẩn Xác:**
   * Ghép nối các file `.vi.vtt` hoặc `.vi.srt` tương ứng đúng tên tập để Plex tự động bật phụ đề tiếng Việt khi phát.
