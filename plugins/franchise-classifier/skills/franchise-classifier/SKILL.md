---
name: franchise-classifier
description: Gom nhóm một danh sách phim lẻ & series (nhận diện qua TMDb ID / TheTVDB ID / IMDb ID) thành các franchise (vũ trụ chung) — ví dụ "Bảy Viên Ngọc Rồng"/"GT"/"Kai" cùng một franchise, các mùa Super Sentai khác nhau cùng một franchise. Ưu tiên TMDb Collection có sẵn cho phim lẻ; nếu phim chưa được TMDb gắn Collection thì tra web tìm franchise rồi tìm ngược trên TMDb xem Collection đã tồn tại chưa (gán lại nếu có, tự tạo nhóm cục bộ nếu chưa); với series (TMDb/TVDB không có "collection" cho series) luôn suy luận AI + tra cứu web. Trả về franchise name + danh sách phim/series thuộc franchise đó.
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
  { "ref": "tmdb-1930", "tmdb_id": 1930, "type": "tv" },
  { "ref": "tvdb-74581", "tvdb_id": 74581, "type": "tv" },
  { "ref": "tmdb-155", "tmdb_id": 155, "type": "movie" },
  { "ref": "tvdb-74599", "tvdb_id": 74599, "type": "tv" }
]
```

- `type`: `"movie"` hoặc `"tv"`. Nếu không chắc, để trống — bước 1 sẽ tự xác định qua `find`.
- `ref` (tuỳ chọn nhưng **khuyến nghị mạnh** khi gọi từ chương trình khác, vd media-hub): chuỗi định danh do caller tự đặt, skill không đọc/diễn giải giá trị này — chỉ **echo nguyên văn** lại trên item tương ứng trong Output (mục Bước 4). Giúp caller map kết quả về đúng bản ghi nội bộ (vd `root_key` union-find) mà không cần tự suy luận ngược từ tmdb_id/tvdb_id trả về, tránh sai lệch khi một title có cả hai ID nhưng response chỉ mang một loại.
- Có thể truyền thêm `title` thô (tên thư mục cục bộ, tên đã biết...) nếu có — dùng để đối chiếu/gỡ rối khi tra cứu ra kết quả mơ hồ, nhưng **ID luôn là nguồn sự thật**, không tin tên thư mục.

## 📤 Output

```json
{
  "franchises": [
    {
      "name": "The Dark Knight Collection",
      "source": "tmdb_collection",
      "tmdb_collection_id": 263,
      "items": [
        { "ref": "tmdb-272", "tmdb_id": 272, "type": "movie", "title": "Batman Begins" },
        { "ref": "tmdb-155", "tmdb_id": 155, "type": "movie", "title": "The Dark Knight" },
        { "ref": "tmdb-49026", "tmdb_id": 49026, "type": "movie", "title": "The Dark Knight Rises" }
      ]
    },
    {
      "name": "The Fast and the Furious Collection",
      "source": "tmdb_collection_recovered",
      "tmdb_collection_id": 9485,
      "items": [
        { "ref": "tmdb-385687", "tmdb_id": 385687, "type": "movie", "title": "Fast X" }
      ],
      "also_in_tmdb_collection_not_in_input": [
        { "tmdb_id": 9799, "title": "The Fast and the Furious" },
        { "tmdb_id": 584, "title": "2 Fast 2 Furious" }
      ]
    },
    {
      "name": "Bảy Viên Ngọc Rồng",
      "source": "local_collection",
      "items": [
        { "ref": "tmdb-12609", "tmdb_id": 12609, "type": "tv", "title": "Dragon Ball" },
        { "ref": "tmdb-12610", "tmdb_id": 12610, "type": "tv", "title": "Dragon Ball Z" },
        { "ref": "tvdb-76666", "tvdb_id": 76666, "type": "tv", "title": "Dragon Ball GT" },
        { "ref": "tmdb-32380", "tmdb_id": 32380, "type": "tv", "title": "Dragon Ball Kai" }
      ]
    },
    {
      "name": "Perfect Blue",
      "source": "standalone",
      "items": [
        { "ref": "tmdb-10494", "tmdb_id": 10494, "type": "movie", "title": "Perfect Blue" }
      ]
    }
  ],
  "unresolved": [
    { "ref": "tvdb-999999", "tvdb_id": 999999, "reason": "khong tim thay tren TMDb" }
  ]
}
```

Quy tắc bắt buộc:
- **Mọi title đầu vào phải xuất hiện đúng 1 lần** trong `franchises` (trừ khi rơi vào `unresolved`) — kể cả khi nó độc lập, không thuộc vũ trụ nào: tạo một franchise `source: "standalone"` chỉ chứa chính nó, **KHÔNG** dồn các title độc lập vào một nhóm "chưa phân loại" chung chung.
- `source` cho biết franchise được xác định bằng cách nào — 4 giá trị, xem chi tiết ở Bước 2/3:
  - `tmdb_collection`: phim đã có sẵn `collection` từ TMDb, chắc chắn nhất, không cần AI/web.
  - `tmdb_collection_recovered`: phim KHÔNG có sẵn `collection`, nhưng tra web xác định được franchise rồi tìm ngược ra TMDb thì Collection đó **đã tồn tại** trên TMDb (chỉ là TMDb chưa gắn phim này vào) — dùng đúng `name`/`tmdb_collection_id` của TMDb.
  - `local_collection`: xác định được quan hệ franchise thật qua AI + web, nhưng KHÔNG có TMDb Collection nào tương ứng (luôn đúng với series, vì TMDb/TVDB không có "collection" cho series; cũng áp dụng cho phim lẻ mà franchise của nó chưa từng được TMDb curator tạo) — tự đặt tên, không có `tmdb_collection_id`.
  - `standalone`: không tìm được bằng chứng liên kết nào, đứng một mình.
- `tmdb_collection` và `tmdb_collection_recovered` nên kèm `tmdb_collection_id` để caller tiện tra cứu lại sau. `also_in_tmdb_collection_not_in_input` (tuỳ chọn) liệt kê các phim TMDb ghi nhận thuộc cùng Collection nhưng KHÔNG có trong input ban đầu — thông tin thêm hữu ích, không bắt buộc phải xử lý.
- Nếu input có `ref`, **BẮT BUỘC** echo nguyên văn giá trị đó trên item tương ứng ở output (kể cả trong `unresolved`) — caller dùng field này để map kết quả về đúng bản ghi nội bộ, sai lệch `ref` sẽ làm caller ghi nhầm franchise cho title khác.

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

### Bước 2 — Gom theo TMDb Collection có sẵn (chắc chắn, ưu tiên cao nhất, chỉ áp dụng cho phim lẻ)

TMDb chỉ có khái niệm "Collection" cho **phim lẻ**. Nếu field `collection` (từ bước 1) khác `null`, gom title đó vào franchise tên = `collection.name`, `source: "tmdb_collection"`, `tmdb_collection_id = collection.id`. Không cần AI/web cho nhóm này — đây là dữ liệu do TMDb curator xác nhận sẵn.

### Bước 3 — Xử lý phần còn lại: series (luôn thiếu) + phim lẻ chưa được TMDb gắn Collection

Lấy danh sách title còn lại sau Bước 2. Với **series**, TMDb/TheTVDB không bao giờ có sẵn collection nên luôn đi hết quy trình dưới đây. Với **phim lẻ có `collection: null`**, đừng vội kết luận "độc lập" — có 2 khả năng: phim thật sự độc lập, HOẶC phim thuộc franchise nhưng TMDb curator chưa gắn nó vào Collection (dữ liệu TMDb không đầy đủ, đặc biệt với phim mới ra rạp hoặc phim ít phổ biến).

1. **Tra web tìm quan hệ franchise**: với mỗi title (hoặc cặp/nhóm title có tên gợi ý liên quan — cùng từ khóa chính, cùng studio, cùng nằm trong thư viện người dùng đang quản lý), dùng `search_web`:
   - `search_web("<title> franchise Wikipedia")`
   - `search_web("<title A> and <title B> same universe sequel")`
   - `search_web("<title> part of which film series collection")`
   - Ưu tiên nguồn đáng tin: Wikipedia, trang chính thức của studio, chính TMDb/TVDB (overview đôi khi nhắc franchise).
   - Chỉ xác nhận khi có **bằng chứng cụ thể**: sequel/prequel/spin-off/reboot chính thức, cùng nhân vật/thế giới chính, hoặc cùng series gốc chia mùa khác tên (vd "Dragon Ball" → "Dragon Ball Z" → "Dragon Ball GT" → "Dragon Ball Kai"). **Không** gom chỉ vì cùng thể loại.
   - Không tìm được bằng chứng nào → title đó **độc lập** (`source: "standalone"`) — im lặng-là-đúng tốt hơn đoán sai. Dừng ở đây cho title này.
2. **Nếu tìm được tên franchise VÀ title đang xét là phim lẻ**: tìm ngược lại trên TMDb xem Collection này đã tồn tại chưa, dùng chính tên franchise vừa xác định qua web:
   ```sh
   python3 <tmdb-lookup_skill_dir>/scripts/tmdb_client.py search-collection "<tên franchise>" --json
   ```
   - **Có kết quả khớp** (so tên cẩn thận, TMDb có thể đặt tên hơi khác vd "The Fast and the Furious Collection" thay vì "Fast and Furious"): gọi tiếp `collection <collection_id> --json` để lấy danh sách `parts` đầy đủ, xác nhận phim đang xét thật sự nằm trong đó (so theo `tmdb_id` hoặc tên+năm). Nếu khớp → gán franchise này cho phim, `source: "tmdb_collection_recovered"`, dùng đúng `name`/`id` của TMDb (không tự đặt tên khác). Các phim khác trong `parts` mà không có trong input thì liệt kê vào `also_in_tmdb_collection_not_in_input`, không cần tra cứu tiếp cho chúng.
   - **Không có kết quả khớp nào** (Collection thật sự chưa tồn tại trên TMDb): tự tạo nhóm cục bộ, `source: "local_collection"`, đặt tên franchise theo kết quả tra web ở bước 1.
3. **Nếu title đang xét là series** (hoặc phim lẻ nhưng bước 2 xác nhận TMDb không có Collection tương ứng): `source: "local_collection"`, không cần gọi `search-collection`/`collection` (series chắc chắn không có trên TMDb theo dạng Collection).
4. Đặt tên franchise (`local_collection`) theo tên gốc/tên chung phổ biến nhất được xác nhận qua web (thường là tên title đầu tiên trong bộ, không phải tên season cụ thể — vd đặt "Bảy Viên Ngọc Rồng" chứ không phải "Bảy Viên Ngọc Rồng Kai").

### Bước 4 — Gộp kết quả & trả về đúng schema Output ở trên

Đảm bảo mọi title input đều có mặt đúng 1 lần trong `franchises` hoặc `unresolved`. Các title cùng `local_collection`/`tmdb_collection_recovered` do AI xác định phải được gộp chung một entry (so khớp theo tên franchise đã chuẩn hoá), không tạo nhiều franchise trùng tên chỉ khác cách viết.

---

## 💾 Gợi Ý Cache (khuyến nghị cho caller, không bắt buộc)

Bước 3 (search_web + suy luận AI) tốn thời gian và token — caller nên cache kết quả theo khóa `tmdb_id`/`tvdb_id` đã xử lý (vd bảng `franchise_ai_cache` phía media-hub: `root_key TEXT PRIMARY KEY, franchise TEXT, checked_at REAL`), để lần gọi sau chỉ xử lý các title **mới** chưa từng được phân loại, tránh hỏi lại toàn bộ thư viện mỗi lần.

## ⚠️ Giới Hạn Đã Biết

- Không tự bịa franchise cho title hoàn toàn mới/hiếm không có thông tin trên web — trả về `standalone`.
- `search_web` có thể trả kết quả nhiễu (fan theory, clickbait) — luôn ưu tiên nguồn chính thống, và khi nghi ngờ, thiên về **không gom** thay vì gom sai.
- `search-collection`/`collection` là API TMDb công khai, chỉ **đọc** — skill này không (và không thể) tự PATCH ngược field `collection` lên TMDb thật. `tmdb_collection_recovered` nghĩa là "TMDb đã có Collection này, ta chỉ tự nối phim vào ở phía caller/local", không phải TMDb đã cập nhật dữ liệu của họ.
- Không xử lý phát hiện trùng lặp title (title đã tồn tại 2 lần với 2 ID khác nhau) — đó là việc của bước dedupe phía caller (vd union-find theo `item_uid` như media-hub đang làm), skill này chỉ nhận input đã dedupe.
