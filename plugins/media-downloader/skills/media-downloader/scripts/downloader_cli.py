#!/usr/bin/env python3
"""
Media Downloader Unified CLI
Supports Direct, Aria2 P2P, TorBox Debrid Cloud downloads, and Prowlarr indexer search.
"""

import sys
import json
import argparse
from pathlib import Path

from providers.direct import download_direct
from providers.aria2_provider import download_aria2_torrent
from providers.torbox_provider import list_torrents, add_torrent, get_torbox_token
from providers.prowlarr_provider import search_prowlarr, resolve_magnet
from providers.metube_provider import add_metube_download

from hub_paths import staging_dir

def main():
    parser = argparse.ArgumentParser(description="Media Downloader - Unified Multi-Source Download Engine.")
    subparsers = parser.add_subparsers(dest="command", help="Lệnh thực hiện")

    # Command: download
    p_dl = subparsers.add_parser("download", help="Tải nội dung từ URL hoặc Magnet link")
    p_dl.add_argument("source", help="URL trực tiếp, Magnet link, YouTube stream hoặc đường dẫn file .torrent")
    p_dl.add_argument("--provider", choices=["direct", "aria2", "torbox", "metube"], default="aria2", help="Nguồn tải (direct, aria2, torbox, metube). Mặc định: aria2")
    p_dl.add_argument("--out-dir", default=None,
                      help="Thư mục đệm (mặc định: staging_dir trong cấu hình Media Hub)")
    p_dl.add_argument("--connections", type=int, default=16, help="Số kết nối song song")

    # Command: search
    p_sr = subparsers.add_parser("search", help="Tìm kiếm torrent qua Prowlarr Indexers")
    p_sr.add_argument("query", help="Tên phim hoặc từ khóa cần tìm")
    p_sr.add_argument("--quality", default=None, help="Lọc chất lượng (vd: '1080p hevc', '720p', '4k')")
    p_sr.add_argument("--limit", type=int, default=10, help="Giới hạn số kết quả (mặc định: 10)")
    p_sr.add_argument("--auto-download", action="store_true", help="Tự động nạp kết quả tốt nhất vào Aria2c")
    p_sr.add_argument("--out-dir", default=None, help="Thư mục đích lưu phim khi auto-download")

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
        out_dir = args.out_dir or staging_dir()
        print(f"🚀 Khởi chạy Media Downloader [Provider: {prov.upper()}] -> {out_dir}")

        if prov == "direct":
            success = download_direct(src, out_dir, connections=args.connections)
            sys.exit(0 if success else 1)
        elif prov == "aria2":
            success = download_aria2_torrent(src, out_dir, connections=args.connections)
            sys.exit(0 if success else 1)
        elif prov == "metube":
            success = add_metube_download(src, subfolder=args.out_dir)
            sys.exit(0 if success else 1)
        elif prov == "torbox":
            res = add_torrent(src)
            print(json.dumps(res, indent=2, ensure_ascii=False))
            if res.get("success"):
                print("✅ Đã thêm vào TorBox Cloud thành công!")
            else:
                print(f"❌ Lỗi: {res.get('detail') or res.get('error')}")

    elif args.command == "search":
        print(f"🔍 Đang tìm kiếm trên Prowlarr: '{args.query}' (Quality filter: {args.quality or 'None'})...")
        results = search_prowlarr(args.query, quality=args.quality, limit=args.limit)
        if not results:
            print("⚠️ Không tìm thấy kết quả phù hợp.")
            sys.exit(0)

        print(f"\n✅ Tìm thấy {len(results)} bản phát hành:")
        for idx, r in enumerate(results, 1):
            print(f"  [{idx}] {r['title']} | {r['size_mb']}MB | Seeds: {r['seeders']} | Indexer: {r['indexer']}")

        if args.auto_download:
            best = results[0]
            print(f"\n🎯 Chọn bản tốt nhất: {best['title']}")
            mag = resolve_magnet(best.get("download_url") or best.get("magnet_url"))
            if not mag:
                print("❌ Không giải mã được Magnet link từ release này.")
                sys.exit(1)
            target_dir = args.out_dir or staging_dir()
            print(f"🧲 Bắn sang Aria2c tải về: {target_dir}")
            success = download_aria2_torrent(mag, target_dir)
            sys.exit(0 if success else 1)

    elif args.command == "list":
        if args.provider == "torbox":
            res = list_torrents()
            print(json.dumps(res, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
