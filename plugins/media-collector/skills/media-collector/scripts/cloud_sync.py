#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Post-Curation Cloud Sync Tool
Sync completed Plex structures to Google Drive and NAS after curation.
media-collector v2.0 — scripts/cloud_sync.py
"""

import os
import sys
import subprocess
import argparse


def check_rclone():
    """Verify rclone is installed and configured."""
    try:
        result = subprocess.run(["rclone", "version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return True
    except Exception:
        pass
    print("❌ rclone not found. Install: https://rclone.org/install/")
    return False


def sync_to_gdrive(local_path, gdrive_dest, transfers=4, checkers=8, dry_run=False):
    """Sync local directory to Google Drive using rclone copy."""
    cmd = [
        "rclone", "copy", local_path, gdrive_dest,
        "--transfers", str(transfers),
        "--checkers", str(checkers),
        "-v", "--stats", "15s"
    ]
    if dry_run:
        cmd.append("--dry-run")

    print(f"{'🧪 DRY RUN' if dry_run else '🚀 UPLOADING'}: {local_path} → {gdrive_dest}")
    result = subprocess.run(cmd)
    return result.returncode == 0


def sync_to_nas(local_path, nas_path, nas_host="chungnh@192.168.1.37", dry_run=False):
    """Sync local directory to NAS using rsync over SSH."""
    # Ensure trailing slash for rsync directory sync
    if not local_path.endswith("/"):
        local_path += "/"

    cmd = [
        "rsync", "-avz", "--progress",
        local_path,
        f"{nas_host}:{nas_path}"
    ]
    if dry_run:
        cmd.insert(1, "--dry-run")

    print(f"{'🧪 DRY RUN' if dry_run else '🚀 SYNCING'}: {local_path} → {nas_host}:{nas_path}")
    result = subprocess.run(cmd)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(
        description="Sync completed media to Google Drive and/or NAS",
        epilog="""
Examples:
  python3 cloud_sync.py ./Kindaichi_Plex/ --gdrive "gdrive:Phim/TV Shows/Kindaichi..."
  python3 cloud_sync.py ./Black_Jack_Movies/ --gdrive "gdrive:Phim/Movies" --nas "/srv/mergerfs/MainPool/Phim/Movies"
  python3 cloud_sync.py ./output/ --gdrive "gdrive:Phim/" --nas "/srv/..." --dry-run
        """
    )
    parser.add_argument("local_dir", help="Local directory to sync")
    parser.add_argument("--gdrive", help="Google Drive rclone destination path")
    parser.add_argument("--nas", help="NAS destination path")
    parser.add_argument("--nas-host", default="chungnh@192.168.1.37", help="NAS SSH host")
    parser.add_argument("--transfers", type=int, default=4, help="rclone parallel transfers")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, don't actually transfer")

    args = parser.parse_args()

    if not os.path.exists(args.local_dir):
        print(f"❌ Local directory not found: {args.local_dir}")
        sys.exit(1)

    success = True

    if args.gdrive:
        if check_rclone():
            ok = sync_to_gdrive(args.local_dir, args.gdrive, args.transfers, dry_run=args.dry_run)
            if ok:
                print("✅ Google Drive sync complete!")
            else:
                print("❌ Google Drive sync failed!")
                success = False

    if args.nas:
        ok = sync_to_nas(args.local_dir, args.nas, args.nas_host, dry_run=args.dry_run)
        if ok:
            print("✅ NAS sync complete!")
        else:
            print("❌ NAS sync failed!")
            success = False

    if not args.gdrive and not args.nas:
        print("⚠️  No destination specified. Use --gdrive and/or --nas.")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
