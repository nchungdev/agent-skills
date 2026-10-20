#!/usr/bin/env python3
"""
hardsub-extractor: Batch Processor
Orchestrates multi-episode hardsub OCR extraction across television seasons or film collections.
"""

import os
import sys
import re
import glob
import time
import argparse
from extract_hardsub import process_video_with_ref, load_gemini_api_key, DEFAULT_MODEL, DEFAULT_CROP

def find_season_ep_tag(filename):
    m = re.search(r'S(\d+)E(\d+)', filename, re.IGNORECASE)
    if m:
        return f"S{int(m.group(1)):02d}E{int(m.group(2)):02d}"
    m = re.search(r'E(\d+)', filename, re.IGNORECASE)
    if m:
        return f"E{int(m.group(1)):02d}"
    return None

def run_batch(hardsub_dir, target_dir, api_key=None, model=DEFAULT_MODEL,
              batch_size=15, crop=DEFAULT_CROP, delay_sec=1.5, resume=True,
              limit=None, selected_episodes=None, fallback_ref=False):
    api_key = load_gemini_api_key(api_key)
    if not api_key:
        print("❌ Error: GEMINI_API_KEY chưa được cấu hình! Hãy chạy `hardsub-extractor setup` hoặc thêm vào ~/.env", file=sys.stderr)
        return False
    
    print("=" * 70)
    print("🚀 HARDSUB-EXTRACTOR: BATCH OCR PIPELINE")
    print("=" * 70)
    print(f"📁 Hardsub Source:  {hardsub_dir}")
    print(f"📁 Target Library:  {target_dir}")
    print(f"🤖 Vision Model:    {model}")
    print(f"📦 Batch Size:      {batch_size} frames/request")
    print(f"⏳ Inter-call Delay:{delay_sec}s")
    print(f"🔄 Resume Mode:     {resume}")
    print("=" * 70)

    # Gather hardsub video files
    video_exts = ("*.mp4", "*.mkv", "*.m4v", "*.avi")
    hardsub_files = []
    for ext in video_exts:
        hardsub_files.extend(glob.glob(os.path.join(hardsub_dir, ext)))
    hardsub_files.sort()

    if not hardsub_files:
        print(f"❌ No video files found in {hardsub_dir}")
        return False

    # Gather target reference SRT files
    target_srts = {}
    target_mkvs = {}
    hardsub_abs = os.path.abspath(hardsub_dir)
    for root, _, files in os.walk(target_dir):
        # Automatically skip the source hardsub directory if nested inside target_dir
        if os.path.abspath(root).startswith(hardsub_abs):
            continue
        for f in files:
            full_path = os.path.join(root, f)
            tag = find_season_ep_tag(f)
            if not tag:
                continue
            if f.endswith(".vi.srt") and not f.endswith(".ocr.srt") and not f.endswith(".OCR.srt"):
                target_srts[tag] = full_path
            elif f.endswith(".mkv") or (f.endswith(".mp4") and "WEBDL" in f):
                target_mkvs[tag] = full_path

    # Match episodes
    tasks = []
    for h_file in hardsub_files:
        tag = find_season_ep_tag(os.path.basename(h_file))
        if not tag:
            continue
        
        # Check filter
        if selected_episodes and tag not in selected_episodes:
            continue

        ref_srt = target_srts.get(tag)
        if not ref_srt:
            # Try looking in hardsub_dir
            candidate = os.path.splitext(h_file)[0] + ".vi.srt"
            if os.path.exists(candidate):
                ref_srt = candidate

        if not ref_srt:
            print(f"⚠️  [Skip] No reference SRT found for {tag} ({os.path.basename(h_file)})")
            continue

        # Determine output path
        # Prefer putting alongside target MKV in target_dir
        target_mkv = target_mkvs.get(tag)
        if target_mkv:
            out_base = os.path.splitext(target_mkv)[0]
            out_srt = f"{out_base}.vi.OCR.srt"
        else:
            ref_base = os.path.splitext(ref_srt)[0]
            if ref_base.endswith(".vi"):
                out_srt = f"{ref_base[:-3]}.vi.OCR.srt"
            else:
                out_srt = f"{ref_base}.vi.OCR.srt"

        tasks.append({
            "tag": tag,
            "video": h_file,
            "ref_srt": ref_srt,
            "out_srt": out_srt
        })

    total_tasks = len(tasks)
    print(f"📋 Found {total_tasks} matching episodes ready to process.")
    if limit and limit > 0:
        tasks = tasks[:limit]
        print(f"⚙️  Limited to {len(tasks)} episodes.")

    success_count = 0
    skipped_count = 0
    fail_count = 0
    start_total_time = time.time()

    for idx, t in enumerate(tasks, 1):
        print("\n" + "-" * 70)
        print(f"▶️  [{idx:02d}/{len(tasks):02d}] Episode Tag: {t['tag']}")

        # Check resume
        if resume and os.path.exists(t["out_srt"]) and os.path.getsize(t["out_srt"]) > 1024:
            print(f"⏩ [Skipped] Output already exists and valid: {os.path.basename(t['out_srt'])}")
            skipped_count += 1
            continue

        t0 = time.time()
        ok = process_video_with_ref(
            video_path=t["video"],
            ref_srt_path=t["ref_srt"],
            out_srt_path=t["out_srt"],
            api_key=api_key,
            model=model,
            batch_size=batch_size,
            crop_filter=crop,
            delay_sec=delay_sec,
            fallback_ref=fallback_ref
        )
        elapsed = time.time() - t0

        if ok:
            success_count += 1
            print(f"✨ Completed in {elapsed:.1f}s")
        else:
            fail_count += 1
            print(f"❌ Failed after {elapsed:.1f}s")

    total_time = time.time() - start_total_time
    print("\n" + "=" * 70)
    print("🏁 HARDSUB-EXTRACTOR: BATCH EXECUTION SUMMARY")
    print("=" * 70)
    print(f"⏱️  Total Duration: {total_time/60:.1f} minutes")
    print(f"✅ Success:        {success_count} episodes")
    print(f"⏩ Skipped:        {skipped_count} episodes")
    print(f"❌ Failed:         {fail_count} episodes")
    print("=" * 70)
    return fail_count == 0

def main():
    parser = argparse.ArgumentParser(description="Batch Hardsub OCR Extractor")
    parser.add_argument("--hardsub-dir", required=True, help="Directory containing hardsub video files")
    parser.add_argument("--target-dir", required=True, help="Target library directory (Season 1, Specials, etc.)")
    parser.add_argument("--api-key", default=None, help="Gemini API Key (default: loads from ~/.env)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model (default: gemini-3.5-flash-lite)")
    parser.add_argument("--batch-size", type=int, default=15, help="Batch size (default: 15)")
    parser.add_argument("--crop", default=DEFAULT_CROP, help="FFmpeg crop filter")
    parser.add_argument("--sleep", type=float, default=1.5, help="Delay between batches in seconds")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of episodes to process")
    parser.add_argument("--episodes", default=None, help="Comma-separated episode tags e.g. S01E01,S01E02")
    parser.add_argument("--no-resume", action="store_true", help="Overwrite existing output files")
    parser.add_argument("--fallback-ref", action="store_true", help="Fallback to ref text when hardsub is absent")

    args = parser.parse_args()
    selected = [ep.strip().upper() for ep in args.episodes.split(",")] if args.episodes else None

    run_batch(
        hardsub_dir=args.hardsub_dir,
        target_dir=args.target_dir,
        api_key=args.api_key,
        model=args.model,
        batch_size=args.batch_size,
        crop=args.crop,
        delay_sec=args.sleep,
        resume=not args.no_resume,
        limit=args.limit,
        selected_episodes=selected,
        fallback_ref=args.fallback_ref
    )

if __name__ == "__main__":
    main()
