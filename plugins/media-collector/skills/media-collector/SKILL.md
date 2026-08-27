---
name: media-collector
description: Universal Film, TV Show & Anime Curator. Interactively clarifies user download preferences (film/subtitles & target languages), maps franchise censuses with direct TVDB/TMDb/IMDb links, creates standardized Plex & Jellyfin library hierarchies, handles subtitle acquisition/engineering (1080p styling, timecode syncing), and generates comprehensive download blueprints containing video quality ratings, codecs, resolutions, and subtitle accuracy evaluations for each source.
---

# Universal Media Collector Skill (Interactive & Quality-Rated Curation)

This skill guides agents in discovering, structuring, and curating complete media collections for **ANY** entertainment franchise—including Hollywood Cinema, Western TV Series, Anime, Tokusatsu, Asian Dramas, and Documentaries.

---

## 🚦 Step 0: User Preference Clarification (REQUIRED FIRST STEP)

Before generating final assets, the agent **MUST** proactively ask the user two essential questions:

1. **Subtitle Preferences**:
   - *"Bạn có muốn tải phụ đề sẵn về máy không? Ngôn ngữ bạn muốn ưu tiên tìm là gì? (Ví dụ: Tiếng Việt, Tiếng Trung, Tiếng Anh, Tiếng Nhật...)"*
2. **Video Download Preferences**:
   - *"Bạn có muốn tải các file video phim về máy không, hay chỉ cần tạo cấu trúc thư mục Plex/Jellyfin và file tổng hợp link tải (DOWNLOAD_LINKS.txt)?"*

> [!IMPORTANT]
> **CRITICAL EXECUTION MANDATE FOR SUBTITLES**:
> - If the user responds **YES** to downloading subtitles: The agent **MUST ACTIVELY DOWNLOAD** and extract the subtitle files into the corresponding `Season XX/` folders (e.g. `.eng.ass`, `.vie.srt`, `.chi.ass`). The agent **MUST NOT** only provide links when the user explicitly asked to download subtitles!

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

Every show/movie directory **MUST** contain a comprehensive `DOWNLOAD_LINKS.txt` enriched with **Quality Badges, Codecs, Resolution, and Source Ratings**.
