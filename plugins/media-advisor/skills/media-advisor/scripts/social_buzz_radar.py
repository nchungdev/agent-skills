#!/usr/bin/env python3
"""
Social Buzz Radar & Forum / Video Ingestion Engine.
Scrapes and aggregates real-time movie discussions from:
1. Domestic Vietnamese Hubs: MoMo Cinema (verified tickets/reviews), Moveek (critic ratings),
   Vietnamese Reviewers (Phê Phim, Cuồng Phim, Lucas Luân Nguyễn), TikTok #reviewphim, and Facebook cinephile hubs.
2. Global Discussions: Reddit (r/movies, r/boxoffice) and Google Trends.
Includes persistent disk caching to avoid network spam and guarantee instant response times.
"""

import re
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Set
from vn_cinema_scraper import VnCinemaScraper, DiskCache

class SocialBuzzRadar:
    def __init__(self):
        self.cache = DiskCache(Path.home() / ".cache" / "agent-skills" / "buzz_radar")
        self.vn_scraper = VnCinemaScraper()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }

    def _get_url(self, url: str, timeout: int = 8) -> str:
        req = urllib.request.Request(url, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="ignore")
        except Exception:
            return ""

    def _post_ddg_lite(self, query: str) -> List[str]:
        """Queries DuckDuckGo Lite to capture public discussions without IP bans or captchas (Cached: 6h)."""
        cache_key = f"radar_ddg_{query}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        data = urllib.parse.urlencode({"q": query}).encode()
        req = urllib.request.Request("https://lite.duckduckgo.com/lite/", data=data, headers=self.headers)
        results = []
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                blocks = re.findall(r'<td class=[\'\"]result-snippet[\'\"]>(.*?)</td>', html, re.DOTALL)
                for b in blocks:
                    clean = re.sub(r'<[^>]+>', ' ', b).strip()
                    clean = " ".join(clean.split())
                    if len(clean) > 20:
                        results.append(clean)
        except Exception:
            pass

        self.cache.set(cache_key, results, ttl=21600)
        return results

    def fetch_reddit_buzz(self) -> List[Dict[str, str]]:
        """Scrapes Reddit r/movies and r/boxoffice official RSS feeds for discussion megathreads."""
        cached = self.cache.get("reddit_buzz")
        if cached is not None:
            return cached

        buzz_items = []
        for sub in ["movies", "boxoffice"]:
            url = f"https://www.reddit.com/r/{sub}/hot.rss"
            xml_data = self._get_url(url)
            if not xml_data:
                continue
            try:
                root = ET.fromstring(xml_data)
                ns = {"atom": "http://www.w3.org/2005/Atom"}
                for entry in root.findall("atom:entry", ns)[:12]:
                    title_elem = entry.find("atom:title", ns)
                    if title_elem is not None and title_elem.text:
                        text = title_elem.text.strip()
                        if any(k in text.lower() for k in ["discussion", "megathread", "review", "box office", "trailer", "weekend"]):
                            buzz_items.append({"source": f"Reddit r/{sub}", "title": text})
            except Exception:
                pass

        if buzz_items:
            self.cache.set("reddit_buzz", buzz_items, ttl=14400) # 4h
        return buzz_items

    def fetch_youtube_reviews(self) -> List[str]:
        """Captures viral movie reviews on YouTube from Vietnamese reviewers."""
        query = 'site:youtube.com "review phim" (Phê Phim OR "Cuồng Phim" OR "chiếu rạp") 2026'
        return self._post_ddg_lite(query)

    def fetch_tiktok_trends(self) -> List[str]:
        """Captures trending movies on TikTok review channels and hashtags."""
        query = 'site:tiktok.com "review phim" OR "#phimhay" OR "#reviewphim" 2026'
        return self._post_ddg_lite(query)

    def fetch_google_trends_vn(self) -> List[str]:
        """Fetches Google Trends Daily RSS for Vietnam to catch viral topics."""
        cached = self.cache.get("gtrends_vn")
        if cached is not None:
            return cached

        url = "https://trends.google.com/trending/rss?geo=VN"
        xml_data = self._get_url(url)
        if not xml_data:
            return []
        try:
            root = ET.fromstring(xml_data)
            items = root.findall(".//item")
            titles = []
            for it in items[:15]:
                t = it.find("title")
                if t is not None and t.text:
                    titles.append(t.text.strip())
            if titles:
                self.cache.set("gtrends_vn", titles, ttl=7200) # 2h
            return titles
        except Exception:
            return []

    def extract_film_entities(self, text_corpus: List[str]) -> Dict[str, int]:
        """Extracts and counts potential movie titles mentioned in discussion posts."""
        mention_counts: Dict[str, int] = {}
        patterns = [
            r'[\'\"“]([^\'\"“”]{3,40})[\'\"”]',
            r'(?:Phim|Review|Bom tấn|Siêu phẩm)[:\-–]\s*([^|–\-\n]{3,40})',
            r'\[(?:Review Phim|Review|Phim)\]\s*([^|–\-\n]{3,40})',
            r'Discussion Megathread\s*\(([^)]+)\)'
        ]
        
        for text in text_corpus:
            for p in patterns:
                matches = re.findall(p, text, re.IGNORECASE)
                for m in matches:
                    parts = [m] if "/" not in m else m.split("/")
                    for part in parts:
                        clean = re.sub(r'[\(\)\[\]#]', '', part).strip()
                        if 3 <= len(clean) <= 40 and not any(w in clean.lower() for w in ["việt nam", "chiếu rạp", "mới nhất", "bom tấn", "full hd", "official", "xem trọn bộ"]):
                            mention_counts[clean] = mention_counts.get(clean, 0) + 1
        return mention_counts

    def get_social_signals(self) -> Dict[str, Any]:
        """Aggregates all social feeds (MoMo, Moveek, YouTube, TikTok, Reddit) with caching."""
        # 1. Domestic signals (MoMo & Moveek)
        domestic_signals = self.vn_scraper.get_domestic_trending_signals()
        momo_hot = domestic_signals.get("momo_hot", {})

        # 2. Global & Video signals
        reddit_items = self.fetch_reddit_buzz()
        youtube_items = self.fetch_youtube_reviews()
        tiktok_items = self.fetch_tiktok_trends()
        gtrends_items = self.fetch_google_trends_vn()

        all_texts = [r["title"] for r in reddit_items] + youtube_items + tiktok_items + gtrends_items
        entities = self.extract_film_entities(all_texts)

        # Boost domestic MoMo titles into entities
        for t, d in momo_hot.items():
            entities[t] = entities.get(t, 0) + 5

        return {
            "reddit_count": len(reddit_items),
            "youtube_count": len(youtube_items),
            "tiktok_count": len(tiktok_items),
            "gtrends_count": len(gtrends_items),
            "momo_hot_count": len(momo_hot),
            "momo_hot": momo_hot,
            "extracted_entities": entities,
            "sample_discussions": {
                "reddit": [r["title"] for r in reddit_items[:3]],
                "youtube": youtube_items[:3],
                "tiktok": tiktok_items[:3]
            }
        }

if __name__ == "__main__":
    radar = SocialBuzzRadar()
    print("Gathering Multi-Source Social Buzz Signals...")
    signals = radar.get_social_signals()
    print(f"✅ Reddit topics: {signals['reddit_count']}")
    print(f"✅ YouTube reviews: {signals['youtube_count']}")
    print(f"✅ TikTok trends: {signals['tiktok_count']}")
    print(f"✅ MoMo Hot titles: {signals['momo_hot_count']}")
    print("Extracted film candidates:", len(signals["extracted_entities"]))
    print("Sample MoMo Hot:", list(signals["momo_hot"].keys())[:5])
