import os
import sys
import json
import shutil
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

def add_aria2_rpc(torrent_or_magnet, out_dir, rpc_url="http://127.0.0.1:6800/jsonrpc", token="As123456"):
    """
    Push torrent or magnet link into Aria2 RPC Daemon.
    Tasks immediately appear in AriaNg Web GUI (http://192.168.1.37:6880).
    """
    payload = {
        "jsonrpc": "2.0",
        "id": "media-downloader",
        "method": "aria2.addUri",
        "params": [f"token:{token}", [torrent_or_magnet], {"dir": str(out_dir)}]
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        rpc_url,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            if "result" in res:
                gid = res["result"]
                print(f"✅ [Aria2 RPC] Đã nạp task thành công (GID: {gid})!")
                print(f"🌐 Quản lý và xem tiến độ trên AriaNg: http://192.168.1.37:6880")
                return True
            else:
                print(f"⚠️ [Aria2 RPC] Phản hồi lỗi: {res}", file=sys.stderr)
                return False
    except Exception as e:
        print(f"ℹ️ [Aria2 RPC] Không kết nối được daemon ({e}), chuyển sang chạy binary cục bộ...")
        return False

def download_aria2_torrent(torrent_or_magnet, out_dir, connections=16, prefer_rpc=True):
    """Download a torrent or magnet link via Aria2 RPC (AriaNg GUI) or local binary fallback."""
    out_folder = Path(out_dir)
    out_folder.mkdir(parents=True, exist_ok=True)

    if prefer_rpc:
        if add_aria2_rpc(torrent_or_magnet, out_folder):
            return True

    # Fallback to local aria2c binary execution
    aria2 = shutil.which("aria2c") or "/usr/bin/aria2c" or "/opt/homebrew/bin/aria2c"
    if not (os.path.isfile(aria2) and os.access(aria2, os.X_OK)):
        print("❌ Error: aria2c binary not found. Please install aria2.", file=sys.stderr)
        return False

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
        print(f"🧲 [Aria2 P2P CLI] Đang bắt đầu kéo torrent về {out_folder}...")
        subprocess.run(cmd, check=True)
        return True
    except Exception as e:
        print(f"❌ Aria2 P2P download failed: {e}", file=sys.stderr)
        return False
