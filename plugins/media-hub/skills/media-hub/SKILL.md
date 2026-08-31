---
name: media-hub
description: Khởi chạy và quản lý Dashboard Antigravity Media Hub & AI Agent Command Center (Web UI thời gian thực cổng 8888, giám sát chuỗi đồng bộ tải phim TorBox Cloud ➔ Google Drive, quản lý torrent, duyệt thư viện Google Drive và điều phối tương tác trực tiếp với AI Agent qua Web UI).
---

# 🚀 Antigravity Media Hub & Agent Command Center Skill

Kỹ năng đặc biệt giúp khởi chạy, điều khiển và theo dõi toàn bộ tiến trình hoạt động của các **Agent Skills** (như `torbox-manager`, `media-collector`, `translate-subtitle`) trên giao diện Web thời gian thực (**Real-Time Dashboard**).

---

## 🛡️ Nguyên Tắc Hoạt Động Của AI Agent Assistant (Skill-Scoped Guardrails)

Để đảm bảo AI Agent Assistant phản hồi và thực thi hành động **chính xác 100% trong ngữ cảnh của các Skill**, hệ thống sử dụng cơ chế **Intent Routing & Domain Whitelisting**:

### 1. Phân Loại Ý Định & Phạm Vi Kỹ Năng (Intent Map):
| Intent | Skill Tương Ứng | Phạm Vi & Thẩm Quyền |
| :--- | :--- | :--- |
| **`TORBOX_OP`** | `torbox-manager` | Tra cứu torrents trên Cloud, lọc torrent đã Ready/Cached, thêm Magnet link, xóa torrent giải phóng dung lượng. |
| **`PIPELINE_OP`** | `sequential-pipeline` | Kiểm tra tiến độ chuỗi stream cuốn chiếu (`Cross Fight B-Daman`, `Monster`, `WUKONG`...), báo cáo % hoàn thành. |
| **`GDRIVE_OP`** | `media-collector` | Quét thư mục media Google Drive, kiểm tra quan hệ series, chuẩn hóa tên mùa/tập (`S01E01`), cập nhật NFO/Poster. |
| **`SUBTITLE_OP`** | `translate-subtitle` | Tra cứu, tải về, dịch phụ đề Vietsub và chuyển đổi định dạng phụ đề WebVTT zerolatency. |
| **`SYSTEM_OP`** | `media-hub` | Báo cáo dung lượng ổ đĩa, kiểm tra RAM/Disk buffer và tự động dọn dẹp thư mục tạm. |
| **`OUT_OF_SCOPE`** | *Ngoài phạm vi* | **Từ chối lịch sự** đối với các câu hỏi không liên quan đến Media Hub và hướng dẫn người dùng lệnh mẫu. |

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
   * Xem chi tiết từng Season và danh sách tập đã chuẩn hóa theo quy chuẩn Plex/Jellyfin.
   * Trình phát video chuyên biệt toàn màn hình (Full-Screen Dedicated Player View) hỗ trợ phát trực tiếp, VLC, IINA, M3U.

5. **🤖 AI Agent Assistant (Web Command Center):**
   * Chat và gửi lệnh trực tiếp cho Antigravity AI từ giao diện Web.
   * Tự động phân tích ý định qua `intent_router.py` và giải quyết lệnh ngay lập tức.
   * Thanh nhập lệnh neo cố định chuẩn Mobile App trên điện thoại.

---

## 💻 Cách Khởi Chạy Dashboard

### 1. Khởi Chạy 1-Chạm (Tự Động Bật TryCloudflare & In Link Ra Màn Hình):
```bash
python3 /path/to/agent-skills/plugins/media-hub/skills/media-hub/scripts/launcher.py
# Hoặc:
bash /path/to/agent-skills/plugins/media-hub/skills/media-hub/scripts/launch_dashboard.sh
```

Khi chạy, script sẽ tự động tạo đường truyền **TryCloudflare** miễn phí, bắt link và in ngay ra màn hình cho người dùng:
```text
================================================================
🎉 LINK TRUY CẬP ONLINE THỜI GIAN THỰC (TRYCLOUDFLARE):
👉 https://constitution-plates-leisure-delegation.trycloudflare.com
================================================================
```

---

## 🌐 Truy Cập Giao Diện Web

* **Localhost:** `http://127.0.0.1:8888`
* **Public Cloudflare Tunnel:** Truy cập an toàn qua URL `https://*.trycloudflare.com` từ điện thoại iPhone / Android hoặc máy tính từ xa.
