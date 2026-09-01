#!/usr/bin/env python3
"""
Media Downloader Unified CLI
Supports Direct, Aria2 P2P, and TorBox Debrid Cloud downloads.
"""

import sys
import json
import argparse
from pathlib import Path

from providers.direct import download_direct
from providers.aria2_provider import download_aria2_torrent
from providers.torbox_provider import list_torrents, add_torrent, get_torbox_token

from hub_paths import staging_dir

def main():
    parser = argparse.ArgumentParser(description="Media Downloader - Unified Multi-Source Download Engine.")
    subparsers = parser.add_subparsers(dest="command", help="Lệnh thực hiện")

    # Command: download
    p_dl = subparsers.add_parser("download", help="Tải nội dung từ URL hoặc Magnet link")
    p_dl.add_argument("source", help="URL trực tiếp, Magnet link hoặc đường dẫn file .torrent")
    p_dl.add_argument("--provider", choices=["direct", "aria2", "torbox"], default="torbox", help="Nguồn tải (direct, aria2, torbox). Mặc định: torbox")
    p_dl.add_argument("--out-dir", default=None,
                      help="Thư mục đệm (mặc định: staging_dir trong cấu hình Media Hub)")
    p_dl.add_argument("--connections", type=int, default=8, help="Số kết nối song song")

    # Command: list
    p_ls = subparsers.add_parser("list", help="Xem danh sách torrents")
    p_ls.add_argument("--provider", choices=["torbox", "aria2"], default="torbox", help="Provider cần liệt kê")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "download":
        src = args.source.strip()
        prov = args.provider.lower()
        # Resolved here rather than as an argparse default so the configured
        # staging directory is picked up at run time.
        out_dir = args.out_dir or staging_dir()
        print(f"🚀 Khởi chạy Media Downloader [Provider: {prov.upper()}] -> {out_dir}")

        if prov == "direct":
            success = download_direct(src, out_dir, connections=args.connections)
            sys.exit(0 if success else 1)
        elif prov == "aria2":
            success = download_aria2_torrent(src, out_dir, connections=args.connections)
            sys.exit(0 if success else 1)
        elif prov == "torbox":
            res = add_torrent(src)
            print(json.dumps(res, indent=2, ensure_ascii=False))
            if res.get("success"):
                print("✅ Đã thêm vào TorBox Cloud thành công!")
            else:
                print(f"❌ Lỗi: {res.get('detail') or res.get('error')}")

    elif args.command == "list":
        if args.provider == "torbox":
            res = list_torrents()
            print(json.dumps(res, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
