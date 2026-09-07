#!/usr/bin/env python3
"""
Subtitle Frame Aligner
Căn chỉnh mốc thời gian (Speech Onset Alignment) từng dòng thoại theo sóng âm VAD.
Khóa bảo vệ các track bài hát, KFX animation và title cards.
"""

import os
import sys
import re
import json
import argparse

def to_sec(ts):
    parts = ts.strip().split(":")
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])

def to_ass_ts(sec):
    if sec < 0:
        sec = 0.0
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def clean_ass_tags(text):
    cleaned = re.sub(r"\{.*?\}", "", text)
    cleaned = cleaned.replace(r"\N", "\n").replace(r"\n", "\n").strip()
    return cleaned

def align_ass_file(ass_input, vad_input, ass_output=None, tolerance=0.85, min_duration=1.2, dialogue_styles=None):
    """
    Căn chỉnh file .ass dựa theo dữ liệu khoảng giọng nói VAD JSON.
    """
    if dialogue_styles is None:
        dialogue_styles = ["Default", "*Default", "text", "Main", "Default-Italic"]

    with open(vad_input, "r", encoding="utf-8") as f:
        voice_ranges = json.load(f)

    with open(ass_input, "r", encoding="utf-8") as f:
        lines = f.readlines()

    events = []
    header_lines = []
    aligned_count = 0
    preserved_count = 0

    for line in lines:
        if line.startswith("Dialogue:"):
            parts = line.split(",", 9)
            layer = parts[0].replace("Dialogue: ", "").strip()
            start = parts[1].strip()
            end = parts[2].strip()
            style = parts[3].strip()
            actor = parts[4].strip()
            ml, mr, mv = parts[5].strip(), parts[6].strip(), parts[7].strip()
            effect = parts[8].strip()
            text = parts[9].strip()

            s_sec = to_sec(start)
            e_sec = to_sec(end)

            # Quy tắc Style Lock: Chỉ căn chỉnh style hội thoại, bỏ qua bài hát, title và KFX
            is_locked = (
                style.startswith("Song-") or
                style.startswith("title") or
                style.startswith("summon-") or
                style.startswith("atk-") or
                style.startswith("transform-")
            )
            is_dialogue = (style in dialogue_styles) and not is_locked

            if is_dialogue and len(clean_ass_tags(text)) > 1:
                best_v = None
                min_dist = 999.0
                for v_start, v_end in voice_ranges:
                    dist = abs(v_start - s_sec)
                    if dist < tolerance and dist < min_dist:
                        min_dist = dist
                        best_v = v_start

                if best_v is not None:
                    new_start = best_v
                    new_end = max(new_start + min_duration, e_sec)
                    start = to_ass_ts(new_start)
                    end = to_ass_ts(new_end)
                    aligned_count += 1
            else:
                preserved_count += 1

            events.append({
                "layer": layer,
                "start": start,
                "end": end,
                "style": style,
                "actor": actor,
                "ml": ml, "mr": mr, "mv": mv,
                "effect": effect,
                "text": text
            })
        else:
            header_lines.append(line)

    dest_path = ass_output if ass_output else ass_input
    with open(dest_path, "w", encoding="utf-8") as f:
        for hl in header_lines:
            f.write(hl)
        for ev in events:
            f.write(f"Dialogue: {ev['layer']},{ev['start']},{ev['end']},{ev['style']},{ev['actor']},{ev['ml']},{ev['mr']},{ev['mv']},{ev['effect']},{ev['text']}\n")

    return aligned_count, preserved_count

def main():
    parser = argparse.ArgumentParser(description="Frame-Perfect Subtitle Aligner based on VAD Audio Speech Intervals")
    parser.add_argument("sub_file", help="Đường dẫn file phụ đề (.ass)")
    parser.add_argument("vad_file", help="Đường dẫn file VAD JSON biên độ giọng nói")
    parser.add_argument("--out", help="Đường dẫn file .ass xuất ra (mặc định ghi đè file gốc)")
    parser.add_argument("--tolerance", type=float, default=0.85, help="Ngưỡng lệch tối đa để match giọng nói (giây, mặc định 0.85s)")
    parser.add_argument("--min-duration", type=float, default=1.2, help="Thời lượng hiển thị tối thiểu của câu thoại (giây, mặc định 1.2s)")
    parser.add_argument("--styles", default="Default,*Default,text,Main,Default-Italic", help="Danh sách style thoại cần căn chỉnh, phân tách bởi dấu phẩy")

    args = parser.parse_args()
    styles = [s.strip() for s in args.styles.split(",")]

    aligned, preserved = align_ass_file(
        args.sub_file,
        args.vad_file,
        ass_output=args.out,
        tolerance=args.tolerance,
        min_duration=args.min_duration,
        dialogue_styles=styles
    )

    print(f"Căn chỉnh thành công {aligned} dòng thoại (Đã khóa bảo vệ {preserved} dòng bài hát/KFX/title).")

if __name__ == "__main__":
    main()
