#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shopee Order Fetcher for Expense Tracker Skill
- Tự động mở trình duyệt Chrome cho người dùng quét QR / đăng nhập
- Lưu session vào ~/.expense_tracker/shopee_session.json (chỉ đăng nhập 1 lần)
- Tự động kéo lịch sử đơn hàng từ Shopee Internal API và chuẩn hoá dữ liệu
"""

import os
import sys
import json
import time
import argparse
import urllib.request
import urllib.parse
from datetime import datetime

SESSION_DIR = os.path.expanduser("~/.expense_tracker")
SESSION_FILE = os.path.join(SESSION_DIR, "shopee_session.json")

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
    print(f"💾 Đã lưu phiên đăng nhập Shopee vào {SESSION_FILE}")

def run_browser_login():
    """Mở trình duyệt cho người dùng quét mã QR đăng nhập Shopee."""
    print("🌐 Đang chuẩn bị trình duyệt đăng nhập Shopee...")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("⚠️ Chưa tìm thấy thư viện 'playwright'. Đang tự động cài đặt...")
        os.system(f"{sys.executable} -m pip install playwright")
        os.system(f"{sys.executable} -m playwright install chromium")
        from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        print("🚀 Đang mở cửa sổ Google Chrome / Chromium...")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            locale="vi-VN"
        )
        page = context.new_page()
        
        print("\n========================================================")
        print("👉 VUI LÒNG QUÉT MÃ QR HOẶC ĐĂNG NHẬP TRÊN CỬA SỔ CHROME")
        print("========================================================\n")
        
        page.goto("https://shopee.vn/buyer/login?next=https%3A%2F%2Fshopee.vn%2Fuser%2Fpurchase")
        
        # Chờ người dùng đăng nhập thành công (chuyển hướng sang purchase hoặc có cookie SPC_EC / SPC_ST)
        max_wait = 300 # 5 phút
        start_t = time.time()
        logged_in = False
        
        while time.time() - start_t < max_wait:
            cookies = context.cookies()
            cookie_dict = {c["name"]: c["value"] for c in cookies if "shopee.vn" in c.get("domain", "")}
            
            # Kiểm tra cookie định danh đăng nhập
            if "SPC_EC" in cookie_dict or "SPC_ST" in cookie_dict or "SPC_U" in cookie_dict:
                if "/user/purchase" in page.url or "shopee.vn" in page.url:
                    logged_in = True
                    save_session(cookie_dict)
                    print("✅ Đăng nhập Shopee thành công!")
                    time.sleep(1)
                    break
            time.sleep(1)
            
        browser.close()
        
        if not logged_in:
            raise TimeoutError("Quá thời gian chờ đăng nhập (5 phút).")
        return cookie_dict

def cookie_dict_to_header(c_dict):
    return "; ".join([f"{k}={v}" for k, v in c_dict.items()])

def fetch_orders(cookies_dict, limit=20, max_pages=30, since_date=None):
    """Kéo danh sách đơn hàng từ Shopee API."""
    cookie_str = cookie_dict_to_header(cookies_dict)
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Referer": "https://shopee.vn/user/purchase",
        "x-shopee-language": "vi",
        "x-api-source": "pc",
        "Cookie": cookie_str,
        "Accept": "application/json"
    }

    all_orders = []
    offset = 0
    page_count = 0

    print(f"📦 Đang tải danh sách đơn hàng Shopee...")

    while page_count < max_pages:
        url = f"https://shopee.vn/api/v4/order/get_all_order_and_checkout_list?limit={limit}&offset={offset}"
        req = urllib.request.Request(url, headers=headers)
        
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                res_data = json.loads(response.read().decode("utf-8"))
        except Exception as e:
            print(f"❌ Lỗi khi gọi Shopee API: {e}")
            break

        order_data = res_data.get("data", {}).get("order_data", {})
        details_list = order_data.get("details_list", [])

        if not details_list:
            break

        for item in details_list:
            order_id = str(item.get("order_id") or item.get("checkout_id") or "")
            create_time = item.get("create_time", 0)
            dt = datetime.fromtimestamp(create_time) if create_time else None
            date_str = dt.strftime("%Y-%m-%d %H:%M:%S") if dt else "Unspecified"
            month_str = dt.strftime("%Y-%m") if dt else "Unspecified"

            raw_amount = item.get("final_total", 0) or item.get("total_price", 0)
            amount = raw_amount / 100000.0 if raw_amount > 10000 else float(raw_amount)

            # Lấy tên mặt hàng và shop
            product_names = []
            shop_name = item.get("shop_info", {}).get("shop_name", "Shopee Seller")
            
            ext_info = item.get("list_order_ext_info") or []
            for ext in ext_info:
                name = ext.get("item_info", {}).get("name")
                if name:
                    product_names.append(name)

            status_label = item.get("status", {}).get("status_label", "Hoàn thành")
            
            # Lọc trạng thái đã hủy
            if "hủy" in status_label.lower() or "cancel" in status_label.lower():
                continue

            # Kiểm tra mốc thời gian since_date
            if since_date and dt and dt.strftime("%Y-%m-%d") < since_date:
                print(f"⏱️ Đã đạt mốc thời gian {since_date}, dừng quét.")
                return all_orders

            order_record = {
                "id": f"shopee_{order_id}",
                "source": "shopee",
                "platform": "Shopee",
                "order_id": order_id,
                "merchant": f"Shopee - {shop_name}",
                "date": date_str,
                "month": month_str,
                "timestamp": create_time,
                "amount": amount,
                "currency": "VND",
                "status": status_label,
                "items_summary": " | ".join(product_names) if product_names else "Đơn hàng Shopee",
                "items_list": product_names,
                "date_quality": "exact"
            }
            all_orders.append(order_record)

        print(f"   -> Đã tải {len(all_orders)} đơn hàng...")
        offset += limit
        page_count += 1
        time.sleep(0.5)

    return all_orders

def main():
    parser = argparse.ArgumentParser(description="Shopee Order Fetcher for Expense Tracker")
    parser.add_argument("--output-dir", default="./expense_data", help="Thư mục xuất kết quả")
    parser.add_argument("--force-login", action="store_true", help="Bắt buộc quét lại mã QR")
    parser.add_argument("--since", default=None, help="Lọc đơn từ ngày YYYY-MM-DD")
    parser.add_argument("--max-pages", type=int, default=20, help="Số trang tối đa cần quét")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    session = None if args.force_login else load_saved_session()
    
    if not session or not session.get("cookies"):
        print("🔑 Chưa có phiên đăng nhập Shopee hợp lệ. Bắt đầu đăng nhập...")
        cookies = run_browser_login()
    else:
        print("🔑 Đang sử dụng phiên đăng nhập Shopee đã lưu...")
        cookies = session["cookies"]

    orders = fetch_orders(cookies, max_pages=args.max_pages, since_date=args.since)

    # Nếu token hết hạn (0 đơn), thử đăng nhập lại
    if len(orders) == 0 and not args.force_login:
        print("⚠️ Session có thể đã hết hạn. Đang mở trình duyệt để làm mới phiên...")
        cookies = run_browser_login()
        orders = fetch_orders(cookies, max_pages=args.max_pages, since_date=args.since)

    out_file = os.path.join(args.output_dir, "shopee_orders.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 Hoàn tất! Đã lấy thành công {len(orders)} đơn hàng Shopee.")
    print(f"📁 Kết quả được lưu tại: {out_file}")

if __name__ == "__main__":
    main()
