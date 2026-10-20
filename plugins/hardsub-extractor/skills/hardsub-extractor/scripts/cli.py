#!/usr/bin/env python3
"""
hardsub-extractor: Unified CLI
Single interface for extracting, batch processing, and testing hardsub OCR.
"""

import os
import sys
import argparse
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    parser = argparse.ArgumentParser(description="hardsub-extractor CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # single
    p_single = subparsers.add_parser("single", help="Extract single episode hardsub OCR")
    p_single.add_argument("--video", required=True, help="Video path")
    p_single.add_argument("--ref-srt", required=True, help="Reference SRT path")
    p_single.add_argument("--out", required=True, help="Output SRT path")
    p_single.add_argument("--api-key", help="Gemini API Key")
    p_single.add_argument("--batch-size", type=int, default=15, help="Batch size")
    p_single.add_argument("--sleep", type=float, default=1.5, help="Delay between batches")
    p_single.add_argument("--fallback-ref", action="store_true", help="Fallback to ref text")

    # batch
    p_batch = subparsers.add_parser("batch", help="Batch process entire directory of episodes")
    p_batch.add_argument("--hardsub-dir", required=True, help="Hardsub video directory")
    p_batch.add_argument("--target-dir", required=True, help="Target library directory")
    p_batch.add_argument("--api-key", help="Gemini API Key")
    p_batch.add_argument("--batch-size", type=int, default=15, help="Batch size")
    p_batch.add_argument("--sleep", type=float, default=1.5, help="Delay between batches")
    p_batch.add_argument("--limit", type=int, default=None, help="Limit number of episodes")
    p_batch.add_argument("--episodes", help="Specific episode tags e.g. S01E01,S01E02")
    p_batch.add_argument("--no-resume", action="store_true", help="Overwrite existing files")
    p_batch.add_argument("--fallback-ref", action="store_true", help="Fallback to ref text")

    # test
    p_test = subparsers.add_parser("test", help="Test OCR on a single frame or interval")
    p_test.add_argument("--video", required=True, help="Video path")
    p_test.add_argument("--timestamp", default="00:10:28", help="Timestamp to sample")
    p_test.add_argument("--api-key", help="Gemini API Key")

    # setup
    p_setup = subparsers.add_parser("setup", help="Configure GEMINI_API_KEY into ~/.env")

    args = parser.parse_args()

    if args.command == "setup":
        cmd = [sys.executable, os.path.join(SCRIPT_DIR, "setup.py")]
        sys.exit(subprocess.run(cmd).returncode)

    elif args.command == "single":
        cmd = [sys.executable, os.path.join(SCRIPT_DIR, "extract_hardsub.py"),
               "--video", args.video, "--ref-srt", args.ref_srt, "--out", args.out,
               "--batch-size", str(args.batch_size), "--sleep", str(args.sleep)]
        if args.api_key:
            cmd.extend(["--api-key", args.api_key])
        if args.fallback_ref:
            cmd.append("--fallback-ref")
        sys.exit(subprocess.run(cmd).returncode)

    elif args.command == "batch":
        cmd = [sys.executable, os.path.join(SCRIPT_DIR, "batch_processor.py"),
               "--hardsub-dir", args.hardsub_dir, "--target-dir", args.target_dir,
               "--batch-size", str(args.batch_size), "--sleep", str(args.sleep)]
        if args.api_key:
            cmd.extend(["--api-key", args.api_key])
        if args.limit:
            cmd.extend(["--limit", str(args.limit)])
        if args.episodes:
            cmd.extend(["--episodes", args.episodes])
        if args.no_resume:
            cmd.append("--no-resume")
        if args.fallback_ref:
            cmd.append("--fallback-ref")
        sys.exit(subprocess.run(cmd).returncode)

    elif args.command == "test":
        import extract_hardsub
        key = extract_hardsub.load_gemini_api_key(args.api_key)
        if not key:
            print("❌ GEMINI_API_KEY chưa cấu hình! Hãy chạy `hardsub-extractor setup`", file=sys.stderr)
            sys.exit(1)
        cmd = [sys.executable, "-c", f"""
import sys, os, subprocess, base64, json, urllib.request
sys.path.append('{SCRIPT_DIR}')
import extract_hardsub

key = '{key}'
ts = extract_hardsub.srt_time_to_sec('{args.timestamp}')
img = extract_hardsub.extract_frame_bytes('{args.video}', ts)
if not img:
    print('Failed to extract frame at {args.timestamp}')
    sys.exit(1)

b64 = base64.b64encode(img).decode('utf-8')
url = f'https://generativelanguage.googleapis.com/v1beta/models/{extract_hardsub.DEFAULT_MODEL}:generateContent?key={{key}}'
payload = {{'contents': [{{'parts': [
    {{'text': 'Đọc chính xác phụ đề tiếng Việt trong ảnh:'}},
    {{'inline_data': {{'mime_type': 'image/jpeg', 'data': b64}}}}
]}}]}}

req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={{'Content-Type': 'application/json'}})
with urllib.request.urlopen(req, timeout=15) as resp:
    res = json.loads(resp.read().decode('utf-8'))
    print('RESULT:', res['candidates'][0]['content']['parts'][0]['text'])
"""]
        sys.exit(subprocess.run(cmd).returncode)

if __name__ == "__main__":
    main()
