---
name: media-sync
description: Media destination dispatcher, library standardizer, and multi-target cloud/NAS synchronization engine. Normalizes directory naming according to strict Plex/TheTVDB conventions, auto-discovers NAS library paths via SSH, executes parallel high-throughput transfers to NAS (SSH/SFTP/rsync) and Google Drive (Rclone), guides Rclone account onboarding/switching, enforces post-transfer local cache auto-purging, and reports sync status (`media-sync report`).
---

# Media Sync & Library Dispatcher Skill

Bộ kỹ năng đóng vai trò **Thủ thư chuẩn hóa (Librarian)** và **Động cơ phân phối dữ liệu đa đích (Sync Engine)**: Chuẩn hóa tên file theo chuẩn Plex/TheTVDB, tự động dò tìm thư mục NAS qua SSH, điều phối truyền tải lên Google Drive (qua Rclone) và NAS, kèm cơ chế tự động xóa đệm (Auto-Purge).

---

## 🚀 Các Lệnh CLI Cốt Lõi

```bash
# 1. Báo cáo trạng thái đồng bộ (Sync Report):
python3 <skill_dir>/scripts/sync_cli.py report

# 2. Dò tìm thư mục thư viện trên NAS từ xa qua SSH:
python3 <skill_dir>/scripts/librarian_cli.py scan-nas --host "<nas-ip>" --user "<username>"

# 3. Sinh đường dẫn chuẩn Plex/TheTVDB cho tập phim:
python3 <skill_dir>/scripts/librarian_cli.py format-name --title "The Westward" --year 2018 --tvdb 371131 --season 5 --episode 1

# 4. Đồng bộ lên Google Drive (qua Rclone):
python3 <skill_dir>/scripts/sync_cli.py sync --target gdrive --source "/local/path" --remote-path "Phim/TV Shows" [--auto-purge]

# 5. Đồng bộ lên NAS lưu trữ (qua SSH/SFTP/Rsync):
python3 <skill_dir>/scripts/sync_cli.py sync --target nas --source "/local/path" --remote-path "/srv/mergerfs/MainPool/Phim" [--auto-purge]
```

---

## 🏛️ 1. Chuẩn Hóa Tên Thư Mục Plex / TheTVDB (Librarian)

Tự động làm sạch các tag rác torrent (`1080p`, `WEB-DL`, `x265`, `AAC`, `[EMBER]`) và sinh layout chuẩn:

```
TV Shows/
└── The Westward (2018) {tvdb-371131} {tmdb-83031}/
    └── Season 05/
        ├── The Westward - S05E01.mkv
        └── The Westward - S05E01.vi.srt
```

---

## ☁️ 2. Hướng Dẫn Cấu Hình & Đổi Tài Khoản Rclone

Rclone quản lý tài khoản theo **Tên Remote (Remote Names)**:
* `gdrive_plex:` — Google Drive lưu trữ phim
* `gdrive_personal:` — Google Drive cá nhân

### Đăng nhập tài khoản mới (Interactive Login):
```bash
# Máy có trình duyệt web (tự động bật tab OAuth):
rclone config create gdrive_plex drive scope drive

# Máy không có trình duyệt (Headless):
rclone config create gdrive_plex drive scope drive config_is_local false
```

### Đổi tài khoản hoặc đăng nhập lại:
```bash
rclone config reconnect gdrive_plex:
```

### Lưu cấu hình theo từng Workspace:
Cấu hình target của dự án được lưu tại `./.agent/storage_targets.json`:
```json
{
  "cloud_target": {
    "provider": "rclone",
    "remote_name": "gdrive_plex",
    "remote_path": "Media/Phim"
  }
}
```

---

## 🧹 3. Cơ Chế Auto-Purge (Giải Phóng Đĩa Cục Bộ)

Sau khi phim được tải về máy cá nhân và đẩy thành công lên NAS hoặc Google Drive:
* Thêm cờ `--auto-purge` để Agent **tự động xóa sạch file đệm trên máy cá nhân**.
* Đảm bảo laptop/PC không bao giờ bị đầy ổ cứng khi xử lý hàng trăm GB phim.

---

## 📊 4. Định Dạng Báo Cáo: `media-sync report`

```markdown
### 📊 Báo Cáo Trạng Thái Đồng Bộ (Media Sync Dashboard)
> **Google Drive Remote**: `gdrive_plex:` | **NAS Host**: `192.168.1.50`

| Thư Mục / Series | Trạng Thái NAS | Trạng Thái Cloud (Drive) | Local Buffer |
|---|:---:|:---:|:---:|
| `The Westward/Season 01` | ✅ 16/16 tập | ✅ 16/16 tập | 🧹 Đã dọn sạch |
| `The Westward/Season 05` | ⏳ 33/64 tập | ⏳ 0/64 tập (Đang chờ) | ⚠️ Còn 12GB chưa đẩy |
```
