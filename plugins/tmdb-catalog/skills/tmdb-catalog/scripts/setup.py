#!/usr/bin/env python3
"""
TMDb Catalog interactive setup tool with secret masking.
"""

import os
import sys
import getpass
import json
import urllib.request
import urllib.parse
from pathlib import Path

def mask_token(token):
    if not token or len(token) < 8:
        return "[REDACTED]"
    return token[:4] + "..." + token[-4:]

def verify_tmdb_key(api_key):
    url = f"https://api.themoviedb.org/3/authentication?api_key={api_key}"
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "Antigravity-TMDb/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return data.get("success", False)
    except Exception:
        return False

def main():
    print("🎬 TMDb Catalog Environment Setup")
    print("-----------------------------------")
    
    # Try reading existing
    existing_key = os.environ.get("TMDB_API_KEY")
    if not existing_key and os.path.exists(os.path.expanduser("~/.env")):
        with open(os.path.expanduser("~/.env")) as f:
            for l in f:
                if l.startswith("TMDB_API_KEY="):
                    existing_key = l.strip().split("=", 1)[1].strip("\"'")

    if existing_key:
        print(f"ℹ️ Đã tìm thấy TMDB_API_KEY hiện tại: {mask_token(existing_key)}")
        ans = input("Bạn có muốn đổi key mới không? (y/N): ").strip().lower()
        if ans != "y":
            print("Giữ nguyên cấu hình hiện tại.")
            return

    new_key = getpass.getpass("Nhập TMDB_API_KEY của bạn (ký tự sẽ được ẩn đi): ").strip()
    if not new_key:
        print("❌ Chưa nhập key. Hủy cài đặt.")
        return

    print("🔍 Đang xác thực khóa API với TMDb CDN...")
    if verify_tmdb_key(new_key):
        print(f"✅ Xác thực thành công! Khóa: {mask_token(new_key)}")
    else:
        print("⚠️ Cảnh báo: API TMDb trả về lỗi hoặc không phản hồi. Vẫn sẽ lưu key.")

    # Save to workspace .agent/credentials.json if in workspace
    agent_dir = Path.cwd() / ".agent"
    agent_dir.mkdir(parents=True, exist_ok=True)
    creds_file = agent_dir / "credentials.json"
    creds = {}
    if creds_file.exists():
        try:
            with open(creds_file) as f:
                creds = json.load(f)
        except Exception:
            creds = {}
    creds["TMDB_API_KEY"] = new_key
    with open(creds_file, "w") as f:
        json.dump(creds, f, indent=2)

    # Also save to ~/.env for backward compatibility
    env_file = Path.home() / ".env"
    lines = []
    if env_file.exists():
        with open(env_file) as f:
            lines = [l for l in f if not l.startswith("TMDB_API_KEY=")]
    lines.append(f"TMDB_API_KEY={new_key}\n")
    with open(env_file, "w") as f:
        f.writelines(lines)

    print(f"✅ Đã lưu cấu hình an toàn vào {creds_file} và ~/.env")

if __name__ == "__main__":
    main()
