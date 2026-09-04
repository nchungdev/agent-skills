---
name: franchise-classifier
description: Gom nhóm một danh sách phim lẻ, series, anime, live-action (nhận diện qua TMDb ID / TheTVDB ID / IMDb ID) thành các franchise. Hỗ trợ 2 loại: (1) franchise thương hiệu/IP tổng thể — không phải TMDb Collection (Collection chỉ là MỘT tín hiệu hẹp hơn nhiều); ví dụ "Spider-Man" gồm cả 3 bộ ba phim live-action KHÁC TMDb Collection lẫn phim hoạt hình Spider-Verse, "Dragon Ball" gồm cả anime (Dragon Ball/Z/GT/Kai/Super) lẫn phim live-action "Dragonball Evolution". (2) Auteur Collection — tuyển tập tác phẩm cùng một đạo diễn/tác giả dù không chia sẻ IP/cốt truyện, ví dụ "Makoto Shinkai Collection". Dùng AI suy luận + tra cứu web để gom xuyên suốt mọi hình thức, không chỉ dựa vào Collection có sẵn. Trả về franchise name + danh sách toàn bộ nội dung thuộc franchise đó.
---

# Franchise Classifier Skill (Gom Nhóm Thương Hiệu/IP Xuyên Suốt Mọi Hình Thức)

Kỹ năng nhận một danh sách title (phim lẻ, series, anime, live-action — nhận diện qua **TMDb ID** và/hoặc **TheTVDB ID**), tra cứu metadata thật qua skill `tmdb-lookup`, rồi gom chúng thành các nhóm **franchise** (thương hiệu/IP tổng thể) — dùng cho việc tổ chức thư viện kiểu Plex/Jellyfin theo "một franchise = một thư mục cha".

## 🧭 Franchise Là Gì?

> [!IMPORTANT]
> **Franchise = thương hiệu/IP tổng thể**, cái tên chung mà khán giả bình thường gọi khi nhắc tới cả một "vũ trụ" tác phẩm — bất kể có bao nhiêu đạo diễn, dàn diễn viên, mốc thời gian, reboot, hay hình thức thể hiện (anime, live-action, phim lẻ, series, OVA, phim chuyển thể...) khác nhau. Ví dụ: "Batman", "Spider-Man", "Dragon Ball", "Fast & Furious", "Godzilla".

### ⚠️ TMDb Collection KHÔNG PHẢI là Franchise — chỉ là một tín hiệu hẹp hơn nhiều

TMDb Collection chỉ gom các phim **cùng một mạch truyện liên tục** (thường là một bộ ba/series sequel trực tiếp do cùng ê-kíp), **không** gom xuyên suốt cả thương hiệu. Một franchise thật sự thường trải dài trên **NHIỀU** TMDb Collection khác nhau, cộng thêm cả series/anime hoàn toàn không có khái niệm Collection.

Ví dụ franchise **Spider-Man** nằm rải trong ít nhất 4 TMDb Collection riêng biệt cộng thêm series/anime không TMDb Collection nào bao trùm hết:
- *Sam Raimi's Spider-Man Trilogy* (Collection A — 3 phim)
- *The Amazing Spider-Man Collection* (Collection B — 2 phim)
- *Spider-Man (MCU) Collection* (Collection C)
- *Spider-Man: Into/Across the Spider-Verse Collection* (Collection D — hoạt hình)

Ví dụ franchise **Dragon Ball** còn rõ hơn: anime (Dragon Ball, Z, GT, Kai, Super — series, TMDb không có Collection cho series) + phim live-action *Dragonball Evolution* (2009, một phim lẻ độc lập, KHÔNG nằm trong Collection nào vì không có sequel) — tất cả đều thuộc CÙNG MỘT franchise "Dragon Ball" dù không có bất kỳ TMDb Collection nào gom đủ cả.

**Hệ quả**: skill này KHÔNG được lấy thẳng `collection.name` làm tên franchise rồi dừng lại. TMDb Collection chỉ là một **bằng chứng đầu vào** cho bước suy luận — luôn phải hỏi tiếp "có nội dung nào khác (hình thức khác, Collection khác) cùng thương hiệu này không?" trước khi chốt tên và thành viên franchise.

### 🎬 Loại thứ 2: Franchise theo Tác Giả/Đạo Diễn (Auteur Collection)

Ngoài franchise theo IP/thương hiệu ở trên, còn một loại **hoàn toàn khác bản chất** nhưng vẫn được công nhận là franchise cho mục đích gom thư viện: **tuyển tập tác phẩm của cùng MỘT đạo diễn/tác giả**, dù các tác phẩm đó **KHÔNG chia sẻ nhân vật, thế giới truyện, hay bất kỳ liên kết cốt truyện nào**. Đây là cách tổ chức phổ biến với các đạo diễn có phong cách riêng, hay được xem/sưu tầm trọn bộ như một "tác giả" (auteur) hơn là từng phim rời rạc.

Ví dụ: các phim của đạo diễn **Makoto Shinkai** (*5 Centimet Trên Giây*, *Tên Cậu Là Gì?*, *Khu Vườn Ngôn Từ*, *Đứa Con Của Thời Tiết*...) không phim nào là sequel/liên quan cốt truyện của phim khác, nhưng vẫn nên gom chung 1 franchise vì cùng một đạo diễn và thường được khán giả/thư viện phim sưu tầm trọn bộ theo tác giả.

**Cách nhận diện**: khi 2+ title không có bất kỳ quan hệ IP/thương hiệu nào (đã xác nhận qua Bước 2 dưới), NHƯNG bạn biết chắc chúng cùng một đạo diễn/tác giả (dựa vào kiến thức có sẵn hoặc `search_web`), và đạo diễn/tác giả đó đủ nổi bật để tác phẩm của họ thường được sưu tầm/nhắc tới như một "tuyển tập" (không áp dụng cho đạo diễn chỉ làm 1 phim duy nhất trong danh sách, hay đạo diễn commercial làm phim không có phong cách/thương hiệu tác giả rõ rệt).

**Cách đặt tên**: dùng đúng tên đạo diễn/tác giả, có thể thêm hậu tố rõ nghĩa để phân biệt với franchise-IP, ví dụ **"Makoto Shinkai Collection"** hoặc **"Đạo diễn Makoto Shinkai"** — nhất quán một kiểu trong toàn bộ output, không trộn lẫn 2 cách đặt tên cho cùng 1 tác giả giữa các lần gọi khác nhau (nếu caller đã cache tên cũ, giữ nguyên format đó).

### 🏛️ Loại thứ 3: Franchise theo Hãng Phim/Studio (Studio Collection)

Loại này rút ra từ dữ liệu thật: một thư viện có **17 phim Studio Ghibli** (*Vùng Đất Linh Hồn*, *Totoro*, *Mononoke*, *Howl*, *Kiki*, *Mộ Đom Đóm*, *Chỉ Còn Ngày Hôm Qua*, *Marnie*, *Arrietty*, *Kaguya*...) nằm rải rác thành 17 nhóm độc lập vì:
- Chúng **không chia sẻ IP/nhân vật/cốt truyện** nào → không phải franchise loại 1.
- Chúng **KHÔNG cùng một đạo diễn** → cũng không phải Auteur Collection loại 2. Miyazaki Hayao đạo diễn phần lớn, nhưng Takahata Isao đạo diễn *Mộ Đom Đóm*/*Chỉ Còn Ngày Hôm Qua*/*Gia Đình Nhà Yamada*, Yonebayashi Hiromasa đạo diễn *Marnie*/*Arrietty*.

Nhưng ai cũng gom chúng lại thành "phim Ghibli" — vì thương hiệu **hãng sản xuất** đủ mạnh để bản thân nó là một bộ sưu tập. Đây là loại thứ 3: **cùng một studio/hãng phim có bản sắc thương hiệu rõ rệt**.

**Cách nhận diện**: 2+ title không có quan hệ IP (loại 1) lẫn không cùng đạo diễn (loại 2), NHƯNG cùng một studio mà studio đó nổi tiếng đến mức khán giả sưu tầm theo hãng — điển hình: Studio Ghibli, Pixar, Aardman, Kyoto Animation, Disney Animated Classics. **KHÔNG** áp dụng cho hãng phát hành đại trà không mang bản sắc tuyển tập (Warner Bros., Universal, Netflix... — gom theo mấy hãng này là vô nghĩa vì gần như phim nào cũng thuộc một hãng lớn nào đó).

**Cách đặt tên**: dùng đúng tên studio, ví dụ **"Studio Ghibli"**, **"Pixar"**.

> [!IMPORTANT]
> Đây KHÔNG phải là gán thể loại (genre) hay độ nổi tiếng. Franchise chỉ được gom khi có **MỘT trong ba** loại quan hệ thật:
> 1. **Quan hệ thương hiệu/IP**: sequel, prequel, spin-off, reboot, chuyển thể (anime ↔ live-action), các mùa/season khác nhau của cùng gốc, hoặc chính thức cùng chia sẻ nhân vật/thế giới truyện gốc.
> 2. **Cùng đạo diễn/tác giả** đủ nổi bật (Auteur Collection).
> 3. **Cùng hãng phim/studio** có bản sắc tuyển tập rõ rệt (Studio Collection).
>
> Thứ tự ưu tiên khi một title thoả nhiều loại: (1) > (2) > (3) — vd một phim Ghibli thuộc series *Totoro* thì xếp vào franchise IP "Totoro" trước, không xếp thẳng vào "Studio Ghibli". Không suy đoán bừa — thà để một title đứng độc lập còn hơn gom sai.

### 🔁 Luôn đối chiếu với franchise ĐÃ TỒN TẠI trước khi kết luận độc lập

Rút ra từ dữ liệu thật: rất nhiều title bị bỏ sót chỉ vì **tên khác ngôn ngữ** so với franchise đã có sẵn trong thư viện — 8 phim *"One Piece: Episode of..."* đứng lẻ trong khi franchise *"Loạt phim Đảo Hải Tặc"* (15 title) đã tồn tại; *"Thor: Truyền Thuyết Về Asgard"* đứng lẻ trong khi franchise *"Thor"* đã có; hàng loạt *"Kindaichi Case Files"* / *"The Files of Young Kindaichi"* / *"Thám tử Kindaichi"* nằm rời nhau. So khớp chuỗi thuần **không bao giờ** bắt được các trường hợp này.

**Quy tắc**: nếu caller cung cấp danh sách franchise đã tồn tại (mục `existing_franchises` trong Input), thì với MỖI title, luôn kiểm tra "nó có thuộc về một franchise nào trong danh sách đó không" — kể cả khi tên hoàn toàn khác ngôn ngữ — TRƯỚC khi kết luận độc lập hay đặt tên franchise mới. Khi khớp, trả về **chính xác tên franchise cũ** (copy y nguyên), không tự đặt tên biến thể mới, để không tạo thêm nhóm trùng nghĩa.

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
- `ref` (tuỳ chọn nhưng **khuyến nghị mạnh** khi gọi từ chương trình khác, vd media-hub): chuỗi định danh do caller tự đặt, skill không đọc/diễn giải giá trị này — chỉ **echo nguyên văn** lại trên item tương ứng trong Output. Giúp caller map kết quả về đúng bản ghi nội bộ (vd `root_key` union-find) mà không cần tự suy luận ngược từ tmdb_id/tvdb_id trả về, tránh sai lệch khi một title có cả hai ID nhưng response chỉ mang một loại.
- Có thể truyền thêm `title` thô (tên thư mục cục bộ, tên đã biết...) nếu có — dùng để đối chiếu/gỡ rối khi tra cứu ra kết quả mơ hồ, nhưng **ID luôn là nguồn sự thật**, không tin tên thư mục.
- `existing_franchises` (tuỳ chọn nhưng **rất nên truyền**): danh sách tên các franchise ĐÃ TỒN TẠI trong thư viện của caller. Truyền kèm ở cấp ngoài cùng, song song với mảng title:

```json
{
  "existing_franchises": ["Loạt phim Đảo Hải Tặc", "Thor", "Thám Tử Lừng Danh Conan"],
  "items": [ { "ref": "tmdb-...", "tmdb_id": 123, "type": "movie" } ]
}
```

  Skill BẮT BUỘC đối chiếu mỗi title với danh sách này trước khi kết luận độc lập (xem mục "Luôn đối chiếu với franchise ĐÃ TỒN TẠI" ở trên) và **copy y nguyên tên cũ** khi khớp.

## 📤 Output

```json
{
  "franchises": [
    {
      "name": "Spider-Man",
      "source": "ai_verified",
      "tmdb_collection_ids": [556, 531241, 573848],
      "items": [
        { "ref": "tmdb-557", "tmdb_id": 557, "type": "movie", "title": "Spider-Man" },
        { "ref": "tmdb-1930", "tmdb_id": 1930, "type": "movie", "title": "The Amazing Spider-Man" },
        { "ref": "tmdb-324857", "tmdb_id": 324857, "type": "movie", "title": "Spider-Man: Into the Spider-Verse" }
      ]
    },
    {
      "name": "Dragon Ball",
      "source": "ai_verified",
      "items": [
        { "ref": "tmdb-12609", "tmdb_id": 12609, "type": "tv", "title": "Dragon Ball" },
        { "ref": "tmdb-12610", "tmdb_id": 12610, "type": "tv", "title": "Dragon Ball Z" },
        { "ref": "tvdb-76666", "tvdb_id": 76666, "type": "tv", "title": "Dragon Ball GT" },
        { "ref": "tmdb-32380", "tmdb_id": 32380, "type": "tv", "title": "Dragon Ball Kai" },
        { "ref": "tmdb-14210", "tmdb_id": 14210, "type": "movie", "title": "Dragonball Evolution" }
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
- **Mọi title đầu vào phải xuất hiện đúng 1 lần** trong `franchises` (trừ khi rơi vào `unresolved`) — kể cả khi nó độc lập, không thuộc thương hiệu nào: tạo một franchise `source: "standalone"` chỉ chứa chính nó, **KHÔNG** dồn các title độc lập vào một nhóm "chưa phân loại" chung chung.
- `source` chỉ còn 2 giá trị:
  - `ai_verified`: xác định được quan hệ thương hiệu/IP thật qua suy luận + tra cứu web (áp dụng cho MỌI trường hợp có gom nhóm — kể cả khi trong nhóm có phim đã sẵn TMDb Collection, vì bước suy luận vẫn phải chạy để kiểm tra có nội dung nào khác thuộc cùng thương hiệu không).
  - `standalone`: không tìm được bằng chứng liên kết nào, đứng một mình.
- `tmdb_collection_ids` (tuỳ chọn, mảng): liệt kê TẤT CẢ TMDb Collection ID đã gặp trong quá trình gom nhóm franchise này (một franchise có thể trải dài nhiều Collection) — thông tin tham khảo thêm cho caller, không quyết định tên/thành viên franchise.
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

Với mỗi title, giữ lại: `tmdb_id`, `type`, `title`, `original_title`, `year`, và với phim lẻ là field `collection` (nếu có — chỉ dùng làm TÍN HIỆU cho Bước 2, không phải kết luận cuối).

Nếu `find`/`get` không trả kết quả nào, đưa title đó vào `unresolved` với lý do rõ ràng, không đoán mò.

### Bước 2 — Suy luận franchise (thương hiệu/IP) cho MỌI title, xuyên suốt mọi hình thức

Áp dụng đồng nhất cho cả phim lẻ (có hoặc không có TMDb Collection) và series/anime — vì Collection không bao giờ là câu trả lời cuối cùng, chỉ là một manh mối.

> [!NOTE]
> **Các title cùng `collection.id` chắc chắn cùng nội dung/franchise với nhau** — khỏi cần tra web để xác nhận QUAN HỆ GIỮA CHÚNG (TMDb curator đã xác nhận rồi). Việc còn lại chỉ là tra web xem Collection đó có phải TOÀN BỘ franchise hay chỉ một phần (vd còn anime/series/Collection khác cùng thương hiệu) — xem bước 2 dưới.

1. **Gom nhóm ứng viên**: (a) mọi title cùng `collection.id` gộp sẵn một nhóm ứng viên (chắc chắn cùng nhau, xem NOTE trên); (b) các title còn lại trong cùng batch có chung từ khóa chính trong tên (vd "Spider-Man", "Dragon Ball", "Godzilla") là ứng viên cùng franchise — xét chung để đỡ tra web lặp lại.
2. **Tra web xác định franchise thật sự trải rộng tới đâu**, dùng `search_web`:
   - `search_web("<tên chung> franchise all movies anime tv series list")`
   - `search_web("<title> part of which franchise")`
   - `search_web("<title A> and <title B> same franchise universe")`
   - Nếu title là phim có sẵn `collection` (từ Bước 1): đừng dừng lại ở đó — hỏi thêm `search_web("<collection name> franchise other movies series anime")` để biết Collection này có phải toàn bộ franchise hay chỉ một phần (vd chỉ 1 trong 4 collection của Spider-Man).
   - **Không tìm được quan hệ IP nào**: trước khi kết luận độc lập, kiểm tra thêm khả năng **Auteur Collection** (xem mục "Loại thứ 2" ở trên) — `search_web("<title> director")` rồi `search_web("<tên đạo diễn> filmography")` xem có title KHÁC trong cùng batch cũng của đạo diễn đó không.

   > [!IMPORTANT]
   > **CHỈ dùng `search_web`, KHÔNG tự `curl`/`urllib`/`fetch` trực tiếp vào một trang web** (IMDb, Wikipedia, ...) qua `run_command`. Các trang này có thể tải chậm, chặn bot, hoặc yêu cầu render JS — một lệnh treo lâu có thể kéo timeout cả cuộc hội thoại (đã từng xảy ra: một lần `curl imdb.com` trực tiếp treo gần 5 phút làm toàn bộ batch bị huỷ giữa chừng). `search_web` đã đủ nhanh và đủ thông tin cho hầu hết trường hợp.

   - Ưu tiên nguồn đáng tin: Wikipedia, trang chính thức của studio/nhà xuất bản, chính TMDb/TVDB (overview đôi khi nhắc franchise).
   - Chỉ xác nhận khi có **bằng chứng cụ thể**: sequel/prequel/spin-off/reboot/chuyển thể chính thức, cùng nhân vật/thế giới chính, cùng series gốc chia mùa/hình thức khác (vd anime ↔ live-action cùng IP) — HOẶC cùng đạo diễn/tác giả đủ nổi bật (Auteur Collection). **Không** gom chỉ vì cùng thể loại hay tình cờ trùng từ trong tên.
   - Không tìm được bằng chứng nào → title đó **độc lập** (`source: "standalone"`) — im lặng-là-đúng tốt hơn đoán sai.
3. **Đặt tên franchise** theo tên thương hiệu gốc phổ biến nhất, KHÔNG phải tên một Collection cụ thể hay tên một season/phần cụ thể (vd đặt "Spider-Man" chứ không phải "The Amazing Spider-Man Collection"; đặt "Dragon Ball" chứ không phải "Dragon Ball Kai").
4. Nếu trong quá trình tra cứu gặp `tmdb_collection_id` (từ field `collection` ở Bước 1, hoặc tự tìm thêm qua `search-collection`/`collection` của `tmdb-lookup` khi cần xác minh thành viên một Collection cụ thể), gom hết vào mảng `tmdb_collection_ids` của franchise — chỉ mang tính tham khảo, KHÔNG dùng để đặt tên.

### Bước 3 — Gộp kết quả & trả về đúng schema Output ở trên

Đảm bảo mọi title input đều có mặt đúng 1 lần trong `franchises` hoặc `unresolved`. Các title cùng franchise do AI xác định phải được gộp chung một entry (so khớp theo tên thương hiệu đã chuẩn hoá), không tạo nhiều franchise trùng nghĩa chỉ khác cách viết (vd "Spider Man" và "Spider-Man" phải là MỘT franchise).

---

## 💾 Gợi Ý Cache (khuyến nghị cho caller, không bắt buộc)

Bước 2 (search_web + suy luận AI) tốn thời gian và token — caller nên cache kết quả theo khóa `tmdb_id`/`tvdb_id` đã xử lý (vd bảng `franchise_ai_cache` phía media-hub: `root_key TEXT PRIMARY KEY, franchise TEXT, checked_at REAL`), để lần gọi sau chỉ xử lý các title **mới** chưa từng được phân loại, tránh hỏi lại toàn bộ thư viện mỗi lần.

## ⚠️ Giới Hạn Đã Biết

- Không tự bịa franchise cho title hoàn toàn mới/hiếm không có thông tin trên web — trả về `standalone`.
- `search_web` có thể trả kết quả nhiễu (fan theory, clickbait) — luôn ưu tiên nguồn chính thống, và khi nghi ngờ, thiên về **không gom** thay vì gom sai.
- `search-collection`/`collection` (của `tmdb-lookup`) chỉ là API TMDb công khai, chỉ **đọc**, chỉ dùng để lấy `tmdb_collection_ids` tham khảo — không dùng để quyết định tên hay thành viên franchise.
- Không xử lý phát hiện trùng lặp title (title đã tồn tại 2 lần với 2 ID khác nhau) — đó là việc của bước dedupe phía caller (vd union-find theo `item_uid` như media-hub đang làm), skill này chỉ nhận input đã dedupe.
