#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TorBox CLI Manager — Full Interactive Auth, Browser Login & Transfer Operations
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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from torbox_client import TorBoxClient, CONFIG_FILE

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

    # Validate token against API
    client = TorBoxClient(api_key=token)
    res = client.get_user_info()
    
    if res.get("success"):
        data = res.get("data", {})
        email = data.get("email", "Unknown")
        plan_id = data.get("plan", 0)
        plan_name = "Pro / Standard" if plan_id >= 2 else ("Essential" if plan_id == 1 else "Free")
        expires = data.get("premium_expires_at", "N/A")
        
        # Save validated token
        TorBoxClient.save_api_key(token)
        print("\n🎉 ĐĂNG NHẬP THÀNH CÔNG 100%!")
        print(f"  • 👤 Email:         {email}")
        print(f"  • 📦 Gói cước:      {plan_name} (Plan ID: {plan_id})")
        print(f"  • ⏳ Hạn Premium:   {expires}")
        print(f"  • 📁 Cấu hình lưu:  {CONFIG_FILE}")
    else:
        print(f"\n❌ Xác thực thất bại: {res.get('error') or res.get('detail')}")
        print("Vui lòng kiểm tra lại mã Token của anh trên https://torbox.app/settings.")

def cmd_logout(args):
    TorBoxClient.clear_api_key()
    print("👋 Đã đăng xuất và xóa sạch cấu hình TorBox API Key trên máy.")

def cmd_whoami(args):
    client = TorBoxClient(args.api_key)
    if not client.is_authenticated():
        print("⚠️ Bạn chưa đăng nhập TorBox. Vui lòng chạy: python3 torbox_cli.py login")
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
        print("⚠️ Bạn chưa đăng nhập TorBox. Vui lòng chạy: python3 torbox_cli.py login")
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
        print("⚠️ Bạn chưa đăng nhập TorBox. Vui lòng chạy: python3 torbox_cli.py login")
        return
        
    target = args.target.strip()
    if target.startswith("magnet:?"):
        print("🧲 Đang thêm Magnet Link vào TorBox...")
        res = client.add_torrent_magnet(target, seed=args.seed, allow_zip=True)
    elif os.path.exists(target) and target.endswith(".torrent"):
        print(f"📁 Đang tải file torrent lên TorBox: {os.path.basename(target)}...")
        res = client.add_torrent_file(target, seed=args.seed, allow_zip=True)
    else:
        print(f"❌ Lỗi: Target không phải là Magnet link hợp lệ hay file .torrent tồn tại: {target}")
        return
        
    if res.get("success"):
        data = res.get("data", {})
        print(f"✅ Thêm thành công! ID: {data.get('torrent_id')} | Hash: {data.get('hash')}")
        print(f"  • Message: {res.get('detail')}")
    else:
        print(f"❌ Lỗi khi thêm torrent: {res.get('error') or res.get('detail')}")

def cmd_remove(args):
    client = TorBoxClient(args.api_key)
    if not client.is_authenticated():
        print("⚠️ Bạn chưa đăng nhập TorBox. Vui lòng chạy: python3 torbox_cli.py login")
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
        print("⚠️ Bạn chưa đăng nhập TorBox. Vui lòng chạy: python3 torbox_cli.py login")
        return
        
    res = client.get_download_link(args.torrent_id, as_zip=args.zip)
    if res.get("success"):
        url = res.get("data")
        print(f"🔗 DIRECT DOWNLOAD LINK (CDN DDL):")
        print(url)
        return url
    else:
        print(f"❌ Lỗi lấy link: {res.get('error') or res.get('detail')}")
        return None

def cmd_download(args):
    client = TorBoxClient(args.api_key)
    if not client.is_authenticated():
        print("⚠️ Bạn chưa đăng nhập TorBox. Vui lòng chạy: python3 torbox_cli.py login")
        return
        
    print(f"🔍 Đang yêu cầu link tải cho Torrent ID: {args.torrent_id}...")
    res = client.get_download_link(args.torrent_id, as_zip=True)
    if not res.get("success") or not res.get("data"):
        print(f"❌ Không thể lấy link tải: {res.get('error') or res.get('detail')}")
        return
        
    url = res.get("data")
    dest_dir = os.path.abspath(args.out_dir or ".")
    os.makedirs(dest_dir, exist_ok=True)
    
    zip_filename = f"torbox_{args.torrent_id}.zip"
    zip_path = os.path.join(dest_dir, zip_filename)
    
    print(f"🚀 Bắt đầu kéo đa luồng qua aria2c vào: {dest_dir}")
    cmd_aria = [
        "aria2c",
        "-x16", "-s16", "-k1M",
        "--summary-interval=10",
        f"--dir={dest_dir}",
        f"--out={zip_filename}",
        url
    ]
    
    dl_res = subprocess.run(cmd_aria)
    if dl_res.returncode != 0:
        print("❌ Lỗi trong quá trình tải bằng aria2c.")
        return
        
    print("\n🎉 [TẢI XONG 100%] Đã tải thành công file zip từ TorBox CDN!")
    
    if args.unzip:
        print("📦 Đang giải nén nội dung...")
        temp_dir = os.path.join(dest_dir, f"_extracted_{args.torrent_id}")
        os.makedirs(temp_dir, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(temp_dir)
            
        print("✨ Giải nén hoàn tất. Dọn dẹp file zip...")
        try:
            os.remove(zip_path)
        except Exception:
            pass
        print(f"✅ Thư mục hoàn chỉnh: {temp_dir}")

def main():
    parser = argparse.ArgumentParser(description="TorBox CLI Manager — Quản lý TorBox toàn diện")
    parser.add_argument("--api-key", help="TorBox API Key")
    
    subparsers = parser.add_subparsers(dest="command", help="Lệnh thực thi")
    
    # login
    p_login = subparsers.add_parser("login", help="Đăng nhập tài khoản TorBox (nhập API Token)")
    p_login.add_argument("--token", "-t", help="TorBox API Token")
    p_login.add_argument("--browser", "-b", action="store_true", default=False, help="Mở trình duyệt tới trang cài đặt TorBox để lấy Token")
    p_login.set_defaults(func=cmd_login)
    
    # logout
    p_logout = subparsers.add_parser("logout", help="Đăng xuất và xóa API Key đã lưu")
    p_logout.set_defaults(func=cmd_logout)
    
    # whoami
    p_whoami = subparsers.add_parser("whoami", help="Xem thông tin tài khoản đang đăng nhập")
    p_whoami.set_defaults(func=cmd_whoami)
    
    # list
    p_list = subparsers.add_parser("list", help="Liệt kê danh sách torrents")
    p_list.set_defaults(func=cmd_list)
    
    # add
    p_add = subparsers.add_parser("add", help="Thêm torrent (Magnet hoặc file .torrent)")
    p_add.add_argument("target", help="Magnet link hoặc đường dẫn file .torrent")
    p_add.add_argument("--seed", type=int, default=1, help="Chế độ seed: 1 (mặc định), 2 (seed dài hạn)")
    p_add.set_defaults(func=cmd_add)
    
    # remove
    p_rm = subparsers.add_parser("remove", help="Xóa torrent trên TorBox")
    p_rm.add_argument("torrent_ids", nargs="+", help="ID các torrent cần xóa")
    p_rm.set_defaults(func=cmd_remove)
    
    # get-link
    p_link = subparsers.add_parser("get-link", help="Lấy link tải trực tiếp (DDL) từ TorBox")
    p_link.add_argument("torrent_id", help="ID của torrent")
    p_link.add_argument("--no-zip", dest="zip", action="store_false", help="Không tải dạng zip")
    p_link.set_defaults(func=cmd_get_link)
    
    # download
    p_dl = subparsers.add_parser("download", help="Tải trực tiếp torrent về máy với aria2c")
    p_dl.add_argument("torrent_id", help="ID của torrent trên TorBox")
    p_dl.add_argument("--out-dir", "-o", help="Thư mục lưu file")
    p_dl.add_argument("--unzip", action="store_true", default=True, help="Tự động giải nén sau khi tải xong")
    p_dl.set_defaults(func=cmd_download)
    
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
