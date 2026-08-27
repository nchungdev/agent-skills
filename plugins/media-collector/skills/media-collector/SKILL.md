---
name: media-collector
description: Universal Film, TV Show & Anime Curator. Interactively clarifies user download preferences (film/subtitles & target languages), maps franchise censuses with direct TVDB/TMDb/IMDb links, creates standardized Plex & Jellyfin library hierarchies, handles subtitle acquisition/engineering (1080p styling, timecode syncing), and generates comprehensive download blueprints containing video quality ratings, codecs, resolutions, and subtitle accuracy evaluations for each source.
---

# Universal Media Collector Skill (Interactive & Quality-Rated Curation)

This skill guides agents in discovering, structuring, and curating complete media collections for **ANY** entertainment franchise—including Hollywood Cinema, Western TV Series, Anime, Tokusatsu, Asian Dramas, and Documentaries.

---

## 🚦 Step 0: User Preference Clarification (REQUIRED FIRST STEP)

Before downloading any files or generating final assets, the agent **MUST** proactively ask the user two essential questions:

1. **Subtitle Preferences**:
   - *"Bạn có muốn tải phụ đề sẵn về máy không? Ngôn ngữ bạn muốn ưu tiên tìm là gì? (Ví dụ: Tiếng Việt, Tiếng Trung, Tiếng Anh, Tiếng Nhật...)"*
2. **Video Download Preferences**:
   - *"Bạn có muốn tải các file video phim về máy không, hay chỉ cần tạo cấu trúc thư mục Plex/Jellyfin và file tổng hợp link tải (DOWNLOAD_LINKS.txt)?"*

---

## 🎯 Universal 5-Step Media Curation Pipeline

### Step 1: Franchise Census & Multi-Database Metadata Resolution
1. **Map Release Types**: Movies, TV Seasons, Canonical OVAs, Bonus Extras.
2. **Resolve All Direct Database URLs**:
   - **TheTVDB**: Series/Movie URL + ID `{tvdb-XXXXX}`
   - **TMDb (The Movie Database)**: URL + ID `{tmdb-XXXXX}`
   - **IMDb**: Title URL + ID `ttXXXXXXX`

---

### Step 2: Standardized Plex & Jellyfin Layout
Build a zero-guesswork folder hierarchy:
- `TV_Shows/` & `Movies/`
- Separate canonical specials into `Season 00/` and extras into `Behind The Scenes/`, `Trailers/`, `Featurettes/`.

---

### Step 3: Multi-Source Subtitle Hunting Protocol
- **Hollywood / International**: SubDL, OpenSubtitles, Subsource, Phudeviet.
- **Anime / Asian Cinema**: ACG.RIP, ASSRT, Anime Tosho attachments (.ass.xz), Kitsunekko, SubHD.

---

### Step 4: Subtitle Engineering & Formatting
1. Standardize format to clean UTF-8 `.srt` or 1080p styled `.ass` (`scripts/srt_to_ass.py`).
2. Assign standardized ISO language codes (`.vie.srt`, `.eng.srt`, `.chi.ass`, `.jpn.ass`).
3. Align / split timecodes when mapping compilation movies to episode series.

---

### Step 5: Comprehensive Verified Blueprint with Quality Ratings (`DOWNLOAD_LINKS.txt`)

Every show/movie directory **MUST** contain a comprehensive `DOWNLOAD_LINKS.txt` enriched with **Quality Badges, Codecs, Resolution, and Source Ratings**:

```text
================================================================================
{SHOW / MOVIE NAME} ({YEAR}) - TỔNG HỢP LINK TẢI PHIM & PHỤ ĐỀ
================================================================================
Tên gốc / Quốc tế: {Original Title}
TheTVDB: https://thetvdb.com/series/... {tvdb-XXXXX}
TMDb: https://www.themoviedb.org/... {tmdb-XXXXX}
IMDb: https://www.imdb.com/title/... (ttXXXXXXX)
Số tập: {Season / Episode Count}

--------------------------------------------------------------------------------
1. LINK TẢI VIDEO PHIM (KÈM ĐÁNH GIÁ CHẤT LƯỢNG & CODEC):
   • [⭐ ⭐ ⭐ ⭐ ⭐] [1080p BDRip / HEVC 10-bit / FLAC Audio] - Bản đẹp nhất:
     Nhóm phát hành: [Nhóm Sub / Encoder]
     Đặc điểm: Master sắc nét, màu sắc chuẩn, âm thanh gốc không nén.
     Link tải (Nyaa / Torrent): https://...

   • [⭐ ⭐ ⭐ ⭐] [1080p WEB-DL / x264 / AAC Dual Audio] - Bản tiện lợi:
     Nhóm phát hành: [Nhóm]
     Link tải (Anime Tosho / DDL): https://...

   • [⭐ ⭐ ⭐] [480p DVDRip / DDL Trọn bộ]:
     Link tải (Internet Archive): https://...

--------------------------------------------------------------------------------
2. LINK TẢI PHỤ ĐỀ (KÈM ĐÁNH GIÁ ĐỘ CHUẨN XÁC & ĐỊNH DẠNG):
   • [⭐ ⭐ ⭐ ⭐ ⭐] [Định dạng .ASS 1080p có Styles & Hiệu ứng] - Dịch trực tiếp từ tiếng gốc:
     Nhóm dịch: [Nhóm Fansub]
     Độ khớp: 100% timecode với bản BDRip [Tên nhóm encode].
     Link tải: https://...

   • [⭐ ⭐ ⭐ ⭐] [Định dạng .SRT UTF-8 Chuẩn] - Phụ đề quốc tế:
     Nguồn: SubDL / OpenSubtitles
     Link tải: https://...
================================================================================
```

---

## 🛠️ Included Tools & Scripts

- `scripts/srt_to_ass.py`: Converts SRT files to styled 1080p ASS subtitles.
