#!/usr/bin/env python3
"""
Media Downloader interactive environment setup with secret masking.
Configures Aria2 RPC, TorBox Debrid API, and Prowlarr API.
"""

import os
import sys
import getpass
import json
from pathlib import Path

def mask_token(token):
    if not token or len(token) < 8:
        return "[REDACTED]"
    return token[:4] + "..." + token[-4:]

def main():
    print("🧲 Media Downloader Environment Setup")
    print("---------------------------------------")
    
    agent_dir = Path.cwd() / ".agent"
    agent_dir.mkdir(parents=True, exist_ok=True)
    creds_file = agent_dir / "downloader_config.json"
    
    config = {}
    if creds_file.exists():
        try:
            with open(creds_file) as f:
                config = json.load(f)
        except Exception:
            config = {}

    # 1. Aria2 RPC
    print("\n1. ⚡ Cấu hình Aria2c RPC:")
    curr_rpc = config.get("ARIA2_RPC_URL", "http://127.0.0.1:6800/jsonrpc")
    rpc_in = input(f"Aria2 RPC URL (mặc định: {curr_rpc}): ").strip()
    config["ARIA2_RPC_URL"] = rpc_in or curr_rpc
    
    curr_sec = config.get("ARIA2_SECRET", "")
    sec_prompt = f"Aria2 Secret Token (hiện tại: {mask_token(curr_sec)}, Enter để giữ nguyên): " if curr_sec else "Aria2 Secret Token (ẩn ký tự): "
    sec_in = getpass.getpass(sec_prompt).strip()
    if sec_in:
        config["ARIA2_SECRET"] = sec_in

    # 2. TorBox API
    print("\n2. ☁️ Cấu hình TorBox Debrid Cloud:")
    curr_torbox = config.get("TORBOX_API_KEY", "")
    tb_prompt = f"TorBox API Key (hiện tại: {mask_token(curr_torbox)}, Enter để giữ nguyên): " if curr_torbox else "TorBox API Key (ẩn ký tự): "
    tb_in = getpass.getpass(tb_prompt).strip()
    if tb_in:
        config["TORBOX_API_KEY"] = tb_in

    # 3. Prowlarr
    print("\n3. 🔍 Cấu hình Prowlarr Indexer:")
    curr_prowlarr_url = config.get("PROWLARR_URL", "http://localhost:9696")
    prowlarr_in = input(f"Prowlarr URL (mặc định: {curr_prowlarr_url}): ").strip()
    config["PROWLARR_URL"] = prowlarr_in or curr_prowlarr_url

    curr_prowlarr_key = config.get("PROWLARR_API_KEY", "")
    pr_prompt = f"Prowlarr API Key (hiện tại: {mask_token(curr_prowlarr_key)}, Enter để giữ nguyên): " if curr_prowlarr_key else "Prowlarr API Key (ẩn ký tự): "
    pr_in = getpass.getpass(pr_prompt).strip()
    if pr_in:
        config["PROWLARR_API_KEY"] = pr_in

    # Save to .agent/downloader_config.json
    with open(creds_file, "w") as f:
        json.dump(config, f, indent=2)

    # Also update ~/.env safely
    env_file = Path.home() / ".env"
    existing_lines = []
    if env_file.exists():
        with open(env_file) as f:
            existing_lines = [l for l in f if not any(l.startswith(k + "=") for k in ["ARIA2_RPC_URL", "ARIA2_SECRET", "TORBOX_API_KEY", "PROWLARR_URL", "PROWLARR_API_KEY"])]
    
    for k, v in config.items():
        if v:
            existing_lines.append(f"{k}={v}\n")
    
    with open(env_file, "w") as f:
        f.writelines(existing_lines)

    print("\n---------------------------------------")
    print(f"✅ Đã lưu cấu hình an toàn vào {creds_file} và ~/.env")
    print(f"* Aria2 RPC: {config.get('ARIA2_RPC_URL')}")
    print(f"* TorBox: {mask_token(config.get('TORBOX_API_KEY', ''))}")
    print(f"* Prowlarr: {config.get('PROWLARR_URL')} (Key: {mask_token(config.get('PROWLARR_API_KEY', ''))})")

if __name__ == "__main__":
    main()
