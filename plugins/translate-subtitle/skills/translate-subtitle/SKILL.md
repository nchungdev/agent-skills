---
name: translate-subtitle
description: Dịch phụ đề phim chuyên sâu. Lõi chung áp dụng cho mọi ngôn ngữ nguồn, kèm mô-đun riêng cho nguồn CJK (Nhật/Trung/Hàn) xử lý tên riêng, Hán-Việt và karaoke tên chiêu. Có kho lưu trữ glossary dài hạn và nhật ký cạm bẫy lỗi ERRORS_AND_PITFALLS.md bồi đắp theo từng tác phẩm.
---

# Translate Subtitle Skill

Kỹ năng dịch phụ đề chuyên nghiệp, đúc kết từ các dự án dịch anime và live-action quy mô lớn.

## 🚀 Kích hoạt

`translate-subtitle <tên_phim/tmdbid/tvdbid/imdbid> <đường_dẫn_subtitle> <ngôn_ngữ_đích>`

---

## 0. Xác định ngôn ngữ nguồn & thể loại TRƯỚC KHI dịch

| | Là gì | Quyết định |
|---|---|---|
| **Ngôn ngữ nguyên tác** | Phim được sản xuất bằng tiếng gì | Chọn mô-đun (phần B/C), tra tên riêng ở đâu |
| **Ngôn ngữ file phụ đề đang có** | File nguồn ta cầm trong tay viết bằng tiếng gì | Biết nó là bản gốc hay bản qua trung gian |

### 0.1. Nhận dạng ngôn ngữ nguyên tác
* **Metadata âm thanh của file video:** `ffprobe -v error -select_streams a -show_entries stream=index:stream_tags=language,title -of csv=p=0 "phim.mkv"`
* **Trường original_language từ TMDB/TVDB/IMDb.**
* **Tên file / nhóm phát hành:** `[AI-Raws]`, `[DBD-Raws]`, `[SubsPlease]` -> nguồn Nhật.

### 0.2. Nhận dạng hệ chữ viết
* Nhật: có Kana (`[ぁ-んァ-ヶ]`)
* Hàn: có Hangul (`[가-힣]`)
* Trung: Chữ Hán không có Kana (`[一-鿿]`)
* Latin (Anh/Pháp/Việt): Phân biệt bằng mật độ dấu phụ và hư từ (`the, is, are, that, you...`).

---

# PHẦN A — LÕI CHUNG & QUẢN TRỊ DỮ LIỆU DÀI HẠN

## 1. Khởi tạo workspace & nạp Kho Glossary Dài Hạn

* **Kho lưu trữ dài hạn tập trung:** Mọi dự án phải kiểm tra và nạp dữ liệu từ:
  `<skill_dir>/resources/glossaries/<id_glossary>/` (vd: `resources/glossaries/Black_Jack_{tvdb-78864}/`)
  * `glossary.json` — Bộ nhớ dài hạn, nhân vật, ma trận xưng hô, bảng quy đổi.
  * `ERRORS_AND_PITFALLS.md` — Nhật ký cạm bẫy và lỗi thực chiến đã sửa (thay thế LOI-DA-GAP).
  * `AUDIT_REPORT.md` — Báo cáo kiểm định toàn vẹn dòng và đối chiếu 3 chiều.
  * `WORKFLOW.md` — Quy trình dịch thuật và phân tích bối cảnh.
  * `metadata.json` — Thông tin định danh TheTVDB / TMDb / IMDb.
* **Không gian làm việc cục bộ:**
  * `_style/` — File style ASS (nếu có karaoke chiêu thức).
  * `_work/` — File thoại bóc tách, script Python.
  * `translated/` — Kết quả phụ đề xuất bản.
* **Quy tắc bồi đắp vĩnh viễn:** Khi sửa lỗi mới, luôn cập nhật vào `ERRORS_AND_PITFALLS.md` và `glossary.json` của kho skill để tái sử dụng mãi mãi.

## 2. Thứ bậc nguồn & Đối chiếu 3 chiều
```text
1. Trang chính thức của phim (Artbook, ảnh tên sản xuất)  ← Ưu tiên tối thượng
2. Wikipedia / CSDL bằng CHÍNH ngôn ngữ gốc của phim
3. Phụ đề bằng ngôn ngữ gốc hoặc ngôn ngữ trung gian gần gốc
4. Phụ đề tiếng Anh qua trung gian                         ← Thấp nhất
```

## 3. Cấu trúc Glossary Chuẩn Quốc Tế
* `nhan_vat`: Danh sách nhân vật chính / phụ.
* `address_matrix`: Ma trận xưng hô (Ai gọi ai bằng gì tùy theo tuổi tác, địa vị).
* `ten_chinh_thuc`: Bảng đối chiếu nguồn cấp 1.
* `bang_quy_doi_bat_buoc`: Chuyển đổi từ sai qua trung gian -> tên chuẩn.
* `Romaji_Catchphrase`: Giữ nguyên Romaji các câu cửa miệng (vd: *"Achoko-poko!"*).

## 4. Kiểm định Toàn Vẹn & Xuất Bản
* **Đối chiếu 3 chiều:** `Nguyên tác gốc ↔ Trung gian ↔ Tiếng Việt`.
* **Kiểm toàn vẹn:** `Số dòng Dialogue trước == sau`, `0 từ tiếng nguồn sót`, `UTF-8 chuẩn`.
* **Đặt tên xuất bản chuẩn Plex/Jellyfin:** `<Tên Phim> - S01E01.vi.ass` & `.vi.srt`.

---

# PHẦN B — MÔ-ĐUN CJK (Nhật / Trung / Hàn)

* **Tên người, mecha, vũ khí:** Giữ phiên âm Romaji / Pinyin gốc.
* **Chiêu thức, thần chú hô to:** Dùng Hán-Việt uy lực + Karaoke hai lớp (Dòng trên: Romaji - Dòng dưới: Hán-Việt đồng nhịp).
