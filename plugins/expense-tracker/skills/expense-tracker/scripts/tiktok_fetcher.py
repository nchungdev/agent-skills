#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TikTok Shop Order Fetcher for Expense Tracker Skill
- Tự động mở trình duyệt Chrome cho người dùng quét QR / đăng nhập TikTok
- Lưu session vào ~/.expense_tracker/tiktok_session.json
- Tự động kéo lịch sử đơn hàng từ TikTok Shop Web / API và chuẩn hoá dữ liệu
"""

import os
import sys
import json
import time
import argparse
import urllib.request
from datetime import datetime

SESSION_DIR = os.path.expanduser("~/.expense_tracker")
SESSION_FILE = os.path.join(SESSION_DIR, "tiktok_session.json")

def ensure_session_dir():
    os.makedirs(SESSION_DIR, exist_ok=True)

def load_saved_session():
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("cookies"):
                    return data
        except Exception as e:
            print(f"⚠️ Không đọc được session đã lưu: {e}")
    return None

def save_session(cookies_dict):
    ensure_session_dir()
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "updated_at": datetime.now().isoformat(),
            "cookies": cookies_dict
        }, f, indent=2)
    print(f"💾 Đã lưu phiên đăng nhập TikTok Shop vào {SESSION_FILE}")

def run_browser_login_and_fetch():
    """Mở trình duyệt cho người dùng quét mã QR đăng nhập TikTok và trích xuất đơn hàng trực tiếp."""
    print("🌐 Đang chuẩn bị trình duyệt đăng nhập TikTok Shop...")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("⚠️ Chưa tìm thấy thư viện 'playwright'. Đang tự động cài đặt...")
        os.system(f"{sys.executable} -m pip install playwright")
        os.system(f"{sys.executable} -m playwright install chromium")
        from playwright.sync_api import sync_playwright

    all_orders = []

    with sync_playwright() as p:
        print("🚀 Đang mở cửa sổ Google Chrome / Chromium...")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            locale="vi-VN"
        )
        page = context.new_page()

        print("\n========================================================")
        print("👉 VUI LÒNG QUÉT MÃ QR HOẶC ĐĂNG NHẬP TRÊN CỬA SỔ TIKTOK")
        print("========================================================\n")

        # Điều hướng đến trang đơn hàng TikTok
        page.goto("https://www.tiktok.com/order/list")

        max_wait = 300 # 5 phút
        start_t = time.time()
        logged_in = False

        while time.time() - start_t < max_wait:
            cookies = context.cookies()
            cookie_dict = {c["name"]: c["value"] for c in cookies if "tiktok.com" in c.get("domain", "")}

            if "sessionid" in cookie_dict or "sid_tt" in cookie_dict:
                logged_in = True
                save_session(cookie_dict)
                print("✅ Đăng nhập TikTok thành công!")
                time.sleep(2)
                break
            time.sleep(1)

        if not logged_in:
            browser.close()
            raise TimeoutError("Quá thời gian chờ đăng nhập (5 phút).")

        # Quét đơn hàng từ DOM / API
        print("📦 Đang trích xuất danh sách đơn hàng TikTok Shop...")
        page.wait_for_timeout(3000)

        # Cuộn trang để tải thêm đơn hàng
        for _ in range(5):
            page.mouse.wheel(0, 3000)
            page.wait_for_timeout(1500)

        # Trích xuất dữ liệu DOM
        order_elements = page.query_selector_all("[data-e2e='order-item'], .order-card, div[class*='OrderCard']")
        print(f"📦 Tìm thấy {len(order_elements)} khối đơn hàng hiển thị...")

        for idx, el in enumerate(order_elements):
            text_content = el.inner_text()
            lines = [l.strip() for l in text_content.split("\n") if l.strip()]
            
            # Phân tích text đơn giản
            title = lines[0] if len(lines) > 0 else f"TikTok Order #{idx+1}"
            amount = 0
            for line in lines:
                if "₫" in line or "đ" in line or "VND" in line:
                    clean_num = ''.join(c for c in line if c.isdigit())
                    if clean_num:
                        amount = float(clean_num)
                        break

            all_orders.append({
                "id": f"tiktok_{int(time.time())}_{idx}",
                "source": "tiktok",
                "platform": "TikTok Shop",
                "order_id": f"TT_{idx+1}",
                "merchant": "TikTok Shop",
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "month": datetime.now().strftime("%Y-%m"),
                "timestamp": int(time.time()),
                "amount": amount,
                "currency": "VND",
                "status": "Hoàn thành",
                "items_summary": title,
                "items_list": [title],
                "date_quality": "estimated_from_page"
            })

        browser.close()

    return all_orders

def main():
    parser = argparse.ArgumentParser(description="TikTok Shop Order Fetcher for Expense Tracker")
    parser.add_argument("--output-dir", default="./expense_data", help="Thư mục xuất kết quả")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    orders = run_browser_login_and_fetch()

    out_file = os.path.join(args.output_dir, "tiktok_orders.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 Hoàn tất! Đã lấy thành công {len(orders)} đơn hàng TikTok Shop.")
    print(f"📁 Kết quả được lưu tại: {out_file}")

if __name__ == "__main__":
    main()
