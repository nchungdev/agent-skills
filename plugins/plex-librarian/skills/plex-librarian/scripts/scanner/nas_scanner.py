import os
import sys
import subprocess
import json

COMMON_NAS_PATHS = [
    "/volume1/video",
    "/volume1/Media",
    "/volume1/Plex",
    "/volume2/video",
    "/share/Multimedia",
    "/share/CACHEDEV1_DATA/Multimedia",
    "/mnt/user/Media",
    "/srv/media",
    "/var/media"
]

def scan_nas_ssh(host, user, port=22, key_path=None):
    """Scan NAS via SSH to detect Plex/Jellyfin library directories."""
    candidates = []
    
    # Construct SSH test command
    ssh_cmd = ["ssh", "-p", str(port), "-o", "BatchMode=yes", "-o", "ConnectTimeout=5"]
    if key_path and os.path.isfile(key_path):
        ssh_cmd.extend(["-i", key_path])
    
    target = f"{user}@{host}"
    
    # Check common paths
    paths_str = " ".join(COMMON_NAS_PATHS)
    remote_cmd = f"for p in {paths_str}; do if [ -d \"$p\" ]; then echo \"FOUND:$p\"; fi; done"
    
    cmd = ssh_cmd + [target, remote_cmd]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        found_paths = []
        for line in res.stdout.splitlines():
            if line.startswith("FOUND:"):
                p = line.split(":", 1)[1].strip()
                found_paths.append(p)
        
        return {
            "success": True,
            "host": host,
            "user": user,
            "libraries_found": found_paths
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "host": host
        }
