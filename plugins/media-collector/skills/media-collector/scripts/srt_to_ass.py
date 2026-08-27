#!/usr/bin/env python3
import sys
import os

def srt_time_to_ass(t_str):
    t_str = t_str.strip().replace(",", ".")
    parts = t_str.split(":")
    h = int(parts[0])
    m = parts[1]
    s, ms = parts[2].split(".")
    return h + ":" + m + ":" + s + "." + ms[:2]

def convert(srt_path, ass_path=None, font_name="Noto Sans", font_size=75):
    if not ass_path:
        ass_path = os.path.splitext(srt_path)[0] + ".ass"
        
    with open(srt_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read().strip()
        
    title = os.path.splitext(os.path.basename(srt_path))[0]
    header = "[Script Info]\nTitle: " + title + "\nScriptType: v4.00+\nWrapStyle: 0\nScaledBorderAndShadow: yes\nPlayResX: 1920\nPlayResY: 1080\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default," + font_name + "," + str(font_size) + ",&H00FFFFFF,&H00000000,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,4.5,0,2,20,20,50,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"

    blocks = text.split("\n\n")
    dialogues = []
    for b in blocks:
        lines = [l.strip() for l in b.splitlines() if l.strip()]
        if len(lines) >= 3 and "-->" in lines[1]:
            times = lines[1].split("-->")
            start = srt_time_to_ass(times[0])
            end = srt_time_to_ass(times[1])
            dialogue_text = r"\N".join(lines[2:])
            dialogues.append("Dialogue: 0," + start + "," + end + ",Default,,0,0,0,," + dialogue_text)
            
    with open(ass_path, "w", encoding="utf-8") as out:
        out.write(header + "\n".join(dialogues) + "\n")
    print("✅ Converted " + str(len(dialogues)) + " lines -> " + ass_path)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 srt_to_ass.py <file.srt> [output.ass]")
    else:
        convert(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
