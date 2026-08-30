#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TorBox API Client with Secure Interactive Auth & Config Management
torbox-manager — torbox_client.py
"""

import os
import json
import urllib.request
import urllib.parse
import urllib.error

CONFIG_DIR = os.path.expanduser("~/.config/torbox")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
API_BASE_URL = "https://api.torbox.app/v1/api"

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
        """Lưu API Key an toàn vào file cấu hình người dùng"""
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"api_key": api_key.strip()}, f, indent=2)
        # Set file permission to 0600 (chỉ chủ sở hữu đọc/ghi)
        try:
            os.chmod(CONFIG_FILE, 0o600)
        except Exception:
            pass

    @classmethod
    def clear_api_key(cls):
        """Đăng xuất / xóa API Key đã lưu"""
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)

    def is_authenticated(self):
        return bool(self.api_key)

    def _request(self, endpoint, method="GET", data=None, params=None):
        if not self.api_key:
            return {"success": False, "error": "Chưa đăng nhập TorBox. Vui lòng chạy: torbox login"}

        url = f"{API_BASE_URL}/{endpoint}"
        if params:
            query = urllib.parse.urlencode(params)
            url = f"{url}?{query}"

        req = urllib.request.Request(url, method=method)
        req.add_header("Authorization", f"Bearer {self.api_key}")
        req.add_header("User-Agent", "TorBoxManager/1.0")

        if data is not None:
            if isinstance(data, dict):
                req.add_header("Content-Type", "application/x-www-form-urlencoded")
                encoded_data = urllib.parse.urlencode(data).encode("utf-8")
            else:
                encoded_data = data
        else:
            encoded_data = None

        try:
            with urllib.request.urlopen(req, data=encoded_data, timeout=30) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            try:
                return json.loads(err_body)
            except Exception:
                return {"success": False, "error": f"HTTP {e.code}: {err_body}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_user_info(self):
        """Lấy thông tin tài khoản và gói cước"""
        return self._request("user/me")

    def list_torrents(self, bypass_cache=True):
        """Lấy danh sách tất cả torrents trong tài khoản"""
        return self._request("torrents/mylist", params={"bypass_cache": "true" if bypass_cache else "false"})

    def add_torrent_magnet(self, magnet_link, seed=1, allow_zip=True):
        """Thêm torrent bằng Magnet Link"""
        data = {
            "magnet": magnet_link,
            "seed": str(seed),
            "allow_zip": "true" if allow_zip else "false"
        }
        return self._request("torrents/createtorrent", method="POST", data=data)

    def add_torrent_file(self, file_path, seed=1, allow_zip=True):
        """Thêm torrent bằng file .torrent vật lý"""
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
        req = urllib.request.Request(url, data=payload, method="POST")
        req.add_header("Authorization", f"Bearer {self.api_key}")
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
        
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            return {"success": False, "error": str(e)}

    def control_torrent(self, torrent_id, operation):
        """Điều khiển torrent: 'delete', 'pause', 'resume', 'reannounce'"""
        data = {
            "torrent_id": str(torrent_id),
            "operation": operation
        }
        return self._request("torrents/controltorrent", method="POST", data=data)

    def get_download_link(self, torrent_id, file_id=None, as_zip=True):
        """Lấy Direct Download Link (CDN DDL) từ TorBox"""
        params = {
            "token": self.api_key,
            "torrent_id": str(torrent_id)
        }
        if as_zip:
            params["zip"] = "true"
        elif file_id is not None:
            params["file_id"] = str(file_id)
            
        return self._request("torrents/requestdl", params=params)
