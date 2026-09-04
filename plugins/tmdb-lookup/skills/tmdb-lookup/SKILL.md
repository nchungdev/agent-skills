---
name: tmdb-lookup
description: Tra cứu và phân tích metadata điện ảnh & truyền hình qua The Movie Database (TMDb) API v3. Hỗ trợ tìm kiếm theo tên, tra cứu theo TMDb/TheTVDB/IMDb ID, trích xuất dàn nhân vật & diễn viên (Cast & Characters), tải poster/fanart chất lượng cao, và xuất file NFO chuẩn Plex/Jellyfin/Kodi.
---

# TMDb Lookup Skill (Cinema & TV Metadata Engine)

Kỹ năng tra cứu, phân tích và trích xuất dữ liệu điện ảnh chuyên sâu từ **The Movie Database (TMDb) API v3**.

---

## 🚀 Cú Pháp Kích Hoạt & Các Lệnh CLI

```sh
# 1. Tìm kiếm phim / TV series theo tên:
python3 <skill_dir>/scripts/tmdb_client.py search "<tên_phim>" [--type movie|tv|multi]

# 2. Lấy thông tin chi tiết đầy đủ (kèm diễn viên, nhân vật, ID external):
python3 <skill_dir>/scripts/tmdb_client.py get <movie|tv> <tmdb_id>

# 3. Tải poster, fanart và tạo file NFO chuẩn Plex/Jellyfin:
python3 <skill_dir>/scripts/tmdb_client.py get <movie|tv> <tmdb_id> --poster --fanart --nfo --output "<thư_mục>"

# 4. Xuất JSON có cấu trúc cho các skill khác (media-collector, translate-subtitle):
python3 <skill_dir>/scripts/tmdb_client.py get <movie|tv> <tmdb_id> --json

# 5. Chưa có tmdb_id, chỉ có ID hệ thống khác (TheTVDB/IMDb) -> tra ngược ra tmdb_id:
python3 <skill_dir>/scripts/tmdb_client.py find <external_id> --source tvdb_id --json
python3 <skill_dir>/scripts/tmdb_client.py find <external_id> --source imdb_id --json

# 6. Tìm TMDb Collection theo tên franchise (vd để gán lại collection cho
#    phim TMDb chưa gắn sẵn -- xem skill franchise-classifier):
python3 <skill_dir>/scripts/tmdb_client.py search-collection "<tên franchise>" --json

# 7. Lấy chi tiết + toàn bộ phim (parts) thuộc một Collection theo ID:
python3 <skill_dir>/scripts/tmdb_client.py collection <collection_id> --json
```

---

## 🔑 Cấu Hình API Key An Toàn

Skill tự động nạp `TMDB_API_KEY` từ file `~/.env` (tuân thủ Safe Credentials Protocol).

```bash
# Thêm hoặc cập nhật key:
printf "Enter TMDB_API_KEY (typing hidden): " && read -s val && echo && echo "TMDB_API_KEY=$val" >> ~/.env && echo "Saved."
```

---

## 🛠️ Các Tính Năng Cốt Lõi

### 1. Phân Giải Đa Cơ Sở Dữ Liệu (Multi-Database ID Resolution):
Từ một TMDb ID, skill tự động truy vấn và ánh xạ sang:
- **TheTVDB ID** (dành cho TV Series / Anime)
- **IMDb ID** (dành cho Hollywood / Quốc tế)
- **Wikidata ID** (nếu có)

Chiều ngược lại (chưa có tmdb_id, chỉ có tvdb_id/imdb_id) dùng lệnh `find`
(mục 5 ở trên) — tra qua endpoint `/find` của TMDb.

### 1b. Collection (Franchise cho Phim Lẻ):
`get movie <tmdb_id> --json` trả thêm field `collection: {id, name}` khi
phim thuộc một TMDb Collection (vd "The Dark Knight" → collection "The Dark
Knight Collection"). `null` nếu TMDb chưa gắn phim này vào Collection nào
(có thể phim thật sự độc lập, hoặc TMDb chỉ đơn giản là chưa curator kịp).
Khi đó dùng `search-collection "<tên>"` (mục 6) để tìm xem Collection đã
tồn tại trên TMDb chưa, rồi `collection <id>` (mục 7) để lấy toàn bộ phim
thuộc Collection đó và xác nhận phim đang xét có thật sự nằm trong không.

**Lưu ý**: TMDb chỉ có khái niệm Collection cho **phim lẻ** — TV series
không bao giờ có field này, nên việc gom nhóm series cùng vũ trụ (nhiều
mùa/spin-off) luôn cần suy luận AI + tra web, xem skill `franchise-classifier`
(cũng là nơi quy trình đầy đủ ở trên được dùng tới).

### 2. Trích Xuất Dàn Nhân Vật (Cast & Character Mapping):
- Trích xuất tên nhân vật gốc + diễn viên lồng tiếng/thủ vai.
- Tự động phân loại nhân vật chính / nhân vật phụ cho kho thuật ngữ (`glossary.json`).

### 3. Xuất Bản Metadata & Artwork Chuẩn Plex / Jellyfin:
- Tự động tạo `tvshow.nfo` hoặc `movie.nfo` chuẩn XML schema.
- Tải ảnh bìa chuẩn HD (`poster.jpg` w500) và hình nền đại cảnh (`fanart.jpg` w1280).
