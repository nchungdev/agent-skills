#!/usr/bin/env python3
"""
Sub-to-WebVTT Converter Engine
Converts SRT, ASS, and SSA subtitle files to clean, W3C-standard WebVTT format.
"""

import os
import re
import sys
import argparse
from pathlib import Path

def clean_ass_text(text, strip_all_tags=False):
    """Clean ASS override tags and convert basic styling to HTML/WebVTT tags."""
    # Convert newline tags
    text = text.replace(r"\N", "\n").replace(r"\n", "\n").replace(r"\h", " ")
    
    if strip_all_tags:
        # Strip all {...} blocks
        text = re.sub(r"\{.*?\}", "", text)
        return text.strip()

    # Convert basic formatting
    # Bold: {\b1} -> <b>, {\b0} -> </b>
    text = re.sub(r"\{\\b1\}", "<b>", text)
    text = re.sub(r"\{\\b0\}", "</b>", text)
    
    # Italic: {\i1} -> <i>, {\i0} -> </i>
    text = re.sub(r"\{\\i1\}", "<i>", text)
    text = re.sub(r"\{\\i0\}", "</i>", text)
    
    # Underline: {\u1} -> <u>, {\u0} -> </u>
    text = re.sub(r"\{\\u1\}", "<u>", text)
    text = re.sub(r"\{\\u0\}", "</u>", text)

    # Strip remaining complex override tags: {\pos(..)}, {\an8}, {\c&H...&}, {\fad(..)}, etc.
    text = re.sub(r"\{.*?\}", "", text)
    
    return text.strip()

def ass_time_to_vtt(time_str):
    """Convert ASS timestamp (H:MM:SS.cs) to WebVTT timestamp (HH:MM:SS.mmm)."""
    parts = time_str.strip().split(":")
    if len(parts) == 3:
        h = int(parts[0])
        m = int(parts[1])
        s_cs = parts[2].split(".")
        s = int(s_cs[0])
        cs = int(s_cs[1]) if len(s_cs) > 1 else 0
        ms = cs * 10  # Centiseconds to Milliseconds
        return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"
    return time_str

def srt_time_to_vtt(time_str):
    """Convert SRT timestamp (00:00:00,000) to WebVTT timestamp (00:00:00.000)."""
    return time_str.strip().replace(",", ".")

def convert_ass_to_vtt(ass_path, vtt_path, strip_tags=False):
    """Convert .ass or .ssa file to .vtt."""
    with open(ass_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    cues = []
    events_found = False
    format_indices = {}

    for line in lines:
        line_clean = line.strip()
        if line_clean.lower() == "[events]":
            events_found = True
            continue

        if events_found and line_clean.lower().startswith("format:"):
            fields = [x.strip().lower() for x in line_clean[7:].split(",")]
            format_indices = {field: idx for idx, field in enumerate(fields)}
            continue

        if events_found and line_clean.lower().startswith("dialogue:"):
            content = line_clean[9:].strip()
            # Split with maxsplit based on format fields
            max_splits = len(format_indices) - 1 if format_indices else 9
            parts = [p.strip() for p in content.split(",", max_splits)]
            
            start_idx = format_indices.get("start", 1)
            end_idx = format_indices.get("end", 2)
            text_idx = format_indices.get("text", len(parts) - 1)

            if len(parts) > max(start_idx, end_idx, text_idx):
                start_time = ass_time_to_vtt(parts[start_idx])
                end_time = ass_time_to_vtt(parts[end_idx])
                raw_text = parts[text_idx]
                clean_txt = clean_ass_text(raw_text, strip_all_tags=strip_tags)
                if clean_txt:
                    cues.append((start_time, end_time, clean_txt))

    with open(vtt_path, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n")
        f.write(f"NOTE Converted from {Path(ass_path).name} by Antigravity Sub-to-WebVTT\n\n")
        for idx, (st, et, txt) in enumerate(cues, 1):
            f.write(f"{idx}\n{st} --> {et}\n{txt}\n\n")

    return len(cues)

def convert_srt_to_vtt(srt_path, vtt_path):
    """Convert .srt file to .vtt."""
    with open(srt_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # Normalize newlines
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    
    # Regex to match SRT cues
    cue_pattern = re.compile(r"(\d+)\n(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})\n([\s\S]*?)(?=\n\n|\Z)")
    matches = cue_pattern.findall(content)

    cues = []
    if matches:
        for idx, st, et, txt in matches:
            cues.append((srt_time_to_vtt(st), srt_time_to_vtt(et), txt.strip()))
    else:
        # Fallback line by line parser
        lines = content.split("\n")
        curr_time = None
        curr_txt = []
        for line in lines:
            line_s = line.strip()
            if "-->" in line_s:
                if curr_time and curr_txt:
                    cues.append((curr_time[0], curr_time[1], "\n".join(curr_txt)))
                    curr_txt = []
                times = [srt_time_to_vtt(t) for t in line_s.split("-->")]
                if len(times) == 2:
                    curr_time = (times[0], times[1])
            elif curr_time and line_s and not line_s.isdigit():
                curr_txt.append(line_s)
        if curr_time and curr_txt:
            cues.append((curr_time[0], curr_time[1], "\n".join(curr_txt)))

    with open(vtt_path, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n")
        f.write(f"NOTE Converted from {Path(srt_path).name} by Antigravity Sub-to-WebVTT\n\n")
        for idx, (st, et, txt) in enumerate(cues, 1):
            f.write(f"{idx}\n{st} --> {et}\n{txt}\n\n")

    return len(cues)

def convert_file(input_file, out_file=None, strip_tags=False):
    in_p = Path(input_file)
    if not in_p.is_file():
        print(f"❌ File not found: {input_file}")
        return None

    if not out_file:
        out_p = in_p.with_suffix(".vtt")
    else:
        out_p = Path(out_file)
        out_p.parent.mkdir(parents=True, exist_ok=True)

    ext = in_p.suffix.lower()
    cue_count = 0
    if ext in [".ass", ".ssa"]:
        cue_count = convert_ass_to_vtt(in_p, out_p, strip_tags=strip_tags)
    elif ext in [".srt"]:
        cue_count = convert_srt_to_vtt(in_p, out_p)
    elif ext in [".vtt"]:
        print(f"  ⚪ File {in_p.name} đã là định dạng WebVTT.")
        return str(in_p)
    else:
        print(f"❌ Unsupported format: {ext}")
        return None

    size_kb = os.path.getsize(out_p) / 1024
    print(f"  ✅ Converted: {in_p.name} ➔ {out_p.name} ({cue_count} thoại, {size_kb:.1f} KB)")
    return str(out_p)

def main():
    parser = argparse.ArgumentParser(description="Sub-to-WebVTT Converter CLI - Convert subtitles to WebVTT format.")
    subparsers = parser.add_subparsers(dest="command", help="Lệnh thực hiện")

    # Command: convert
    p_conv = subparsers.add_parser("convert", help="Chuyển đổi 1 file phụ đề sang WebVTT")
    p_conv.add_argument("subtitle", help="Đường dẫn file phụ đề (.ass, .ssa, .srt)")
    p_conv.add_argument("--out-file", help="Đường dẫn file .vtt xuất ra")
    p_conv.add_argument("--strip-tags", action="store_true", help="Xóa hoàn toàn thẻ định dạng styling")

    # Command: batch
    p_batch = subparsers.add_parser("batch", help="Chuyển đổi hàng loạt toàn bộ thư mục")
    p_batch.add_argument("directory", help="Thư mục chứa các file phụ đề")
    p_batch.add_argument("--out-dir", help="Thư mục lưu các file .vtt xuất ra")
    p_batch.add_argument("--strip-tags", action="store_true", help="Xóa hoàn toàn thẻ định dạng styling")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "convert":
        convert_file(args.subtitle, out_file=args.out_file, strip_tags=args.strip_tags)

    elif args.command == "batch":
        folder = Path(args.directory)
        if not folder.is_dir():
            print(f"❌ Thư mục không tồn tại: {args.directory}")
            sys.exit(1)
        sub_exts = {".ass", ".ssa", ".srt"}
        sub_files = sorted([f for f in folder.rglob("*") if f.suffix.lower() in sub_exts])
        print(f"🚀 Tìm thấy {len(sub_files)} file phụ đề trong: {folder.name}")
        
        converted = 0
        for sf in sub_files:
            out_f = None
            if args.out_dir:
                out_f = Path(args.out_dir) / f"{sf.stem}.vtt"
            res = convert_file(sf, out_file=out_f, strip_tags=args.strip_tags)
            if res:
                converted += 1
        print(f"\n🎉 HOÀN TẤT: Đã chuyển đổi thành công {converted}/{len(sub_files)} file WebVTT!")

if __name__ == "__main__":
    main()
