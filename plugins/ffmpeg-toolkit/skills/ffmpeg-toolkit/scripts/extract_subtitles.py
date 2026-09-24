#!/usr/bin/env python3
"""
Subtitle Extractor CLI & Engine
Extracts embedded subtitle tracks from MKV/MP4 containers with standard Plex/TVDB naming.
"""

import os
import sys
import json
import shutil
import argparse
import subprocess
from pathlib import Path

# Locate ffmpeg & ffprobe
def find_binary(name):
    candidate_paths = [
        shutil.which(name),
        f"/opt/homebrew/bin/{name}",
        f"/usr/local/bin/{name}",
        f"/usr/bin/{name}"
    ]
    for path in candidate_paths:
        if path and os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None

FFPROBE = find_binary("ffprobe")
FFMPEG = find_binary("ffmpeg")

# ISO 639-2 / 639-1 Language Mapping
LANG_MAP = {
    "eng": "en", "en": "en", "english": "en",
    "vie": "vi", "vi": "vi", "vietnamese": "vi",
    "jpn": "ja", "ja": "ja", "japanese": "ja",
    "chi": "zh", "zho": "zh", "zh": "zh", "chinese": "zh",
    "kor": "ko", "ko": "ko", "korean": "ko",
    "fre": "fr", "fra": "fr", "fr": "fr", "french": "fr",
    "ger": "de", "deu": "de", "de": "de", "german": "de",
    "spa": "es", "es": "es", "spanish": "es",
    "rus": "ru", "ru": "ru", "russian": "ru",
    "und": "und", "": "und"
}

def probe_subtitles(video_path):
    """Probe all subtitle streams in a video file using ffprobe."""
    if not FFPROBE:
        print("❌ Error: ffprobe not found. Please install ffmpeg/ffprobe.", file=sys.stderr)
        return []

    cmd = [
        FFPROBE,
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        "-select_streams", "s",
        str(video_path)
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        streams = data.get("streams", [])
        sub_tracks = []
        for s in streams:
            tags = s.get("tags", {})
            raw_lang = tags.get("language", "und").lower()
            lang_code = LANG_MAP.get(raw_lang, raw_lang)
            title = tags.get("title", tags.get("handler_name", ""))
            codec_name = s.get("codec_name", "unknown")
            sub_tracks.append({
                "index": s.get("index"),
                "sub_index": len(sub_tracks),
                "codec": codec_name,
                "raw_lang": raw_lang,
                "lang": lang_code,
                "title": title,
                "disposition": s.get("disposition", {})
            })
        return sub_tracks
    except Exception as e:
        print(f"❌ Error probing {video_path}: {e}", file=sys.stderr)
        return []

def extract_track(video_path, track, out_dir=None, format_choice=None):
    """Extract a single subtitle track from video."""
    if not FFMPEG:
        print("❌ Error: ffmpeg not found.", file=sys.stderr)
        return None

    video_p = Path(video_path)
    if out_dir:
        out_folder = Path(out_dir)
        out_folder.mkdir(parents=True, exist_ok=True)
    else:
        out_folder = video_p.parent

    # Determine extension
    codec = track.get("codec", "").lower()
    if format_choice:
        ext = format_choice.lower()
    elif "ass" in codec or "ssa" in codec:
        ext = "ass"
    elif "subrip" in codec or "srt" in codec or "mov_text" in codec:
        ext = "srt"
    else:
        ext = "srt"

    lang = track.get("lang", "und")
    base_name = video_p.stem
    
    # Avoid duplicate names if multiple tracks of same language exist
    sub_idx = track.get("sub_index", 0)
    suffix = f".{lang}" if sub_idx == 0 else f".{lang}.track{sub_idx+1}"
    out_file = out_folder / f"{base_name}{suffix}.{ext}"

    cmd = [
        FFMPEG,
        "-y",
        "-i", str(video_p),
        "-map", f"0:{track['index']}",
        "-c:s", "copy" if (("ass" in codec and ext == "ass") or ("subrip" in codec and ext == "srt")) else ("text" if ext == "srt" else "copy"),
        str(out_file)
    ]

    try:
        subprocess.run(cmd, capture_output=True, check=True)
        if out_file.exists() and out_file.stat().st_size > 0:
            return str(out_file)
    except Exception as e:
        # Fallback to standard srt transcode if copy fails
        try:
            cmd_fallback = [
                FFMPEG, "-y", "-i", str(video_p),
                "-map", f"0:{track['index']}",
                "-c:s", "srt",
                str(out_file)
            ]
            subprocess.run(cmd_fallback, capture_output=True, check=True)
            if out_file.exists() and out_file.stat().st_size > 0:
                return str(out_file)
        except Exception as e2:
            print(f"❌ Failed to extract track {track['index']} from {video_p.name}: {e2}", file=sys.stderr)
            return None
    return None

def process_file(video_path, out_dir=None, lang_filter="all", format_choice=None):
    video_p = Path(video_path)
    if not video_p.is_file():
        print(f"❌ File not found: {video_path}")
        return []

    print(f"\n🎬 Probing: {video_p.name}")
    tracks = probe_subtitles(video_p)
    if not tracks:
        print(f"  ⚪ Không tìm thấy track phụ đề nhúng nào.")
        return []

    print(f"  📋 Tìm thấy {len(tracks)} track phụ đề:")
    for t in tracks:
        flags = []
        if t['disposition'].get('default'): flags.append("Default")
        if t['disposition'].get('forced'): flags.append("Forced")
        flag_str = f" [{', '.join(flags)}]" if flags else ""
        print(f"     • Stream #{t['index']}: [{t['codec']}] Lang: {t['lang']} ({t['title']}){flag_str}")

    extracted = []
    langs_to_extract = [l.strip().lower() for l in lang_filter.split(',')]

    for t in tracks:
        if "all" not in langs_to_extract and t['lang'] not in langs_to_extract and t['raw_lang'] not in langs_to_extract:
            continue
        
        print(f"  ✂️ Đang bóc tách track #{t['index']} ({t['lang']})...")
        out_path = extract_track(video_p, t, out_dir=out_dir, format_choice=format_choice)
        if out_path:
            size_kb = os.path.getsize(out_path) / 1024
            print(f"     ✅ Xuất thành công: {Path(out_path).name} ({size_kb:.1f} KB)")
            extracted.append(out_path)
    return extracted

def main():
    parser = argparse.ArgumentParser(description="Subtitle Extractor CLI - Extract embedded subtitles from videos.")
    subparsers = parser.add_subparsers(dest="command", help="Lệnh thực hiện")

    # Command: probe
    p_probe = subparsers.add_parser("probe", help="Quét thông tin track phụ đề trong video")
    p_probe.add_argument("video", help="Đường dẫn file video")

    # Command: extract
    p_ext = subparsers.add_parser("extract", help="Bóc tách phụ đề từ 1 file video")
    p_ext.add_argument("video", help="Đường dẫn file video")
    p_ext.add_argument("--lang", default="all", help="Ngôn ngữ cần bóc (en, vi, ja, all). Mặc định: all")
    p_ext.add_argument("--format", choices=["ass", "srt"], help="Định dạng xuất (ass, srt)")
    p_ext.add_argument("--out-dir", help="Thư mục lưu file phụ đề xuất ra")

    # Command: batch
    p_batch = subparsers.add_parser("batch", help="Bóc tách phụ đề hàng loạt cho toàn bộ thư mục")
    p_batch.add_argument("directory", help="Thư mục chứa các file video")
    p_batch.add_argument("--lang", default="all", help="Ngôn ngữ cần bóc (en, vi, ja, all). Mặc định: all")
    p_batch.add_argument("--format", choices=["ass", "srt"], help="Định dạng xuất (ass, srt)")
    p_batch.add_argument("--out-dir", help="Thư mục lưu file phụ đề xuất ra")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "probe":
        tracks = probe_subtitles(args.video)
        print(json.dumps(tracks, indent=2, ensure_ascii=False))

    elif args.command == "extract":
        process_file(args.video, out_dir=args.out_dir, lang_filter=args.lang, format_choice=args.format)

    elif args.command == "batch":
        folder = Path(args.directory)
        if not folder.is_dir():
            print(f"❌ Thư mục không tồn tại: {args.directory}")
            sys.exit(1)
        video_exts = {".mkv", ".mp4", ".m4v", ".avi", ".ts"}
        video_files = sorted([f for f in folder.rglob("*") if f.suffix.lower() in video_exts])
        print(f"🚀 Tìm thấy {len(video_files)} file video trong thư mục: {folder.name}")
        
        all_extracted = []
        for vf in video_files:
            res = process_file(vf, out_dir=args.out_dir, lang_filter=args.lang, format_choice=args.format)
            all_extracted.extend(res)
        
        print(f"\n🎉 HOÀN TẤT: Đã bóc tách thành công {len(all_extracted)} file phụ đề!")

if __name__ == "__main__":
    main()
