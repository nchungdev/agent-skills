import os
import sys
import shutil
import subprocess
from pathlib import Path

def download_aria2_torrent(torrent_or_magnet, out_dir, connections=16):
    """Download a torrent or magnet link via aria2c local P2P client."""
    aria2 = shutil.which("aria2c") or "/opt/homebrew/bin/aria2c"
    if not (os.path.isfile(aria2) and os.access(aria2, os.X_OK)):
        print("❌ Error: aria2c binary not found. Please install aria2.", file=sys.stderr)
        return False

    out_folder = Path(out_dir)
    out_folder.mkdir(parents=True, exist_ok=True)

    cmd = [
        aria2,
        "--seed-time=0",
        "--max-connection-per-server=16",
        f"--split={connections}",
        "--enable-dht=true",
        "--enable-peer-exchange=true",
        "--bt-enable-lpd=true",
        "-d", str(out_folder),
        torrent_or_magnet
    ]

    try:
        print(f"🧲 [Aria2 P2P] Đang bắt đầu kéo torrent về {out_folder}...")
        subprocess.run(cmd, check=True)
        return True
    except Exception as e:
        print(f"❌ Aria2 P2P download failed: {e}", file=sys.stderr)
        return False
