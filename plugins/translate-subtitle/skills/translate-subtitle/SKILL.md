---
name: translate-subtitle
description: Dịch phụ đề phim chuyên sâu. Hỗ trợ đa CSDL định danh (TMDb ID, TheTVDB ID). Kiến trúc 2 tầng (Two-Tier Architecture): Workspace cục bộ tự quản lý tiến độ, độ mơ hồ, audit report và override style; Kho Skill tập trung chỉ lưu trữ tri thức tái sử dụng vĩnh viễn (glossary.json, WORKFLOW.md, ERRORS_AND_PITFALLS.md) trên GitHub nchungdev/subtitle-glossary-hub.
---

# Translate Subtitle Skill

Kỹ năng dịch phụ đề chuyên nghiệp, vận hành theo **Kiến Trúc Phân Tách Hai Tầng (Two-Tier Architecture)**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 📂 TẦNG RIÊNG (LOCAL PROJECT WORKSPACE — <Tên_Phim>_Curation/ hoặc Project) │
│    ├── 📄 PROGRESS.md        -> Checklist tiến độ từng tập (Dịch/Audit/Plex) │
│    ├── ❓ AMBIGUITY_LOG.md   -> Đoạn thoại mờ nghĩa, chơi chữ đang duyệt     │
│    ├── 📊 AUDIT_REPORT.md    -> Báo cáo kiểm định toàn vẹn & kỹ thuật dòng   │
│    ├── 🎨 _style/            -> Style ASS riêng của người dịch (OVERRIDE)   │
│    ├── 🛠️ _work/             -> Dữ liệu nháp & script bóc tách tạm thời      │
│    └── 📦 output/ (translated)-> Kết quả phụ đề xuất bản .vi.ass & .vi.srt  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ (Chỉ đẩy TRI THỨC VĨNH CỬU)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🏛️ TẦNG CHUNG (KHO TẬP TRUNG SKILL & GITHUB SUBTITLE-GLOSSARY-HUB)          │
│    ├── 📑 glossary.json      -> Bảng thuật ngữ, ma trận xưng hô ĐÃ CHỐT 100% │
│    ├── 📋 WORKFLOW.md        -> Cẩm nang & phương pháp luận dịch tác phẩm   │
│    ├── 🚨 ERRORS_AND_PITFALLS.md -> Cạm bẫy thực chiến & bài học đã sửa     │
│    ├── 🎭 resources/genres/  -> Quy tắc & Style mặc định theo Thể Loại       │
│    └── 🏷️ metadata.json      -> Định danh chuẩn TheTVDB / TMDb ID            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Kích Hoạt & Các Chế Độ Style

```sh
translate-subtitle <tên_phim/tmdbid/tvdbid> <đường_dẫn_subtitle> <ngôn_ngữ_đích> [--style <tùy_chọn>]
```

### 🎨 Các Chế Độ Chọn Style (`--style`):
* `--style default` *(hoặc bỏ trống)*: Tự động nhận diện thể loại và áp dụng style tương ứng.
* `--style classic-cinema`: Style điện ảnh kinh điển (Arial/Helvetica), viền mỏng, đổ bóng dịu mắt.
* `--style detective-mystery`: Style trinh thám hiện đại (Trebuchet MS), viền đen tương phản cao.
* `--style mecha-robot-karaoke`: Shounen chiến đấu, Karaoke 2 lớp cho câu triệu hồi & tên chiêu.
* `--style medical-drama`: Style y khoa chuẩn mực, hỗ trợ style chú thích thuật ngữ phẫu thuật.
* `--style original`: Giữ nguyên 100% typography/styling gốc từ file phụ đề ban đầu.
* `--style <path/to/custom.ass>`: Override trực tiếp bằng file style do người dịch tự thiết kế.

---

## 🏛️ PHÂN ĐỊNH CHI TIẾT 2 TẦNG

### 1. TẦNG RIÊNG (LOCAL PROJECT WORKSPACE):
* 📄 **`PROGRESS.md`:** Checklist trạng thái từng tập (Đang dịch / Đã dịch / Đã audit / Đã lên Plex).
* ❓ **`AMBIGUITY_LOG.md`:** Ghi nhận các đoạn thoại chơi chữ, tiếng lóng, ngữ cảnh mờ nghĩa cần duyệt.
* 📊 **`AUDIT_REPORT.md`:** Báo cáo kiểm định toàn vẹn của dự án (kiểm tra số dòng trước vs sau, 0 từ tiếng nguồn sót lại, UTF-8 sạch).
* 🎨 **`_style/custom_style.ass`:** Nơi chứa font chữ, màu sắc do người dịch thiết kế riêng để override.
* 🛠️ **`_work/`:** Lưu file thoại bóc tách, script Python đối chiếu.
* 📦 **`output/`:** Chứa các file phụ đề `.vi.ass` và `.vi.srt` hoàn thiện.

---

### 2. TẦNG CHUNG (KHO TẬP TRUNG SKILL & GITHUB HUB):
* 📑 **`glossary.json`:** Bảng từ điển chính thức (Nhân vật, ma trận xưng hô, chiêu thức) độ chắc chắn cao.
* 📋 **`WORKFLOW.md`:** Cẩm nang phương pháp dịch và bối cảnh đặc thù để người dịch sau tiếp nối nhất quán.
* 🚨 **`ERRORS_AND_PITFALLS.md`:** Nhật ký các cạm bẫy lỗi đã trả giá và phương án sửa để tránh lặp lại.
* 🏷️ **`metadata.json`:** Thông tin định danh TheTVDB `{tvdb-ID}` và TMDb `{tmdb-ID}`.
