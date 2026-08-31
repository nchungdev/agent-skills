#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity Media Hub - Auto Launcher with Ephemeral TryCloudflare Tunnel
Automatically boots Server + Agent Watcher + Quick Cloudflare Tunnel and prints the Live URL.
"""

import os
import sys
import time
import subprocess
import re
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PORT = 8888
URL_FILE = os.path.join(BASE_DIR, "active_public_url.txt")

def find_cloudflared():
    for path in ["/opt/homebrew/bin/cloudflared", "/usr/local/bin/cloudflared", "cloudflared"]:
        resolved = shutil.which(path)
        if resolved and os.path.exists(resolved):
            return resolved
    return None

def start_hub():
    print("================================================================", flush=True)
    print("🚀 Đang khởi chạy Antigravity Media Hub Dashboard v2.4...", flush=True)
    print("================================================================", flush=True)

    # 1. Start Server if not running
    server_script = os.path.join(BASE_DIR, "server.py")
    server_proc = subprocess.Popen([sys.executable, server_script])
    print(f"✅ Web Server đã chạy tại Localhost: http://127.0.0.1:{PORT}", flush=True)

    # 2. Start Agent Queue Watcher
    watcher_script = os.path.join(BASE_DIR, "agent_queue_watcher.py")
    if os.path.exists(watcher_script):
        subprocess.Popen([sys.executable, watcher_script])
        print("✅ Agent Queue Watcher Daemon đã kích hoạt.", flush=True)

    # 3. Start TryCloudflare Tunnel
    cloudflared_bin = find_cloudflared()
    public_url = None

    if cloudflared_bin:
        print("🌐 Đang khởi tạo đường truyền TryCloudflare tốc độ cao...", flush=True)
        tunnel_proc = subprocess.Popen(
            [cloudflared_bin, "tunnel", "--url", f"http://127.0.0.1:{PORT}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        # Parse tunnel url from stderr
        start_time = time.time()
        while time.time() - start_time < 15:
            line = tunnel_proc.stderr.readline()
            if not line:
                time.sleep(0.2)
                continue
            
            # Match trycloudflare url
            match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
            if match:
                public_url = match.group(0)
                break

        if public_url:
            with open(URL_FILE, "w", encoding="utf-8") as f:
                f.write(public_url)
            print("\n" + "=" * 64, flush=True)
            print(f"🎉 LINK TRUY CẬP ONLINE THỜI GIAN THỰC (TRYCLOUDFLARE):", flush=True)
            print(f"👉 {public_url}", flush=True)
            print("=" * 64 + "\n", flush=True)
        else:
            print("⚠️ Không lấy được link trycloudflare kịp thời, vui lòng dùng http://127.0.0.1:8888", flush=True)
    else:
        print("⚠️ Chưa cài đặt cloudflared (brew install cloudflared). Dùng http://127.0.0.1:8888", flush=True)

    # Keep alive
    try:
        server_proc.wait()
    except KeyboardInterrupt:
        print("\n👋 Đang dừng Media Hub Dashboard...")
        server_proc.terminate()

if __name__ == "__main__":
    start_hub()
