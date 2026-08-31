# 💰 Expense Tracker & Invoice Analyzer Plugin

Plugin chuyên dụng quản lý, tổng hợp và phân tích chi tiêu cá nhân hợp nhất (**Multi-Source Unified Expense Intelligence**).

## ✨ Điểm Nổi Bật

1. **Đa Nguồn Dữ Liệu (Multi-Source Ingestion):**
   - **Hình ảnh hoá đơn / Biên lai:** Đọc ảnh hoá đơn giấy, biên lai POS, ảnh chụp màn hình chuyển khoản ngân hàng (VCB, MB, Techcombank, TPBank...), ví điện tử (MoMo, ZaloPay).
   - **Shopee Direct Fetch:** Tự động mở trình duyệt cho người dùng quét mã QR đăng nhập 1 lần, sau đó tự kéo toàn bộ đơn hàng theo khoảng thời gian.
   - **TikTok Shop Direct Fetch:** Tự động lấy lịch sử mua sắm TikTok Shop.
2. **Xử Lý Thông Minh Ảnh Thiếu Ngày (Smart Date Fallback):**
   - Tự động quét EXIF metadata / File timestamp nếu ảnh không có ngày in sẵn.
   - Gom các trường hợp không rõ vào nhóm `Chưa xác định ngày (Unspecified)` kèm cảnh báo.
3. **Phân Loại Danh Mục Thông Minh (10+ Categories):**
   - Ăn uống, Mua sắm, Tiện ích (Điện/Nước/Net), Di chuyển, Y tế, Giáo dục, Giải trí, Tài chính...
4. **Phát Hiện Trùng Lặp (De-duplication):**
   - Phát hiện khi người dùng vừa chụp ảnh chuyển khoản ngân hàng vừa đồng bộ đơn Shopee để tránh tính 2 lần.
5. **Xuất Báo Cáo Đa Kênh:**
   - Bảng Markdown trực tiếp trong chat.
   - File `expenses_unified.csv` (nhập Excel / Google Sheets).
   - `summary.json` cho các hệ thống khác.
   - **Interactive HTML Dashboard** độc lập xem biểu đồ tròn, biểu đồ cột và thumbnail ảnh hoá đơn.
