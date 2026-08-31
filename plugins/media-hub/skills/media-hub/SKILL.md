---
name: media-hub
description: Khởi chạy và quản lý Dashboard Antigravity Media Hub & AI Agent Command Center (Web UI thời gian thực cổng 8888, giám sát chuỗi đồng bộ tải phim TorBox Cloud ➔ Google Drive, quản lý torrent, duyệt thư viện Google Drive và điều phối tương tác trực tiếp với AI Agent qua Web UI).
---

# 🚀 Antigravity Media Hub & Agent Command Center Skill

Kỹ năng đặc biệt giúp khởi chạy, điều khiển và theo dõi toàn bộ tiến trình hoạt động của các **Agent Skills** (như `torbox-manager`, `media-collector`, `translate-subtitle`) trên giao diện Web thời gian thực (**Real-Time Dashboard**).

---

## 🌟 Tính Năng Trọng Tâm

1. **📊 Tổng Quan Hệ Thống (System KPIs):**
   * Theo dõi dung lượng ổ cứng, thông số cache RAM/Disk, và trạng thái toàn bộ tiến trình.
   * Hiển thị tác vụ đang stream trực tiếp theo thời gian thực (Giai đoạn Download ➔ Transcode ➔ Google Drive).

2. **🚀 Giám Sát Chuỗi Đồng Bộ (Sequential Pipelines):**
   * Theo dõi trạng thái từng bộ phim/anime (`Cross Fight B-Daman eS`, `Monster`, `WUKONG`, `Kindaichi`, `Transformers`...).
   * Bộ lọc thông minh: `Tất Cả`, `⚡ Đang Chạy`, `✓ Hoàn Thành`, `⏳ Hàng Đợi`.

3. **⚡ Quản Lý TorBox Cloud Cache:**
   * Hiển thị bảng danh sách torrent, dung lượng, trạng thái (`ready`, `cached`, `queued`, `downloading`).
   * Thêm Magnet Link trực tiếp qua Modal, lấy link Direct Download (DDL), xóa torrent giải phóng slot.

4. **📁 Trình Duyệt Thư Viện Google Drive:**
   * Duyệt poster phim chuẩn 2:3 với tag chất lượng (`1080p BDRip`, `480p DVD`, `Anime`, `Live Action`).
   * Xem chi tiết từng Season và danh sách tập đã chuẩn hóa theo quy chuẩn Plex/Jellyfin (`Show Name - S01E01 - [1080p BluRay]`).
   * Nút Back thông minh ghim cố định ở Header và Breadcrumb điều hướng cực kỳ tiện lợi.

5. **🤖 AI Agent Assistant (Web Command Center):**
   * Chat và gửi lệnh trực tiếp cho Antigravity AI từ giao diện Web.
   * Có sẵn các mẫu prompt nhanh: *Đồng bộ phim mới*, *Tải Anime*, *Quét kho Google Drive*, *Kiểm tra ổ đĩa*.
   * Lịch sử hội thoại phản hồi theo thời gian thực.

---

## 💻 Cách Khởi Chạy Dashboard

### 1. Khởi Chạy Trực Tiếp Bằng Lệnh Python:
```bash
# Chạy Dashboard Server trên cổng 8888:
python3 /path/to/agent-skills/plugins/media-hub/skills/media-hub/scripts/server.py
```

### 2. Khởi Chạy Trọn Gói (Server + Cloudflare Tunnel + Agent Queue Watcher):
```bash
bash /path/to/agent-skills/plugins/media-hub/skills/media-hub/scripts/launch_dashboard.sh
```

### 3. Khởi Chạy Riêng Agent Queue Watcher Daemon:
```bash
python3 /path/to/agent-skills/plugins/media-hub/skills/media-hub/scripts/agent_queue_watcher.py
```

---

## 🔗 Liên Kết Với Các Skill Khác Trong Repository

| Skill | Vai Trò Trong Dashboard |
| :--- | :--- |
| **`torbox-manager`** | Cung cấp API quản lý danh sách torrent, tải tập lẻ/Zip và xóa slot cloud. |
| **`media-collector`** | Quản lý cấu trúc thư mục, chuẩn hóa tên tập và tạo metadata NFO. |
| **`tmdb-lookup`** | Tự động lấy poster, backdrop, plot và thông tin diễn viên. |
| **`translate-subtitle`** | Tự động dịch phụ đề SRT/ASS sang tiếng Việt chuẩn văn cảnh. |

---

## 🌐 Truy Cập Giao Diện Web

* **Localhost:** `http://127.0.0.1:8888`
* **Mạng nội bộ LAN:** `http://<IP-MÁY-BẠN>:8888`
* **Public Cloudflare Tunnel (nếu bật):** Truy cập an toàn qua URL `https://*.trycloudflare.com` từ điện thoại hoặc máy tính từ xa.
