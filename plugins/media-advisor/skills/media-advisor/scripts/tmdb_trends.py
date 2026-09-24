#!/usr/bin/env python3
"""
TMDb Trends, Streaming Providers & Discover Engine.
Fetches real-time cinema and OTT releases, downloads local w185 thumbnails,
resolves where to watch (Netflix, Apple TV+, etc.), and discovers movies by surveyed taste.
"""

import os
import re
import json
import urllib.request
import urllib.parse
from pathlib import Path
from typing import List, Dict, Any, Optional

GENRE_MAP = {
    "action": 28, "hành động": 28,
    "adventure": 12, "phiêu lưu": 12,
    "animation": 16, "anime": 16, "hoạt hình": 16,
    "comedy": 35, "hài": 35, "hài hước": 35,
    "crime": 80, "tội phạm": 80,
    "documentary": 99, "tài liệu": 99,
    "drama": 18, "chính kịch": 18, "tâm lý": 18,
    "family": 10751, "gia đình": 10751,
    "fantasy": 14, "giả tưởng": 14,
    "history": 36, "lịch sử": 36,
    "horror": 27, "kinh dị": 27,
    "mystery": 9648, "bí ẩn": 9648, "trinh thám": 9648,
    "romance": 10749, "lãng mạn": 10749, "tình cảm": 10749,
    "science fiction": 878, "sci-fi": 878, "khoa học viễn tưởng": 878,
    "thriller": 53, "giật gân": 53,
    "war": 10752, "chiến tranh": 10752
}

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
        """Downloads poster to local cache to bypass web UI CSP restrictions."""
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

    def get_watch_providers(self, tmdb_id: int, media_type: str = "movie") -> List[str]:
        """Resolves where to stream (Netflix, Apple TV, Disney+, HBO Max, etc.)."""
        endpoint = f"/{media_type}/{tmdb_id}/watch/providers"
        data = self._get(endpoint)
        results = data.get("results", {})
        
        # Check VN first, then US as fallback
        providers = set()
        for region in ["VN", "US"]:
            reg_data = results.get(region, {})
            for p in reg_data.get("flatrate", []):
                name = p.get("provider_name")
                if name:
                    clean_name = name.replace("Standard with Ads", "").strip()
                    providers.add(clean_name)
        return list(providers)[:4]

    def get_details_by_id(self, tmdb_id: int, media_type: str = "movie") -> Optional[Dict[str, Any]]:
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
        actual_type = "Movie" if "release_date" in data else "TV Show"
        providers = self.get_watch_providers(data.get("id"), "movie" if actual_type == "Movie" else "tv")

        return {
            "tmdb_id": data.get("id"),
            "title": title,
            "original_title": data.get("original_title") or data.get("original_name"),
            "release_date": data.get("release_date") or data.get("first_air_date"),
            "vote_average": data.get("vote_average", 0.0),
            "vote_count": data.get("vote_count", 0),
            "overview": data.get("overview") or "",
            "poster_local": poster,
            "type": actual_type,
            "watch_providers": providers
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
                "type": "Movie",
                "watch_providers": ["Rạp Chiếu Phim (Theatrical)"]
            })
        return items

    def get_trending(self, media_type: str = "all", time_window: str = "week", limit: int = 10) -> List[Dict[str, Any]]:
        data = self._get(f"/trending/{media_type}/{time_window}")
        results = data.get("results", [])
        items = []
        for m in results[:limit]:
            title = m.get("title") or m.get("name") or m.get("original_title") or m.get("original_name")
            poster = self.ensure_local_poster(m.get("poster_path"), title or "item")
            m_type = "Movie" if m.get("media_type") == "movie" else "TV Show"
            providers = self.get_watch_providers(m.get("id"), "movie" if m_type == "Movie" else "tv")
            items.append({
                "tmdb_id": m.get("id"),
                "title": title,
                "original_title": m.get("original_title") or m.get("original_name"),
                "release_date": m.get("release_date") or m.get("first_air_date"),
                "vote_average": m.get("vote_average", 0.0),
                "vote_count": m.get("vote_count", 0),
                "overview": m.get("overview") or "",
                "poster_local": poster,
                "type": m_type,
                "watch_providers": providers
            })
        return items

    def discover_by_survey(self, genres: List[str] = None, min_rating: float = 7.0, min_votes: int = 300, limit: int = 10) -> List[Dict[str, Any]]:
        """Discovers top acclaimed cinema from the internet based on surveyed tastes."""
        params = {
            "sort_by": "vote_average.desc",
            "vote_count.gte": min_votes,
            "vote_average.gte": min_rating,
            "page": 1
        }
        
        # Resolve genre IDs
        genre_ids = []
        if genres:
            for g in genres:
                gid = GENRE_MAP.get(g.lower().strip())
                if gid:
                    genre_ids.append(str(gid))
        if genre_ids:
            params["with_genres"] = ",".join(genre_ids)

        data = self._get("/discover/movie", params)
        results = data.get("results", [])
        items = []
        for m in results[:limit]:
            title = m.get("title") or m.get("original_title")
            poster = self.ensure_local_poster(m.get("poster_path"), title or "item")
            providers = self.get_watch_providers(m.get("id"), "movie")
            items.append({
                "tmdb_id": m.get("id"),
                "title": title,
                "original_title": m.get("original_title"),
                "release_date": m.get("release_date"),
                "vote_average": m.get("vote_average", 0.0),
                "vote_count": m.get("vote_count", 0),
                "overview": m.get("overview") or "",
                "poster_local": poster,
                "type": "Movie",
                "watch_providers": providers
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
            m_type = "Movie" if m.get("media_type") == "movie" else "TV Show"
            providers = self.get_watch_providers(m.get("id"), "movie" if m_type == "Movie" else "tv")
            items.append({
                "tmdb_id": m.get("id"),
                "title": title,
                "release_date": m.get("release_date") or m.get("first_air_date"),
                "vote_average": m.get("vote_average", 0.0),
                "vote_count": m.get("vote_count", 0),
                "overview": m.get("overview") or "",
                "poster_local": poster,
                "type": m_type,
                "watch_providers": providers
            })
        return items
