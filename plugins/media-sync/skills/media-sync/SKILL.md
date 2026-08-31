---
name: media-sync
description: Đồng bộ đa đích chuyên nghiệp qua Rclone và SSH/SFTP. Hỗ trợ đồng bộ song song hoặc tùy chọn lên NAS Storage và Google Drive Plex, điều chỉnh số luồng truyền tải, và tự động xóa sạch file đệm cục bộ (Auto-Purge) ngay sau khi hoàn tất để tiết kiệm tối đa dung lượng ổ cứng.
---

# Media Sync Skill (Đồng Bộ Đa Đích & Auto-Purge)

Kỹ năng chuyên trách đẩy dữ liệu từ bộ đệm cục bộ (`Staging Buffer`) lên các đích lưu trữ đám mây hoặc mạng nội bộ, kèm cơ chế **Auto-Purge** giải phóng 100% ổ cứng máy sau khi đồng bộ thành công.

---

## 🚀 Cú Pháp Kích Hoạt CLI

```bash
# 1. Đồng bộ lên cả NAS và Google Drive kèm tự động dọn dẹp cache:
python3 <skill_dir>/scripts/sync_cli.py sync "/path/to/staging" --targets nas,drive --purge

# 2. Chỉ đồng bộ lên Google Drive:
python3 <skill_dir>/scripts/sync_cli.py sync "/path/to/staging" --targets drive --transfers 4

# 3. Chỉ đồng bộ lên NAS qua SSH/Rsync:
python3 <skill_dir>/scripts/sync_cli.py sync "/path/to/staging" --targets nas
```

---

## 🛠️ Các Tính Năng Cốt Lõi

1. ☁️ **Google Drive Dispatcher (Rclone Engine):**
   * Sử dụng Rclone chuyển tải trực tiếp tới `gdrive:Phim/TV Shows` hoặc `gdrive:Phim/Movies`.
   * Tối ưu hóa băng thông với `--transfers=4` và `--checkers=8`.

2. 🖥️ **NAS Dispatcher (SSH / SFTP / Rsync):**
   * Đẩy file trực tiếp vào thư mục Plex trên NAS nội bộ với tốc độ mạng Gigabit.

3. 🗑️ **Auto-Purge Garbage Collection:**
   * Chỉ xóa file đệm cục bộ khi **toàn bộ các đích được chọn** đã xác nhận lưu file nguyên vẹn 100% (`checksum / size verified`).
   * Giúp bạn có thể tải hàng trăm GB hoặc hàng TB phim mà ổ cứng máy lúc nào cũng chỉ tốn 2-4 GB!
