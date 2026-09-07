#!/usr/bin/env python3
"""
Clean SRT Exporter
Trích xuất file SubRip (.srt) siêu sạch từ file Advanced SubStation Alpha (.ass).
Tự động lọc bỏ các layer hiệu ứng hoạt họa KFX (Layer > 0), khử trùng lặp chữ và gộp các time-slice.
"""

import os
import sys
import re
import argparse

def to_sec(ts):
    parts = ts.strip().split(":")
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])

def to_srt_ts(sec):
    if sec < 0:
        sec = 0.0
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int(round((sec - int(sec)) * 1000))
    if ms >= 1000:
        ms = 999
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def clean_ass_tags(text):
    cleaned = re.sub(r"\{.*?\}", "", text)
    cleaned = cleaned.replace(r"\N", "\n").replace(r"\n", "\n").strip()
    return cleaned

def export_clean_srt(ass_path, srt_path):
    """
    Đọc file ASS và xuất file SRT sạch:
    1. Chỉ lấy Layer 0 (loại trừ các hiệu ứng đè của Layer 1..n).
    2. Làm sạch các thẻ override format ASS.
    3. Hợp nhất các time-slice liên kề có cùng nội dung text.
    """
    with open(ass_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    valid_events = []
    for line in lines:
        if line.startswith("Dialogue:"):
            parts = line.split(",", 9)
            layer = parts[0].replace("Dialogue: ", "").strip()
            start = parts[1].strip()
            end = parts[2].strip()
            text = parts[9].strip()

            if layer in ["0", 0]:
                clean_text = clean_ass_tags(text)
                if clean_text:
                    valid_events.append((to_sec(start), to_sec(end), clean_text))

    valid_events.sort(key=lambda x: x[0])

    # Hợp nhất các sự kiện liền kề có cùng text (đặc biệt hữu ích khi xử lý KFX single-layer time-slice)
    merged = []
    for s_t, e_t, txt in valid_events:
        if merged and merged[-1][2] == txt and abs(s_t - merged[-1][1]) < 0.1:
            merged[-1] = (merged[-1][0], max(e_t, merged[-1][1]), txt)
        else:
            merged.append((s_t, e_t, txt))

    os.makedirs(os.path.dirname(os.path.abspath(srt_path)), exist_ok=True)
    with open(srt_path, "w", encoding="utf-8") as f:
        for idx, (s_t, e_t, txt) in enumerate(merged, 1):
            f.write(f"{idx}\n")
            f.write(f"{to_srt_ts(s_t)} --> {to_srt_ts(e_t)}\n")
            f.write(f"{txt}\n\n")

    return len(merged)

def main():
    parser = argparse.ArgumentParser(description="Clean SRT Exporter from ASS subtitle with KFX de-duplication")
    parser.add_argument("ass_file", help="Đường dẫn file .ass nguồn")
    parser.add_argument("srt_file", help="Đường dẫn file .srt đích cần xuất")
    args = parser.parse_args()

    count = export_clean_srt(args.ass_file, args.srt_file)
    print(f"Xuất thành công {count} khối phụ đề SRT sạch vào: {args.srt_file}")

if __name__ == "__main__":
    main()
