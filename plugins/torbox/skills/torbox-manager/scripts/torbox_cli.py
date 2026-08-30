#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TorBox CLI Manager — Full Interactive Auth, Smart Download Strategy (5GB Threshold),
Single & Multi-file Resumable Downloads, and Randomized Jitter Backoff (5s->90s)
torbox-manager — torbox_cli.py
"""

import sys
import os
import argparse
import json
import subprocess
import zipfile
import re
import shutil
import webbrowser
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from torbox_client import TorBoxClient, CONFIG_FILE

ZIP_THRESHOLD_GB = 5.0  # Chuẩn cố định: < 5 GB tải Zip, >= 5 GB tải Single-File
MAX_CONCURRENT_DOWNLOADS = 2

def format_size(bytes_val):
    if not bytes_val:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} PB"

def cmd_login(args):
    print("================================================================================")
    print("🔐 ĐĂNG NHẬP XÁC THỰC TÀI KHOẢN TORBOX (AUTHENTICATION)")
    print("================================================================================")
    token = args.token
    if not token:
        if args.browser:
            print("🌐 Đang mở trình duyệt tới trang cài đặt TorBox Settings để lấy API Token...")
            try:
                webbrowser.open("https://torbox.app/settings")
            except Exception:
                pass
        print("\n👉 Vui lòng lấy API Token của anh tại: https://torbox.app/settings (mục API / Account Token)")
        token = input("🔑 Nhập TorBox API Token / Key của anh: ").strip()
        
    if not token:
        print("❌ Lỗi: Bạn chưa nhập API Token. Đăng nhập bị hủy.")
        return

    client = TorBoxClient(api_key=token)
    res = client.get_user_info()
    if res.get("success"):
        data = res.get("data", {})
        email = data.get("email", "Unknown")
        plan_id = data.get("plan", 0)
        plan_name = "Pro / Standard" if plan_id >= 2 else ("Essential" if plan_id == 1 else "Free")
        expires = data.get("premium_expires_at", "N/A")
        TorBoxClient.save_api_key(token)
        print("\n🎉 ĐĂNG NHẬP THÀNH CÔNG 100%!")
        print(f"  • 👤 Email:         {email}")
        print(f"  • 📦 Gói cước:      {plan_name} (Plan ID: {plan_id})")
        print(f"  • ⏳ Hạn Premium:   {expires}")
        print(f"  • 📁 Cấu hình lưu:  {CONFIG_FILE}")
    else:
        print(f"\n❌ Xác thực thất bại: {res.get('error') or res.get('detail')}")

def cmd_logout(args):
    TorBoxClient.clear_api_key()
    print("👋 Đã đăng xuất và xóa sạch cấu hình TorBox API Key trên máy.")

def cmd_whoami(args):
    client = TorBoxClient(args.api_key)
    if not client.is_authenticated():
        print("⚠️ Bạn chưa đăng nhập TorBox. Vui lòng chạy: torbox login")
        return
    res = client.get_user_info()
    if res.get("success"):
        data = res.get("data", {})
        print("================================================================================")
        print("👤 THÔNG TIN TÀI KHOẢN TORBOX ĐANG ĐĂNG NHẬP")
        print("================================================================================")
        print(f"  • Email:             {data.get('email')}")
        print(f"  • Gói cước (Plan):   {data.get('plan')}")
        print(f"  • Hạn dùng Premium:  {data.get('premium_expires_at')}")
        print(f"  • Đã tải:            {format_size(data.get('total_bytes_downloaded', 0))}")
        print(f"  • Tổng số Torrents:  {data.get('torrents_downloaded', 0)} torrents")
    else:
        print(f"❌ Không thể lấy thông tin tài khoản: {res.get('error') or res.get('detail')}")

def cmd_list(args):
    client = TorBoxClient(args.api_key)
    if not client.is_authenticated():
        print("⚠️ Bạn chưa đăng nhập TorBox. Vui lòng chạy: torbox login")
        return
    res = client.list_torrents()
    if not res.get("success"):
        print(f"❌ Lỗi khi lấy danh sách: {res.get('error') or res.get('detail')}")
        return
    torrents = res.get("data", [])
    print("====================================================================================================")
    print(f"📋 DANH SÁCH TORRENTS TRÊN TORBOX ({len(torrents)} MỤC)")
    print("====================================================================================================")
    print(f"{'ID':<10} | {'TRẠNG THÁI':<12} | {'TIẾN ĐỘ':<8} | {'DUNG LƯỢNG':<10} | {'TÊN PHIM / TORRENT'}")
    print("-" * 100)
    for t in torrents:
        tid = str(t.get("id"))
        name = t.get("name", "Unknown")
        state = t.get("download_state", "unknown")
        prog = f"{t.get('progress', 0)*100:.1f}%" if t.get('progress', 0) <= 1 else f"{t.get('progress')}%"
        size = format_size(t.get("size", 0))
        state_icon = "🟢" if state in ["completed", "cached"] else ("🚀" if state == "downloading" else "⚠️")
        print(f"{tid:<10} | {state_icon} {state:<9} | {prog:<8} | {size:<10} | {name}")

def cmd_add(args):
    client = TorBoxClient(args.api_key)
    if not client.is_authenticated():
        print("⚠️ Bạn chưa đăng nhập TorBox. Vui lòng chạy: torbox login")
        return
    target = args.target.strip()
    if target.startswith("magnet:?"):
        print("🧲 Đang thêm Magnet Link vào TorBox...")
        res = client.add_torrent_magnet(target, seed=args.seed, allow_zip=True)
    elif os.path.exists(target) and target.endswith(".torrent"):
        print(f"📁 Đang tải file torrent lên TorBox: {os.path.basename(target)}...")
        res = client.add_torrent_file(target, seed=args.seed, allow_zip=True)
    else:
        print(f"❌ Target không hợp lệ: {target}")
        return
    if res.get("success"):
        data = res.get("data", {})
        print(f"✅ Thêm thành công! ID: {data.get('torrent_id')} | Hash: {data.get('hash')}")
    else:
        print(f"❌ Lỗi khi thêm torrent: {res.get('error') or res.get('detail')}")

def cmd_remove(args):
    client = TorBoxClient(args.api_key)
    if not client.is_authenticated():
        print("⚠️ Bạn chưa đăng nhập TorBox. Vui lòng chạy: torbox login")
        return
    for tid in args.torrent_ids:
        print(f"🗑️ Đang xóa torrent ID {tid} trên TorBox...")
        res = client.control_torrent(tid, operation="delete")
        if res.get("success"):
            print(f"✅ Đã xóa thành công torrent ID {tid}")
        else:
            print(f"❌ Lỗi khi xóa ID {tid}: {res.get('error') or res.get('detail')}")

def cmd_get_link(args):
    client = TorBoxClient(args.api_key)
    if not client.is_authenticated():
        print("⚠️ Bạn chưa đăng nhập TorBox. Vui lòng chạy: torbox login")
        return
    res = client.get_download_link(args.torrent_id, as_zip=args.zip)
    if res.get("success"):
        print(f"🔗 DIRECT DOWNLOAD LINK (CDN DDL):\n{res.get('data')}")
    else:
        print(f"❌ Lỗi lấy link: {res.get('error') or res.get('detail')}")

def cmd_download(args):
    client = TorBoxClient(args.api_key)
    if not client.is_authenticated():
        print("⚠️ Bạn chưa đăng nhập TorBox. Vui lòng chạy: torbox login")
        return
    
    # 1. Inspect torrent info
    res = client.list_torrents()
    target_torrent = None
    if res.get("success"):
        for t in res.get("data", []):
            if str(t.get("id")) == str(args.torrent_id):
                target_torrent = t
                break
                
    if not target_torrent:
        print(f"❌ Không tìm thấy torrent ID: {args.torrent_id}")
        return
        
    size_gb = target_torrent.get("size", 0) / (1024**3)
    dest_dir = os.path.abspath(args.out_dir or ".")
    os.makedirs(dest_dir, exist_ok=True)
    
    # Check threshold: < 5 GB -> Zip, >= 5 GB -> Single-file
    if size_gb < ZIP_THRESHOLD_GB and not args.force_single:
        print(f"📦 [CHIẾN LƯỢC ZIP] Dung lượng {size_gb:.2f} GB < {ZIP_THRESHOLD_GB} GB ➜ Tải nhanh trọn gói Zip...")
        res_dl = client.get_download_link(args.torrent_id, as_zip=True)
        if res_dl.get("success") and res_dl.get("data"):
            zip_file = os.path.join(dest_dir, f"torbox_{args.torrent_id}.zip")
            cmd_aria = ["aria2c", "-c", "--continue=true", "-x4", "-s4", "-k1M", f"--dir={dest_dir}", f"--out=torbox_{args.torrent_id}.zip", res_dl.get("data")]
            subprocess.run(cmd_aria)
            if os.path.exists(zip_file) and zipfile.is_zipfile(zip_file):
                print("📦 Đang giải nén...")
                with zipfile.ZipFile(zip_file, 'r') as zf:
                    zf.extractall(dest_dir)
                os.remove(zip_file)
                print("✅ Hoàn tất giải nén và dọn dẹp!")
    else:
        print(f"⚡ [CHIẾN LƯỢC SINGLE-FILE] Dung lượng {size_gb:.2f} GB >= {ZIP_THRESHOLD_GB} GB ➜ Tải cuốn chiếu từng tập (Max 2 luồng, nghỉ 5s-90s)...")
        files = target_torrent.get("files", [])
        for f in files:
            if any(f.get("name", "").lower().endswith(ext) for ext in [".mkv", ".mp4", ".avi", ".ts"]):
                # Request single file link with polite pause
                time.sleep(round(random.uniform(1.5, 4.5), 2))
                res_link = client.get_download_link(args.torrent_id, file_id=f.get("id"), as_zip=False)
                if res_link.get("success") and res_link.get("data"):
                    fname = os.path.basename(f.get("name"))
                    print(f"📥 Đang tải: {fname}...")
                    subprocess.run(["aria2c", "-c", "--continue=true", "-x4", "-s4", "-k1M", f"--dir={dest_dir}", f"--out={fname}", res_link.get("data")])
                else:
                    backoff = round(random.uniform(5.0, 90.0), 1)
                    print(f"⏳ Nghỉ ngẫu nhiên {backoff}s tránh rate limit...")
                    time.sleep(backoff)

def main():
    parser = argparse.ArgumentParser(description="TorBox CLI Manager — Quản lý TorBox toàn diện (Ngưỡng 5GB & Random Jitter Backoff 5s-90s)")
    parser.add_argument("--api-key", help="TorBox API Key")
    subparsers = parser.add_subparsers(dest="command")
    
    p_login = subparsers.add_parser("login")
    p_login.add_argument("--token", "-t")
    p_login.add_argument("--browser", "-b", action="store_true", default=False)
    p_login.set_defaults(func=cmd_login)
    
    p_logout = subparsers.add_parser("logout")
    p_logout.set_defaults(func=cmd_logout)
    
    p_whoami = subparsers.add_parser("whoami")
    p_whoami.set_defaults(func=cmd_whoami)
    
    p_list = subparsers.add_parser("list")
    p_list.set_defaults(func=cmd_list)
    
    p_add = subparsers.add_parser("add")
    p_add.add_argument("target")
    p_add.add_argument("--seed", type=int, default=1)
    p_add.set_defaults(func=cmd_add)
    
    p_rm = subparsers.add_parser("remove")
    p_rm.add_argument("torrent_ids", nargs="+")
    p_rm.set_defaults(func=cmd_remove)
    
    p_link = subparsers.add_parser("get-link")
    p_link.add_argument("torrent_id")
    p_link.add_argument("--no-zip", dest="zip", action="store_false")
    p_link.set_defaults(func=cmd_get_link)
    
    p_dl = subparsers.add_parser("download")
    p_dl.add_argument("torrent_id")
    p_dl.add_argument("--out-dir", "-o")
    p_dl.add_argument("--force-single", action="store_true", default=False)
    p_dl.set_defaults(func=cmd_download)
    
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
