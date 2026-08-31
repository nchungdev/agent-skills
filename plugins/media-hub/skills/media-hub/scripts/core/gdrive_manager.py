#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Drive & Plex Library Core Module
"""

import subprocess
import json
import os
import shutil
import time
import threading

RCLONE_BIN = shutil.which("rclone") or "/opt/homebrew/bin/rclone"

def find_rclone_config():
    candidates = [
        os.path.expanduser("~/.config/rclone/rclone.conf"),
        "/Users/chungnh/.config/rclone/rclone.conf",
        "/Users/chungnh/.agy-account2/.config/rclone/rclone.conf",
        os.path.expanduser("~/.rclone.conf"),
        "/Users/chungnh/.rclone.conf"
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]

RCLONE_CONFIG = find_rclone_config()
BASE_GDRIVE = "gdrive:Phim/TV Shows"
CACHE_FILE = "/Volumes/512GB/AI Workspace/antigravity-media-hub/gdrive_cache.json"
DEFAULT_TTL = 900  # 15 minutes

class GDriveManager:
    def __init__(self, rclone_bin=RCLONE_BIN, rclone_config=None, cache_file=CACHE_FILE):
        self.rclone_bin = rclone_bin if (isinstance(rclone_bin, str) and os.path.exists(rclone_bin)) else "rclone"
        self.rclone_config = rclone_config or find_rclone_config()
        self.cache_file = cache_file
        self.lock = threading.Lock()
        self._cache = self._load_cache()

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_cache(self):
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _run(self, args):
        cmd = [self.rclone_bin, "--config", self.rclone_config] + args
        return subprocess.run(cmd, capture_output=True, text=True)

    def list_tv_shows(self, force_refresh=False):
        cache_key = "__all_shows__"
        now = time.time()
        
        with self.lock:
            cached = self._cache.get(cache_key)
            if not force_refresh and cached and (now - cached.get("timestamp", 0) < DEFAULT_TTL):
                return cached.get("data", [])

        res = self._run(["lsf", BASE_GDRIVE, "--dirs-only", "--timeout=10s"])
        if res.returncode != 0:
            return self._cache.get(cache_key, {}).get("data", [])
            
        shows = []
        for line in res.stdout.splitlines():
            s = line.strip().strip("/")
            if s:
                shows.append({"name": s, "path": f"{BASE_GDRIVE}/{s}"})

        with self.lock:
            self._cache[cache_key] = {"data": shows, "timestamp": now}
            self._save_cache()
            
        return shows

    def get_show_seasons(self, show_name, force_refresh=False):
        cache_key = f"seasons:{show_name}"
        now = time.time()
        
        with self.lock:
            cached = self._cache.get(cache_key)
            if not force_refresh and cached and (now - cached.get("timestamp", 0) < DEFAULT_TTL):
                return cached.get("data", [])

        dest = f"{BASE_GDRIVE}/{show_name}"
        res = self._run(["lsf", dest, "--dirs-only", "--timeout=10s"])
        if res.returncode != 0:
            return self._cache.get(cache_key, {}).get("data", [])
            
        seasons = [line.strip().strip("/") for line in res.stdout.splitlines() if line.strip()]

        with self.lock:
            self._cache[cache_key] = {"data": seasons, "timestamp": now}
            self._save_cache()
            
        return seasons

    def get_season_files(self, show_name, season_name, force_refresh=False):
        cache_key = f"files:{show_name}/{season_name}"
        now = time.time()
        
        with self.lock:
            cached = self._cache.get(cache_key)
            if not force_refresh and cached and (now - cached.get("timestamp", 0) < DEFAULT_TTL):
                return cached.get("data", [])

        dest = f"{BASE_GDRIVE}/{show_name}/{season_name}"
        res = self._run(["lsf", dest, "--timeout=10s"])
        if res.returncode != 0:
            return self._cache.get(cache_key, {}).get("data", [])
            
        files = []
        for line in res.stdout.splitlines():
            f = line.strip()
            if f and not f.endswith("/"):
                files.append(f)

        with self.lock:
            self._cache[cache_key] = {"data": files, "timestamp": now}
            self._save_cache()
            
        return files

    def get_cache_version(self):
        return getattr(self, "manual_version", 1)

    def bump_version(self):
        self.manual_version = getattr(self, "manual_version", 1) + 1
        return self.manual_version
