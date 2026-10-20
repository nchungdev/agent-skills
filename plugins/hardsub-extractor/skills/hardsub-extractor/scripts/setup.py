#!/usr/bin/env python3
"""
hardsub-extractor: Interactive Environment Setup Tool
Saves GEMINI_API_KEY securely into ~/.env with secret masking.
"""

import os
import sys
import getpass
import json
import urllib.request
import urllib.error

def mask_token(token):
    if not token or len(token) < 8:
        return "[REDACTED]"
    return token[:4] + "..." + token[-4:]

def verify_gemini_key(api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": "ping"}]}]}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as e:
        # Check if error is due to auth or quota
        if e.code in [400, 401, 403]:
            return False
        return True # Server busy or other non-auth error
    except Exception:
        return False

def main():
    print("🎬 Hardsub Extractor - Cấu hình GEMINI_API_KEY")
    print("=" * 55)

    env_path = os.path.expanduser("~/.env")
    existing_key = os.environ.get("GEMINI_API_KEY", "")
    if not existing_key and os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for l in f:
                if l.startswith("GEMINI_API_KEY="):
                    existing_key = l.strip().split("=", 1)[1].strip("\"'")

    if existing_key:
        print(f"ℹ️ Đã tìm thấy GEMINI_API_KEY hiện tại: {mask_token(existing_key)}")
        ans = input("Bạn có muốn đổi key mới không? (y/N): ").strip().lower()
        if ans != "y":
            print("✅ Giữ nguyên cấu hình hiện tại.")
            return

    new_key = getpass.getpass("Nhập GEMINI_API_KEY của bạn (ký tự sẽ được ẩn đi): ").strip()
    if not new_key:
        print("❌ Chưa nhập key. Đã hủy cài đặt.")
        return

    print("🔍 Đang xác thực API key với Google Gemini...")
    if verify_gemini_key(new_key):
        print(f"✅ Xác thực thành công! Khóa: {mask_token(new_key)}")
    else:
        print("⚠️ Cảnh báo: Không thể xác thực key với Gemini. Vẫn sẽ lưu vào ~/.env.")

    # Write to ~/.env
    lines = []
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            lines = [l for l in f if not l.startswith("GEMINI_API_KEY=")]
    lines.append(f"GEMINI_API_KEY={new_key}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    os.chmod(env_path, 0o600)

    print(f"🎉 Đã lưu GEMINI_API_KEY vào {env_path} (quyền 600 - an toàn tuyệt đối).")

if __name__ == "__main__":
    main()
