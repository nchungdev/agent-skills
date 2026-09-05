---
name: media-hub-franchise
description: >-
  Tra cứu franchise phim từ kho Media Hub, liệt kê các franchise trong list phim,
  xem danh sách phim trong từng franchise (kèm ID tmdb/tvdb để map với file input CSV),
  và tự động sắp xếp/phân loại một danh sách phim bất kỳ vào đúng franchise.
---

# Media Hub Franchise Skill

Skill này chuyên biệt dùng để xử lý danh mục phim Media Hub, phân loại và ánh xạ các phim theo franchise, kèm theo mã định danh `tmdb` và `tvdb` chuẩn xác từ nguồn CSV.

## Các tệp dữ liệu và script

- **Data source CSV**: `data/movies.csv`
- **Rules mapping**: `rules/franchise_rules.json`
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
Script sẽ tự động bóc tách ID, áp dụng rules và cập nhật lại toàn bộ `data/catalog.json`.
