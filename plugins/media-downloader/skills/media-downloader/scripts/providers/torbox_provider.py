import os
import sys
import json
import time
import urllib.request
import urllib.parse
from pathlib import Path

TORBOX_API_BASE = "https://api.torbox.app/v1/api"

def get_torbox_token():
    """Retrieve TorBox token from env, ~/.env, or settings.json."""
    token = os.environ.get("TORBOX_API_TOKEN") or os.environ.get("TORBOX_TOKEN")
    if token:
        return token.strip()
    
    env_file = Path.home() / ".env"
    if env_file.is_file():
        with open(env_file, "r") as f:
            for line in f:
                if line.startswith("TORBOX_API_TOKEN=") or line.startswith("TORBOX_TOKEN="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    
    settings_file = Path.home() / ".gemini" / "config" / "media_hub_settings.json"
    if settings_file.is_file():
        try:
            with open(settings_file, "r") as f:
                data = json.load(f)
                return data.get("torbox_token", "").strip()
        except Exception:
            pass
    return None

def torbox_request(endpoint, method="GET", data=None, token=None):
    if not token:
        token = get_torbox_token()
    if not token:
        return {"error": "Missing TorBox API Token"}

    url = f"{TORBOX_API_BASE}/{endpoint.lstrip('/')}"
    headers = {"Authorization": f"Bearer {token}"}
    req_data = None
    if data:
        if isinstance(data, dict):
            req_data = urllib.parse.urlencode(data).encode("utf-8")
        elif isinstance(data, bytes):
            req_data = data
    
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode("utf-8"))
        except Exception:
            return {"error": f"HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"error": str(e)}

def list_torrents():
    """List all torrents in TorBox Cloud."""
    return torbox_request("torrents/mylist?bypass_cache=true")

def add_torrent(magnet_or_url):
    """Add a magnet link or torrent URL to TorBox Cloud."""
    data = {"magnet": magnet_or_url}
    return torbox_request("torrents/createtorrent", method="POST", data=data)
