#!/usr/bin/env python3
"""
Remote REST API Client for Plex & Jellyfin.
Allows connecting to media servers across LAN, remote NAS, or cloud instances using API Tokens.
Supports automated connectivity validation and seamless fallback to SQLite or Internet.
"""

import os
import json
import urllib.request
import urllib.parse
from pathlib import Path
from typing import List, Dict, Any, Optional

def mask_token(token: Optional[str]) -> str:
    if not token or len(token) < 8:
        return "[REDACTED]"
    return token[:4] + "..." + token[-4:]

class PlexApiClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.token = token

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        p = params or {}
        p["X-Plex-Token"] = self.token
        query_str = urllib.parse.urlencode(p)
        url = f"{self.base_url}{endpoint}?{query_str}"
        req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "Antigravity-MediaAdvisor/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                return json.loads(resp.read().decode())
        except Exception:
            return None

    def verify(self) -> bool:
        """Verifies if the Plex URL and Token are valid."""
        data = self._get("/identity")
        return bool(data and "MediaContainer" in data)

    def get_in_progress(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Fetches On Deck / Continue Watching items from Plex."""
        data = self._get("/library/onDeck")
        if not data:
            return []
        
        items = data.get("MediaContainer", {}).get("Metadata", [])
        results = []
        for it in items[:limit]:
            dur_ms = it.get("duration", 0)
            offset_ms = it.get("viewOffset", 0)
            pct = int((offset_ms / dur_ms * 100)) if dur_ms > 0 else 0
            
            show_title = it.get("grandparentTitle")
            ep_title = it.get("title")
            season_title = it.get("parentTitle")
            
            if show_title:
                display_title = f"{show_title} - {season_title or ''} - {ep_title}"
                search_title = show_title
            else:
                display_title = ep_title
                search_title = ep_title

            results.append({
                "id": it.get("ratingKey"),
                "title": display_title,
                "search_title": search_title,
                "year": it.get("year"),
                "type": "Movie" if it.get("type") == "movie" else "Episode",
                "offset_minutes": offset_ms // 60000,
                "duration_minutes": dur_ms // 60000,
                "progress_percent": pct,
                "summary": it.get("summary", ""),
                "nas_status": "🟢 Sẵn sàng xem trên Plex Server"
            })
        return results

    def get_unwatched(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetches unwatched movies from all movie sections in Plex."""
        sections_data = self._get("/library/sections")
        if not sections_data:
            return []

        sections = sections_data.get("MediaContainer", {}).get("Directory", [])
        movie_sections = [s["key"] for s in sections if s.get("type") == "movie"]

        results = []
        for sec_id in movie_sections:
            sec_data = self._get(f"/library/sections/{sec_id}/all", {
                "unwatched": "1",
                "sort": "rating:desc",
                "X-Plex-Container-Start": 0,
                "X-Plex-Container-Size": limit
            })
            if not sec_data:
                continue
            movies = sec_data.get("MediaContainer", {}).get("Metadata", [])
            for m in movies:
                results.append({
                    "id": m.get("ratingKey"),
                    "title": m.get("title"),
                    "year": m.get("year"),
                    "rating": float(m.get("rating")) if m.get("rating") else None,
                    "summary": m.get("summary", ""),
                    "duration_minutes": (m.get("duration", 0)) // 60000,
                    "type": "Movie",
                    "nas_status": "🟢 Sẵn sàng xem trên Plex Server"
                })
                if len(results) >= limit:
                    break
            if len(results) >= limit:
                break
        return results


class JellyfinApiClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        p = params or {}
        p["api_key"] = self.api_key
        query_str = urllib.parse.urlencode(p)
        url = f"{self.base_url}{endpoint}?{query_str}"
        headers = {
            "Accept": "application/json",
            "User-Agent": "Antigravity-MediaAdvisor/1.0",
            "X-Emby-Token": self.api_key
        }
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                return json.loads(resp.read().decode())
        except Exception:
            return None

    def verify(self) -> bool:
        """Verifies if the Jellyfin URL and API Key are valid."""
        data = self._get("/System/Info")
        return bool(data and "ServerName" in data)

    def get_users(self) -> List[Dict[str, Any]]:
        data = self._get("/Users")
        return data if isinstance(data, list) else []

    def get_in_progress(self, user_id: Optional[str] = None, limit: int = 15) -> List[Dict[str, Any]]:
        """Fetches Resume / In-progress items from Jellyfin."""
        uid = user_id
        if not uid:
            users = self.get_users()
            uid = users[0].get("Id") if users else None
        
        endpoint = f"/User/{uid}/Items/Resume" if uid else "/Items"
        params = {"Limit": limit, "MediaTypes": "Video"} if not uid else {"Limit": limit}
        data = self._get(endpoint, params)
        if not data:
            return []

        items = data.get("Items", [])
        results = []
        for it in items[:limit]:
            dur_ticks = it.get("RunTimeTicks", 0)
            offset_ticks = it.get("UserData", {}).get("PlaybackPositionTicks", 0)
            pct = int((offset_ticks / dur_ticks * 100)) if dur_ticks > 0 else 0
            
            show_title = it.get("SeriesName")
            ep_title = it.get("Name")
            if show_title:
                display_title = f"{show_title} - {ep_title}"
                search_title = show_title
            else:
                display_title = ep_title
                search_title = ep_title

            results.append({
                "id": it.get("Id"),
                "title": display_title,
                "search_title": search_title,
                "year": it.get("ProductionYear"),
                "type": "Movie" if it.get("Type") == "Movie" else "Episode",
                "offset_minutes": int(offset_ticks / 10000000 / 60),
                "duration_minutes": int(dur_ticks / 10000000 / 60),
                "progress_percent": pct,
                "summary": it.get("Overview", ""),
                "nas_status": "🟢 Sẵn sàng xem trên Jellyfin Server"
            })
        return results

    def get_unwatched(self, user_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetches unplayed movies/shows from Jellyfin."""
        uid = user_id
        if not uid:
            users = self.get_users()
            uid = users[0].get("Id") if users else None

        endpoint = f"/Users/{uid}/Items" if uid else "/Items"
        params = {
            "Filters": "IsUnplayed",
            "IncludeItemTypes": "Movie",
            "SortBy": "CommunityRating,SortName",
            "SortOrder": "Descending",
            "Limit": limit,
            "Recursive": "true"
        }
        data = self._get(endpoint, params)
        if not data:
            return []

        results = []
        for m in data.get("Items", [])[:limit]:
            results.append({
                "id": m.get("Id"),
                "title": m.get("Name"),
                "year": m.get("ProductionYear"),
                "rating": m.get("CommunityRating"),
                "summary": m.get("Overview", ""),
                "duration_minutes": int(m.get("RunTimeTicks", 0) / 10000000 / 60),
                "type": "Movie",
                "nas_status": "🟢 Sẵn sàng xem trên Jellyfin Server"
            })
        return results

if __name__ == "__main__":
    # Test local Plex API verification if token exists
    pref_path = "/home/chungnh/appdata/plex/Library/Application Support/Plex Media Server/Preferences.xml"
    if os.path.exists(pref_path):
        import re
        with open(pref_path) as f:
            match = re.search(r'PlexOnlineToken=\"([^\"]+)\"', f.read())
            if match:
                client = PlexApiClient("http://127.0.0.1:32400", match.group(1))
                print("Plex API Key verified:", client.verify())
                print("Plex in progress sample count:", len(client.get_in_progress(2)))
