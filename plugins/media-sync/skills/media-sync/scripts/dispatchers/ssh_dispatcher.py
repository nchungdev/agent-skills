import os
import sys
import shutil
import subprocess
from pathlib import Path

def sync_to_nas(local_path, host, user, remote_dest_path, port=22):
    """Sync a local directory or file to NAS via rsync or scp."""
    rsync = shutil.which("rsync") or "/usr/bin/rsync"
    target = f"{user}@{host}:{remote_dest_path}"
    
    cmd = [
        rsync, "-avz",
        "-e", f"ssh -p {port}",
        str(local_path),
        target
    ]
    try:
        print(f"🖥️ [NAS Sync] Đang đẩy {local_path} -> {target}...")
        subprocess.run(cmd, check=True)
        return True
    except Exception as e:
        print(f"❌ NAS sync failed: {e}", file=sys.stderr)
        return False
