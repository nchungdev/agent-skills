---
name: translate-subtitle
description: Skill dùng để dịch phụ đề phim. Tự động xây dựng glossary.json dựa trên thông tin phim (bối cảnh, cốt truyện, xưng hô, thuật ngữ) và tổ chức thư mục dịch thuật chuẩn xác.
---

# Translate Subtitle Skill

Kỹ năng này hướng dẫn Agent cách dịch một file phụ đề phim một cách chuyên nghiệp. Agent sẽ tự động tạo thư mục làm việc, tìm kiếm thông tin về phim để xây dựng từ điển (glossary), và sử dụng từ điển đó để đảm bảo bản dịch nhất quán.

## 🚀 Cách kích hoạt

Người dùng sẽ ra lệnh bằng cú pháp sau:
`translate-subtitle <tên_phim/tmdbid/tvdbid/imdbid> <đường_dẫn_chứa_subtitle> <ngôn_ngữ_đích>`

Ví dụ:
`translate-subtitle "Mashin Hero Wataru" ./subs/ep01.srt vi`
`translate-subtitle tt0094502 /Downloads/movies/ vi`

## 🎯 Quy trình thực hiện (5 Bước Bắt Buộc)

Khi được kích hoạt, Agent **PHẢI** thực hiện tuần tự các bước sau ngay tại thư mục hiện tại:

### Bước 1: Khởi tạo cấu trúc thư mục
Tạo ngay cấu trúc thư mục chuẩn tại nơi người dùng chạy lệnh:
- `glossary.json` (File từ điển)
- `_style/` (Thư mục chứa các file định dạng, ví dụ file style ASS)
- `_work/` (Thư mục làm việc chứa file gốc để nháp)
- `translated/` (Thư mục chứa file phụ đề đã dịch hoàn chỉnh)

### Bước 2: Xây dựng Glossary (Từ điển bối cảnh)
Sử dụng ID hoặc Tên phim `<tên_phim/tmdbid/tvdbid/imdbid>` do người dùng cung cấp:
1. **Tìm kiếm thông tin chính thống:** Quét web, wiki, hoặc các database (TMDb, IMDb, fandom) để thu thập thông tin về bộ phim này.
2. **Trích xuất thông tin:** Thu thập 5 yếu tố cốt lõi:
   - **Bối cảnh (Context/World-building):** Phim diễn ra ở đâu, thời đại nào, luật lệ vũ trụ ra sao.
   - **Cốt truyện (Plot):** Tóm tắt nội dung chính.
   - **Quan hệ nhân vật (Character Relationships):** Ai là bạn, ai là thù, gia phả thế nào.
   - **Cách xưng hô (Pronouns):** Dựa vào quan hệ để quy định cách xưng hô (VD: Wataru - Shibaraku là Cháu - Bác / Sư phụ).
   - **Thuật ngữ (Terminology/Glossary):** Các chiêu thức, tên địa danh, vũ khí (VD: Ryujinmaru, Đăng Long Kiếm).
3. **Tạo file `glossary.json`:** Xuất tất cả các thông tin trên vào file `glossary.json` với cấu trúc JSON rõ ràng.

### Bước 3: Chuẩn bị file Subtitle
1. Copy file phụ đề gốc từ `<đường_dẫn_chứa_subtitle>` vào thư mục `_work/`.
2. Phân tích định dạng của file (`.srt`, `.ass`, `.vtt`...) và nhận diện các tag style nếu có.

### Bước 4: Dịch thuật & Áp dụng Glossary
1. Tiến hành dịch nội dung từ ngôn ngữ gốc sang `<ngôn_ngữ_đích>`.
2. **ĐIỀU KIỆN TIÊN QUYẾT:** Quá trình dịch **PHẢI** tuân thủ 100% các quy định về xưng hô, thuật ngữ, tên riêng đã được chốt trong `glossary.json`.
3. (Tùy chọn) Nếu là file `.ass`, có thể tạo file `00-TAT-CA-STYLE.txt` trong `_style/` để lưu trữ các format Karaoke/Ruby text đẹp mắt giống như cách làm của nhóm sub chuyên nghiệp.

### Bước 5: Hoàn thiện & Báo cáo
1. Lưu file phụ đề đã dịch thuật hoàn chỉnh vào thư mục `translated/`. Đổi tên file phù hợp (VD: `ten-phim.vi.ass`).
2. Trả lời người dùng, tóm tắt nhanh về các thông tin bối cảnh/xưng hô đã lưu trong `glossary.json` và thông báo hoàn thành công việc.
