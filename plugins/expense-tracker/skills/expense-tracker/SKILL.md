---
name: expense-tracker
description: Kỹ năng phân tích chi tiêu hợp nhất từ hình ảnh hoá đơn, biên lai chuyển khoản ngân hàng và tự động đồng bộ đơn hàng trực tiếp từ Shopee & TikTok Shop. Tự động xử lý ảnh thiếu ngày, gom nhóm theo tháng, phân loại 10+ danh mục chi tiêu, và xuất báo cáo Markdown, CSV, JSON, Interactive HTML Dashboard.
---

# 💰 Expense Tracker & Invoice Analyzer Skill

Kỹ năng thông minh giúp người dùng phân tích và quản lý chi tiêu hợp nhất từ nhiều nguồn dữ liệu:
1. **Hình ảnh hoá đơn / Biên lai / Ảnh chụp màn hình chuyển khoản** (kèm cơ chế xử lý ảnh thiếu ngày thông minh).
2. **Lịch sử mua sắm Shopee** (Tự động mở trình duyệt quét QR đăng nhập 1 lần và kéo toàn bộ đơn hàng).
3. **Lịch sử mua sắm TikTok Shop**.

---

## 🚀 Cú Pháp Kích Hoạt & Lệnh CLI

### 1. Đồng bộ và quét đơn Shopee (Tự mở Chrome đăng nhập QR):
```bash
python3 /Volumes/512GB/AI\ Workspace/agent-skills/plugins/expense-tracker/skills/expense-tracker/scripts/shopee_fetcher.py --output /path/to/output_dir
```

### 2. Phân tích danh sách hình ảnh hoá đơn / thư mục ảnh:
```bash
python3 /Volumes/512GB/AI\ Workspace/agent-skills/plugins/expense-tracker/skills/expense-tracker/scripts/image_receipt_parser.py --input-dir /path/to/images --output /path/to/output_dir
```

### 3. Chạy tổng hợp hợp nhất (Unified Pipeline: Cả Ảnh + Shopee + TikTok):
```bash
python3 /Volumes/512GB/AI\ Workspace/agent-skills/plugins/expense-tracker/skills/expense-tracker/scripts/main_unified.py \
    --images-dir /path/to/images \
    --sync-shopee \
    --sync-tiktok \
    --output-dir ./expense_report_$(date +%Y%m%d)
```

---

## 🛡️ Hướng Dẫn Dành Cho AI Agent (Antigravity & Claude)

Khi người dùng gửi yêu cầu liên quan đến chi tiêu:

1. **Khi người dùng cung cấp hình ảnh:**
   - Sử dụng khả năng Multimodal Vision để nhận diện số tiền, ngày giờ, đơn vị bán hàng, nội dung chi tiêu.
   - Nếu ảnh không có ngày in trên hoá đơn:
     - Thử kiểm tra EXIF / File Creation Date.
     - Nếu vẫn không có, xếp vào nhóm `Chưa xác định ngày (Unspecified Date)` và thông báo rõ trong bảng tổng hợp.
2. **Khi người dùng yêu cầu lấy đơn từ Shopee / TikTok Shop:**
   - Chạy script `shopee_fetcher.py` hoặc `tiktok_fetcher.py`.
   - Báo cho người dùng biết một cửa sổ Chrome đã mở ra và hướng dẫn họ quét mã QR trên điện thoại.
   - Sau khi hoàn thành, script sẽ tự động lưu session để các lần sau không cần quét lại.
3. **Tổng hợp & Báo cáo:**
   - Chạy `expense_engine.py` để phân loại danh mục, tính tổng tiền theo tháng, tính % tỷ trọng.
   - Hiển thị bảng Markdown tóm tắt ngay trong chat.
   - Tạo file HTML Dashboard trực quan bằng `report_generator.py` để người dùng mở xem biểu đồ.

---

## 🏷️ Quy Tắc Danh Mục Chi Tiêu (Categories)
- 🍔 **Food & Dining**: Ăn uống, cafe, siêu thị thực phẩm, GrabFood, ShopeeFood.
- 🛍️ **Shopping**: Thời trang, đồ gia dụng, mỹ phẩm, Shopee, TikTok Shop.
- 💡 **Utilities & Housing**: Tiền điện EVN, nước sinh hoạt, internet, tiền nhà.
- 🚗 **Transportation**: Xăng dầu, Grab, Be, taxi, vé xe, máy bay, gửi xe.
- 💊 **Healthcare**: Nhà thuốc (Pharmacity, Long Châu), bệnh viện, khám chữa bệnh.
- 📚 **Education**: Sách vở, học phí, khoá học.
- 🎬 **Entertainment & Travel**: Xem phim CGV, khách sạn, du lịch, Netflix.
- 🏦 **Financial & Fees**: Phí ngân hàng, trả góp, sao kê thẻ tín dụng.
- ❓ **Uncategorized**: Giao dịch chưa rõ danh mục.
