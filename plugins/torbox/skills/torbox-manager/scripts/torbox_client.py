#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TorBox API Client with JDownloader-Grade Engine (Retry-After Parsing,
Exponential Backoff with Jitter, Real Browser Header Emulation)
torbox-manager — torbox_client.py
"""

import os
import json
import urllib.request
import urllib.parse
import urllib.error
import time
import random

CONFIG_DIR = os.path.expanduser("~/.config/torbox")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
API_BASE_URL = "https://api.torbox.app/v1/api"

# JDownloader 2 Core Settings
JD_BASE_DELAY = 5.0
JD_MAX_BACKOFF = 180.0

class TorBoxClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("TORBOX_API_KEY")
        if not self.api_key and os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    self.api_key = cfg.get("api_key")
            except Exception:
                pass

    @classmethod
    def save_api_key(cls, api_key):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"api_key": api_key.strip()}, f, indent=2)
        try:
            os.chmod(CONFIG_FILE, 0o600)
        except Exception:
            pass

    @classmethod
    def clear_api_key(cls):
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)

    def is_authenticated(self):
        return bool(self.api_key)

    def _request(self, endpoint, method="GET", data=None, params=None, max_retries=4):
        if not self.api_key:
            return {"success": False, "error": "Chưa đăng nhập TorBox. Vui lòng chạy: torbox login"}

        url = f"{API_BASE_URL}/{endpoint}"
        if params:
            query = urllib.parse.urlencode(params)
            url = f"{url}?{query}"

        # JDownloader-grade Real Browser Header Emulation
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Sec-Ch-Ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"macOS"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Referer": "https://torbox.app/",
            "Origin": "https://torbox.app"
        }

        if data is not None:
            if isinstance(data, dict):
                headers["Content-Type"] = "application/x-www-form-urlencoded"
                encoded_data = urllib.parse.urlencode(data).encode("utf-8")
            else:
                encoded_data = data
        else:
            encoded_data = None

        retry_count = 0
        while retry_count <= max_retries:
            req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    raw = resp.read().decode("utf-8")
                    return json.loads(raw)
                    
            except urllib.error.HTTPError as e:
                # 1. Check for Rate Limit (HTTP 429) or Server Overload (503)
                if e.code in [429, 503, 504]:
                    retry_count += 1
                    # A. Parse Retry-After header if present
                    retry_after = e.headers.get("Retry-After")
                    if retry_after and retry_after.isdigit():
                        wait_time = float(retry_after) + random.uniform(1.0, 4.0)
                        print(f"⏱️ [JD2 Engine] Máy chủ yêu cầu chờ (Retry-After: {retry_after}s). Tạm dừng {wait_time:.1f}s...")
                    else:
                        # B. JDownloader Exponential Backoff with Jitter
                        wait_time = min(JD_MAX_BACKOFF, (JD_BASE_DELAY * (2 ** retry_count)) + random.uniform(5.0, 25.0))
                        print(f"⚠️ [JD2 Engine] Rate-Limit ({e.code}). Áp dụng Exponential Backoff lần {retry_count}: Nghỉ {wait_time:.1f}s...")
                        
                    time.sleep(wait_time)
                    if retry_count <= max_retries:
                        continue
                        
                err_body = e.read().decode("utf-8", errors="ignore")
                try:
                    return json.loads(err_body)
                except Exception:
                    return {"success": False, "error": f"HTTP {e.code}: {err_body}"}
            except Exception as e:
                retry_count += 1
                if retry_count <= max_retries:
                    wait_time = random.uniform(3.0, 8.0)
                    time.sleep(wait_time)
                    continue
                return {"success": False, "error": str(e)}

        return {"success": False, "error": "Đã vượt quá số lần thử lại tối đa (Max retries exceeded)"}

    def get_user_info(self):
        return self._request("user/me")

    def list_torrents(self, bypass_cache=True):
        return self._request("torrents/mylist", params={"bypass_cache": "true" if bypass_cache else "false"})

    def add_torrent_magnet(self, magnet_link, seed=1, allow_zip=True):
        data = {
            "magnet": magnet_link,
            "seed": str(seed),
            "allow_zip": "true" if allow_zip else "false"
        }
        return self._request("torrents/createtorrent", method="POST", data=data)

    def add_torrent_file(self, file_path, seed=1, allow_zip=True):
        boundary = "----WebKitFormBoundaryTorBoxClient"
        body = []
        body.append(f"--{boundary}".encode())
        body.append(b'Content-Disposition: form-data; name="seed"')
        body.append(b'')
        body.append(str(seed).encode())
        body.append(f"--{boundary}".encode())
        body.append(b'Content-Disposition: form-data; name="allow_zip"')
        body.append(b'')
        body.append(b'true' if allow_zip else b'false')

        filename = os.path.basename(file_path)
        body.append(f"--{boundary}".encode())
        body.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"'.encode())
        body.append(b'Content-Type: application/x-bittorrent')
        body.append(b'')
        with open(file_path, "rb") as f:
            body.append(f.read())
        body.append(f"--{boundary}--".encode())
        body.append(b'')
        payload = b"\r\n".join(body)

        url = f"{API_BASE_URL}/torrents/createtorrent"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        }
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            return {"success": False, "error": str(e)}

    def control_torrent(self, torrent_id, operation):
        data = {
            "torrent_id": str(torrent_id),
            "operation": operation
        }
        return self._request("torrents/controltorrent", method="POST", data=data)

    def get_download_link(self, torrent_id, file_id=None, as_zip=True):
        params = {
            "token": self.api_key,
            "torrent_id": str(torrent_id)
        }
        if as_zip:
            params["zip"] = "true"
        elif file_id is not None:
            params["file_id"] = str(file_id)
            
        return self._request("torrents/requestdl", params=params)
