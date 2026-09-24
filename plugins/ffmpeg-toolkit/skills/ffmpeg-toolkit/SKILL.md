---
name: ffmpeg-toolkit
description: Comprehensive media processing engine powered by FFmpeg & FFprobe. Extracts embedded (muxed) subtitles from MKV/MP4/M4V containers, aligns subtitle timecodes to speech via Voice Activity Detection (VAD) without consuming AI tokens, converts and sanitizes subtitles (ASS/SRT) to W3C-standard WebVTT for browser streaming, and outputs media processing reports. Supports local execution and remote execution on NAS via SSH.
---

# FFmpeg Toolkit (Media & Subtitle Processing Engine)

Bộ công cụ xử lý media và phụ đề toàn diện sử dụng **FFmpeg** và **FFprobe**. Hợp nhất 3 năng lực cốt lõi: Bóc tách phụ đề nhúng, căn chỉnh khẩu hình VAD (không tốn token AI), và chuyển đổi chuẩn WebVTT cho web streaming.

---

## 🚀 Các Lệnh CLI Cốt Lõi

```bash
# 1. Bóc tách toàn bộ phụ đề nhúng (Muxed Subtitles) từ video container:
python3 <skill_dir>/scripts/extract_subtitles.py "<duong_dan_video.mkv>" [--lang vi,en,zh] [--out-dir "<thu_muc_xuat>"]

# 2. Căn chỉnh mốc thời gian khớp khẩu hình bằng FFmpeg VAD (Zero-Token Alignment):
python3 <skill_dir>/scripts/align_frame.py "<sub_goc.srt>" "<video.mkv>" [--out-file "<sub_da_khop.srt>"]

# 3. Chuyển đổi và làm sạch tag override sang chuẩn WebVTT (.vtt) cho Web/Plex Player:
python3 <skill_dir>/scripts/convert_webvtt.py convert "<sub.ass|srt>" [--out-file "<sub.vtt>"]
python3 <skill_dir>/scripts/convert_webvtt.py batch "<thu_muc_phu_de>" [--strip-tags]

# 4. Báo cáo trạng thái các tác vụ media (Report):
python3 <skill_dir>/scripts/ffmpeg_cli.py report
```

---

## 🛠️ Chi Tiết 3 Siêu Năng Lực

### 1. 📤 Bóc Tách Phụ Đề Nhúng (`extract`)
* Tự động quét các track phụ đề nhúng trong file `MKV`, `MP4`, `M4V` bằng `ffprobe`.
* Trích xuất chính xác ra file `.srt` (với SubRip/Text) hoặc `.ass` (với SSA/ASS styling).
* Đặt tên chuẩn hóa Plex: `<Tên_Phim> - S<Mùa>E<Tập>.<mã_ngôn_ngữ>.<ext>` (ví dụ: `Monster - S01E01.en.ass`).

### 2. 🎙️ Căn Chỉnh Khẩu Hình Bằng VAD (`align`)
* Sử dụng bộ lọc `ffmpeg -af silencedetect` để phát hiện chính xác các khoảng im lặng và giọng nói của nhân vật.
* Khớp mốc thời gian (start/end) của từng dòng thoại theo khẩu hình thực tế mà **không tiêu tốn bất kỳ token LLM nào**.
* Bảo toàn 100% các thẻ hiệu ứng karaoke (KFX), chữ lượn sóng và định dạng màu sắc.

### 3. 🌐 Tối Ưu Hóa Chuẩn WebVTT (`to-vtt`)
* Bóc sạch các tag override desktop làm lỗi web viewer (`{\pos}`, `{\fad}`, `{\an8}`, `{\fnFont}`).
* Giữ nguyên các định dạng typography cốt lõi: In đậm `<b>`, in nghiêng `<i>`, gạch chân `<u>` và màu chữ.
* Chuẩn hóa timecode W3C dấu chấm (`00:01:23.456 --> 00:01:25.789`) và header `WEBVTT` để phát trực tiếp zero-latency trên HTML5 video player và Plex Web.

---

## 🖥️ Chế Độ Xử Lý Từ Xa Trên NAS (Remote Execution via SSH)

Nếu video dung lượng lớn (hàng chục GB) nằm trên NAS, Agent **không cần kéo video về máy cá nhân**, mà thực thi trực tiếp trên NAS qua SSH:

```bash
ssh user@nas "ffmpeg -i '/srv/mergerfs/.../video.mkv' -map 0:s:0 '/srv/mergerfs/.../sub.srt'"
```
Thông tin kết nối NAS được đọc tự động từ `./.agent/nas_config.json`.
