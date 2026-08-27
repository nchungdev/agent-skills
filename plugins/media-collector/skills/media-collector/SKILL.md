---
name: media-collector
description: Universal Film, TV Show & Anime Curator. Interactively clarifies user download preferences (film/subtitles & target languages), maps franchise censuses with direct TVDB/TMDb/IMDb links, creates standardized Plex & Jellyfin library hierarchies, handles subtitle acquisition/engineering (1080p styling, timecode syncing), and generates comprehensive download blueprints containing both video and subtitle links.
---

# Universal Media Collector Skill (Interactive Curation)

This skill guides agents in discovering, structuring, and curating complete media collections for **ANY** entertainment franchise—including Hollywood Cinema, Western TV Series, Anime, Tokusatsu, Asian Dramas, and Documentaries.

---

## 🚦 Step 0: User Preference Clarification (REQUIRED FIRST STEP)

Before downloading any files or generating final assets, the agent **MUST** proactively ask the user two essential questions:

1. **Subtitle Preferences**:
   - *"Bạn có muốn tải phụ đề sẵn về máy không? Ngôn ngữ bạn muốn ưu tiên tìm là gì? (Ví dụ: Tiếng Việt, Tiếng Trung, Tiếng Anh, Tiếng Nhật...)"*
2. **Video Download Preferences**:
   - *"Bạn có muốn tải các file video phim về máy không, hay chỉ cần tạo file tổng hợp link tải (DOWNLOAD_LINKS.txt)?"*

> [!IMPORTANT]
> Based on the user's response, tailor the execution:
> - If user only wants links: Do NOT download heavy video/sub files, but still generate the full directory tree, `.folder_info.txt`, and comprehensive `DOWNLOAD_LINKS.txt`.
> - If user wants subtitles downloaded: Hunt, download, extract, and convert them to 1080p `.ass`/`.srt` in the requested language(s).

---

## 🎯 Universal 5-Step Media Curation Pipeline

### Step 1: Franchise Census & Multi-Database Metadata Resolution
1. **Map Release Types**:
   - Theatrical Movies, TV Series (Seasons 1..N), Canonical OVAs/Specials, and Bonus Extras (Behind The Scenes, Interviews, Trailers).
2. **Resolve All Direct Database URLs**:
   - **TheTVDB**: Series/Movie URL + ID `{tvdb-XXXXX}`
   - **TMDb (The Movie Database)**: URL + ID `{tmdb-XXXXX}`
   - **IMDb**: Title URL + ID `ttXXXXXXX`

---

### Step 2: Standardized Plex & Jellyfin Layout
Build a zero-guesswork folder hierarchy:

```text
📁 Media_Library/
│
├── 📁 Movies/
│   └── 📁 Movie Title (Release Year) {tmdb-XXXXX}/
│       ├── 📄 DOWNLOAD_LINKS.txt
│       ├── Movie Title (Release Year).mkv
│       ├── Movie Title (Release Year).vie.srt
│       └── Movie Title (Release Year).eng.srt
│
└── 📁 TV_Shows/
    └── 📁 Show Name (First Air Year) {tvdb-XXXXX}/
        ├── 📄 DOWNLOAD_LINKS.txt
        ├── 📁 Season 01/             --> Show Name - S01E01.mkv / .srt
        ├── 📁 Season 02/             --> Show Name - S02E01.mkv / .srt
        ├── 📁 Season 00/             --> Show Name - S00E01 - [Special Title].mkv
        ├── 📁 Behind The Scenes/     --> Interviews, Making-of, Cast specials
        ├── 📁 Featurettes/           --> VFX breakdowns
        └── 📁 Trailers/              --> Official Trailers, Teasers
```

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

### Step 5: Comprehensive Verified Blueprint (`DOWNLOAD_LINKS.txt`)

Regardless of whether the user chooses to download files immediately or not, every show/movie directory **MUST** contain a comprehensive `DOWNLOAD_LINKS.txt` formatted as follows:

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
1. LINK TẢI VIDEO PHIM (TORRENT, DDL, STREAMING CHÍNH THỨC):
   • Nyaa / Torrent (1080p/4K BDRip): https://...
   • Anime Tosho (Tải trực tiếp & Torrent Mirror): https://...
   • Internet Archive (Tải trực tiếp DDL / Stream): https://...
   • Kênh chính thức / Streaming (YouTube, Netflix, Max): https://...

--------------------------------------------------------------------------------
2. LINK TẢI PHỤ ĐỀ (SUBTITLES - VIETNAMESE, ENGLISH, CHINESE...):
   • SubDL: https://subdl.com/s/subtitle/...
   • OpenSubtitles: https://www.opensubtitles.org/...
   • ACG.RIP / ASSRT: https://...
   • Kitsunekko: https://...
================================================================================
```

---

## 🛠️ Included Tools & Scripts

- `scripts/srt_to_ass.py`: Converts SRT files to styled 1080p ASS subtitles.
