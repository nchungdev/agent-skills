---
name: torbox-manager
description: Quản lý TorBox Debrid Cloud (Đăng nhập/xác thực tài khoản, xem danh sách torrents, thêm/xóa magnet/torrent, lấy link DDL trực tiếp, và tải siêu tốc qua aria2c đa luồng).
---

# TorBox Manager Skill

Kỹ năng điều khiển và tự động hóa toàn bộ quy trình tải phim / dữ liệu qua dịch vụ đám mây **TorBox Debrid** (`api.torbox.app`).

## 🛠️ Khả năng chính

1. 🔐 **Đăng nhập & Quản lý xác thực (`login`, `whoami`, `logout`):** Hỗ trợ đăng nhập tương tác bằng API Token, mở trình duyệt tới trang cài đặt, kiểm tra trạng thái gói cước (Essential / Pro) và xóa thông tin đăng nhập khi cần.
2. 📋 **Liệt kê danh sách (`list`):** Xem toàn bộ torrents trong tài khoản TorBox (trạng thái: `downloading`, `completed`, `cached`, `stalled`, tiến độ %, dung lượng).
3. 🧲 **Thêm Torrent (`add`):** Thêm nhanh bằng **Magnet link** hoặc upload file `.torrent` vật lý.
4. 🗑️ **Xóa Torrent (`remove`):** Giải phóng slot tải trên TorBox khi đã hoàn tất.
5. 🔗 **Lấy Link Tải Trực Tiếp (`get-link`):** Trích xuất link CDN Direct Download (DDL) tốc độ cao (Cloudflare CDN).
6. ⚡ **Tự động tải & giải nén (`download`):** Tự động gọi `aria2c` đa luồng kéo file zip từ TorBox CDN về máy và giải nén chuẩn hóa vào thư mục đích.

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

### 4. Thêm Magnet Link hoặc file .torrent:
```bash
python3 /Users/chungnh/.gemini/config/plugins/torbox/skills/torbox-manager/scripts/torbox_cli.py add "magnet:?xt=urn:btih:..."
python3 /Users/chungnh/.gemini/config/plugins/torbox/skills/torbox-manager/scripts/torbox_cli.py add "/path/to/file.torrent"
```

### 5. Xóa torrent trên TorBox:
```bash
python3 /Users/chungnh/.gemini/config/plugins/torbox/skills/torbox-manager/scripts/torbox_cli.py remove <TORRENT_ID>
```

### 6. Lấy link tải DDL (Zip/File):
```bash
python3 /Users/chungnh/.gemini/config/plugins/torbox/skills/torbox-manager/scripts/torbox_cli.py get-link <TORRENT_ID>
```

### 7. Tự động tải về máy với `aria2c` và giải nén:
```bash
python3 /Users/chungnh/.gemini/config/plugins/torbox/skills/torbox-manager/scripts/torbox_cli.py download <TORRENT_ID> --out-dir "/Volumes/512GB/AI Workspace/Target_Folder"
```

### 8. Đăng xuất:
```bash
python3 /Users/chungnh/.gemini/config/plugins/torbox/skills/torbox-manager/scripts/torbox_cli.py logout
```
