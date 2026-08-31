import os
import sys
import shutil
import subprocess
from pathlib import Path

def download_direct(url, out_dir, filename=None, connections=8):
    """Download a direct URL using aria2c or curl."""
    out_folder = Path(out_dir)
    out_folder.mkdir(parents=True, exist_ok=True)
    
    aria2 = shutil.which("aria2c") or "/opt/homebrew/bin/aria2c"
    if os.path.isfile(aria2) and os.access(aria2, os.X_OK):
        cmd = [
            aria2,
            "-x", str(connections),
            "-s", str(connections),
            "-k", "1M",
            "-d", str(out_folder),
            url
        ]
        if filename:
            cmd.extend(["-o", filename])
        try:
            print(f"📥 [Direct/Aria2c] Đang tải: {url} -> {out_folder}")
            subprocess.run(cmd, check=True)
            return True
        except Exception as e:
            print(f"⚠️ Aria2c failed, falling back to curl: {e}", file=sys.stderr)

    # Fallback to curl
    curl = shutil.which("curl") or "/usr/bin/curl"
    out_target = out_folder / (filename or url.split("?")[0].split("/")[-1])
    cmd = [
        curl,
        "-L",
        "-C", "-",
        "-o", str(out_target),
        url
    ]
    try:
        print(f"📥 [Direct/Curl] Đang tải: {url} -> {out_target}")
        subprocess.run(cmd, check=True)
        return True
    except Exception as e:
        print(f"❌ Direct download failed: {e}", file=sys.stderr)
        return False
