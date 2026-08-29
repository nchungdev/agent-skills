#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Duplicate Detection & Deduplication Tool
Checks local files against NAS and Google Drive to avoid redundant downloads.
media-collector v2.0 — scripts/deduplicate.py
"""

import os
import sys
import subprocess
import argparse
import json
from pathlib import Path


def get_local_files(directory, extensions=None):
    """Recursively scan a local directory and return dict of {relative_path: size_bytes}."""
    if not os.path.exists(directory):
        print(f"⚠️  Directory not found: {directory}")
        return {}

    files = {}
    for root, _, filenames in os.walk(directory):
        for f in filenames:
            if extensions and not any(f.lower().endswith(ext) for ext in extensions):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, directory)
            try:
                files[rel] = os.path.getsize(full)
            except OSError:
                pass
    return files


def get_rclone_files(remote_path):
    """List files on rclone remote and return dict of {relative_path: size_bytes}."""
    try:
        result = subprocess.run(
            ["rclone", "lsjson", "-R", remote_path],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            print(f"⚠️  rclone lsjson failed for {remote_path}: {result.stderr.strip()}")
            return {}

        items = json.loads(result.stdout)
        return {item["Path"]: item["Size"] for item in items if not item.get("IsDir", False)}
    except Exception as e:
        print(f"⚠️  Error scanning remote {remote_path}: {e}")
        return {}


def get_nas_files(nas_path, ssh_host="chungnh@192.168.1.37"):
    """List files on NAS via SSH and return dict of {relative_path: size_bytes}."""
    try:
        result = subprocess.run(
            ["ssh", ssh_host, f"find '{nas_path}' -type f -printf '%P\\t%s\\n'"],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            print(f"⚠️  SSH scan failed for {nas_path}: {result.stderr.strip()}")
            return {}

        files = {}
        for line in result.stdout.strip().splitlines():
            parts = line.split("\t", 1)
            if len(parts) == 2:
                files[parts[0]] = int(parts[1])
        return files
    except Exception as e:
        print(f"⚠️  Error scanning NAS {nas_path}: {e}")
        return {}


def compare_files(local_files, remote_files, remote_label="Remote"):
    """Compare local vs remote files by name and size."""
    duplicates = []
    missing_remote = []
    size_mismatch = []

    for rel, local_size in sorted(local_files.items()):
        if rel in remote_files:
            remote_size = remote_files[rel]
            if abs(local_size - remote_size) < 1024:  # within 1KB tolerance
                duplicates.append((rel, local_size))
            else:
                size_mismatch.append((rel, local_size, remote_size))
        else:
            missing_remote.append((rel, local_size))

    return duplicates, missing_remote, size_mismatch


def format_size(size_bytes):
    """Human-readable file size."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def main():
    parser = argparse.ArgumentParser(
        description="Check local files against NAS/Google Drive for duplicates before downloading"
    )
    parser.add_argument("local_dir", help="Local directory to check")
    parser.add_argument("--gdrive", help="Google Drive rclone path (e.g. gdrive:Phim/TV Shows/...)")
    parser.add_argument("--nas", help="NAS directory path (e.g. /srv/mergerfs/MainPool/Phim/TV Shows/...)")
    parser.add_argument("--nas-host", default="chungnh@192.168.1.37", help="NAS SSH host")
    parser.add_argument("--extensions", nargs="+", default=[".mkv", ".mp4", ".avi", ".srt", ".ass"],
                        help="File extensions to check")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    local_files = get_local_files(args.local_dir, args.extensions)
    print(f"📁 Local: {len(local_files)} files ({format_size(sum(local_files.values()))})")

    results = {}

    if args.gdrive:
        print(f"\n☁️  Scanning Google Drive: {args.gdrive}...")
        gdrive_files = get_rclone_files(args.gdrive)
        dupes, missing, mismatch = compare_files(local_files, gdrive_files, "Google Drive")
        dupe_size = sum(s for _, s in dupes)
        results["gdrive"] = {
            "duplicates": len(dupes),
            "duplicate_size": format_size(dupe_size),
            "missing": len(missing),
            "size_mismatch": len(mismatch),
        }
        print(f"   ✅ Trùng lặp (đã có trên Drive): {len(dupes)} files ({format_size(dupe_size)})")
        print(f"   📥 Chưa có trên Drive: {len(missing)} files")
        if mismatch:
            print(f"   ⚠️  Khác kích thước: {len(mismatch)} files")

    if args.nas:
        print(f"\n🖥️  Scanning NAS: {args.nas}...")
        nas_files = get_nas_files(args.nas, args.nas_host)
        dupes, missing, mismatch = compare_files(local_files, nas_files, "NAS")
        dupe_size = sum(s for _, s in dupes)
        results["nas"] = {
            "duplicates": len(dupes),
            "duplicate_size": format_size(dupe_size),
            "missing": len(missing),
            "size_mismatch": len(mismatch),
        }
        print(f"   ✅ Trùng lặp (đã có trên NAS): {len(dupes)} files ({format_size(dupe_size)})")
        print(f"   📥 Chưa có trên NAS: {len(missing)} files")
        if mismatch:
            print(f"   ⚠️  Khác kích thước: {len(mismatch)} files")

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
