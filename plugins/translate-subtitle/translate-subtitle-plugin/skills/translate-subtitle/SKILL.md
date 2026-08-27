---
name: translate-subtitle
description: Skill dùng để dịch phụ đề phim chuyên sâu. Tích hợp quy trình dịch chuẩn xác, phân cấp nguồn dữ liệu, xử lý thuật ngữ/tên riêng, áp dụng Karaoke 2 lớp cho chiêu thức và quy trình kiểm duyệt (Audit) tự động.
---

# Translate Subtitle Skill (Chuyên sâu)

Kỹ năng này hướng dẫn Agent cách dịch một file phụ đề phim một cách chuyên nghiệp, kế thừa bộ quy trình chuẩn xác đã được tinh chỉnh qua các dự án dịch thuật lớn. Agent sẽ tự động tạo thư mục, đối chiếu đa nguồn, áp dụng quy tắc dịch tên riêng, tạo hiệu ứng Karaoke 2 lớp, và audit phát hiện lỗi.

## 🚀 Cách kích hoạt

Người dùng sẽ ra lệnh bằng cú pháp sau:
`translate-subtitle <tên_phim/tmdbid/tvdbid/imdbid> <đường_dẫn_chứa_subtitle> <ngôn_ngữ_đích>`

## 🎯 Quy trình thực hiện (5 Bước Cốt Lõi)

Khi được kích hoạt, Agent **PHẢI** thực hiện tuần tự các bước sau ngay tại thư mục hiện tại:

### Bước 1: Khởi tạo Workspace & Bộ nhớ dài hạn
Tạo ngay cấu trúc thư mục chuẩn tại nơi người dùng chạy lệnh:
- `glossary.json` (Bộ nhớ dài hạn: Chứa thuật ngữ, xưng hô, phân loại độ tin cậy)
- `LOI-DA-GAP.md` (Nhật ký lỗi: Ghi nhận các lỗi sai từng gặp để tránh tái phạm)
- `_style/` (Chứa các file định dạng ASS, ví dụ: 00-TAT-CA-STYLE.txt)
- `_work/` (Chứa file gốc, script nháp, và code xử lý Python)
- `translated/` (Chứa file phụ đề đã dịch hoàn chỉnh)

### Bước 2: Xây dựng Glossary (Nguyên tắc Đối chiếu Đa nguồn)
Dịch thuật không bao giờ được tin tưởng mù quáng vào một nguồn duy nhất (đặc biệt là bản tiếng Anh vì thường là bản dịch đời thứ 3 từ tiếng Trung/Nhật).
**Thứ bậc nguồn dữ liệu (Từ cao xuống thấp):**
1. Thông tin/ảnh tên chính thức từ Website của phim.
2. Wikipedia tiếng Nhật / Cơ sở dữ liệu gốc.
3. Bản phụ đề ngôn ngữ gốc hoặc ngôn ngữ thứ 2 (VD: Tiếng Trung).
4. Bản phụ đề tiếng Anh (Thấp nhất - Dùng để đối chiếu, tuyệt đối không dịch mù quáng).
*(Lưu ý: Cần ít nhất 2 nguồn Nhật độc lập để chốt việc đổi hàng loạt một cái tên)*

**Cấu trúc `glossary.json` cần trích xuất:**
- Bối cảnh (Context) & Cốt truyện (Plot).
- Quan hệ nhân vật & Cách xưng hô (Phải giữ nguyên sắc thái gốc).
- Tên riêng, Tên chiêu thức, Địa danh (Kèm trường `"do_chac": "cao/trung_binh/thap"` để đánh giá độ tin cậy).

### Bước 3: Quy tắc dịch Tên Riêng & Thuật ngữ
Áp dụng quy tắc sau cho mọi bản dịch:
- **Giữ nguyên Romaji (Không dịch):** Tên người, Tên Robot/Mecha (Mashin), Tên vũ khí/kiếm, Địa danh đọc theo âm Nhật.
- **Dịch sang Hán-Việt:** Địa danh/Cõi đọc theo âm Hán (Thiên Bộ Giới, Thần Bộ Giới...).
- **Tên Chiêu thức khi Hô to (Đặc biệt):** Dịch sang Hán-Việt kết hợp hiệu ứng Karaoke. **Số âm tiết Hán-Việt PHẢI khớp với số âm tiết Romaji** (VD: En-ryuu-ken = Viêm-Long-Quyền). Không áp dụng quy tắc đếm âm tiết này cho thoại thường.

### Bước 4: Chế bản Subtitle & Hiệu ứng Karaoke (Dành cho ASS)
Copy file phụ đề gốc vào `_work/` và bắt đầu dịch. Nếu file là `.ass`:
1. **Karaoke 2 lớp cho tên chiêu:** Khi nhân vật hô to tuyệt chiêu, KHÔNG dùng `\N` để ngắt dòng (sẽ làm hỏng timing `\kf`). Phải tách thành 2 dòng `Dialogue` có cùng mốc thời gian:
   - **Dòng Romaji:** `MarginV` cao hơn (VD: `0068`), text to, rõ ràng. (VD: `{\kf62}Sen\h{\kf62}jin\h{\kf62}maru`)
   - **Dòng Hán-Việt (Ruby text):** `MarginV` thấp hơn (VD: `0040`), size nhỏ hơn, hiệu ứng mờ/trong suốt. (VD: `{\kf62}Chiến\h{\kf62}Thần\h{\kf62}Hoàn`)
2. **Dấu cách:** Luôn dùng `\h` (hard space) thay vì khoảng trắng thường để tránh bị lỗi hiển thị.
3. **Phân tách Karaoke:** Tách theo CHỮ HÁN/Ý NGHĨA (VD: `Ryu|jin|maru`), không tách theo mora tiếng Nhật.

### Bước 5: Audit & Kiểm toàn vẹn (Cực kỳ quan trọng)
Không bao giờ tin vào cảm giác "chắc xong rồi". Phải chạy các bước audit sau:
1. **Quét hư từ tiếng Anh:** Quét các từ như `the, is, are, of, and, that`... (Dấu hiệu câu chưa dịch hết).
2. **Kiểm tra chéo 3 chiều:** (Nguồn 1 ↔ Nguồn 2 ↔ Bản dịch). Đặt cạnh bản gốc để phán xét.
3. **Thay thế hàng loạt bằng Python:** Mọi phép thay chuỗi tiếng Việt phải dùng Python script, sau đó đếm số lần xuất hiện để xác minh. KHÔNG dùng `sed` hay lệnh shell cơ bản cho text Unicode tiếng Việt.
4. **Kiểm toàn vẹn File:** 
   - Số dòng `Dialogue` trước == sau (Không được sót dòng nào).
   - Số lượng thẻ `\kf` trước == sau.
   - Đảm bảo encoding luôn là UTF-8 hợp lệ.

*Nếu phát hiện lỗi, phải cập nhật ngay vào `LOI-DA-GAP.md` và `glossary.json` để thế hệ Agent tiếp theo không lặp lại.*

### Bước 6: Hoàn thiện
Lưu file vào `translated/` với tên chuẩn (VD: `ten-phim.vi.ass`). Tóm tắt cho User về quá trình dịch, các quy tắc xưng hô đã chốt, và báo cáo kết quả audit.
