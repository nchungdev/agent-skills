---
name: franchise-classifier
description: Gom nhóm một danh sách phim lẻ & series (nhận diện qua TMDb ID / TheTVDB ID / IMDb ID) thành các franchise (vũ trụ chung) — ví dụ "Bảy Viên Ngọc Rồng"/"GT"/"Kai" cùng một franchise, các mùa Super Sentai khác nhau cùng một franchise. Dùng TMDb Collection (đáng tin cậy, có sẵn) cho phim lẻ, và suy luận AI + tra cứu web cho series/anime (TMDb & TheTVDB không có khái niệm "collection" cho series). Trả về franchise name + danh sách phim/series thuộc franchise đó.
---

# Franchise Classifier Skill (Gom Nhóm Vũ Trụ Phim & Series)

Kỹ năng nhận một danh sách title (phim lẻ hoặc series, nhận diện qua **TMDb ID** và/hoặc **TheTVDB ID**), tra cứu metadata thật qua skill `tmdb-lookup`, rồi gom chúng thành các nhóm **franchise** (vũ trụ chung) — dùng cho việc tổ chức thư viện kiểu Plex/Jellyfin theo "một franchise = một thư mục cha".

> [!IMPORTANT]
> Đây KHÔNG phải là gán thể loại (genre) hay độ nổi tiếng. Franchise chỉ được gom khi có **quan hệ thật** giữa các title: sequel, prequel, spin-off, reboot, các mùa/season khác nhau của cùng một series, hoặc cùng chia sẻ nhân vật/thế giới truyện chính thức. Không suy đoán bừa — thà để một title đứng độc lập còn hơn gom sai.

---

## 📥 Input

Một danh sách title, mỗi phần tử cần **ít nhất một trong hai ID**:

```json
[
  { "tmdb_id": 1930, "type": "tv" },
  { "tvdb_id": 74581, "type": "tv" },
  { "tmdb_id": 155, "type": "movie" },
  { "tvdb_id": 74599, "type": "tv" }
]
```

- `type`: `"movie"` hoặc `"tv"`. Nếu không chắc, để trống — bước 1 sẽ tự xác định qua `find`.
- Có thể truyền thêm `title` thô (tên thư mục cục bộ, tên đã biết...) nếu có — dùng để đối chiếu/gỡ rối khi tra cứu ra kết quả mơ hồ, nhưng **ID luôn là nguồn sự thật**, không tin tên thư mục.

## 📤 Output

```json
{
  "franchises": [
    {
      "name": "Bảy Viên Ngọc Rồng",
      "source": "ai_web",
      "items": [
        { "tmdb_id": 12609, "type": "tv", "title": "Dragon Ball" },
        { "tmdb_id": 12610, "type": "tv", "title": "Dragon Ball Z" },
        { "tvdb_id": 76666, "type": "tv", "title": "Dragon Ball GT" },
        { "tmdb_id": 32380, "type": "tv", "title": "Dragon Ball Kai" }
      ]
    },
    {
      "name": "The Dark Knight Collection",
      "source": "tmdb_collection",
      "items": [
        { "tmdb_id": 272, "type": "movie", "title": "Batman Begins" },
        { "tmdb_id": 155, "type": "movie", "title": "The Dark Knight" },
        { "tmdb_id": 49026, "type": "movie", "title": "The Dark Knight Rises" }
      ]
    },
    {
      "name": "Perfect Blue",
      "source": "standalone",
      "items": [
        { "tmdb_id": 10494, "type": "movie", "title": "Perfect Blue" }
      ]
    }
  ],
  "unresolved": [
    { "tvdb_id": 999999, "reason": "khong tim thay tren TMDb" }
  ]
}
```

Quy tắc bắt buộc:
- **Mọi title đầu vào phải xuất hiện đúng 1 lần** trong `franchises` (trừ khi rơi vào `unresolved`) — kể cả khi nó độc lập, không thuộc vũ trụ nào: tạo một franchise `source: "standalone"` chỉ chứa chính nó, **KHÔNG** dồn các title độc lập vào một nhóm "chưa phân loại" chung chung.
- `source` cho biết franchise được xác định bằng cách nào: `tmdb_collection` (chắc chắn nhất, chỉ có ở phim lẻ), `ai_web` (suy luận + tra cứu web, dùng cho series), `local` (nếu người gọi skill tự truyền franchise đã biết từ trước — hiếm khi cần).

---

## 🚀 Quy Trình Thực Thi

### Bước 1 — Tra cứu metadata thật cho từng title (dùng skill `tmdb-lookup`)

Không bao giờ suy luận franchise chỉ từ ID hay tên thư mục thô — luôn tra ra metadata thật trước:

```sh
# Đã có tmdb_id -> lấy chi tiết trực tiếp (kèm collection nếu là phim lẻ):
python3 <tmdb-lookup_skill_dir>/scripts/tmdb_client.py get movie <tmdb_id> --json
python3 <tmdb-lookup_skill_dir>/scripts/tmdb_client.py get tv <tmdb_id> --json

# Chỉ có tvdb_id/imdb_id -> tra ngược ra tmdb_id trước:
python3 <tmdb-lookup_skill_dir>/scripts/tmdb_client.py find <tvdb_id> --source tvdb_id --json
python3 <tmdb-lookup_skill_dir>/scripts/tmdb_client.py find <imdb_id> --source imdb_id --json
# rồi lấy chi tiết bằng tmdb_id vừa tra ra như trên
```

Với mỗi title, giữ lại: `tmdb_id`, `type`, `title`, `original_title`, `year`, và với phim lẻ là field `collection` (đã có sẵn trong `tmdb-lookup` — không cần tự gọi API TMDb thô).

Nếu `find`/`get` không trả kết quả nào, đưa title đó vào `unresolved` với lý do rõ ràng, không đoán mò.

### Bước 2 — Gom theo TMDb Collection (chắc chắn, ưu tiên cao nhất, chỉ áp dụng cho phim lẻ)

TMDb chỉ có khái niệm "Collection" cho **phim lẻ**. Nếu field `collection` (từ bước 1) khác `null`, gom title đó vào franchise tên = `collection.name`, `source: "tmdb_collection"`. Không cần AI/web cho nhóm này — đây là dữ liệu do TMDb curator xác nhận.

### Bước 3 — Suy luận franchise cho phần còn lại (series + phim lẻ không có collection)

Đây là phần việc chính của skill này, vì **TMDb và TheTVDB đều không có khái niệm "collection" cho series** — nhiều series cùng vũ trụ (các mùa khác nhau, spin-off) không có cách nào tự động gom qua API.

1. Lấy danh sách các title còn lại sau Bước 2 (chưa có franchise).
2. Với mỗi cặp/nhóm title có tên **gợi ý** liên quan (cùng từ khóa chính trong tên, cùng studio sản xuất, cùng năm phát hành gần nhau, hoặc cùng nằm trong cùng một thư mục/thư viện người dùng đang quản lý) — dùng **`search_web`** để xác minh quan hệ thật, ví dụ:
   - `search_web("<title A> and <title B> same universe sequel")`
   - `search_web("<title A> franchise timeline order")`
   - `search_web("<title>  Wikipedia franchise")`
   - Ưu tiên nguồn đáng tin: Wikipedia, trang chính thức của studio, TVDB/TMDb chính nó (mô tả series đôi khi nhắc franchise trong overview).
3. Chỉ xác nhận cùng franchise khi có **bằng chứng cụ thể**: cùng nhân vật/thế giới chính, quan hệ sequel/prequel/spin-off/reboot chính thức, hoặc cùng series gốc chia mùa khác tên (vd "Dragon Ball" → "Dragon Ball Z" → "Dragon Ball GT" → "Dragon Ball Kai"). **Không** gom chỉ vì cùng thể loại (vd "hai anime shounen cùng năm 2020" KHÔNG phải lý do đủ).
4. Nếu không tìm được bằng chứng rõ ràng sau khi tra cứu, để title đó **độc lập** (`source: "standalone"`) — im lặng-là-đúng tốt hơn đoán sai.
5. Đặt tên franchise theo tên gốc/tên chung phổ biến nhất được xác nhận (thường là tên của title đầu tiên/tên chung trong bộ, không phải tên season cụ thể — vd đặt "Bảy Viên Ngọc Rồng" chứ không phải "Bảy Viên Ngọc Rồng Kai").

### Bước 4 — Gộp kết quả & trả về đúng schema Output ở trên

Đảm bảo mọi title input đều có mặt đúng 1 lần trong `franchises` hoặc `unresolved`.

---

## 💾 Gợi Ý Cache (khuyến nghị cho caller, không bắt buộc)

Bước 3 (search_web + suy luận AI) tốn thời gian và token — caller nên cache kết quả theo khóa `tmdb_id`/`tvdb_id` đã xử lý (vd bảng `franchise_ai_cache` phía media-hub: `root_key TEXT PRIMARY KEY, franchise TEXT, checked_at REAL`), để lần gọi sau chỉ xử lý các title **mới** chưa từng được phân loại, tránh hỏi lại toàn bộ thư viện mỗi lần.

## ⚠️ Giới Hạn Đã Biết

- Không tự bịa franchise cho title hoàn toàn mới/hiếm không có thông tin trên web — trả về `standalone`.
- `search_web` có thể trả kết quả nhiễu (fan theory, clickbait) — luôn ưu tiên nguồn chính thống, và khi nghi ngờ, thiên về **không gom** thay vì gom sai.
- Không xử lý phát hiện trùng lặp title (title đã tồn tại 2 lần với 2 ID khác nhau) — đó là việc của bước dedupe phía caller (vd union-find theo `item_uid` như media-hub đang làm), skill này chỉ nhận input đã dedupe.
