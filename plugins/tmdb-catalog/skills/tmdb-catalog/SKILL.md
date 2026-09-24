---
name: tmdb-catalog
description: Cinema & television knowledge graph powered by The Movie Database (TMDb) API v3 and TheTVDB. Resolves rich metadata, downloads HD posters/fanart, generates Plex/Kodi-compliant NFO files, renders visual 2-column movie cards with local poster thumbnails, and classifies titles into overarching Franchises (IP Universes, Auteur Collections, Studio Collections).
---

# TMDb Catalog & Franchise Intelligence Skill

Bộ kỹ năng kết hợp giữa đồ thị tri thức điện ảnh **The Movie Database (TMDb v3)**, **TheTVDB**, và động cơ phân loại thương hiệu **Franchise Classifier**.

---

## 🚀 Các Lệnh CLI Cốt Lõi

```bash
# 1. Tìm kiếm phim / series theo tên:
python3 <skill_dir>/scripts/tmdb_client.py search "The Westward" --type tv

# 2. Lấy chi tiết siêu dữ liệu & dàn nhân vật:
python3 <skill_dir>/scripts/tmdb_client.py get tv 83031

# 3. Tạo file NFO và tải poster/fanart chuẩn Plex/Kodi:
python3 <skill_dir>/scripts/tmdb_client.py nfo tv 83031 --out-dir "<folder_phim>"

# 4. Quản lý danh mục Franchise từ dữ liệu Media Hub:
python3 <skill_dir>/scripts/catalog_manager.py list-franchises [--alpha]
python3 <skill_dir>/scripts/catalog_manager.py show-franchise "<Tên_Franchise>"
```

---

## 🎨 Quy Chuẩn Hiển Thị Khung Chat (Visual Movie Cards)

> [!IMPORTANT]
> Khung chat chặn hiển thị link web ảnh trực tiếp (`https://...`) do cơ chế bảo mật CSP (gây lỗi *"Preview unavailable"*). Agent **bắt buộc phải tải thumbnail `w185` về thư mục cache cục bộ** (ví dụ trong thư mục brain/artifact hoặc `.agent/cache/`) và nhúng đường dẫn file local `![Poster](/absolute/path)` vào bảng Markdown.

### 1. Thẻ Phim Chi Tiết (Movie / Series Card)
Bắt buộc render dạng **Bảng 2 cột (Poster nhỏ bên trái `width="120"`, Chi tiết bên phải)**:

| Poster | Thông Tin Chi Tiết |
|:---:|---|
| <img src="/absolute/path/to/poster_w185.jpg" width="120" alt="Poster" /> | **🎬 Tây Hành Kỷ (The Westward) — 2018**<br>⭐ **Đánh giá**: `7.6/10` \| 🎬 **Quy mô**: 5 Mùa (134 Tập)<br>🏷️ **Mã ID**: TMDb `83031` • TheTVDB `371131`<br>🎭 **Thể loại**: Animation, Action & Adventure, Tiên hiệp 3D<br>🏢 **Studio**: BYMENT<br><br>📖 *Tóm tắt: Cuộc thỉnh kinh Tây Thiên thực chất là một âm mưu to lớn của Thiên đình. Sau khi Kỳ Kinh biến mất hơn một thập kỷ, Thiên đình phái đại quân lùng sục khắp nơi...* |

---

### 2. Danh Sách Các Mùa (Season Breakdown)
Khi người dùng yêu cầu liệt kê các Season, render bảng với ảnh poster của từng mùa (`width="85"`):

* **Khi Agent chạy trên máy cá nhân (điều khiển NAS từ xa)**:
| Poster Season | Chi Tiết Từng Mùa | Trạng Thái Lưu Trữ (Local / NAS / Drive) |
|:---:|---|---|
| <img src="/path/s1_w185.jpg" width="85" /> | **Season 01 (Mùa 1)** — 2018<br>🎬 **Tổng số**: 16 Tập (Trọn bộ) | 💻 **Local**: `0/16`<br>🏠 **NAS**: `16/16` tập (Đủ)<br>☁️ **Drive**: `16/16` tập (Đủ) |
| <img src="/path/s5_w185.jpg" width="85" /> | **Season 05 (Mùa 5)** — 2023 - 2024<br>🎬 **Tổng số**: 64 Tập (Đang phát hành) | 💻 **Local**: `0/64`<br>🏠 **NAS**: `33/64` tập *(đang kéo)*<br>☁️ **Drive**: `0/64` tập |

* **Khi Agent chạy trực tiếp trên máy NAS**: Tự động ẩn dòng `Local`, chỉ giữ lại `NAS` và `Drive`.

---

## 🧭 Triết Lý Phân Loại Franchise (3 Cấp Độ)

Không đồng nhất **TMDb Collection** với **Franchise** (Collection chỉ là một nhánh truyện hẹp). Phân loại theo 3 hình thức:

1. **Franchise Thương Hiệu / IP Tổng Thể**:
   - Gom toàn bộ phim lẻ, series, anime, live-action, reboot chia sẻ chung thế giới hoặc nhân vật (Ví dụ: *"Spider-Man"*, *"Dragon Ball"*, *"Batman"*).
   - **Bộ lọc bản chất IP (Disambiguation)**: Phân biệt rõ các phim trùng tên nhưng khác IP:
     - *Journey to the West (1996)* (Tây Du Ký TVB) ≠ *The Westward* (Tây Hành Kỷ 3D donghua).
     - *Kingdom (2012)* (Anime Chiến Quốc Nhật) ≠ *Kingdom: Ashin of the North* (Zombie Hàn Quốc).
2. **Auteur Collection (Tuyển Tập Đạo Diễn / Tác Giả)**:
   - Gom tác phẩm của các đạo diễn có phong cách tác giả nổi bật dù các phim không chung cốt truyện (Ví dụ: *"Makoto Shinkai Collection"*, *"Đạo diễn Christopher Nolan"*).
3. **Studio Collection (Hãng Phim Có Bản Sắc)**:
   - Gom các bộ sưu tập theo studio nổi tiếng được khán giả sưu tầm trọn bộ (Ví dụ: *"Studio Ghibli"*, *"Pixar"*).
