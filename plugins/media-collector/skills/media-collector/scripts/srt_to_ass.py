#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced SRT-to-ASS Converter with Style Presets, Batch Mode & Font Fallback
media-collector v2.0 — scripts/srt_to_ass.py
"""

import sys
import os
import glob
import argparse
import re

# ─────────────────────────────────────────────────────────────────
# STYLE PRESETS (built-in)
# ─────────────────────────────────────────────────────────────────
STYLE_PRESETS = {
    "default": {
        "font": "Noto Sans",
        "size": 60,
        "primary": "&H00FFFFFF",
        "outline_color": "&H00000000",
        "back_color": "&H80000000",
        "outline": 2.5,
        "shadow": 1,
        "bold": 0,
        "margin_v": 40,
    },
    "classic-cinema": {
        "font": "Arial",
        "size": 58,
        "primary": "&H00FFFFFF",
        "outline_color": "&H00000000",
        "back_color": "&H80000000",
        "outline": 2,
        "shadow": 1,
        "bold": -1,
        "margin_v": 35,
    },
    "detective-mystery": {
        "font": "Trebuchet MS",
        "size": 60,
        "primary": "&H00F0F0F0",
        "outline_color": "&H00101010",
        "back_color": "&H80000000",
        "outline": 2,
        "shadow": 1,
        "bold": 0,
        "margin_v": 38,
    },
    "mecha-robot": {
        "font": "Arial",
        "size": 60,
        "primary": "&H00FFFFFF",
        "outline_color": "&H00000000",
        "back_color": "&H80000000",
        "outline": 2.2,
        "shadow": 1,
        "bold": -1,
        "margin_v": 35,
    },
    "medical-drama": {
        "font": "Helvetica",
        "size": 58,
        "primary": "&H00FFFFFF",
        "outline_color": "&H00151515",
        "back_color": "&H80000000",
        "outline": 2,
        "shadow": 1,
        "bold": 0,
        "margin_v": 36,
    },
    "minimal": {
        "font": "Noto Sans",
        "size": 54,
        "primary": "&H00FFFFFF",
        "outline_color": "&H00000000",
        "back_color": "&H00000000",
        "outline": 1.5,
        "shadow": 0,
        "bold": 0,
        "margin_v": 30,
    },
    "large-tv": {
        "font": "Noto Sans",
        "size": 75,
        "primary": "&H00FFFFFF",
        "outline_color": "&H00000000",
        "back_color": "&H00000000",
        "outline": 4.5,
        "shadow": 0,
        "bold": 0,
        "margin_v": 50,
    },
}

# Font fallback chain — try in order until one is found on the system
FONT_FALLBACK_CHAINS = {
    "Noto Sans": ["Noto Sans", "Noto Sans CJK SC", "Noto Sans CJK JP", "Source Han Sans", "Roboto", "Arial", "Helvetica"],
    "Arial": ["Arial", "Helvetica Neue", "Helvetica", "Noto Sans", "Roboto"],
    "Trebuchet MS": ["Trebuchet MS", "Segoe UI", "Noto Sans", "Arial"],
    "Helvetica": ["Helvetica Neue", "Helvetica", "Arial", "Noto Sans"],
}


def srt_time_to_ass(t_str):
    """Convert SRT timestamp (HH:MM:SS,mmm) to ASS timestamp (H:MM:SS.cc)."""
    t_str = t_str.strip().replace(",", ".")
    parts = t_str.split(":")
    h = int(parts[0])
    m = parts[1]
    s, ms = parts[2].split(".")
    return f"{h}:{m}:{s}.{ms[:2]}"


def detect_system_fonts():
    """Get list of available font family names on macOS/Linux."""
    try:
        import subprocess
        result = subprocess.run(
            ["fc-list", "--format", "%{family}\n"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            fonts = set()
            for line in result.stdout.strip().splitlines():
                for f in line.split(","):
                    fonts.add(f.strip())
            return fonts
    except Exception:
        pass
    return set()


def resolve_font(requested_font, system_fonts=None):
    """Resolve font using fallback chain if requested font is not available."""
    if not system_fonts:
        return requested_font

    if requested_font in system_fonts:
        return requested_font

    chain = FONT_FALLBACK_CHAINS.get(requested_font, [requested_font])
    for candidate in chain:
        if candidate in system_fonts:
            print(f"⚠️  Font '{requested_font}' not found, using fallback: '{candidate}'")
            return candidate

    print(f"⚠️  No fallback found for '{requested_font}', using as-is (may not render correctly)")
    return requested_font


def build_ass_header(title, style_name="default", custom_font=None, custom_size=None, res_x=1920, res_y=1080):
    """Build ASS header with selected style preset."""
    preset = STYLE_PRESETS.get(style_name, STYLE_PRESETS["default"])

    system_fonts = detect_system_fonts()
    font = custom_font or preset["font"]
    font = resolve_font(font, system_fonts)
    size = custom_size or preset["size"]

    header = f"""[Script Info]
Title: {title}
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
PlayResX: {res_x}
PlayResY: {res_y}
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{size},{preset['primary']},&H00000000,{preset['outline_color']},{preset['back_color']},{preset['bold']},0,0,0,100,100,0,0,1,{preset['outline']},{preset['shadow']},2,20,20,{preset['margin_v']},1
Style: Top,{font},{size - 4},{preset['primary']},&H00000000,{preset['outline_color']},{preset['back_color']},{preset['bold']},0,0,0,100,100,0,0,1,{preset['outline']},{preset['shadow']},8,20,20,20,1
Style: Note,{font},{size - 8},&H00FFFF00,&H00000000,{preset['outline_color']},{preset['back_color']},0,1,0,0,100,100,0,0,1,{preset['outline'] - 0.5},{preset['shadow']},8,20,20,20,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    return header


def parse_srt_blocks(text):
    """Parse SRT content into list of (index, start, end, text) tuples."""
    blocks = re.split(r"\n\s*\n", text.strip())
    dialogues = []
    for b in blocks:
        lines = [l.strip() for l in b.splitlines() if l.strip()]
        if len(lines) >= 3 and "-->" in lines[1]:
            times = lines[1].split("-->")
            start = srt_time_to_ass(times[0])
            end = srt_time_to_ass(times[1])
            dialogue_text = r"\N".join(lines[2:])
            # Clean common SRT artifacts
            dialogue_text = re.sub(r"</?[biusBIUS]>", "", dialogue_text)  # strip HTML tags
            dialogue_text = re.sub(r"\{\\an\d\}", "", dialogue_text)  # strip existing ASS alignment
            dialogues.append((start, end, dialogue_text))
    return dialogues


def convert(srt_path, ass_path=None, style="default", font=None, size=None):
    """Convert a single SRT file to ASS with the specified style preset."""
    if not ass_path:
        ass_path = os.path.splitext(srt_path)[0] + ".ass"

    with open(srt_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    title = os.path.splitext(os.path.basename(srt_path))[0]
    header = build_ass_header(title, style, font, size)
    dialogues = parse_srt_blocks(text)

    lines = []
    for start, end, txt in dialogues:
        lines.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{txt}")

    with open(ass_path, "w", encoding="utf-8") as out:
        out.write(header + "\n".join(lines) + "\n")

    print(f"✅ [{style}] Converted {len(dialogues)} lines → {os.path.basename(ass_path)}")
    return len(dialogues)


def batch_convert(input_dir, output_dir=None, style="default", pattern="*.srt", font=None, size=None):
    """Batch convert all matching SRT files in a directory."""
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    files = sorted(glob.glob(os.path.join(input_dir, "**", pattern), recursive=True))
    if not files:
        print(f"⚠️  No files matching '{pattern}' found in {input_dir}")
        return

    total_lines = 0
    for srt_path in files:
        if output_dir:
            rel = os.path.relpath(srt_path, input_dir)
            ass_path = os.path.join(output_dir, os.path.splitext(rel)[0] + ".ass")
            os.makedirs(os.path.dirname(ass_path), exist_ok=True)
        else:
            ass_path = None

        total_lines += convert(srt_path, ass_path, style, font, size)

    print(f"\n🎬 Batch complete: {len(files)} files, {total_lines} total lines, style: {style}")


def main():
    parser = argparse.ArgumentParser(
        description="Advanced SRT → ASS converter with style presets, batch mode & font fallback",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available style presets:
  default           Standard balanced subtitle style
  classic-cinema    Elegant cinema style (bold, shadowed)
  detective-mystery Modern high-contrast style for crime/mystery shows
  mecha-robot       Bold anime style with support for dual-layer karaoke
  medical-drama     Clean professional style for medical/surgical content
  minimal           Ultra-clean, borderless style
  large-tv          Extra large for TV viewing at distance

Examples:
  python3 srt_to_ass.py input.srt
  python3 srt_to_ass.py input.srt -o output.ass --style detective-mystery
  python3 srt_to_ass.py --batch ./subs/ --style classic-cinema
  python3 srt_to_ass.py --batch ./subs/ -o ./ass_out/ --style medical-drama --font "Helvetica Neue"
        """
    )
    parser.add_argument("input", nargs="?", help="Input SRT file (single mode)")
    parser.add_argument("-o", "--output", help="Output ASS file (single) or directory (batch)")
    parser.add_argument("--style", default="default", choices=list(STYLE_PRESETS.keys()),
                        help="Style preset to apply (default: 'default')")
    parser.add_argument("--font", help="Override font family name")
    parser.add_argument("--size", type=int, help="Override font size")
    parser.add_argument("--batch", metavar="DIR", help="Batch convert all SRT files in directory")
    parser.add_argument("--pattern", default="*.srt", help="Glob pattern for batch mode (default: *.srt)")
    parser.add_argument("--list-styles", action="store_true", help="List available style presets and exit")

    args = parser.parse_args()

    if args.list_styles:
        print("Available style presets:\n")
        for name, preset in STYLE_PRESETS.items():
            print(f"  {name:<22} font={preset['font']}, size={preset['size']}, outline={preset['outline']}")
        return

    if args.batch:
        batch_convert(args.batch, args.output, args.style, args.pattern, args.font, args.size)
    elif args.input:
        convert(args.input, args.output, args.style, args.font, args.size)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
