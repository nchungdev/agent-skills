# 🌐 Translate Subtitle Plugin (`translate-subtitle`)

Plugin chuyên sâu phục vụ dịch thuật và chuẩn hóa phụ đề phim cho **Google Antigravity (AGY)**.

## 🌟 Tính năng nổi bật
1. **Khởi tạo Workspace chuẩn:** Tự động tạo bộ cấu trúc `glossary.json`, `LOI-DA-GAP.md`, `_style/`, `_work/`, `translated/`.
2. **Xây dựng Glossary đa nguồn:** Tra cứu và đối chiếu 4 cấp độ nguồn (Official JP > Wiki JP > Sub Trung > Sub Anh).
3. **Chuẩn hóa Tên riêng & Xưng hô:** Giữ nguyên Romaji cho tên người, mecha, vũ khí; Hán-Việt cho chiêu thức và cõi.
4. **Hiệu ứng Karaoke 2 tầng:** Tự động tạo 2 dòng Dialogue (Romaji + Hán-Việt Ruby) với timing `\kf` và MarginV chuẩn.
5. **Quy trình Audit tự động:** Quét hư từ tiếng Anh, đếm số lượng dòng trước/sau, kiểm tra tính toàn vẹn UTF-8.
