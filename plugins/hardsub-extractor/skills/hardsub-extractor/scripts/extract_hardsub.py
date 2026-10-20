#!/usr/bin/env python3
"""
hardsub-extractor: High-accuracy Hardsub OCR & Timing Synchronization Engine
Powered by FFmpeg memory streaming and Gemini Multimodal Vision API.
"""

import os
import sys
import re
import json
import time
import argparse
import subprocess
import base64
import urllib.request
import urllib.error

DEFAULT_MODEL = "gemini-3.5-flash-lite"
DEFAULT_CROP = "crop=in_w:in_h*0.25:0:in_h*0.75"

def load_gemini_api_key(explicit_key=None):
    if explicit_key:
        return explicit_key.strip()
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key:
        return key
    env_path = os.path.expanduser("~/.env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("GEMINI_API_KEY="):
                    return line.strip().split("=", 1)[1].strip()
    return ""

# 16x16 minimal black JPEG fallback for out-of-bounds frames
DUMMY_BLACK_JPEG = (
    b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x02\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06'
    b'\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a'
    b'\x1f\x1e\x1d\x1a\x1c\x1c $.\' \",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00\x10'
    b'\x00\x10\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00'
    b'\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00'
    b'\xbf\x80\xff\xd9'
)

def srt_time_to_sec(tc):
    tc = tc.strip().replace(',', '.')
    parts = tc.split(':')
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    return float(tc)

def sec_to_srt_time(sec):
    if sec < 0:
        sec = 0
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int(round((sec - int(sec)) * 1000))
    if ms >= 1000:
        s += 1
        ms -= 1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def parse_srt(path):
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    blocks = re.split(r'\n\s*\n', content.strip())
    entries = []
    for block in blocks:
        lines = [l.strip() for l in block.split('\n') if l.strip()]
        if len(lines) >= 2:
            tc_line = None
            text_lines = []
            if '-->' in lines[0]:
                tc_line = lines[0]
                text_lines = lines[1:]
            elif len(lines) >= 2 and '-->' in lines[1]:
                tc_line = lines[1]
                text_lines = lines[2:]
            
            if tc_line:
                parts = tc_line.split('-->')
                start_str = parts[0].strip()
                end_str = parts[1].strip().split()[0]
                try:
                    start_sec = srt_time_to_sec(start_str)
                    end_sec = srt_time_to_sec(end_str)
                    entries.append({
                        'start_str': start_str,
                        'end_str': end_str,
                        'start_sec': start_sec,
                        'end_sec': end_sec,
                        'ref_text': '\n'.join(text_lines)
                    })
                except Exception:
                    pass
    return entries

def extract_frame_bytes(video_path, timestamp_sec, crop_filter=DEFAULT_CROP):
    if crop_filter and not crop_filter.startswith("crop="):
        crop_filter = f"crop={crop_filter}"
    cmd = [
        'ffmpeg', '-y', '-ss', f"{timestamp_sec:.3f}",
        '-i', video_path,
        '-vframes', '1',
        '-filter:v', crop_filter,
        '-f', 'image2pipe',
        '-vcodec', 'mjpeg',
        '-'
    ]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    if p.returncode == 0 and len(p.stdout) > 0:
        return p.stdout
    return None

def call_gemini_vision_batch(image_bytes_list, api_key, model=DEFAULT_MODEL, max_retries=3):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    parts = [
        {
            "text": (
                f"Dưới đây là {len(image_bytes_list)} ảnh cắt vùng phụ đề tiếng Việt của video phim hoạt hình.\n"
                f"Nhiệm vụ: Đọc chính xác nội dung phụ đề tiếng Việt trên từng ảnh theo thứ tự đánh số [1] đến [{len(image_bytes_list)}].\n"
                "Quy tắc nghiêm ngặt:\n"
                "1. Nếu ảnh có phụ đề tiếng Việt: Chép lại đúng 100% nội dung chữ, bảo toàn dấu thanh hỏi/ngã/sắc/huyền/nặng/ư/ơ/đ.\n"
                "2. Nếu ảnh KHÔNG có phụ đề (chỉ có hình nền hoạt hình) hoặc chữ logo/credit đài, trả về chuỗi rỗng \"\".\n"
                "3. Trả về đúng định dạng JSON Array chứa các object:\n"
                "[{\"id\": 1, \"text\": \"...\"}, {\"id\": 2, \"text\": \"...\"}]\n"
                "Tuyệt đối không giải thích, không bọc markdown ngoài JSON."
            )
        }
    ]
    for idx, img_bytes in enumerate(image_bytes_list, 1):
        b64 = base64.b64encode(img_bytes).decode('utf-8')
        parts.append({"text": f"Ảnh {idx}:"})
        parts.append({"inline_data": {"mime_type": "image/jpeg", "data": b64}})

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.1
        }
    }
    data = json.dumps(payload).encode('utf-8')

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                res = json.loads(resp.read().decode('utf-8'))
                text_out = res['candidates'][0]['content']['parts'][0]['text']
                items = json.loads(text_out)
                # Map back to dict
                result_map = {}
                for item in items:
                    result_map[int(item.get('id', 0))] = item.get('text', '').strip()
                return [result_map.get(i, "") for i in range(1, len(image_bytes_list) + 1)]
        except Exception as e:
            time.sleep(2 * (attempt + 1))
            if attempt == max_retries - 1:
                print(f"      [Warning] API call failed after {max_retries} retries: {e}", file=sys.stderr)
                return ["" for _ in range(len(image_bytes_list))]

def clean_ocr_text(text):
    if not text:
        return ""
    text = text.replace('""', '').strip()
    if text.upper() in ["[NONE]", "NONE", "NULL", "KHÔNG CÓ", "[KHÔNG CÓ PHỤ ĐỀ]"]:
        return ""
    return text

def process_video_with_ref(video_path, ref_srt_path, out_srt_path, api_key=None, 
                           model=DEFAULT_MODEL, batch_size=15, crop_filter=DEFAULT_CROP,
                           delay_sec=1.5, fallback_ref=False):
    api_key = load_gemini_api_key(api_key)
    if not api_key:
        print("❌ Error: GEMINI_API_KEY chưa được cấu hình! Hãy chạy `hardsub-extractor setup` hoặc thêm vào ~/.env", file=sys.stderr)
        return False
    print(f"🎬 Processing: {os.path.basename(video_path)}")
    print(f"   Ref SRT:    {os.path.basename(ref_srt_path)}")
    print(f"   Output:     {os.path.basename(out_srt_path)}")

    entries = parse_srt(ref_srt_path)
    if not entries:
        print(f"❌ Error: Could not parse reference SRT {ref_srt_path}")
        return False

    total_entries = len(entries)
    print(f"   Found {total_entries} reference dialogue intervals.")

    extracted_texts = []
    batches = [entries[i:i + batch_size] for i in range(0, total_entries, batch_size)]
    total_batches = len(batches)

    start_time = time.time()
    for b_idx, batch in enumerate(batches, 1):
        img_bytes_list = []
        for item in batch:
            # Sample at 40% into the duration to avoid edge transitions
            duration = item['end_sec'] - item['start_sec']
            sample_t = item['start_sec'] + min(0.6, max(0.2, duration * 0.4))
            img = extract_frame_bytes(video_path, sample_t, crop_filter)
            if not img:
                img = DUMMY_BLACK_JPEG
            img_bytes_list.append(img)

        # Send batch to Gemini
        ocr_texts = call_gemini_vision_batch(img_bytes_list, api_key, model)
        extracted_texts.extend(ocr_texts)

        elapsed = time.time() - start_time
        pct = (b_idx / total_batches) * 100
        print(f"   ↳ Batch [{b_idx:02d}/{total_batches:02d}] ({len(batch)} frames) - {pct:.1f}% done ({elapsed:.1f}s)", flush=True)
        if b_idx < total_batches and delay_sec > 0:
            time.sleep(delay_sec)

    # Post-processing & Merging
    final_events = []
    for item, raw_text in zip(entries, extracted_texts):
        ocr_clean = clean_ocr_text(raw_text)
        if not ocr_clean:
            if fallback_ref:
                ocr_clean = item['ref_text']
            else:
                continue # Skip empty entries
        
        # Check merge with previous event if text is identical (spanning lines)
        if final_events and final_events[-1]['text'] == ocr_clean:
            # Extend end time of previous event if gap is small (< 1.5s)
            if item['start_sec'] - final_events[-1]['end_sec'] <= 1.5:
                final_events[-1]['end_sec'] = item['end_sec']
                continue
        
        final_events.append({
            'start_sec': item['start_sec'],
            'end_sec': item['end_sec'],
            'text': ocr_clean
        })

    # Write output SRT
    os.makedirs(os.path.dirname(os.path.abspath(out_srt_path)), exist_ok=True)
    with open(out_srt_path, 'w', encoding='utf-8') as f:
        for idx, ev in enumerate(final_events, 1):
            start_tc = sec_to_srt_time(ev['start_sec'])
            end_tc = sec_to_srt_time(ev['end_sec'])
            f.write(f"{idx}\n{start_tc} --> {end_tc}\n{ev['text']}\n\n")

    print(f"✅ Successfully exported: {out_srt_path}")
    print(f"   Lines captured: {len(final_events)}/{total_entries} ({len(final_events)/total_entries*100:.1f}%)")
    return True

def main():
    parser = argparse.ArgumentParser(description="Extract hardsub text via Gemini Vision OCR & sync timing")
    parser.add_argument("--video", required=True, help="Path to hardsub video file")
    parser.add_argument("--ref-srt", required=True, help="Path to reference SRT file for timecodes")
    parser.add_argument("--out", required=True, help="Path to output .vi.ocr.srt file")
    parser.add_argument("--api-key", default=None, help="Gemini API Key (default: loads from ~/.env)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model (default: gemini-3.5-flash-lite)")
    parser.add_argument("--batch-size", type=int, default=15, help="Batch size (default: 15)")
    parser.add_argument("--crop", default=DEFAULT_CROP, help="FFmpeg crop filter")
    parser.add_argument("--sleep", type=float, default=1.5, help="Delay between batches in seconds")
    parser.add_argument("--fallback-ref", action="store_true", help="Fallback to ref text when hardsub is absent")

    args = parser.parse_args()
    success = process_video_with_ref(
        video_path=args.video,
        ref_srt_path=args.ref_srt,
        out_srt_path=args.out,
        api_key=args.api_key,
        model=args.model,
        batch_size=args.batch_size,
        crop_filter=args.crop,
        delay_sec=args.sleep,
        fallback_ref=args.fallback_ref
    )
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
