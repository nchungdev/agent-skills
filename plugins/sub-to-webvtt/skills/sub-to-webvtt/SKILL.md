---
name: sub-to-webvtt
description: Chuyển đổi và tối ưu hóa phụ đề (SRT, ASS, SSA) sang định dạng WebVTT (.vtt) chuẩn W3C, làm sạch các tag override làm lỗi trình duyệt web ({\pos}, {\fade}, {\fn}), giữ lại định dạng typography cốt lõi (bold, italic, màu sắc), chuẩn hóa timecode dấu chấm (00:00:00.000), và tự động đặt tên theo chuẩn stream zero-latency của Media Hub Dashboard.
---

# Sub-to-WebVTT Converter Skill

Kỹ năng chuyên trách làm sạch, chuẩn hóa và chuyển đổi các file phụ đề định dạng phim (`.ass`, `.ssa`, `.srt`) sang chuẩn **WebVTT (Web Video Text Tracks - `.vtt`)** của hiệp hội W3C, đảm bảo tương thích 100% khi phát trực tuyến qua trình duyệt Web, iPad, iPhone (Safari) và Plex Web Client.

---

## 🚀 Cú Pháp Kích Hoạt CLI

```bash
# 1. Chuyển đổi 1 file phụ đề sang WebVTT:
python3 <skill_dir>/scripts/convert_webvtt.py convert "<đường_dẫn_sub.ass|srt>" [--out-file "<đường_dẫn_xuat.vtt>"]

# 2. Chuyển đổi hàng loạt toàn bộ thư mục phim:
python3 <skill_dir>/scripts/convert_webvtt.py batch "<thư_mục_chứa_phụ_đề>" [--out-dir "<thư_mục_xuất>"] [--strip-tags]

# 3. Đồng bộ và tự động tạo phụ đề WebVTT cho Media Hub Video Player:
python3 <skill_dir>/scripts/convert_webvtt.py sync-hub "<thư_mục_phim_gdrive>"
```

---

## 🛠️ Các Tính Năng Cốt Lõi

1. 🧹 **Làm Sạch Override Tag ASS/SSA Thông Minh:**
   * Bóc tách các thẻ đặc thù của Desktop player (`{\pos(x,y)}`, `{\fad(t1,t2)}`, `{\an8}`, `{\fnFontName}`) mà trình duyệt Web không hỗ trợ để tránh bị lỗi hiển thị rác ký tự trên màn hình.
   * Giữ lại các hiệu ứng quan trọng: In đậm `<b>`, In nghiêng `<i>`, Gạch chân `<u>`, và Màu sắc văn bản `<c.color>`.

2. ⏱️ **Chuẩn Hóa Timecode & Header Chuẩn W3C:**
   * Chuyển đổi dấu phẩy `,` trong SRT sang dấu chấm `.` chuẩn WebVTT (`00:01:23.456 --> 00:01:25.789`).
   * Tự động bổ sung Header `WEBVTT` và khối `NOTE Metadata` (Title, Language, Timing).

3. 🌐 **Tối Ưu Zero-Latency Cho Media Hub Video Player:**
   * Tự động xuất file `<Tên_Phim>.vi.vtt` hoặc `<Tên_Phim>.en.vtt` đặt cạnh video.
   * Giúp trình phát video HTML5 tích hợp trong Media Hub Dashboard tự động tải phụ đề ngay khi người dùng bấm nút `▶️ Phát` mà không cần cấu hình thủ công.
