---
name: media-hub
description: Trung tâm điều phối & Quản trị cấu hình / tài khoản tập trung cho toàn bộ hệ sinh thái Media Skills, đồng thời là Dashboard Web UI thời gian thực cổng 8888 kết nối AI Agent Command Center, giám sát chuỗi đồng bộ tải phim TorBox Cloud ➔ NAS & Google Drive, duyệt thư viện Plex và điều phối tương tác trực tiếp với AI Agent.
---

# 🚀 Antigravity Media Hub & Centralized Configuration Hub

Kỹ năng cốt lõi đóng vai trò là **Trung Tâm Điều Phối & Quản Trị Cấu Hình / Tài Khoản Tập Trung (Centralized Credential & Config Hub)** cho toàn bộ hệ sinh thái Media Skills (`media-downloader`, `plex-librarian`, `media-sync`, `tmdb-lookup`, `translate-subtitle`), đồng thời cung cấp giao diện Web thời gian thực (**Real-Time Dashboard cổng 8888**).

---

## 🔑 Quản Trị Tài Khoản & Cấu Hình Tập Trung

Media Hub tự động quét, gộp và đồng bộ cấu hình từ **Biến môi trường hệ thống (`os.environ`)**, file **`~/.env`** và file **`~/.gemini/config/media_hub_settings.json`**:
1. ⚡ **TorBox Token**: Dùng chung cho `media-downloader` và `torbox`.
2. 🎬 **TMDb API Key**: Dùng chung cho `tmdb-lookup` và `media-collector`.
3. 🌐 **Gemini API Key**: Dùng chung cho `translate-subtitle` và `ai-agent`.
4. 🖥️ **NAS SSH Credentials**: Dùng chung cho `media-sync` và `plex-librarian` (tự động nhận diện thư mục Plex).
5. ☁️ **Google Drive Rclone**: Dùng chung cho `media-sync` và `plex-librarian`.
6. ⚙️ **Download & Sync Policy**: Tự động load lên UI và lưu trữ phản hồi tức thì qua REST API `/api/settings`.

---

## 📂 Quy Ước Thư Mục Làm Việc (Shared Filesystem Contract)

Các skill là plugin **độc lập** (không import lẫn nhau), nhưng cùng đọc/ghi trên một
hợp đồng thư mục do Media Hub sở hữu.

Gốc là **`.media-hub/` nằm ngay tại nơi chạy skill**, tự ẩn. Skill đi ngược lên từ thư
mục hiện tại để tìm nó, đúng cách `git` tìm `.git` — chạy từ thư mục con sâu vẫn ra
đúng gốc.

```
/Volumes/512GB/AI Workspace/            <- chạy ở đây
└── .media-hub/
    ├── config.json          # cấu hình dự án
    ├── .media_hub.db        # job queue + library index
    ├── .staging/  .cache/  .logs/  .gitignore
    │
    ├── Black Jack/                     <- collection (franchise)
    │   ├── Movies/
    │   │   └── Black Jack: The Movie (1996) {tmdb-...}/
    │   │       ├── Black Jack: The Movie (1996) [1080p BDRip].mkv
    │   │       ├── Black Jack: The Movie (1996) [1080p BDRip].vi.srt
    │   │       └── movie.nfo  poster.jpg  fanart.jpg  .work/
    │   └── TV Shows/
    │       ├── Black Jack (1993) {tvdb-78864}/
    │       │   ├── tvshow.nfo  poster.jpg  fanart.jpg  .work/
    │       │   └── Season 01/
    │       │       ├── Black Jack (1993) - S01E01 - Tên Tập [1080p BDRip].mkv
    │       │       └── Black Jack (1993) - S01E01 - Tên Tập [1080p BDRip].vi.ass
    │       └── Young Black Jack (2015) {tvdb-299770}/
    └── Monster/                        <- title đứng một mình vẫn có collection riêng
        └── TV Shows/Monster (2004) {tvdb-74599}/
```

**Database và config nằm ở tầng ngoài** (ngay trong `.media-hub/`), không lẫn vào
collection hay thư mục title.

**Collection trước, kiểu sau.** Franchise có cả series lẫn phim lẻ được giữ chung một
chỗ — Black Jack có 1 TV universe và 2 movie. Thư mục collection **luôn** được tạo; một
title đứng một mình chỉ đơn giản có collection mang tên chính nó, để độ sâu đồng nhất
và script không phải xử lý ngoại lệ.

> [!IMPORTANT]
> Đây **không** phải Plex scan root. Library của Plex/Jellyfin có kiểu cố định, một gốc
> lẫn cả movie lẫn tv sẽ bị nhận diện sai. Trỏ Plex vào từng thư mục `Movies/` và
> `TV Shows/` bên trong collection, hoặc sync lên library đã phân kiểu sẵn trên
> Drive/NAS.

**Một title = một thư mục chứa tất cả.** Video, phụ đề, `.nfo`, artwork nằm chung —
đúng layout Plex/Jellyfin. Nghĩa là `translate-subtitle` sửa phụ đề ngay cạnh tập phim
nó thuộc về, và chính thư mục đó là thứ được sync. Không có cây `curation/` song song.

**Thứ tự phân giải gốc:**

| Ưu tiên | Nguồn | Dùng khi |
| :--- | :--- | :--- |
| 1 | `MEDIA_HUB_HOME` | Ép cho một lần chạy |
| 2 | `.media-hub/` tìm ngược lên từ cwd | **Mặc định** |
| 3 | `media_hub_home` trong settings | Chốt cứng; server chạy nền dùng cái này |
| 4 | `<cwd>/.media-hub` | Chưa có gì thì tạo tại chỗ |

Setting đã chốt **không** thắng `.media-hub` của dự án — nếu không, làm việc trong một
dự án vẫn ghi ra gốc toàn cục. Discovery cũng bỏ qua kết quả nằm trong chính thư mục
cài đặt skill, để server (cwd là `scripts/`) không tạo `.media-hub` trong repo.

Ghi đè từng phần: `movies_dir`, `tv_dir`, `staging_dir`, `logs_dir`, `cache_dir`,
`db_path`, `queue_path` — qua config hoặc `MEDIA_HUB_*_DIR`. `movies_dirname` /
`tv_dirname` là *tên* thư mục con trong mỗi collection, không phải đường dẫn tuyệt đối.

**Đường dẫn chuẩn Plex trong hợp đồng** (`hub_paths.py`), để mọi skill tính ra cùng
một chỗ thay vì mỗi skill tự đặt tên:

| Hàm | Kết quả |
| :--- | :--- |
| `collection_dir(c)` | `<root>/<Collection>/` |
| `title_dir(t, kind, collection)` | `<Collection>/TV Shows/<t>/` hoặc `.../Movies/<t>/` |
| `season_dir(t, n, collection=)` | `.../<t>/Season 01/` (mùa 0 = specials) |
| `episode_path(...)` | `.../Monster (2004) - S01E01 - Tên Tập [1080p BluRay].mkv` |
| `movie_path(...)` | `.../Movies/<t>/Inception (2010) [2160p HDR].mkv` |
| `subtitle_path(v, "vi")` | `<video>.vi.srt` — cạnh video, đúng luật sidecar của Plex |

### Nguyên tắc
1. **Không skill nào được mặc định ghi vào `.`** — cwd của agent là ngẫu nhiên.
2. **Artwork/NFO ghi thẳng vào thư mục title**, không qua thư mục trung gian.
3. **Phụ đề nằm cạnh video** — Plex yêu cầu `<tên_video>.vi.srt` cùng thư mục.
4. **`.staging/` chỉ chứa thứ tái tạo được** — auto-purge xóa sau khi verify.
   `.work/` trong mỗi thư mục title là bản nháp, không bao giờ sync.
5. **Config nằm trong gốc:** `<root>/config.json`. Không có vấn đề bootstrap vì việc
   tìm gốc chỉ dùng env → discovery → cwd, không cần đọc config. File cũ
   `~/.gemini/config/media_hub_settings.json` vẫn được đọc làm nền (giữ cấu hình sẵn
   có chạy được, và cho phép chốt gốc cho server), `config.json` của dự án đè lên.
   *Lưu ý:* config chứa token/API key, nên `.media-hub` trên ổ cắm rời đồng nghĩa với
   việc khóa cũng đi theo ổ đó.
6. Mỗi skill đọc hợp đồng qua `scripts/hub_paths.py` (bản sao cùng schema, vì plugin
   phải chạy độc lập). Schema gốc: `media-hub/scripts/core/settings.py`.

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

### 1. Khởi Chạy Mặc Định (Chế Độ Nội Bộ / Localhost):
```bash
python3 /path/to/agent-skills/plugins/media-hub/skills/media-hub/scripts/launcher.py
# Hoặc:
bash /path/to/agent-skills/plugins/media-hub/skills/media-hub/scripts/launch_dashboard.sh
```
* Dashboard khởi động ngay tại `http://127.0.0.1:8888` và IP mạng LAN nội bộ.

### 2. Mở Rộng Truy Cập Online Từ Xa (Tùy Chọn `--tunnel`):
Khi muốn truy cập Dashboard từ điện thoại di động 4G/5G hoặc máy tính bên ngoài, thêm cờ `--tunnel` (hoặc `--public`):
```bash
python3 /path/to/agent-skills/plugins/media-hub/skills/media-hub/scripts/launcher.py --tunnel
# Hoặc:
bash /path/to/agent-skills/plugins/media-hub/skills/media-hub/scripts/launch_dashboard.sh --tunnel
```
Script sẽ tự động tạo đường truyền **TryCloudflare** miễn phí, bắt link và in ngay ra màn hình cho người dùng:
```text
================================================================
🎉 LINK TRUY CẬP ONLINE TỪ XA (TRYCLOUDFLARE):
👉 https://constitution-plates-leisure-delegation.trycloudflare.com
================================================================
```

---

## 🌐 Truy Cập Giao Diện Web

* **Mặc định (Nội bộ):** `http://127.0.0.1:8888` (hoặc `http://<LAN-IP>:8888`)
* **Tùy chọn Online (Khi bật `--tunnel`):** Truy cập an toàn qua URL `https://*.trycloudflare.com` từ điện thoại iPhone / Android hoặc máy tính từ xa.

