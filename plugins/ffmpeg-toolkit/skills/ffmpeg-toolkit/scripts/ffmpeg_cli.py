#!/usr/bin/env python3
"""
FFmpeg Toolkit CLI entrypoint & reporter.
"""

import sys
import argparse
import subprocess
from pathlib import Path

def check_tools():
    tools = {}
    for tool in ["ffmpeg", "ffprobe"]:
        try:
            res = subprocess.run([tool, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            first_line = res.stdout.split("\n")[0] if res.stdout else "Available"
            tools[tool] = {"installed": True, "version": first_line[:40]}
        except FileNotFoundError:
            tools[tool] = {"installed": False, "version": "Not found"}
    return tools

def report():
    tools = check_tools()
    print("# 📊 FFmpeg Toolkit Status Report")
    print("\n## 🛠️ Trạng Thái Công Cụ Hệ Thống:")
    for name, info in tools.items():
        icon = "✅" if info["installed"] else "❌"
        print(f"* {icon} **{name}**: `{info['version']}`")
    
    print("\n## 🚀 Năng Lực Sẵn Sàng:")
    print("* `extract`: Bóc tách track phụ đề ngầm từ MKV/MP4")
    print("* `align`: Căn chỉnh timecode bằng FFmpeg VAD (Zero-token)")
    print("* `to-vtt`: Convert phụ đề sang WebVTT chuẩn W3C")

def main():
    parser = argparse.ArgumentParser(description="FFmpeg Toolkit Manager")
    parser.add_argument("command", choices=["report", "status"], default="report", nargs="?", help="Command to run")
    args = parser.parse_args()
    
    if args.command in ["report", "status"]:
        report()

if __name__ == "__main__":
    main()
