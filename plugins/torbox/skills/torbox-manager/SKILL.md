---
name: torbox-manager
description: Quản lý TorBox Debrid Cloud (Đăng nhập/xác thực tài khoản, xem danh sách torrents, thêm/xóa magnet/torrent, lấy link DDL trực tiếp, tải từng tập hoặc Zip với ngưỡng 5GB và khoảng nghỉ ngẫu nhiên 5s-90s chống DDoS, đồng bộ Google Drive).
---

# TorBox Manager Skill

Kỹ năng điều khiển và tự động hóa toàn bộ quy trình tải phim / dữ liệu qua dịch vụ đám mây **TorBox Debrid** (`api.torbox.app`).

## 🛠️ Khả năng chính

1. 🔐 **Đăng nhập & Quản lý xác thực (`login`, `whoami`, `logout`):** Hỗ trợ đăng nhập tương tác bằng API Token, mở trình duyệt tới trang cài đặt, kiểm tra trạng thái gói cước và xóa thông tin đăng nhập khi cần.
2. 📋 **Liệt kê danh sách (`list`):** Xem toàn bộ torrents trong tài khoản TorBox (trạng thái: `downloading`, `completed`, `cached`, `stalled`, tiến độ %, dung lượng).
3. 🧲 **Thêm Torrent (`add`):** Thêm nhanh bằng **Magnet link** hoặc upload file `.torrent` vật lý.
4. 🗑️ **Xóa Torrent (`remove`):** Giải phóng slot tải trên TorBox khi đã hoàn tất.
5. ⚡ **Chiến lược tải thông minh (Smart Download Strategy - Ngưỡng 5 GB):**
   * 📦 **`< 5.0 GB`:** Tải nhanh dạng **Zip** trọn gói (phim ngắn, OVA, mini series).
   * 🎬 **`>= 5.0 GB`:** Tự động chia nhỏ tải **Single-File từng tập** (tối đa 2 file song song).
   * 🛡️ **Anti-DDoS & Randomized Jitter Backoff:** Nghỉ ngẫu nhiên **`5s -> 90s`** khi có lỗi/rate-limit và **`1.5s -> 4.5s`** giữa các request thông thường, triệt tiêu hoàn toàn dấu vết bot và chống bị chặn tài khoản.
6. ☁️ **Đồng bộ lũy tiến Google Drive:** Tập nào tải xong là đẩy ngay lên `gdrive:Phim/TV Shows/`.

---

## 💻 Hướng dẫn sử dụng CLI

CLI nằm tại:
`python3 /Users/chungnh/.gemini/config/plugins/torbox/skills/torbox-manager/scripts/torbox_cli.py <command>`

### 1. Đăng nhập tài khoản TorBox:
```bash
# Đăng nhập tương tác (mở trình duyệt tới trang lấy Token):
python3 /Users/chungnh/.gemini/config/plugins/torbox/skills/torbox-manager/scripts/torbox_cli.py login --browser

# Hoặc truyền trực tiếp Token:
python3 /Users/chungnh/.gemini/config/plugins/torbox/skills/torbox-manager/scripts/torbox_cli.py login --token "<API_TOKEN>"
```

### 2. Kiểm tra thông tin tài khoản đang đăng nhập:
```bash
python3 /Users/chungnh/.gemini/config/plugins/torbox/skills/torbox-manager/scripts/torbox_cli.py whoami
```

### 3. Xem danh sách torrents trên TorBox:
```bash
python3 /Users/chungnh/.gemini/config/plugins/torbox/skills/torbox-manager/scripts/torbox_cli.py list
```

### 4. Tự động tải về máy theo chiến lược thông minh (Ngưỡng 5GB):
```bash
python3 /Users/chungnh/.gemini/config/plugins/torbox/skills/torbox-manager/scripts/torbox_cli.py download <TORRENT_ID> --out-dir "/Volumes/512GB/AI Workspace/Target_Folder"
```
