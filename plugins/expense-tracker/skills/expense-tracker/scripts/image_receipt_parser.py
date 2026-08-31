#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Image Receipt & Invoice Parser for Expense Tracker
- Quét danh sách hình ảnh (hoá đơn giấy, biên lai POS, ảnh chuyển khoản ngân hàng/ví điện tử)
- Đọc thông tin ngày tháng, số tiền, đơn vị thụ hưởng, nội dung
- Xử lý thông minh ảnh thiếu ngày: EXIF metadata / File timestamp fallback hoặc gán nhãn 'Unspecified'
- Xuất dữ liệu giao dịch chuẩn hoá
"""

import os
import sys
import re
import json
import time
import argparse
import subprocess
from datetime import datetime

SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".bmp", ".tiff"}

def get_file_metadata_date(image_path):
    """Trích xuất ngày tạo ảnh từ EXIF / macOS mdls / sips hoặc file mtime."""
    # 1. Thử dùng lệnh `mdls` trên macOS để lấy ngày chụp ảnh gốc
    try:
        res = subprocess.run(
            ["mdls", "-name", "kMDItemContentCreationDate", "-raw", image_path],
            capture_output=True, text=True, timeout=3
        )
        val = res.stdout.strip()
        if val and val != "(null)":
            # Định dạng: 2026-08-15 14:30:00 +0000
            dt_part = val.split(" +")[0].strip()
            dt = datetime.strptime(dt_part, "%Y-%m-%d %H:%M:%S")
            return dt, "exif_metadata"
    except Exception:
        pass

    # 2. Fallback sang ngày sửa đổi file mtime
    try:
        mtime = os.path.getmtime(image_path)
        dt = datetime.fromtimestamp(mtime)
        return dt, "file_mtime"
    except Exception:
        pass

    return None, "unspecified"

def parse_date_from_text(text):
    """Tìm ngày tháng trong nội dung text OCR."""
    patterns = [
        r'(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})',        # DD/MM/YYYY hoặc DD-MM-YYYY
        r'(\d{4})[/.-](\d{1,2})[/.-](\d{1,2})',        # YYYY-MM-DD
        r'ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})', # ngày DD tháng MM năm YYYY
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            groups = m.groups()
            try:
                if len(groups[0]) == 4: # YYYY-MM-DD
                    year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                else: # DD-MM-YYYY
                    day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                if 1 <= month <= 12 and 1 <= day <= 31 and 2000 <= year <= 2035:
                    return f"{year:04d}-{month:02d}-{day:02d}", f"{year:04d}-{month:02d}"
            except Exception:
                continue
    return None, None

def parse_amount_from_text(text):
    """Tìm số tiền từ nội dung text."""
    # Tìm các mẫu số tiền thông dụng: 120.000 VND, 50,000đ, 1.500.000 VNĐ, $25.00
    patterns = [
        r'(?:số\s*tiền|tổng\s*cộng|thành\s*tiền|total|amount|giá|thanh\s*toán)[\s:]*([0-9]{1,3}(?:[.,][0-9]{3})*(?:[.,][0-9]{2})?)\s*(?:đ|vnd|vnđ|\$)?',
        r'([0-9]{1,3}(?:[.,][0-9]{3})+)\s*(?:đ|vnd|vnđ)',
        r'(?:đ|vnd|vnđ|\$)\s*([0-9]{1,3}(?:[.,][0-9]{3})+)',
    ]
    for p in patterns:
        matches = re.finditer(p, text, re.IGNORECASE)
        for m in matches:
            num_str = m.group(1).replace(".", "").replace(",", "")
            try:
                val = float(num_str)
                if val > 100: # Lọc bỏ các số nhỏ không phải tiền VND
                    return val
            except Exception:
                continue
    return 0.0

def process_single_image(image_path, ocr_text=None):
    """Phân tích một hình ảnh đơn lẻ."""
    file_name = os.path.basename(image_path)
    meta_dt, dt_source = get_file_metadata_date(image_path)

    date_str = "Unspecified"
    month_str = "Unspecified"
    date_quality = "unspecified"
    amount = 0.0
    merchant = "Hoá đơn / Biên lai"
    items_summary = file_name

    if ocr_text:
        d_str, m_str = parse_date_from_text(ocr_text)
        if d_str:
            date_str = d_str
            month_str = m_str
            date_quality = "exact_ocr"
        amt = parse_amount_from_text(ocr_text)
        if amt > 0:
            amount = amt

    # Nếu OCR không tìm thấy ngày, sử dụng Metadata Fallback
    if date_quality == "unspecified" and meta_dt:
        date_str = meta_dt.strftime("%Y-%m-%d %H:%M:%S")
        month_str = meta_dt.strftime("%Y-%m")
        date_quality = f"fallback_{dt_source}"

    # Trích xuất gợi ý merchant từ tên file
    name_clean = re.sub(r'[\-_.]+', ' ', os.path.splitext(file_name)[0])
    if any(k in name_clean.lower() for k in ["vcb", "vietcombank", "techcombank", "mbbank", "tcb", "tpbank"]):
        merchant = f"Chuyển khoản ({name_clean})"
    elif any(k in name_clean.lower() for k in ["momo", "zalopay", "viettelpay"]):
        merchant = f"Ví điện tử ({name_clean})"

    record = {
        "id": f"img_{abs(hash(image_path)) % 10000000}",
        "source": "image",
        "platform": "Image / Offline Receipt",
        "order_id": file_name,
        "merchant": merchant,
        "date": date_str,
        "month": month_str,
        "timestamp": int(meta_dt.timestamp()) if meta_dt else int(time.time()),
        "amount": amount,
        "currency": "VND",
        "status": "Hoàn thành",
        "items_summary": items_summary,
        "items_list": [items_summary],
        "date_quality": date_quality,
        "image_path": os.path.abspath(image_path)
    }
    return record

def scan_images(target_path):
    """Quét ảnh từ 1 file hoặc cả thư mục."""
    image_files = []
    if os.path.isfile(target_path):
        ext = os.path.splitext(target_path)[1].lower()
        if ext in SUPPORTED_EXTS:
            image_files.append(target_path)
    elif os.path.isdir(target_path):
        for root, _, files in os.walk(target_path):
            for f in sorted(files):
                ext = os.path.splitext(f)[1].lower()
                if ext in SUPPORTED_EXTS:
                    image_files.append(os.path.join(root, f))
    return image_files

def main():
    parser = argparse.ArgumentParser(description="Image Receipt Parser for Expense Tracker")
    parser.add_argument("--input-dir", required=True, help="Đường dẫn file ảnh hoặc thư mục chứa ảnh")
    parser.add_argument("--output-dir", default="./expense_data", help="Thư mục xuất kết quả")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    images = scan_images(args.input_dir)

    print(f"📸 Tìm thấy {len(images)} hình ảnh cần phân tích...")
    results = []
    for img in images:
        rec = process_single_image(img)
        results.append(rec)

    out_file = os.path.join(args.output_dir, "image_expenses.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ Đã xử lý xong {len(results)} hình ảnh. Dữ liệu lưu tại: {out_file}")

if __name__ == "__main__":
    main()
