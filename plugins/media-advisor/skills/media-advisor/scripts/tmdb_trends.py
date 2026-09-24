#!/usr/bin/env python3
"""
TMDb Trends & Theatrical / Streaming Ingestion Engine.
Fetches real-time cinema and OTT releases, downloading local w185 thumbnails for visual cards.
"""

import os
import re
import json
import urllib.request
import urllib.parse
from pathlib import Path
from typing import List, Dict, Any, Optional

def get_tmdb_api_key() -> Optional[str]:
    key = os.environ.get("TMDB_API_KEY")
    if key:
        return key

    cred_file = Path.cwd() / ".agent" / "credentials.json"
    if cred_file.exists():
        try:
            with open(cred_file, "r") as f:
                creds = json.load(f)
                if "TMDB_API_KEY" in creds:
                    return creds["TMDB_API_KEY"]
        except Exception:
            pass

    env_file = Path.home() / ".env"
    if env_file.exists():
        try:
            with open(env_file, "r") as f:
                for line in f:
                    if line.startswith("TMDB_API_KEY="):
                        return line.strip().split("=", 1)[1].strip("\"'")
        except Exception:
            pass
    return None

class TMDbTrends:
    BASE_URL = "https://api.themoviedb.org/3"
    IMAGE_BASE = "https://image.tmdb.org/t/p/w185"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or get_tmdb_api_key()
        self.cache_dir = Path.home() / ".cache" / "media-advisor" / "posters"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.api_key:
            return {}
        p = params or {}
        p["api_key"] = self.api_key
        p.setdefault("language", "vi-VN")
        query_str = urllib.parse.urlencode(p)
        url = f"{self.BASE_URL}{endpoint}?{query_str}"
        req = urllib.request.Request(url, headers={"User-Agent": "Antigravity-MediaAdvisor/1.0", "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except Exception:
            p["language"] = "en-US"
            query_str = urllib.parse.urlencode(p)
            url = f"{self.BASE_URL}{endpoint}?{query_str}"
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Antigravity-MediaAdvisor/1.0"}), timeout=10) as resp:
                    return json.loads(resp.read().decode())
            except Exception:
                return {}

    def ensure_local_poster(self, poster_path: Optional[str], slug: str) -> Optional[str]:
        """Downloads poster to local cache to bypass web UI CSP / sandbox restrictions."""
        if not poster_path:
            return None
        clean_slug = "".join(c if c.isalnum() else "_" for c in slug).strip("_")
        local_path = self.cache_dir / f"{clean_slug}_w185.jpg"
        if local_path.exists() and local_path.stat().st_size > 1000:
            return str(local_path)

        url = f"{self.IMAGE_BASE}{poster_path}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                content = resp.read()
                if len(content) > 1000:
                    with open(local_path, "wb") as f:
                        f.write(content)
                    return str(local_path)
        except Exception:
            pass
        return None

    def get_details_by_id(self, tmdb_id: int, media_type: str = "movie") -> Optional[Dict[str, Any]]:
        """Fetch item details directly by TMDb ID."""
        endpoint = f"/{media_type}/{tmdb_id}"
        data = self._get(endpoint)
        if not data or "id" not in data:
            if media_type == "movie":
                data = self._get(f"/tv/{tmdb_id}")
            else:
                data = self._get(f"/movie/{tmdb_id}")
        if not data or "id" not in data:
            return None

        title = data.get("title") or data.get("name")
        poster = self.ensure_local_poster(data.get("poster_path"), title or f"item_{tmdb_id}")
        return {
            "tmdb_id": data.get("id"),
            "title": title,
            "original_title": data.get("original_title") or data.get("original_name"),
            "release_date": data.get("release_date") or data.get("first_air_date"),
            "vote_average": data.get("vote_average", 0.0),
            "vote_count": data.get("vote_count", 0),
            "overview": data.get("overview") or "",
            "poster_local": poster,
            "type": "Movie" if "release_date" in data else "TV Show"
        }

    def get_theatrical_releases(self, limit: int = 10) -> List[Dict[str, Any]]:
        data = self._get("/movie/now_playing", {"page": 1})
        results = data.get("results", [])
        items = []
        for m in results[:limit]:
            poster = self.ensure_local_poster(m.get("poster_path"), m.get("title", "movie"))
            items.append({
                "tmdb_id": m.get("id"),
                "title": m.get("title") or m.get("original_title"),
                "original_title": m.get("original_title"),
                "release_date": m.get("release_date"),
                "vote_average": m.get("vote_average", 0.0),
                "vote_count": m.get("vote_count", 0),
                "overview": m.get("overview") or "",
                "poster_local": poster,
                "type": "Movie"
            })
        return items

    def get_trending(self, media_type: str = "all", time_window: str = "week", limit: int = 10) -> List[Dict[str, Any]]:
        data = self._get(f"/trending/{media_type}/{time_window}")
        results = data.get("results", [])
        items = []
        for m in results[:limit]:
            title = m.get("title") or m.get("name") or m.get("original_title") or m.get("original_name")
            poster = self.ensure_local_poster(m.get("poster_path"), title or "item")
            items.append({
                "tmdb_id": m.get("id"),
                "title": title,
                "original_title": m.get("original_title") or m.get("original_name"),
                "release_date": m.get("release_date") or m.get("first_air_date"),
                "vote_average": m.get("vote_average", 0.0),
                "vote_count": m.get("vote_count", 0),
                "overview": m.get("overview") or "",
                "poster_local": poster,
                "type": "Movie" if m.get("media_type") == "movie" else "TV Show"
            })
        return items

    def search_multi(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        clean_q = re.sub(r"\[.*?\]|\(.*?\)|\*|🎶|BẢN LỒNG TIẾNG", "", query).strip()
        data = self._get("/search/multi", {"query": clean_q or query, "page": 1})
        results = data.get("results", [])
        items = []
        for m in results[:limit]:
            if m.get("media_type") not in ("movie", "tv"):
                continue
            title = m.get("title") or m.get("name")
            poster = self.ensure_local_poster(m.get("poster_path"), title or "item")
            items.append({
                "tmdb_id": m.get("id"),
                "title": title,
                "release_date": m.get("release_date") or m.get("first_air_date"),
                "vote_average": m.get("vote_average", 0.0),
                "vote_count": m.get("vote_count", 0),
                "overview": m.get("overview") or "",
                "poster_local": poster,
                "type": "Movie" if m.get("media_type") == "movie" else "TV Show"
            })
        return items
