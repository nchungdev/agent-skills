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
  - New: `--estimate` (dry-run: show disk estimation only, don't download)
  - New: `--translate` (after curation, ask user to trigger Vietnamese subtitle translation)
- **Natural language syntax**:
  - *"media-collector Cậu bé 3 mắt sub vi,en chỉ lấy link"*
  - *"media-collector Transformers RiD tải sub tiếng anh, video chỉ lấy link"*
  - *"media-collector Lord of the Rings full 4K kèm sub việt"*

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

| Resolution & Codec | Typical Size Per Episode (24 min) | Typical Size Per Episode (45 min) | Typical Size Per Movie (90-120 min) |
| :--- | :---: | :---: | :---: |
| 480p DVD-Rip (H.264) | ~200 MB | ~400 MB | ~700 MB – 1.5 GB |
| 720p BDRip (H.264) | ~300 MB | ~600 MB | ~1.5 – 3 GB |
| 1080p BDRip (H.264) | ~500 MB – 1 GB | ~1 – 2 GB | ~3 – 8 GB |
| 1080p BDRip (HEVC/x265) | ~300 – 600 MB | ~600 MB – 1.2 GB | ~2 – 5 GB |
| 1080p BD Remux (Lossless) | ~2 – 4 GB | ~4 – 8 GB | ~15 – 35 GB |
| 2160p 4K UHD (HEVC/HDR) | ~3 – 6 GB | ~5 – 10 GB | ~20 – 60 GB |
| Subtitle files (.srt/.ass) | ~30 – 80 KB | ~50 – 120 KB | ~50 – 150 KB |

### 2. Estimation Procedure (Agent MUST Follow):

```
1. Xác định số lượng tập / movie cần tải.
2. Nhân với kích thước ước lượng theo bảng trên (dựa vào resolution & codec từ nguồn).
3. Chạy `df -h <target_disk>` để lấy dung lượng trống hiện tại.
4. Tính phần trăm ổ cứng sẽ bị chiếm sau khi tải.
5. Hiển thị Bảng Ước Lượng cho user trước khi bắt đầu.
```

### 3. Output Format (MUST SHOW TO USER):

```markdown
## 💾 Ước Lượng Dung Lượng Tải Về

| Hạng Mục | Giá Trị |
| :--- | ---: |
| **Tổng số tập / movie** | XX tập |
| **Chất lượng nguồn** | 1080p BDRip HEVC |
| **Dung lượng ước lượng** | ~XX GB |
| **Phụ đề (~XX files)** | ~X MB (không đáng kể) |
| **Tổng cộng ước tính** | **~XX GB** |
| --- | --- |
| **Dung lượng trống hiện tại** | XXX GB |
| **Dung lượng trống sau khi tải** | XXX GB |
| **Phần trăm ổ cứng sau tải** | XX% |
```

### 4. Cảnh Báo Tự Động Theo Ngưỡng:

| Phần Trăm Ổ Cứng Sau Tải | Hành Động |
| :---: | :--- |
| ≤ 75% | 🟢 **AN TOÀN** — Tiến hành tải bình thường. |
| 76% – 85% | 🟡 **CẨN THẬN** — Cảnh báo: *"Ổ cứng sẽ khá đầy sau khi tải. Anh có muốn tiếp tục?"* |
| 86% – 92% | 🟠 **NGUY HIỂM** — Cảnh báo mạnh: *"Ổ cứng sẽ gần đầy! Nên cân nhắc thu hồi dung lượng phim cũ đã đủ 3 tiêu chí trước khi tải."* |
| > 92% | 🔴 **CHẶN** — Không cho tải, yêu cầu dọn dẹp trước: *"KHÔNG ĐỦ DUNG LƯỢNG. Cần giải phóng ít nhất XX GB trước khi tải."* |

---

## 🔗 Translate-Subtitle Handoff (ASK FIRST — NEVER AUTO-EXECUTE)

> [!IMPORTANT]
> After completing the curation pipeline, if subtitle source files are available for translation, the agent **MUST ASK** the user whether they want to trigger the `translate-subtitle` skill. **NEVER auto-execute translation without explicit user consent.**

### Handoff Procedure:

1. **Detect Translatable Subtitles:**
   After Step 3 (Subtitle Hunting), check if any acquired subtitles can serve as source for Vietnamese translation:
   - English `.en.srt` / `.en.ass` → Translatable
   - Japanese `.ja.ass` / `.jpn.ass` → Translatable (CJK module)
   - Chinese `.zh.ass` / `.chi.ass` → Translatable (CJK module)
   - Vietnamese `.vi.srt` already exists → Skip (already done)

2. **Present Handoff Prompt to User:**
   ```
   📝 Phụ đề nguồn sẵn sàng để dịch sang tiếng Việt:
   • Nguồn: 48 file .en.srt (Tiếng Anh)
   • Thể loại gợi ý: detective-mystery
   • Glossary có sẵn: The_Files_of_Young_Kindaichi_{tvdb-79354}
   • Style gợi ý: --style detective-mystery

   Anh có muốn bắt đầu dịch phụ đề tiếng Việt cho bộ phim này không?
   ```

3. **If User Accepts:**
   - Pass the franchise ID, subtitle paths, genre, and style recommendation to the `translate-subtitle` skill.
   - Create `PROGRESS.md` and `AMBIGUITY_LOG.md` in the project workspace (per Two-Tier Architecture).

4. **If User Declines or Doesn't Respond:**
   - Do nothing. The curation output stands on its own.

---

## 🏷️ Subtitle Distribution Badging (MANDATORY TO AVOID CONFUSION)

The agent **MUST** clearly label the delivery format of subtitles for every release:

- `[📦 MUXED SOFTSUB]`: Subtitles are embedded directly inside the `.mkv` container. Explain to the user: *"File video đã tích hợp sẵn phụ đề bên trong, không cần file sub rời bên ngoài."*
- `[📄 STANDALONE SUB]`: Subtitles are separate external `.ass` or `.srt` files downloaded into the `Season XX/` directory.
- `[🔥 HARDSUB]`: Subtitles are permanently burned into the video stream.

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

## 🎯 Universal 6-Step Media Curation Pipeline

### Step 1: Franchise Census & Multi-Database Metadata Resolution
1. **Map Release Types**: Movies, TV Seasons, Canonical OVAs, Bonus Extras.
2. **Resolve All Direct Database URLs**:
   - **TheTVDB**: Series/Movie URL + ID `{tvdb-XXXXX}`
   - **TMDb (The Movie Database)**: URL + ID `{tmdb-XXXXX}`
   - **IMDb**: Title URL + ID `ttXXXXXXX`

---

### Step 2: Disk Space Estimation & Safety Check
1. **Estimate total download size** using the reference table above.
2. **Check available disk space** with `df -h`.
3. **Display the estimation table** to the user.
4. **Apply threshold rules** (🟢🟡🟠🔴) and warn or block accordingly.
5. Only proceed to Step 3 after user acknowledges the estimation.

---

### Step 3: Standardized Plex & Jellyfin Layout
Build a zero-guesswork folder hierarchy:
- `TV_Shows/` & `Movies/`
- Separate canonical specials into `Season 00/` and extras into `Behind The Scenes/`, `Trailers/`, `Featurettes/`.

---

### Step 4: Multi-Source Subtitle Hunting Protocol
- **Hollywood / International**: SubDL, OpenSubtitles, Subsource, Phudeviet.
- **Anime / Asian Cinema**: ACG.RIP, ASSRT, Anime Tosho attachments (.ass.xz), Kitsunekko, SubHD.

---

### Step 5: Subtitle Engineering & Formatting
1. Standardize format to clean UTF-8 `.srt` or 1080p styled `.ass` (`scripts/srt_to_ass.py`).
2. Assign standardized ISO language codes (`.vie.srt`, `.eng.srt`, `.chi.ass`, `.jpn.ass`).
3. Align / split timecodes when mapping compilation movies to episode series.

---

### Step 6: Blueprint Output & Translation Handoff
1. Every show/movie directory **MUST** contain a comprehensive `DOWNLOAD_LINKS.txt` enriched with **Quality Badges, Codecs, Resolution, Subtitle Delivery Format ([📦 MUXED] vs [📄 FILE RỜI]), and Source Ratings**.
2. **ASK the user** if they want to hand off to `translate-subtitle` for Vietnamese translation (see Handoff section above).
