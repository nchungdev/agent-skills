import os
import sys
import shlex
import shutil
import subprocess
from pathlib import Path

def sync_to_nas(local_path, host, user, remote_dest_path, port=22):
    """Sync a local directory or file to NAS via rsync over SSH.

    A directory source needs a trailing slash so rsync copies its *contents*, matching
    what `rclone copy` does for Google Drive. Without it the two destinations end up
    with different layouts (dest/<basename>/... on NAS vs dest/... on Drive).
    """
    rsync = shutil.which("rsync") or "/usr/bin/rsync"
    src = str(local_path)
    if Path(local_path).is_dir() and not src.endswith("/"):
        src += "/"
    target = f"{user}@{host}:{shlex.quote(remote_dest_path.rstrip('/'))}/"

    cmd = [rsync, "-avz"]
    # --mkpath needs rsync >= 3.2.3; the openrsync shipped as /usr/bin/rsync on macOS
    # rejects it outright, so only pass it when the binary advertises support.
    try:
        help_out = subprocess.run([rsync, "--help"], capture_output=True, text=True, timeout=5)
        if "--mkpath" in (help_out.stdout + help_out.stderr):
            cmd.append("--mkpath")
    except Exception:
        pass
    cmd += ["-e", f"ssh -p {int(port)}", src, target]
    try:
        print(f"🖥️ [NAS Sync] Đang đẩy {local_path} -> {target}...")
        subprocess.run(cmd, check=True)
        return True
    except Exception as e:
        print(f"❌ NAS sync failed: {e}", file=sys.stderr)
        return False
