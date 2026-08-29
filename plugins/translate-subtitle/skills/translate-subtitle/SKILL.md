---
name: translate-subtitle
description: Dịch phụ đề phim chuyên sâu. Hỗ trợ đa cơ sở dữ liệu định danh (TMDb ID, TheTVDB ID, IMDb ID). Tích hợp kho glossary dài hạn và nhật ký cạm bẫy lỗi ERRORS_AND_PITFALLS.md bồi đắp theo từng tác phẩm.
---

# Translate Subtitle Skill

Kỹ năng dịch phụ đề chuyên nghiệp, đúc kết từ các dự án dịch anime, phim chiếu rạp (Movies) và live-action quy mô lớn.

## 🚀 Kích hoạt & Cơ chế Định danh Đa CSDL (Multi-Database ID Resolution)

`translate-subtitle <tên_phim/tmdbid/tvdbid/imdbid> <đường_dẫn_subtitle> <ngôn_ngữ_đích>`

### 📌 Quy chuẩn `id_glossary` cho TV Shows và Movies:
* **TV Series / Anime nhiều mùa:** Định danh qua `{tvdb-ID}` hoặc `{tmdb-ID}` (Ví dụ: `Black_Jack_{tvdb-78864}`, `Monster_{tvdb-74880}`).
* **Movies / Phim lẻ / OVA Chiếu rạp:** Định danh qua `{tmdb-ID}` (Ví dụ: `Black_Jack_The_Movie_1996_{tmdb-54378}`, `Mononoke_Movie_Karakasa_2024_{tmdb-1144933}`).
* **Bộ giải mã tự động (Resolver):** File `resources/MASTER_INDEX.json` tự động ánh xạ mọi truy vấn `tmdb-XXXX`, `tvdb-XXXX`, hoặc tên phim về đúng thư mục glossary chuẩn!

---

# PHẦN A — LÕI CHUNG & QUẢN TRỊ DỮ LIỆU DÀI HẠN

## 1. Khởi tạo workspace & nạp Kho Glossary Dài Hạn

* **Kho lưu trữ dài hạn tập trung:** Mọi dự án phải kiểm tra và nạp dữ liệu từ:
  `<skill_dir>/resources/glossaries/<id_glossary>/`
  * `glossary.json` — Bộ nhớ dài hạn, nhân vật, ma trận xưng hô, bảng quy đổi.
  * `ERRORS_AND_PITFALLS.md` — Nhật ký cạm bẫy và lỗi thực chiến đã sửa.
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
