import os
import sys
import shutil
import subprocess
from pathlib import Path

def sync_to_gdrive(local_path, remote_name="gdrive", remote_path="Phim/TV Shows", transfers=4):
    """Sync a local directory or file to Google Drive using Rclone."""
    rclone = shutil.which("rclone") or "/opt/homebrew/bin/rclone"
    if not (os.path.isfile(rclone) and os.access(rclone, os.X_OK)):
        print("❌ Error: rclone not found.", file=sys.stderr)
        return False

    dest = f"{remote_name}:{remote_path.lstrip('/')}"
    cmd = [
        rclone, "copy",
        str(local_path),
        dest,
        f"--transfers={transfers}",
        "--checkers=8",
        "-P"
    ]
    try:
        print(f"☁️ [Rclone GDrive] Đang đẩy {local_path} -> {dest}...")
        subprocess.run(cmd, check=True)
        return True
    except Exception as e:
        print(f"❌ Rclone GDrive sync failed: {e}", file=sys.stderr)
        return False
