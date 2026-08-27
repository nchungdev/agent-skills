---
name: media-collector
description: Universal Film, TV Show & Anime Curator. Automatically analyzes complete franchise filmographies, cross-references TheTVDB & TMDb IDs, creates standardized Plex & Jellyfin library hierarchies, scrapes multi-language subtitles (.ass / .srt), performs subtitle engineering (1080p styling, timecode syncing), and generates verified download blueprints.
---

# Universal Media Collector Skill (Movies, TV Shows & Anime)

This skill guides agents in discovering, structuring, and curating complete media collections for **ANY** entertainment franchise—including Hollywood Cinema, Western TV Series, Anime, Tokusatsu, Asian Dramas, and Documentaries.

---

## 🎯 Universal 5-Step Media Curation Pipeline

1. **Franchise Census & ID Resolution**:
   - Map all Movies, TV Seasons (1..N), Canonical OVAs/Specials, and Bonus Extras (Behind The Scenes, Interviews, Trailers).
   - Resolve `{tvdb-XXXXX}` (TheTVDB) for TV Shows/Anime and `{tmdb-XXXXX}` (The Movie Database) for Movies & Limited Series.

2. **Standardized Plex & Jellyfin Layout**:
   - Build `TV_Shows/` and `Movies/` folder structures matching Plex/Jellyfin naming rules.
   - Separate canonical specials into `Season 00/` and extras into `Behind The Scenes/`, `Trailers/`, `Featurettes/`.

3. **Multi-Source Subtitle Hunting Protocol**:
   - **Hollywood & Global Cinema/Series**: SubDL, OpenSubtitles, Subsource, Phudeviet.
   - **Anime & Asian Cinema**: ACG.RIP, ASSRT, Anime Tosho attachments (.ass.xz), Kitsunekko, SubHD.

4. **Subtitle Engineering & Formatting**:
   - Standardize format to clean UTF-8 .srt or 1080p styled .ass.
   - Assign standardized ISO language codes (`.vie.srt`, `.eng.srt`, `.chi.ass`, `.jpn.ass`).
   - Align / split timecodes when mapping compilation movies to episode series.

5. **Verified Download Blueprint (`DOWNLOAD_LINKS.txt`)**:
   - Compile verified 1080p/4K BDRip and WEB-DL download links (Torrents, DDL, Archive.org, Official Streams) directly in each show/movie folder.

---

## 🛠️ Included Tools & Scripts

- `scripts/srt_to_ass.py`: Converts SRT files to styled 1080p ASS subtitles.
