#!/usr/bin/env python3
"""
Media Sync CLI
Unified dispatcher for NAS & Google Drive multi-sync with Auto-Purge.
"""

import sys
import argparse
from pathlib import Path

from dispatchers.rclone_dispatcher import sync_to_gdrive
from dispatchers.ssh_dispatcher import sync_to_nas
from dispatchers.auto_purge import purge_local_cache

def main():
    parser = argparse.ArgumentParser(description="Media Sync - Multi-Target Sync & Auto-Purge Engine.")
    subparsers = parser.add_subparsers(dest="command", help="Lệnh thực hiện")

    # Command: sync
    p_sync = subparsers.add_parser("sync", help="Đồng bộ file đệm lên các đích lưu trữ")
    p_sync.add_argument("source", help="Đường dẫn file hoặc thư mục đệm cần đồng bộ")
    p_sync.add_argument("--targets", default="drive", help="Đích đồng bộ (nas, drive, hoặc nas,drive). Mặc định: drive")
    p_sync.add_argument("--purge", action="store_true", help="Tự động xóa file đệm cục bộ sau khi đồng bộ thành công")
    
    # Drive options
    p_sync.add_argument("--drive-remote", default="gdrive", help="Tên remote Rclone")
    p_sync.add_argument("--drive-path", default="Phim/TV Shows", help="Đường dẫn đích trên Drive")
    p_sync.add_argument("--transfers", type=int, default=4, help="Số luồng Rclone transfer")

    # NAS options
    p_sync.add_argument("--nas-host", help="Địa chỉ IP NAS")
    p_sync.add_argument("--nas-user", default="admin", help="Tên người dùng NAS SSH")
    p_sync.add_argument("--nas-path", default="/volume1/video/TV Shows", help="Đường dẫn thư mục trên NAS")
    p_sync.add_argument("--nas-port", type=int, default=22, help="Cổng SSH NAS")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "sync":
        src_path = Path(args.source)
        if not src_path.exists():
            print(f"❌ Đường dẫn không tồn tại: {args.source}")
            sys.exit(1)

        targets = [t.strip().lower() for t in args.targets.split(",")]
        success_all = True

        print(f"🚀 Bắt đầu chuỗi đồng bộ cho: {src_path.name} -> Targets: {targets}")

        if "drive" in targets:
            ok = sync_to_gdrive(src_path, remote_name=args.drive_remote, remote_path=args.drive_path, transfers=args.transfers)
            if not ok: success_all = False

        if "nas" in targets:
            if not args.nas_host:
                print("❌ Thiếu thông số --nas-host khi chọn sync NAS.")
                success_all = False
            else:
                ok = sync_to_nas(src_path, args.nas_host, args.nas_user, args.nas_path, port=args.nas_port)
                if not ok: success_all = False

        if success_all:
            print("✅ ĐỒNG BỘ THÀNH CÔNG 100%!")
            if args.purge:
                purge_local_cache(src_path)
        else:
            print("⚠️ Đồng bộ có lỗi xảy ra. Giữ nguyên file đệm để bảo vệ dữ liệu.")

if __name__ == "__main__":
    main()
