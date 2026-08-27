---
name: media-collector
description: Universal Film, TV Show & Anime Curator. Interactively clarifies user download preferences (film/subtitles & target languages), maps franchise censuses with direct TVDB/TMDb/IMDb links, creates standardized Plex & Jellyfin library hierarchies, handles subtitle acquisition/engineering (1080p styling, timecode syncing), explicitly labels Muxed vs External Subtitles, executes intelligent fallback protocols for non-direct video links (Torrent file downloading, Magnet links, yt-dlp streaming extraction), and generates comprehensive download blueprints.
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

---

## ⚡ Non-Direct Download Fallback Protocol (WHEN USER CHOOSES VIDEO DOWNLOAD)

If the user chooses **Option B (Download Video)**, but the source is NOT a direct HTTP link (e.g. Torrent, Streaming, Cyberlocker):

1. **P2P Torrent / Magnet Sources (Nyaa, 1337x, TorrentGalaxy)**:
   - **Action**: The agent **MUST download the `.torrent` file directly** and save it into the target show/season folder (e.g. `Season 01/Season_01_1080p.torrent`).
   - **Action**: Provide the clickable **Magnet Link** in `DOWNLOAD_LINKS.txt` so the user can open it with their BitTorrent client (qBittorrent/Transmission) in 1 click.
   - **Action**: Search for mirror DDLs (Anime Tosho direct mirror, Archive.org DDL).

2. **Official Streaming Platforms (YouTube, Muse Asia, Ani-One, Vimeo)**:
   - **Action**: Use `yt-dlp` / `ffmpeg` to rip and download the 1080p stream into standard `.mp4`/`.mkv` format if available without DRM.
   - If DRM-protected: Provide the direct streaming link and official app recommendations.

3. **Cloud Lockers (Google Drive, Mega, Mediafire, 1Fichier)**:
   - **Action**: Label clearly as `[⚡ CLOUD LOCKER]` with direct browser access links in `DOWNLOAD_LINKS.txt`.

4. **DRM / Paid Exclusive Platforms (Netflix, Disney+, Max, Apple TV+)**:
   - **Action**: Inform the user transparently that the title is an exclusive streaming license, provide the official title link, and search for community WEBRip releases.

---

## 🏷️ Subtitle Distribution Badging (MANDATORY TO AVOID CONFUSION)

The agent **MUST** clearly label the delivery format of subtitles for every release:

- `[📦 MUXED SOFTSUB]`: Subtitles are embedded directly inside the `.mkv` container. Explain to the user: *"File video đã tích hợp sẵn phụ đề bên trong, không cần file sub rời bên ngoài."*
- `[📄 STANDALONE SUB]`: Subtitles are separate external `.ass` or `.srt` files downloaded into the `Season XX/` directory.
- `[🔥 HARDSUB]`: Subtitles are permanently burned into the video stream.

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

Every show/movie directory **MUST** contain a comprehensive `DOWNLOAD_LINKS.txt` enriched with **Quality Badges, Codecs, Resolution, Subtitle Delivery Format ([📦 MUXED] vs [📄 FILE RỜI]), and Source Ratings**.
