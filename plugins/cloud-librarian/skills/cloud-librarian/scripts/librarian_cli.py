#!/usr/bin/env python3
"""
Cloud Librarian CLI
Scans remote storage (NAS over SSH) and builds standard Plex/Jellyfin paths.
"""

import sys
import json
import argparse
from pathlib import Path

from scanner.nas_scanner import scan_nas_ssh
from scanner.naming_rule import format_plex_episode

def main():
    parser = argparse.ArgumentParser(description="Cloud Librarian - Remote library detection & Plex/Jellyfin path builder.")
    subparsers = parser.add_subparsers(dest="command", help="Lệnh thực hiện")

    # Command: scan-nas
    p_nas = subparsers.add_parser("scan-nas", help="Quét tự động thư mục Plex trên NAS qua SSH")
    p_nas.add_argument("--host", required=True, help="Địa chỉ IP NAS")
    p_nas.add_argument("--user", default="admin", help="Tên người dùng SSH")
    p_nas.add_argument("--port", type=int, default=22, help="Cổng SSH (mặc định: 22)")
    p_nas.add_argument("--key", help="Đường dẫn file SSH private key")

    # Command: format-name
    p_fn = subparsers.add_parser("format-name", help="Tạo đường dẫn chuẩn Plex cho 1 tập phim")
    p_fn.add_argument("--title", required=True, help="Tên phim")
    p_fn.add_argument("--year", type=int, help="Năm phát hành")
    p_fn.add_argument("--tvdb", help="TVDB ID")
    p_fn.add_argument("--season", type=int, default=1, help="Mùa")
    p_fn.add_argument("--episode", type=int, default=1, help="Tập")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "scan-nas":
        res = scan_nas_ssh(args.host, args.user, port=args.port, key_path=args.key)
        print(json.dumps(res, indent=2, ensure_ascii=False))

    elif args.command == "format-name":
        path_res = format_plex_episode(args.title, year=args.year, tvdb_id=args.tvdb, season=args.season, episode=args.episode)
        print(f"🎬 Đường dẫn chuẩn Plex:\n{path_res}")

if __name__ == "__main__":
    main()
