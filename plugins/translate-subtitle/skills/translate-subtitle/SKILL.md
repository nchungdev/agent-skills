---
name: translate-subtitle
description: Dịch phụ đề phim chuyên sâu. Hỗ trợ đa CSDL định danh (TMDb ID, TheTVDB ID). Cho phép linh hoạt chọn Style (Preset, Tự động theo thể loại, Tùy chỉnh override, hoặc Mặc định). Kiến trúc 2 tầng (Two-Tier Architecture).
---

# Translate Subtitle Skill

Kỹ năng dịch phụ đề chuyên nghiệp với cơ chế tùy biến Typography & Style toàn diện.

## 🚀 Cú Pháp Kích Hoạt & Tùy Chọn Style (Style Selection)

```sh
translate-subtitle <tên_phim/tmdbid/tvdbid> <đường_dẫn_subtitle> <ngôn_ngữ_đích> [--style <tùy_chọn>]
```

### 🎨 Các Chế Độ Chọn Style (`--style`):
| Tham Số | Ý Nghĩa / Hoạt Động | Thể Loại Phù Hợp |
| :--- | :--- | :--- |
| `--style default` *(hoặc bỏ trống)* | **Tự động nhận diện thể loại** và áp dụng style chuẩn tương ứng | Tự động phân tích |
| `--style classic-cinema` | Style điện ảnh kinh điển, phông chữ thanh lịch, viền đổ bóng dịu mắt | Phim chiếu rạp, Movies, Drama |
| `--style detective-mystery` | Style trinh thám hiện đại, tương phản cao, hỗ trợ dòng suy luận | Kindaichi, Conan, Tantei Q, Furuhata |
| `--style mecha-robot-karaoke`| Shounen chiến đấu, hỗ trợ **Karaoke 2 lớp** câu triệu hồi & tên chiêu | Wataru, Gundam, Gurren Lagann |
| `--style medical-drama` | Style y khoa chuẩn mực, hỗ trợ style chú thích thuật ngữ phẫu thuật | Black Jack, Young Black Jack, Monster |
| `--style original` | **Giữ nguyên 100%** typography và style của file phụ đề nguồn gốc | Khi file gốc đã có style quá đẹp |
| `--style <path/to/custom.ass>`| **Override trực tiếp** bằng file `.ass` do người dịch tự thiết kế | Tùy biến tự do |

---

## 🏛️ THỨ TỰ ƯU TIÊN STYLE (STYLE RESOLUTION HIERARCHY)

```text
1. Tham số CLI --style <custom/preset>     (Ưu tiên số 1 - Chỉ định rõ)
2. File cục bộ trong dự án: _style/*.ass   (Ưu tiên số 2 - Override theo dự án)
3. Style mặc định theo thể loại: resources/styles/<genre>.ass
4. Style gốc trong file phụ đề nguồn
```

---

## 🏛️ KIẾN TRÚC PHÂN TÁCH 2 TẦNG (TWO-TIER ARCHITECTURE)

* **TẦNG 1 (CỤC BỘ DỰ ÁN):** Chứa `PROGRESS.md` (tiến độ từng tập), `AMBIGUITY_LOG.md` (đoạn thoại mờ nghĩa), `_style/` (style override cục bộ), `output/` (thành phẩm).
* **TẦNG 2 (KHO TẬP TRUNG SKILL & GITHUB):** Chỉ lưu tri thức **ĐÃ CONFIRM 100%** (`glossary.json`, `ERRORS_AND_PITFALLS.md`, `metadata.json`).

---

## 🎬 TỰ ĐỘNG KHỞI TẠO BỐI CẢNH & NHÂN VẬT QUA TMDB API

Khi bắt đầu dịch một bộ phim mới, skill có thể tự động gọi `auto_context_resolver.py` để:
1. **Lấy bối cảnh & cốt truyện chính thức** từ TMDb API.
2. **Tự động trích xuất danh sách nhân vật chính thức** nạp sẵn vào `glossary.json`.
3. **Phân tích thể loại & cốt truyện** để tự động gợi ý / áp dụng `--style` chuẩn (`medical-drama`, `detective-mystery`, `mecha-robot-karaoke`...).
4. **Tự động tạo `PROGRESS.md` và `AMBIGUITY_LOG.md`** cho workspace cục bộ.

```sh
python3 <skill_dir>/scripts/auto_context_resolver.py "<tên_phim_hoặc_tmdb_id>" --type tv|movie --output-dir "<workspace_path>"
```
