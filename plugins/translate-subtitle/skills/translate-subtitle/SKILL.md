---
name: translate-subtitle
description: Dịch phụ đề phim chuyên sâu. Hỗ trợ đa CSDL định danh (TMDb ID, TheTVDB ID). Kiến trúc 2 tầng (Two-Tier Architecture): Workspace cục bộ tự quản lý tiến độ, độ mơ hồ và override style; Kho Skill tập trung chỉ lưu trữ tri thức đã chốt (Confirmed Knowledge) và bồi đắp lên GitHub nchungdev/subtitle-glossary-hub.
---

# Translate Subtitle Skill

Kỹ năng dịch phụ đề chuyên nghiệp, vận hành theo **Kiến Trúc Phân Tách Hai Tầng (Two-Tier Architecture)**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. WORKSPACE CỤC BỘ DỰ ÁN (<Tên_Phim>_Curation/ hoặc Translation Workspace) │
│    ├── PROGRESS.md          -> Tiến độ từng tập (Dịch/Audit/Xuất bản)       │
│    ├── AMBIGUITY_LOG.md     -> Các đoạn thoại mờ nghĩa, nghi vấn cần chốt   │
│    ├── _style/              -> Style ASS riêng của người dịch (OVERRIDE)   │
│    ├── _work/               -> Dữ liệu nháp & script bóc tách               │
│    └── output/ (translated) -> Thành phẩm phụ đề .vi.ass & .vi.srt          │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ (Chỉ đẩy dữ liệu ĐÃ CONFIRM)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. KHO TẬP TRUNG TRONG SKILL & GITHUB HUB (CONFIRMED KNOWLEDGE ONLY)        │
│    ├── glossary.json        -> Thuật ngữ, ma trận xưng hô ĐÃ CHỐT 100%      │
│    ├── ERRORS_AND_PITFALLS.md -> Cạm bẫy & bài học thực chiến đã kiểm chứng  │
│    ├── resources/genres/    -> Quy tắc & style mặc định theo thể loại phim  │
│    └── resources/glossaries/ -> Kho lưu trữ dài hạn theo TMDb / TheTVDB ID  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Kích Hoạt & Cơ Chế Override

### 1. Dịch Phim:
`translate-subtitle <tên_phim/tmdbid/tvdbid/imdbid> <đường_dẫn_subtitle> <ngôn_ngữ_đích>`

### 2. Thứ Tự Ưu Tiên Nạp Style (Style Hierarchy & Override):
1. **Ưu tiên 1 (Cao nhất - Override):** File style trong thư mục cục bộ `_style/*.ass` do người dịch tùy biến.
2. **Ưu tiên 2 (Mặc định):** Style chuẩn theo thể loại trong `resources/genres/<the_loai>/styles.ass`.
3. **Ưu tiên 3 (Cơ bản):** Style mặc định của file phụ đề gốc.

---

## 🏛️ CHI TIẾT CẤU TRÚC 2 TẦNG

### TẦNG 1: THƯ MỤC CỤC BỘ MỖI DỰ ÁN (PROJECT WORKSPACE)
* 📄 **`PROGRESS.md`:** Bảng checklist trạng thái từng tập (Đang dịch / Đã dịch / Đã đối chiếu 3 chiều / Đã lên Plex).
* ❓ **`AMBIGUITY_LOG.md`:** Ghi nhận các đoạn thoại chơi chữ, tiếng lóng, ngữ cảnh mờ nghĩa (`do_chac: thap`) để người dịch thảo luận hoặc tham vấn trước khi chốt.
* 🎨 **`_style/custom_style.ass`:** Nơi chứa font chữ, màu sắc, bóng chữ do người dịch thiết kế riêng cho bộ phim để override style mặc định.
* 🛠️ **`_work/`:** Lưu file thoại bóc tách, script Python đối chiếu.
* 📦 **`output/` (hoặc `translated/`):** Chứa các file phụ đề `.vi.ass` và `.vi.srt` hoàn thiện.

---

### TẦNG 2: KHO TRI THỨC ĐÃ CONFIRM TRONG SKILL (CONFIRMED REPOSITORY)
*Chỉ tiếp nhận những mục đã được kiểm duyệt và xác nhận chắc chắn 100%:*
* 📑 **`glossary.json`:** Bảng từ điển chính thức (Nhân vật, ma trận xưng hô, chiêu thức, bối cảnh) có độ chắc chắn cao (`do_chac: cao`).
* 🚨 **`ERRORS_AND_PITFALLS.md`:** Nhật ký các lỗi sai đã trả giá và phương án sửa chuẩn xác để tái sử dụng vĩnh viễn cho cộng đồng.
* 🏷️ **`metadata.json`:** Thông tin định danh TheTVDB `{tvdb-ID}` và TMDb `{tmdb-ID}`.
* 🌐 **Đồng bộ mở:** Tự động fetch từ kho cộng đồng: [github.com/nchungdev/subtitle-glossary-hub](https://github.com/nchungdev/subtitle-glossary-hub).

---

# PHẦN A — QUY TRÌNH DỊCH THUẬT CHUẨN

1. **Khởi Tạo:**
   * Nạp `glossary.json` đã chốt từ kho Skill.
   * Tạo `PROGRESS.md` và `AMBIGUITY_LOG.md` trong thư mục dự án.
   * Kiểm tra xem dự án có `_style/` để override không; nếu không, lấy style thể loại từ `resources/genres/`.
2. **Xử Lý Thoại:**
   * Gặp câu mờ nghĩa ➜ Ghi vào `AMBIGUITY_LOG.md`.
   * Gặp lỗi sai qua trung gian ➜ Đối chiếu 3 chiều và sửa.
3. **Đóng Gói & Bồi Đắp:**
   * Xuất bản phụ đề vào thư mục `output/` theo tên chuẩn Plex/Jellyfin.
   * Bồi đắp các thuật ngữ đã chốt và lỗi đã sửa ngược lại vào kho Skill `resources/glossaries/<id_glossary>/`.
