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

## ⚡ QUY TẮC PHÂN BATCH & THỰC THI NỀN TUẦN TỰ (BATCHING & SEQUENTIAL EXECUTION)

Nhằm đảm bảo tính ổn định, kiểm soát hạn mức quota API (tránh lỗi `429 / RESOURCE_EXHAUSTED`) và duy trì chất lượng dịch thuật cao nhất:

1. **Giới Hạn Kích Thước Batch**:
   - Mỗi batch chỉ dịch **tối đa 5 file / 5 tập** (`MAX_FILES_PER_BATCH = 5`).
2. **Bắt Buộc Chuyển Sang Tác Vụ Ngầm Khi > 1 File**:
   - Nếu yêu cầu dịch từ 2 file trở lên (hoặc dịch trọn bộ/mùa phim), **Agent bắt buộc phải chuyển sang tác vụ ngầm (Background Task / Subagent)** thay vì xử lý chặn giao diện chính.
3. **Thực Thi Tuần Tự Từng Batch (Sequential Batch Execution)**:
   - Các batch phải được thực thi **tuần tự lần lượt (Batch 1 xong ➔ mới chạy Batch 2 ➔ Batch 3...)**.
   - **Tuyệt đối KHÔNG khởi chạy ồ ạt nhiều batch song song cùng một lúc** để chống tràn bộ nhớ và bảo vệ quota API.
4. **Quy Trình Hoàn Tất Mỗi Batch**:
   - Xuất đủ 3 định dạng phụ đề: `.vi.ass` (Styling), `.vi.srt` (Chuẩn), `.vi.vtt` (WebVTT qua skill `sub-to-webvtt`).
   - Cập nhật checklist tiến độ vào `PROGRESS.md` và kiểm định kỹ thuật vào `AUDIT_REPORT.md`.
   - Tự động kích hoạt đồng bộ cuốn chiếu các file đã dịch sang NAS Storage và Google Drive.

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


