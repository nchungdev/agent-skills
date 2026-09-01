---
name: media-collector
description: Universal Film, TV Show & Anime Curator. Supports instant 1-turn execution via inline parameters (e.g. --sub vi,en,zh --links-only) or interactive clarification, maps franchise censuses with direct TVDB/TMDb/IMDb links, creates standardized Plex & Jellyfin library hierarchies, handles subtitle acquisition/engineering (1080p styling, timecode syncing), explicitly labels Muxed vs External Subtitles, executes intelligent fallback protocols for non-direct video links (Torrent file downloading, Magnet links, yt-dlp streaming extraction), and generates comprehensive download blueprints.
---

# Universal Media Collector Skill (Instant & Interactive Curation)

This skill guides agents in discovering, structuring, and curating complete media collections for **ANY** entertainment franchise—including Hollywood Cinema, Western TV Series, Anime, Tokusatsu, Asian Dramas, and Documentaries.

---

## ⚡ Step 0: Parameter Parsing & Execution Mode

The agent **MUST** first inspect the user's prompt for inline options, flags, or natural language preferences to execute in **1 SINGLE TURN** without unnecessary back-and-forth questions.

### 1. Supported Command Patterns & Inline Options:
- **Flag syntax**:
  - `media-collector <franchise_name> --sub <vi,en,zh,ja,all,none> --video <links|download>`
  - Short flags: `-s <langs>`, `--links-only` (Option A), `--download-video` (Option B)
  - `--estimate` — Dry-run: show disk estimation only, don't download
  - `--translate` — After curation, ask user to trigger Vietnamese subtitle translation
  - `--no-nfo` — Skip metadata generation (NFO + artwork are produced by default)
  - `--sync <gdrive|nas|both>` — Auto-sync completed output to cloud/NAS after download
  - `--aria2c` — Use aria2c for accelerated multi-connection downloads
- **Natural language syntax**:
  - *"media-collector Cậu bé 3 mắt sub vi,en chỉ lấy link"*
  - *"media-collector Transformers RiD tải sub tiếng anh, video chỉ lấy link"*
  - *"media-collector Lord of the Rings full 4K kèm sub việt tạo nfo"*

### 2. Execution Logic:
- **Scenario A (Parameters Provided)**:
  - If the user specifies their preferences in the command, **DO NOT ASK ANY QUESTIONS**. Execute the complete pipeline immediately in **1 TURN**!
- **Scenario B (Parameters Omitted - Bare Title)**:
  - If the user only enters a bare title (e.g. `media-collector Naruto`), politely ask the 2 clarification questions or apply the sensible default (Download multi-language subs + Option A Links-only).

---

## 💾 Disk Space Estimation (MANDATORY — BEFORE ANY DOWNLOAD)

> [!IMPORTANT]
> The agent **MUST** estimate total download size and check available disk space **BEFORE** downloading any video or subtitle files. Never start a download blindly.

### 1. Estimation Reference Table (Per Episode / Per Movie):

| Resolution & Codec | ~Per Episode (24 min) | ~Per Episode (45 min) | ~Per Movie (90-120 min) |
| :--- | :---: | :---: | :---: |
| 480p DVD-Rip (H.264) | ~200 MB | ~400 MB | ~700 MB – 1.5 GB |
| 720p BDRip (H.264) | ~300 MB | ~600 MB | ~1.5 – 3 GB |
| 1080p BDRip (H.264) | ~500 MB – 1 GB | ~1 – 2 GB | ~3 – 8 GB |
| 1080p BDRip (HEVC/x265) | ~300 – 600 MB | ~600 MB – 1.2 GB | ~2 – 5 GB |
| 1080p BD Remux (Lossless) | ~2 – 4 GB | ~4 – 8 GB | ~15 – 35 GB |
| 2160p 4K UHD (HEVC/HDR) | ~3 – 6 GB | ~5 – 10 GB | ~20 – 60 GB |

### 2. Estimation Procedure:

```
1. Xác định số lượng tập / movie cần tải
2. Nhân với kích thước ước lượng theo bảng (dựa vào resolution & codec từ nguồn)
3. Chạy `df -h <target_disk>` để lấy dung lượng trống
4. Tính phần trăm ổ cứng sau tải
5. Hiển thị Bảng Ước Lượng cho user TRƯỚC KHI bắt đầu
```

### 3. Cảnh Báo Tự Động Theo Ngưỡng:

| % Ổ Cứng Sau Tải | Hành Động |
| :---: | :--- |
| ≤ 75% | 🟢 **AN TOÀN** — Tải bình thường |
| 76% – 85% | 🟡 **CẨN THẬN** — Hỏi xác nhận |
| 86% – 92% | 🟠 **NGUY HIỂM** — Khuyên dọn dẹp phim cũ đã đủ 3 tiêu chí |
| > 92% | 🔴 **CHẶN** — Yêu cầu giải phóng dung lượng trước |

---

## 🔗 Translate-Subtitle Handoff (ASK FIRST — NEVER AUTO-EXECUTE)

> [!IMPORTANT]
> After completing curation, if translatable subtitle sources exist, the agent **MUST ASK** the user. **NEVER auto-execute translation.**

### Handoff Flow:
1. Detect translatable subs (`.en.srt`, `.ja.ass`, `.zh.ass` → Vietnamese).
2. Present prompt with franchise ID, genre, glossary availability, and recommended style.
3. Only proceed if user explicitly accepts.

---

## 📺 NFO Metadata & Artwork Generation (MANDATORY)

> [!IMPORTANT]
> Every curated title **MUST** ship complete: `tvshow.nfo` (or `movie.nfo`),
> `poster.jpg` and `fanart.jpg` written into the show folder alongside the media.
> This is not an opt-in flag — a folder without them is an incomplete delivery, and
> media-hub will list it under "thiếu metadata" until someone runs the manual
> **Dựng Metadata** build to backfill it. Only skip when the user passes `--no-nfo`.

### 1. TV Series NFO Structure:
```
<Show_Folder>/
├── tvshow.nfo          # Series-level metadata
├── poster.jpg          # Series poster (download from TMDb/TVDB)
├── fanart.jpg          # Series fanart/backdrop
├── Season 01/
│   ├── S01E01.nfo      # Per-episode metadata
│   ├── S01E01-thumb.jpg
│   └── ...
```

### 2. Movie NFO Structure:
```
<Movie_Folder>/
├── movie.nfo           # Movie metadata
├── poster.jpg
├── fanart.jpg
└── <movie_file>.mkv
```

### 3. NFO Content Template (XML):
```xml
<!-- tvshow.nfo -->
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<tvshow>
  <title>The Files of Young Kindaichi</title>
  <originaltitle>金田一少年の事件簿</originaltitle>
  <year>1997</year>
  <plot>Kindaichi Hajime, grandson of the famous detective...</plot>
  <genre>Mystery</genre>
  <genre>Animation</genre>
  <studio>Toei Animation</studio>
  <uniqueid type="tvdb">79354</uniqueid>
  <uniqueid type="tmdb">1481</uniqueid>
  <uniqueid type="imdb">tt0159171</uniqueid>
</tvshow>
```

### 4. Artwork Sources (Priority Order):
1. **TMDb API** (`api.themoviedb.org/3/`) — Best quality, most complete
2. **TheTVDB** (`thetvdb.com`) — Good alternative for anime
3. **Fanart.tv** (`fanart.tv`) — HD logos, clearart, disc art

### 5. Agent Behavior:
- **ALWAYS** attempt to download `poster.jpg` and `fanart.jpg` from TMDb first.
- Generate `.nfo` files with all available IDs (TVDB, TMDb, IMDb).
- For episodes: include episode title, air date, plot summary, and thumbnail.
- If TMDb API key is not available: generate NFO with IDs only (Plex/Jellyfin will scrape the rest automatically).

---

## ☁️ Post-Curation Cloud Sync (`--sync`)

Automatically sync completed Plex/Jellyfin structures to Google Drive and/or NAS after download.

### 1. Supported Targets:
| Flag | Action |
| :--- | :--- |
| `--sync gdrive` | Upload to Google Drive via `rclone copy` |
| `--sync nas` | Sync to NAS via `rsync` over SSH |
| `--sync both` | Upload to both Google Drive AND NAS |

### 2. Destination Path Convention:
```
Google Drive:  gdrive:Phim/TV Shows/<Show Name> (<Year>) {tvdb-ID} [tvdbid-ID]/
               gdrive:Phim/Movies/<Movie Name> (<Year>) {tmdb-ID} [tmdbid-ID]/
NAS:           /srv/mergerfs/MainPool/Phim/TV Shows/<same>/
               /srv/mergerfs/MainPool/Phim/Movies/<same>/
```

### 3. Helper Script:
```sh
python3 <skill_dir>/scripts/cloud_sync.py ./local_output/ \
  --gdrive "gdrive:Phim/TV Shows/..." \
  --nas "/srv/mergerfs/MainPool/Phim/TV Shows/..." \
  --dry-run   # Preview first, then remove --dry-run to execute
```

### 4. Agent Behavior:
- **ALWAYS** run with `--dry-run` first and show the user what will be transferred.
- Only execute actual transfer after user confirms.
- Monitor transfer progress and report completion percentage.
- After successful sync to both targets, check if local files qualify for cleanup (3-criteria rule).

---

## 🔍 Duplicate Detection Before Download

> [!IMPORTANT]
> Before downloading video files, the agent **MUST** check whether the files already exist on NAS or Google Drive to avoid wasting bandwidth and disk space.

### 1. Check Procedure:
```
1. Scan target NAS path via SSH: ssh chungnh@192.168.1.37 "ls -la '<nas_path>/Season XX/'"
2. Scan target Google Drive via rclone: rclone lsjson -R "gdrive:Phim/TV Shows/<show>/"
3. Compare filename patterns and sizes against planned downloads
4. Report duplicates and skip them
```

### 2. Helper Script:
```sh
python3 <skill_dir>/scripts/deduplicate.py ./local_dir/ \
  --gdrive "gdrive:Phim/TV Shows/..." \
  --nas "/srv/mergerfs/MainPool/Phim/TV Shows/..."
```

### 3. Agent Output Format:
```
🔍 Kiểm Tra Trùng Lặp Trước Khi Tải:
  ✅ Đã có trên NAS: 45/48 tập (bỏ qua, không tải lại)
  ✅ Đã có trên Drive: 48/48 tập
  📥 Cần tải mới: 3 tập (S01E46, S01E47, S01E48)
  💾 Dung lượng tải thực tế: ~1.8 GB (thay vì 28 GB nếu tải cả bộ)
```

---

## 🔄 Resume & Checkpoint (Download Continuity)

### 1. Checkpoint File (`DOWNLOAD_STATE.json`):
The agent **MUST** create and maintain a checkpoint file in the project directory to track download progress:

```json
{
  "franchise": "The Files of Young Kindaichi",
  "tvdb_id": "79354",
  "tmdb_id": "1481",
  "started_at": "2026-08-29T12:00:00+07:00",
  "updated_at": "2026-08-29T14:30:00+07:00",
  "total_episodes": 148,
  "status": "in_progress",
  "episodes": {
    "S01E01": {"status": "done", "file": "S01E01.mkv", "size_mb": 450},
    "S01E02": {"status": "done", "file": "S01E02.mkv", "size_mb": 462},
    "S01E03": {"status": "failed", "error": "HTTP 503", "retries": 2},
    "S01E04": {"status": "pending"}
  },
  "subtitles": {
    "S01E01.en.srt": "done",
    "S01E01.ja.ass": "done"
  }
}
```

### 2. Resume Behavior:
- **On start**: Check for existing `DOWNLOAD_STATE.json` in the target directory.
- **If found**: Read state and skip all `"done"` items, retry `"failed"` items, continue `"pending"` items.
- **If not found**: Create new checkpoint and start from scratch.
- **On each completion**: Update the checkpoint file immediately.
- **On interruption**: The next run picks up exactly where it left off.

### 3. Agent MUST:
- Always use `aria2c --continue=true` or `wget -c` for resumable HTTP downloads.
- Update `DOWNLOAD_STATE.json` after each file completes or fails.
- Report resume status to the user: *"Tiếp tục tải từ S01E35 (34/148 đã hoàn tất từ phiên trước)."*

---

## ⚡ aria2c Integration (Accelerated Downloads)

### 1. When to Use aria2c:
- Direct HTTP/HTTPS downloads (DDL mirrors, Archive.org, cloud links)
- Torrent/Magnet downloads (built-in BitTorrent client)
- Metalink downloads

### 2. Standard aria2c Command Templates:

**HTTP Direct Download (multi-connection):**
```sh
aria2c -x 16 -s 16 -k 1M --continue=true \
  --file-allocation=falloc \
  --dir="<target_directory>" \
  --out="<output_filename>" \
  "<download_url>"
```

**Torrent/Magnet Download:**
```sh
aria2c --seed-time=0 \
  --dir="<target_directory>" \
  --bt-stop-timeout=300 \
  "<torrent_file_or_magnet_link>"
```

**Batch Download from URL List:**
```sh
aria2c -x 16 -s 16 -k 1M --continue=true \
  --file-allocation=falloc \
  --dir="<target_directory>" \
  --input-file="<url_list.txt>"
```

### 3. Batch URL List Format (`download_urls.txt`):
```
https://example.com/S01E01.mkv
  out=Season 01/Show Name - S01E01.mkv
https://example.com/S01E02.mkv
  out=Season 01/Show Name - S01E02.mkv
```

### 4. Agent Behavior:
- **ALWAYS** use `--continue=true` for resumable downloads.
- **ALWAYS** use `--seed-time=0` for torrents (don't seed after completion).
- Generate a `download_urls.txt` batch file when downloading multiple episodes.
- Report download speed and ETA during transfer.
- Check for `aria2c` availability: `which aria2c`. If not installed, fall back to `curl -C -` or `wget -c`.

---

## 🏷️ Subtitle Distribution Badging (MANDATORY)

The agent **MUST** clearly label the delivery format of subtitles for every release:

- `[📦 MUXED SOFTSUB]`: Subtitles embedded in `.mkv` container.
- `[📄 STANDALONE SUB]`: Separate external `.ass` / `.srt` files.
- `[🔥 HARDSUB]`: Burned into video stream permanently.

---

## ⚡ Non-Direct Download Fallback Protocol

If the source is NOT a direct HTTP link:

1. **P2P Torrent / Magnet**: Download `.torrent` file + provide Magnet link + search DDL mirrors (Anime Tosho, Archive.org).
2. **Official Streaming** (YouTube, Muse Asia): Use `yt-dlp` for non-DRM content.
3. **Cloud Lockers** (GDrive, Mega): Label as `[⚡ CLOUD LOCKER]` with direct links.
4. **DRM Platforms** (Netflix, Disney+): Inform user, provide official link, search WEBRip releases.

---

## 🎯 Universal 8-Step Media Curation Pipeline

### Step 1: Franchise Census & Multi-Database Metadata Resolution
Map all release types (Movies, TV Seasons, OVAs, Extras) and resolve TheTVDB, TMDb, IMDb IDs with direct URLs.

### Step 2: Disk Space Estimation & Safety Check
Estimate total download size, check available disk space, display estimation table, apply threshold rules (🟢🟡🟠🔴).

### Step 3: Duplicate Detection
Check NAS and Google Drive for existing files. Skip duplicates, report only files that need downloading.

### Step 4: Standardized Plex & Jellyfin Layout
Build zero-guesswork folder hierarchy with `Season 00/` for specials and `Behind The Scenes/`, `Trailers/`, `Featurettes/` for extras.

### Step 5: Multi-Source Subtitle Hunting
- **Hollywood / International**: SubDL, OpenSubtitles, Subsource, Phudeviet.
- **Anime / Asian Cinema**: ACG.RIP, ASSRT, Anime Tosho (.ass.xz), Kitsunekko, SubHD.

### Step 6: Subtitle Engineering & Formatting
Standardize to UTF-8 `.srt` or 1080p styled `.ass` using `scripts/srt_to_ass.py` (supports 7 style presets, batch mode, font fallback). Assign ISO language codes.

### Step 7: NFO Metadata & Artwork (REQUIRED)
Generate `.nfo` files and download `poster.jpg` / `fanart.jpg` from TMDb/TVDB/Fanart.tv
into the show folder. Do this for every title, not on request — the library is the
source of truth for artwork, and the dashboard reads it from there rather than
re-fetching from TMDb on each page load.

If TMDb cannot be matched confidently (external id does not round-trip and the title
does not match), record the folder as needing review instead of writing metadata that
belongs to a different show.

### Step 8: Blueprint Output, Cloud Sync & Translation Handoff
1. Generate `DOWNLOAD_LINKS.txt` with quality badges, codecs, resolution, and subtitle delivery format.
2. Create/update `DOWNLOAD_STATE.json` checkpoint for resume capability.
3. Offer `--sync` to upload to Google Drive / NAS.
4. **ASK** user if they want to hand off to `translate-subtitle` for Vietnamese translation.

---

## 🛠️ Bundled Scripts Reference

| Script | Purpose | Usage |
| :--- | :--- | :--- |
| `scripts/srt_to_ass.py` | SRT→ASS converter with 7 style presets, batch mode, font fallback | `python3 srt_to_ass.py input.srt --style detective-mystery` |
| `scripts/deduplicate.py` | Check local vs NAS/GDrive for duplicates before downloading | `python3 deduplicate.py ./local/ --gdrive "gdrive:..." --nas "/srv/..."` |
| `scripts/cloud_sync.py` | Post-curation sync to Google Drive (rclone) and NAS (rsync) | `python3 cloud_sync.py ./output/ --gdrive "gdrive:..." --sync both` |
