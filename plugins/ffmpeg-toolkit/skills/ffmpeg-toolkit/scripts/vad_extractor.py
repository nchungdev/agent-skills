#!/usr/bin/env python3
"""
VAD Voice Activity Extractor
Trích xuất waveform biên độ giọng nói siêu tốc sử dụng bộ lọc FFmpeg silencedetect.
Tiêu tốn 0 token, không decode video, không dùng GPU.
"""

import os
import sys
import json
import time
import argparse
import subprocess
import glob

def extract_vad_from_video(video_path, noise="-28dB", duration="0.12", threads=1):
    """
    Trích xuất danh sách các khoảng giọng nói (voice ranges) từ file video/audio.
    Trả về list các tuple: [(voice_start_seconds, voice_end_seconds), ...]
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Không tìm thấy file video: {video_path}")

    cmd = [
        "ffmpeg",
        "-threads", str(threads),
        "-i", video_path,
        "-vn",
        "-af", f"silencedetect=noise={noise}:d={duration}",
        "-f", "null",
        "-"
    ]
    
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True)
    
    voice_ranges = []
    cur_silence_start = 0.0
    
    # FFmpeg xuất log silencedetect qua stderr
    for line in p.stderr.splitlines():
        if "silence_start:" in line:
            try:
                cur_silence_start = float(line.split("silence_start:")[1].strip())
            except (ValueError, IndexError):
                pass
        elif "silence_end:" in line:
            try:
                parts = line.split("silence_end:")[1].split("|")
                silence_end = float(parts[0].strip())
                # Khoảng có âm thanh nằm từ cuối đoạn im lặng trước tới đầu đoạn im lặng tiếp theo
                voice_ranges.append((silence_end, cur_silence_start))
            except (ValueError, IndexError):
                pass
                
    elapsed = time.time() - t0
    return voice_ranges, elapsed

def main():
    parser = argparse.ArgumentParser(description="Zero-Token FFmpeg Voice Activity Detection (VAD) Extractor")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Lệnh probe 1 file
    probe_p = subparsers.add_parser("probe", help="Trích xuất VAD cho 1 file video/audio đơn lẻ")
    probe_p.add_argument("input", help="Đường dẫn file video hoặc audio")
    probe_p.add_argument("--noise", default="-28dB", help="Ngưỡng tiếng ồn (mặc định: -28dB)")
    probe_p.add_argument("--duration", default="0.12", help="Thời lượng khoảng lặng tối thiểu (mặc định: 0.12s)")
    probe_p.add_argument("--out", help="Đường dẫn file JSON xuất ra (nếu bỏ trống in stdout)")
    probe_p.add_argument("--threads", type=int, default=1, help="Số luồng CPU ffmpeg (mặc định: 1)")

    # Lệnh batch quét thư mục
    batch_p = subparsers.add_parser("batch", help="Trích xuất VAD hàng loạt cho toàn bộ file trong thư mục")
    batch_p.add_argument("input_dir", help="Thư mục chứa video")
    batch_p.add_argument("--ext", default="mkv,mp4,m4v,ts", help="Các đuôi file cần quét, cách nhau bởi dấu phẩy")
    batch_p.add_argument("--out-dir", required=True, help="Thư mục lưu các file JSON")
    batch_p.add_argument("--noise", default="-28dB", help="Ngưỡng tiếng ồn (mặc định: -28dB)")
    batch_p.add_argument("--duration", default="0.12", help="Thời lượng khoảng lặng tối thiểu (mặc định: 0.12s)")
    batch_p.add_argument("--threads", type=int, default=1, help="Số luồng CPU ffmpeg cho mỗi file (mặc định: 1)")

    args = parser.parse_args()

    if args.command == "probe":
        ranges, elapsed = extract_vad_from_video(args.input, args.noise, args.duration, args.threads)
        print(f"Trích xuất thành công {len(ranges)} khoảng giọng nói trong {elapsed:.2f}s.")
        if args.out:
            os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
            with open(args.out, "w", encoding="utf-8") as f:
                json.dump(ranges, f, indent=2)
            print(f"Đã lưu kết quả vào: {args.out}")
        else:
            print(json.dumps(ranges[:5], indent=2))
            if len(ranges) > 5:
                print(f"... và {len(ranges)-5} khoảng giọng nói khác.")

    elif args.command == "batch":
        os.makedirs(args.out_dir, exist_ok=True)
        exts = [e.strip().lower() for e in args.ext.split(",")]
        video_files = []
        for ext in exts:
            video_files.extend(glob.glob(os.path.join(args.input_dir, f"*.{ext}")))
            video_files.extend(glob.glob(os.path.join(args.input_dir, f"**/*.{ext}"), recursive=True))
            
        video_files = sorted(list(set(video_files)))
        print(f"Tìm thấy {len(video_files)} file video cần trích xuất VAD trong {args.input_dir}...")
        
        for idx, vf in enumerate(video_files, 1):
            base_name = os.path.splitext(os.path.basename(vf))[0]
            out_json = os.path.join(args.out_dir, f"{base_name}.json")
            if os.path.exists(out_json) and os.path.getsize(out_json) > 10:
                print(f"[{idx}/{len(video_files)}] {base_name}: Đã tồn tại, bỏ qua.")
                continue
                
            ranges, elapsed = extract_vad_from_video(vf, args.noise, args.duration, args.threads)
            with open(out_json, "w", encoding="utf-8") as f:
                json.dump(ranges, f)
            print(f"[{idx}/{len(video_files)}] {base_name}: Hoàn tất trong {elapsed:.2f}s ({len(ranges)} ranges)")
            
        print("Trích xuất VAD hàng loạt hoàn tất 100%!")

if __name__ == "__main__":
    main()
