---
name: media-hub-franchise
description: >-
  Tra cứu franchise phim từ kho Media Hub, liệt kê các franchise trong list phim,
  xem danh sách phim trong từng franchise (kèm ID tmdb/tvdb để map với file input CSV),
  và tự động sắp xếp/phân loại một danh sách phim bất kỳ vào đúng franchise.
---

# Media Hub Franchise Skill

Skill này chuyên biệt dùng để xử lý danh mục phim Media Hub, phân loại và ánh xạ các phim theo franchise, kèm theo mã định danh `tmdb` và `tvdb` chuẩn xác từ nguồn CSV.

## 🧭 Triết lý Phân loại: Bộ Lọc IP ➔ Cấp Độ Franchise

> [!IMPORTANT]
> **Dùng IP làm "Bộ lọc bản chất" (để không gom sai), nhưng dùng Franchise làm "Cấp độ hiển thị" (để thư viện gọn gàng).**

1. **Bước 1: Bộ lọc bản chất IP (Disambiguation)**:
   - Các tác phẩm có tên trùng hoặc gần giống nhưng khác IP bản quyền, khác xuất xứ thì **bắt buộc phải tách riêng**:
     * *Kingdom (2012)* (Anime Chiến Quốc Nhật Bản) ≠ *Kingdom: Ashin of the North* (Zombie Hàn Quốc).
     * *Journey to the West (1996)* (Tây Du Ký TVB) ≠ *The Westward* (Tây Hành Kỷ 3D donghua) ≠ *A Chinese Odyssey* (Đại Thoại Tây Du).
     * *Avatar (2009)* (James Cameron) ≠ *Avatar Aang: The Last Airbender* (Thế thần Aang).
     * *Ne Zha* (Ma Đồng Giáng Thế) ≠ *I Am Nezha*.
     * *Sherlock Holmes* (phim điện ảnh) ≠ *Sherlock* (BBC series).

2. **Bước 2: Cấp độ Franchise hiển thị**:
   - Khi cùng một IP gốc, gom theo thương hiệu mà khán giả cảm thấy tự nhiên nhất để duyệt:
     * **Theo dòng thương hiệu/đồ chơi:** *B-Daman*, *Super Sentai*, *Transformers*, *Pokémon*, *Dragon Ball*, *Doraemon* (dù đổi nhân vật qua các thế hệ vẫn gom chung).
     * **Theo Auteur/Đạo diễn tuyển tập:** *The Makoto Shinkai Collection*, *Higashino Keigo* (chia các nhánh Galileo, Kaga Kyoichiro, Masquerade, Standalone).
     * **Theo Studio có bản sắc:** *Studio Ghibli*.
     * **Theo Vũ trụ điện ảnh lớn:** *Marvel Universe*, *DC Universe*.

3. **Chống trùng nguồn (Deduplication)**:
   - Tự động phát hiện và gộp các dòng bị trùng trong CSV (ví dụ: cùng một phim nhưng xuất hiện ở cả server Jellyfin và Plex) thành 1 bản ghi duy nhất, gộp nguồn (`sources = Draft+JellyPlex`) và gộp đầy đủ `tmdb_ids`, `tvdb_ids`. Các bản remake/khác năm (như Doraemon 1980 vs 2006) được giữ riêng biệt.

---

## Các tệp dữ liệu và script

- **Data source CSV**: `data/movies.csv`
- **Rules mapping**: `rules/franchise_rules.json` (chứa `disambiguation`, `umbrella_rules`, `keyword_franchises`, `canonical_name_map`)
- **Catalog đã phân loại**: `data/catalog.json`
- **Script quản trị**: `scripts/catalog_manager.py`

---

## Hướng dẫn xử lý 3 yêu cầu cốt lõi

### 1. Yêu cầu 1: "Có những franchise nào từ list phim?"
Thực thi lệnh:
```bash
python3 <skill_dir>/scripts/catalog_manager.py list-franchises
```
- Trả về danh sách tất cả các franchise, tổng số phim, kèm theo số lượng `movie` và `series`.
- Có thể thêm flag `--alpha` nếu muốn sắp xếp theo thứ tự bảng chữ cái A-Z.

---

### 2. Yêu cầu 2: "Franchise [Tên] có những phim nào?" (hoặc mỗi franchise có những phim nào)
Thực thi lệnh:
```bash
python3 <skill_dir>/scripts/catalog_manager.py get-franchise "<Tên franchise>"
```
- **Quy tắc hiển thị bắt buộc**: Mỗi phim **phải** đi kèm ID `[tmdb-...]` và/hoặc `[tvdb-...]` để người dùng dễ dàng Ctrl+F hoặc map ngược lại vào file CSV nguồn.
- Định dạng xuất chuẩn:
  `- <Tên gốc> (<Năm>) · <movie/series> · [tmdb-<id>] [tvdb-<id>] · *<Tên tiếng Việt>* [thuyết minh/sub]`
- Ví dụ:
  `- Spider-Man (2002) · movie · [tmdb-557] [tvdb-301] · *Người Nhện*`
  `- Harry Potter and the Philosopher's Stone (2001) · movie · [tmdb-671] [tvdb-66] · *Harry Potter và Hòn Đá Phù Thủy* [thuyết minh VN]`

---

### 3. Yêu cầu 3: "Sắp xếp những phim trong list vào từng franchise"
Khi người dùng đưa vào một danh sách các tên phim (hoặc đường dẫn tới tệp văn bản/danh sách phim mới):
Thực thi lệnh:
```bash
python3 <skill_dir>/scripts/catalog_manager.py categorize "<Danh sách phim hoặc đường dẫn file>"
```
Hoặc đối chiếu với `rules/franchise_rules.json` và `data/catalog.json` để gom cụm các phim vào từng heading `### [Tên Franchise]` rõ ràng.

---

### 4. Cập nhật khi có file CSV mới
Khi người dùng cập nhật hoặc thay thế file CSV mới:
```bash
python3 <skill_dir>/scripts/catalog_manager.py build [path/to/new_movies.csv]
```
Script sẽ tự động chạy quy trình chống trùng đa nguồn, bóc tách ID, áp dụng rules phân tách IP và cập nhật lại toàn bộ `data/catalog.json`.
