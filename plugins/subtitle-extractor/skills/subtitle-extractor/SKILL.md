---
name: subtitle-extractor
description: Tự động phát hiện, liệt kê và bóc tách (extract) các track phụ đề nhúng (Muxed Subtitles) từ video container (MKV, MP4, M4V) ra các file phụ đề độc lập (.srt, .ass) chuẩn hóa tên theo quy chuẩn Plex & TVDB (ví dụ Monster - S01E01.en.ass), hỗ trợ xử lý hàng loạt theo thư mục cả mùa/bộ phim.
---

# Subtitle Extractor Skill

Kỹ năng chuyên trách quét và bóc tách các luồng phụ đề (subtitle streams) bị mux nhúng sâu bên trong các file video container (`.mkv`, `.mp4`, `.m4v`) phục vụ quy trình biên tập, hiệu chỉnh và nạp vào kỹ năng dịch `translate-subtitle`.

---

## 🚀 Cú Pháp Kích Hoạt CLI

```bash
# 1. Quét danh sách các track phụ đề trong file video:
python3 <skill_dir>/scripts/extract_subtitles.py probe "<đường_dẫn_video>"

# 2. Bóc tách toàn bộ phụ đề trong 1 file video:
python3 <skill_dir>/scripts/extract_subtitles.py extract "<đường_dẫn_video>" [--lang <en,vi,ja,all>] [--format <ass|srt>]

# 3. Bóc tách hàng loạt cho toàn bộ thư mục phim / TV Series:
python3 <skill_dir>/scripts/extract_subtitles.py batch "<thư_mục_chứa_phim>" [--lang en] [--out-dir "<thư_mục_xuất>"]
```

---

## 🛠️ Các Tính Năng Cốt Lõi

1. 🔍 **Deep Stream Probing (`ffprobe` + JSON parse):**
   * Tự động nhận diện định dạng track: `subrip` (SRT), `ass`, `ssa`, `mov_text`, `hdmv_pgs_subtitle` (PGS/VobSub).
   * Đọc metadata ngôn ngữ ISO-639 (`eng`, `vie`, `jpn`, `chi`, `zho`, `und`) và title của track (ví dụ: `English [Full]`, `Vietnamese [Signs/Songs]`, `Forced`).

2. ✂️ **Lossless Stream Extraction (`ffmpeg -c:s copy`):**
   * Trích xuất nguyên bản 100% typography, styling, font vector và timecode của file gốc mà không bị re-encode gây sai lệch.
   * Tự động chuyển đổi phụ đề sang định dạng UTF-8 sạch.

3. 🏷️ **Chuẩn Hóa Đặt Tên Plex & Jellyfin Naming Convention:**
   * File phụ đề trích xuất được tự động đặt tên theo cấu trúc:
     `<Tên_Video_Gốc>.<mã_ngôn_ngữ>.<định_dạng>`
     * *Ví dụ:* `Monster (2004) - S01E01 - [1080p BluRay].en.ass`
     * *Ví dụ:* `Monster (2004) - S01E01 - [1080p BluRay].vi.srt`
   * Giúp Plex, Jellyfin, Infuse và Media Hub Web UI tự động nhận diện phụ đề ngay lập tức.

4. 🔄 **Cầu Nối Trực Tiếp Sang `translate-subtitle`:**
   * Sau khi bóc tách phụ đề tiếng Anh (`.en.ass`/`.en.srt`), file xuất ra sẵn sàng để đưa trực tiếp vào `translate-subtitle` để dịch sang tiếng Việt mà không cần thao tác thủ công.
