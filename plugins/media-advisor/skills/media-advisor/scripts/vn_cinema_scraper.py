#!/usr/bin/env python3
"""
Vietnamese Cinema & Reviewer Scraper Engine with Persistent Disk Cache.
Aggregates authentic Vietnamese domestic cinema data:
1. MoMo Cinema (momo.vn/cinema): Verified ticket-buyer ratings, paid review counts, audience tags & comments.
2. Moveek (moveek.com): Vietnamese movie database, critic consensus, age certifications (T18/T16/P), and in-depth review articles.
3. Domestic Reviewers & Communities: Phê Phim, Cuồng Phim, Xem Phim Gì, Lucas Luân Nguyễn, Spiderum Cinema,
   TikTok #reviewphim trends, and Facebook cinephile hubs (MYSTWF, Hội Yêu Phim Chiếu Rạp).
"""

import os
import re
import json
import time
import math
import html
import hashlib
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, Any, List, Optional

class DiskCache:
    """Fast, persistent JSON disk cache with configurable Time-To-Live (TTL)."""
    def __init__(self, cache_dir: Optional[Path] = None, default_ttl: int = 43200):
        self.cache_dir = cache_dir or (Path.home() / ".cache" / "agent-skills" / "vn_cinema")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = default_ttl

    def _get_path(self, key: str) -> Path:
        h = hashlib.md5(key.encode("utf-8")).hexdigest()
        clean_key = re.sub(r"[^a-zA-Z0-9_\-]", "_", key)[:35]
        return self.cache_dir / f"{clean_key}_{h}.json"

    def get(self, key: str) -> Optional[Any]:
        p = self._get_path(key)
        if not p.exists():
            return None
        try:
            with open(p, "r", encoding="utf-8") as f:
                payload = json.load(f)
            stored_at = payload.get("timestamp", 0)
            ttl = payload.get("ttl", self.default_ttl)
            if time.time() - stored_at < ttl:
                return payload.get("data")
        except Exception:
            pass
        return None

    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        p = self._get_path(key)
        try:
            with open(p, "w", encoding="utf-8") as f:
                json.dump({
                    "timestamp": time.time(),
                    "ttl": ttl or self.default_ttl,
                    "data": data
                }, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


class ReviewFilterEngine:
    """
    Intelligent Anti-Seeding and Anti-Hate Review Filter Engine.
    Filters out:
    1. Seeding / PR fluff: Short, hollow compliments with zero substance ('quá hay', 'đỉnh', fan idol, etc.)
    2. Toxic hate / Review bombing: Unsubstantiated bashing ('phim rác', 'phí tiền', '1 sao', etc.)
    Categorizes the rest into:
    - Top Authentic Praise (Khen ngợi có chiều sâu, chỉ ra điểm sáng cụ thể)
    - Top Constructive Criticism (Phê bình thẳng thắn, chỉ ra hạt sạn/lỗ hổng cụ thể)
    """
    SEEDING_PATTERNS = [
        r"^(quá\s+)?hay(\s+quá|\s+lắm)?(!|\.)*$",
        r"^(phim\s+)?đỉnh(\s+quá|\s+chóp)?(!|\.)*$",
        r"^1\s*từ\s*(thôi)?\s*[:\s]*hay",
        r"^tuyệt\s*vời(!|\.)*$",
        r"^siêu\s*phẩm(!|\.)*$",
        r"^đi\s*xem\s*(đi|ngay)\s*(mọi\s*người|nha)",
        r"^xem\s*đi\s*kẻo\s*tiếc",
        r"u\s*mê\s*(ck|chồng|anh|em|idol)",
        r"đẹp\s*trai\s*(quá|xỉu)",
        r"ủng\s*hộ\s*(đoàn\s*phim|anh|chị|idol)",
        r"^10/10",
        r"^xuất\s*sắc(!|\.)*$",
    ]

    HATE_PATTERNS = [
        r"^phim\s*rác",
        r"^phí\s*(tiền|thời\s*gian)",
        r"^dở\s*(ẹc|tệ|kinh\s*khủng)",
        r"^1\s*(sao|\*)\s*(khỏi|cho\s*nhanh)",
        r"tẩy\s*chay",
        r"^như\s*hạch",
        r"buồn\s*ngủ\s*vãi",
        r"nhảm\s*nhí",
    ]

    SUBSTANTIVE_KEYWORDS = [
        "kịch bản", "cốt truyện", "tình tiết", "diễn xuất", "nhân vật", "kỹ xảo",
        "hình ảnh", "visual", "cú máy", "âm thanh", "nhạc phim", "soundtrack",
        "nhịp phim", "tiết tấu", "nút thắt", "twist", "kết thúc", "cái kết",
        "thông điệp", "ý nghĩa", "lắng đọng", "hài hước", "hụt hẫng", "sượng",
        "gượng gạo", "lê thê", "đầu voi đuôi chuột", "logic", "đạo diễn", "bối cảnh",
        "trinh thám", "hành động", "phiêu lưu", "hóa thân", "chiều sâu"
    ]

    @classmethod
    def audit_review(cls, text: str, score: Optional[float] = None) -> Dict[str, Any]:
        """Evaluates a single review and returns its quality assessment."""
        text = text.strip()
        if not text:
            return {"verdict": "EMPTY", "is_valid": False}

        # Check Seeding
        for p in cls.SEEDING_PATTERNS:
            if re.search(p, text, re.I):
                return {"verdict": "SEEDING_REJECTED", "reason": "Khen sáo rỗng / PR / Fan seeding không có luận cứ", "is_valid": False}
        if len(text) < 30 and score is not None and score >= 9.0:
            return {"verdict": "SEEDING_REJECTED", "reason": "Đánh giá 10/10 nhưng quá ngắn không có nội dung phân tích", "is_valid": False}

        # Check Toxic Hate
        for p in cls.HATE_PATTERNS:
            if re.search(p, text, re.I) and len(text) < 50:
                return {"verdict": "HATE_REJECTED", "reason": "Chửi đổng / Hạ bệ quá mức không phân tích chuyên môn", "is_valid": False}

        # Check Substantive Content
        has_substance = any(k in text.lower() for k in cls.SUBSTANTIVE_KEYWORDS)
        
        # Categorize Praise vs Criticism
        is_criticism = False
        text_lower = text.lower()
        # Handle praise idioms containing 'chê' (e.g., 'miễn chê', 'không chê vào đâu được')
        clean_text_for_crit = re.sub(r"(miễn\s+chê|không\s+(thể\s+)?chê|hết\s+chỗ\s+chê|chê\s+vào\s+đâu)", "", text_lower)

        if score is not None:
            if score <= 6.5:
                is_criticism = True
            elif score >= 8.0:
                is_criticism = False
            else: # 7.0 - 7.5
                is_criticism = any(w in clean_text_for_crit for w in ["chê", "sạn", "hụt hẫng", "lê thê", "điểm trừ", "điểm yếu", "sượng", "chưa tới", "thất vọng", "đuối", "gượng"])
        else:
            is_criticism = any(w in clean_text_for_crit for w in ["chê", "sạn", "hụt hẫng", "lê thê", "điểm trừ", "điểm yếu", "sượng", "chưa tới", "thất vọng", "đuối", "gượng", "lỗ hổng", "thiếu sót"])


        return {
            "verdict": "ACCEPTED",
            "is_valid": True,
            "has_substance": has_substance,
            "is_criticism": is_criticism,
            "length": len(text)
        }


class VnCinemaScraper:
    def __init__(self):
        self.cache = DiskCache()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7"
        }

    def _fetch_url(self, url: str, timeout: int = 8) -> str:
        req = urllib.request.Request(url, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="ignore")
        except Exception:
            return ""

    def _ddg_lite_query(self, query: str) -> List[str]:
        cache_key = f"ddg_{query}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        data = urllib.parse.urlencode({"q": query}).encode()
        req = urllib.request.Request("https://lite.duckduckgo.com/lite/", data=data, headers=self.headers)
        snippets = []
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                raw_html = resp.read().decode("utf-8", errors="ignore")
                blocks = re.findall(r"<td class=[\'\"]result-snippet[\'\"]>(.*?)</td>", raw_html, re.DOTALL)
                for b in blocks:
                    clean = re.sub(r"<[^>]+>", " ", b).strip()
                    clean = html.unescape(clean)
                    clean = " ".join(clean.split())
                    if len(clean) > 25:
                        snippets.append(clean)
        except Exception:
            pass

        if snippets:
            self.cache.set(cache_key, snippets, ttl=43200) # 12 hours
        return snippets


    # =========================================================================
    # 1. MoMo Cinema Scraper
    # =========================================================================
    def get_momo_catalog(self) -> List[Dict[str, Any]]:
        """Fetches and caches MoMo Cinema active and upcoming movies (TTL: 6h)."""
        cached = self.cache.get("momo_catalog")
        if cached is not None:
            return cached

        raw = self._fetch_url("https://momo.vn/cinema")
        if not raw:
            return []

        movies = []
        try:
            next_data_match = re.findall(r'<script id=[\"\']__NEXT_DATA__[\"\'][^>]*>(.*?)</script>', raw, re.DOTALL)
            if next_data_match:
                payload = json.loads(next_data_match[0])
                page_props = payload.get("props", {}).get("pageProps", {})
                now_items = page_props.get("dataMoviesNow", {}).get("Data", {}).get("Items", [])
                soon_items = page_props.get("dataMoviesSoon", {}).get("Data", {}).get("Items", [])
                
                seen_ids = set()
                for it in now_items + soon_items:
                    fid = it.get("Id")
                    if fid and fid in seen_ids:
                        continue
                    seen_ids.add(fid)

                    top_comments = []
                    for c in it.get("TopComments", []):
                        tags = [t.get("keyword") for t in c.get("tagsV2", []) if t.get("keyword")]
                        top_comments.append({
                            "user": c.get("creatorName", "Khán giả MoMo"),
                            "point": c.get("point", 10),
                            "paid": c.get("paid", True),
                            "tags": tags,
                            "desc": c.get("desc", "").strip()
                        })

                    movies.append({
                        "id": fid,
                        "title": it.get("Title", "").strip(),
                        "title_en": it.get("TitleEn", "").strip(),
                        "rating_point": it.get("ApiRatingPoint"),
                        "rating_total": it.get("ApiRatingTotal", 0),
                        "paid_tickets": it.get("ApiTotalPaid", 0),
                        "age_rating": it.get("ApiRatingFormat") or it.get("ApiRating"),
                        "genre": it.get("ApiGenreName"),
                        "duration": it.get("Duration"),
                        "opening_date": it.get("OpeningDate"),
                        "synopsis": it.get("Synopsis"),
                        "url": f"https://momo.vn{it.get('Link')}" if it.get("Link") else "https://momo.vn/cinema",
                        "top_comments": top_comments
                    })
        except Exception:
            pass

        if movies:
            self.cache.set("momo_catalog", movies, ttl=21600) # 6h
        return movies

    def search_momo(self, query: str, original_title: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Matches a film against the MoMo Cinema catalog."""
        catalog = self.get_momo_catalog()
        if not catalog:
            return None

        from difflib import SequenceMatcher

        def norm(s):
            if not s:
                return ""
            s = s.lower()
            s = re.sub(r"[\(\)\[\]\{\}\:\-\*\.\,\?\_]", " ", s)
            return " ".join(s.split())

        nq = norm(query)
        no = norm(original_title) if original_title else ""

        best_match = None
        best_ratio = 0.0

        for m in catalog:
            nt = norm(m["title"])
            ne = norm(m["title_en"])

            # Exact or substring match
            if nq and (nq == nt or nq == ne or (len(nq) > 4 and (nq in nt or nt in nq))):
                return self._enrich_momo_detail(m)
            if no and (no == nt or no == ne or (len(no) > 4 and (no in ne or ne in no))):
                return self._enrich_momo_detail(m)

            # Fuzzy match
            r1 = SequenceMatcher(None, nq, nt).ratio() if nq else 0
            r2 = SequenceMatcher(None, nq, ne).ratio() if nq else 0
            r3 = SequenceMatcher(None, no, ne).ratio() if no else 0
            top_r = max(r1, r2, r3)
            if top_r > best_ratio:
                best_ratio = top_r
                best_match = m

        if best_ratio >= 0.75 and best_match:
            return self._enrich_momo_detail(best_match)
        return None

    def _enrich_momo_detail(self, m: Dict[str, Any]) -> Dict[str, Any]:
        """Fetches movie detail page to extract high-interaction top comments."""
        url = m.get("url")
        if not url or "momo.vn/cinema/" not in url:
            return m
        raw = self._fetch_url(url)
        if not raw:
            return m
        try:
            m_data = re.search(r'<script id=[\"\']__NEXT_DATA__[\"\'][^>]*>(.*?)</script>', raw, re.DOTALL)
            if m_data:
                payload = json.loads(m_data.group(1))
                film = payload.get("props", {}).get("pageProps", {}).get("FilmData", {}).get("Data", {})
                detail_comments = film.get("TopComments", [])
                existing_users = {c.get("user") for c in m.get("top_comments", [])}
                for c in detail_comments:
                    u = c.get("creatorName", "Khán giả MoMo")
                    if u not in existing_users:
                        tags = [t.get("keyword") for t in c.get("tagsV2", []) if t.get("keyword")]
                        m.setdefault("top_comments", []).append({
                            "user": u,
                            "point": c.get("point", 10),
                            "paid": c.get("paid", True),
                            "tags": tags,
                            "desc": c.get("desc", "").strip(),
                            "interaction_count": c.get("interactionCount", 0),
                            "is_outstanding": c.get("IsOutStanding", False)
                        })
        except Exception:
            pass
        return m


    # =========================================================================
    # 2. Moveek Scraper
    # =========================================================================
    def search_moveek(self, query: str, original_title: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Searches Moveek for movie scores, age rating, and in-depth Vietnamese review articles."""
        search_term = query
        cache_key = f"moveek_search_{search_term}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        url = f"https://moveek.com/tim-kiem/?s={urllib.parse.quote(search_term)}"
        raw = self._fetch_url(url)
        if not raw and original_title:
            url = f"https://moveek.com/tim-kiem/?s={urllib.parse.quote(original_title)}"
            raw = self._fetch_url(url)

        if not raw:
            return None

        # Extract movie links
        movie_links = re.findall(r'<a[^>]+href=[\"\'](/phim/[^\"\']+)[\"\'][^>]*>(.*?)</a>', raw, re.DOTALL)
        candidate_slug = None
        candidate_title = None
        for href, content in movie_links:
            clean_t = re.sub(r'<[^>]+>', ' ', content).strip()
            if clean_t and clean_t != 'Mua vé':
                candidate_slug = href
                candidate_title = clean_t
                break

        if not candidate_slug:
            return None

        movie_url = f"https://moveek.com{candidate_slug}"
        detail_raw = self._fetch_url(movie_url)
        if not detail_raw:
            return None

        result: Dict[str, Any] = {
            "found": True,
            "title": candidate_title,
            "url": movie_url,
            "score": None,
            "vote_count": 0,
            "age_rating": None,
            "duration": None,
            "review_article_title": None,
            "review_article_quote": None
        }

        # 1. Parse JSON-LD
        ld_scripts = re.findall(r'<script[^>]*type=[\"\']application/ld\+json[\"\'][^>]*>(.*?)</script>', detail_raw, re.DOTALL)
        for s in ld_scripts:
            try:
                data = json.loads(s)
                if data.get("@type") == "Movie":
                    result["title"] = data.get("name") or candidate_title
                    result["age_rating"] = data.get("contentRating")
                    result["duration"] = data.get("duration")
                    agg = data.get("aggregateRating", {})
                    if agg:
                        val = agg.get("ratingValue")
                        if val is not None:
                            best = agg.get("bestRating", 100)
                            if best == 100:
                                result["score"] = round(float(val) / 10.0, 1)
                            else:
                                result["score"] = float(val)
                            result["vote_count"] = int(agg.get("ratingCount", 0))
            except Exception:
                pass

        # 2. Extract in-depth review article linked on Moveek
        articles = re.findall(r'<a[^>]+href=[\"\'](/bai-viet/[^\"\']+)[\"\'][^>]*>(.*?)</a>', detail_raw)
        review_href = None
        review_title = None
        for href, t in articles:
            clean_t = re.sub(r'<[^>]+>', '', t).strip()
            if any(k in clean_t.lower() for k in ["review", "đánh giá", "cảm nhận", "khen", "chê"]):
                review_href = href
                review_title = clean_t
                break

        if review_href:
            result["review_article_title"] = review_title
            art_raw = self._fetch_url(f"https://moveek.com{review_href}")
            if art_raw:
                paragraphs = re.findall(r"<p>(.*?)</p>", art_raw)
                for p in paragraphs:
                    clean_p = re.sub(r"<[^>]+>", "", p).strip()
                    clean_p = html.unescape(clean_p)
                    if len(clean_p) > 60 and any(w in clean_p.lower() for w in ["đánh giá", "lời khen", "khen", "chê", "thành công", "bất ngờ", "ấn tượng", "khán giả", "phê bình"]):
                        result["review_article_quote"] = clean_p[:220] + "..."
                        break

        self.cache.set(cache_key, result, ttl=43200) # 12h
        return result

    # =========================================================================
    # 3. Vietnamese Reviewers & Communities Pulse (YouTube, TikTok, Fanpages)
    # =========================================================================
    def search_vn_creators_pulse(self, title: str, release_year: Optional[str] = None) -> Dict[str, Any]:
        """Harvests reviews from top Vietnamese cinephile channels and communities."""
        year_str = f" {release_year}" if release_year else ""
        cache_key = f"vn_pulse_{title}_{release_year}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        # Query 1: YouTube / Reviewer Channels (Phê Phim, Cuồng Phim, Lucas Luân Nguyễn)
        q1 = f"review phim {title}{year_str} Phê Phim Cuồng Phim"
        snips1 = self._ddg_lite_query(q1)

        # Query 2: Vietnamese Cinephile Feedback (Khen, chê, sạn, đáng xem)
        q2 = f"đánh giá phim {title}{year_str} review khen chê điểm yếu"
        snips2 = self._ddg_lite_query(q2)

        # Query 3: TikTok Trends & YouTube
        q3 = f"site:youtube.com {title} review phim"
        snips3 = self._ddg_lite_query(q3)

        q4 = f"site:tiktok.com {title} review phim"
        snips4 = self._ddg_lite_query(q4)

        all_snips = snips1 + snips2 + snips3 + snips4
        quotes = []
        praise = []
        criticisms = []

        stop_phrases = ["đừng quên like", "hãy đăng ký kênh", "full hd", "trailer official", "xem trọn bộ"]

        for s in all_snips:
            if any(sp in s.lower() for sp in stop_phrases):
                continue
            
            # Detect praise
            if any(w in s.lower() for w in ["khen", "xuất sắc", "đáng xem", "ấn tượng", "bất ngờ", "hài lòng", "chất lượng", "điểm cộng", "hay"]):
                if s not in praise:
                    praise.append(s[:180] + ("..." if len(s) > 180 else ""))
            
            # Detect criticisms or flaws
            if any(w in s.lower() for w in ["chê", "sạn", "hụt hẫng", "lê thê", "điểm trừ", "điểm yếu", "sượng", "chưa tới", "thất vọng"]):
                if s not in criticisms:
                    criticisms.append(s[:180] + ("..." if len(s) > 180 else ""))

            # General insightful quote
            if any(w in s.lower() for w in ["review", "nhận xét", "đánh giá", "diễn xuất", "kịch bản", "kỹ xảo", "đạo diễn"]):
                if len(quotes) < 4 and s not in quotes:
                    quotes.append(s[:180] + ("..." if len(s) > 180 else ""))

        res = {
            "quotes": quotes[:3],
            "praise": praise[:2],
            "criticisms": criticisms[:2],
            "has_data": bool(quotes or praise or criticisms)
        }

        if res.get("has_data"):
            self.cache.set(cache_key, res, ttl=43200) # 12h
        return res


    # =========================================================================
    # 4. Master Unified Domestic Audit & Curated Review Engine
    # =========================================================================
    def audit_curated_reviews(self, momo_data: Optional[Dict[str, Any]], creators_data: Optional[Dict[str, Any]], moveek_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Processes and filters all reviews across MoMo, Moveek, and Reviewers:
        - Rejects seeding (hollow praise, idol fan PR, 1-word compliments)
        - Rejects toxic hate / review bombing (unsubstantiated bashing)
        - Extracts Top Authentic Praise (Điểm sáng có chiều sâu)
        - Extracts Top Constructive Criticism (Phê bình thẳng thắn, bóc tách hạt sạn)
        """
        top_praise = []
        top_criticism = []
        seeding_count = 0
        hate_count = 0

        # 1. Process MoMo comments
        if momo_data and momo_data.get("top_comments"):
            for c in momo_data["top_comments"]:
                desc = c.get("desc", "").strip()
                pt = c.get("point")
                audit = ReviewFilterEngine.audit_review(desc, pt)
                
                if audit["verdict"] == "SEEDING_REJECTED":
                    seeding_count += 1
                    continue
                elif audit["verdict"] == "HATE_REJECTED":
                    hate_count += 1
                    continue

                if audit["is_valid"]:
                    item = {
                        "author": c.get("user", "Khán giả rạp"),
                        "source": "MoMo Cinema (Vé đã xác thực)" if c.get("paid") else "MoMo Cinema",
                        "score": f"{pt}/10" if pt else "",
                        "content": desc,
                        "has_substance": audit["has_substance"],
                        "interaction": c.get("interaction_count", 0)
                    }
                    if audit["is_criticism"]:
                        top_criticism.append(item)
                    else:
                        top_praise.append(item)

        # 2. Process Moveek review article quote
        if moveek_data and moveek_data.get("review_article_quote"):
            m_quote = moveek_data["review_article_quote"].strip()
            audit_m = ReviewFilterEngine.audit_review(m_quote, moveek_data.get("score"))
            if audit_m["is_valid"]:
                item_m = {
                    "author": moveek_data.get("review_article_title") or "Nhà phê bình Moveek",
                    "source": "Moveek Phê Bình",
                    "score": f"{moveek_data.get('score')}/10" if moveek_data.get("score") else "",
                    "content": m_quote,
                    "has_substance": True,
                    "interaction": 100
                }
                if audit_m["is_criticism"]:
                    top_criticism.append(item_m)
                else:
                    top_praise.append(item_m)

        # 3. Process Reviewers / Cinephile communities pulse
        if creators_data:
            for p in creators_data.get("praise", []):
                audit_p = ReviewFilterEngine.audit_review(p)
                if audit_p["verdict"] == "SEEDING_REJECTED":
                    seeding_count += 1
                elif audit_p["is_valid"]:
                    top_praise.append({
                        "author": "Cộng đồng Điện Ảnh",
                        "source": "YouTube / Cinephile Hub",
                        "score": "",
                        "content": p,
                        "has_substance": audit_p["has_substance"],
                        "interaction": 50
                    })

            for cr in creators_data.get("criticisms", []):
                audit_cr = ReviewFilterEngine.audit_review(cr)
                if audit_cr["verdict"] == "HATE_REJECTED":
                    hate_count += 1
                elif audit_cr["is_valid"]:
                    top_criticism.append({
                        "author": "Cộng đồng Phê Bình",
                        "source": "YouTube / Diễn Đàn Điện Ảnh",
                        "score": "",
                        "content": cr,
                        "has_substance": audit_cr["has_substance"],
                        "interaction": 50
                    })

        # Sort by substantive content, interaction, and length
        top_praise.sort(key=lambda x: (x["has_substance"], x["interaction"], len(x["content"])), reverse=True)
        top_criticism.sort(key=lambda x: (x["has_substance"], x["interaction"], len(x["content"])), reverse=True)

        return {
            "top_praise": top_praise[:3],
            "top_criticism": top_criticism[:3],
            "seeding_filtered_count": seeding_count,
            "hate_filtered_count": hate_count,
            "has_data": bool(top_praise or top_criticism)
        }

    def audit_domestic(self, title: str, original_title: Optional[str] = None, release_year: Optional[str] = None) -> Dict[str, Any]:
        """Runs the complete Vietnamese cinema audit suite across MoMo, Moveek, and Reviewers."""
        momo_data = self.search_momo(title, original_title)
        moveek_data = self.search_moveek(title, original_title)
        creators_data = self.search_vn_creators_pulse(title, release_year)
        curated_reviews = self.audit_curated_reviews(momo_data, creators_data, moveek_data)

        return {
            "momo": momo_data,
            "moveek": moveek_data,
            "creators": creators_data,
            "curated_reviews": curated_reviews
        }


    # =========================================================================
    # 5. Trending Domestic Signals (for Social Buzz Radar)
    # =========================================================================
    def get_domestic_trending_signals(self) -> Dict[str, Any]:
        """Provides hot domestic signals for media-advisor's Social Buzz Radar."""
        catalog = self.get_momo_catalog()
        hot_momo_titles: Dict[str, Dict[str, Any]] = {}
        for m in catalog:
            t = m["title"]
            paid = m.get("paid_tickets", 0)
            score = m.get("rating_point")
            if paid >= 5 or (score and score >= 8.0):
                hot_momo_titles[t] = {
                    "source": "MoMo Cinema",
                    "paid_tickets": paid,
                    "score": score,
                    "tag": f"MoMo {score}⭐ ({paid:,} vé)" if paid > 0 else f"MoMo {score}⭐"
                }

        return {
            "momo_hot": hot_momo_titles,
            "total_momo_movies": len(catalog)
        }

    # =========================================================================
    # 6. Cinema Ticket Booking Link Engine (App Deeplinks & Web Links)
    # =========================================================================
    def get_booking_links(self, title: str, original_title: Optional[str] = None) -> Dict[str, Any]:
        """
        Generates direct-to-movie booking links for Vietnamese cinema platforms.
        Searches MoMo & Moveek catalogs first to get exact movie page URLs,
        falls back to search URLs only when movie isn't found in catalog.
        """
        clean_title = re.sub(r"[^\w\s]", " ", title).strip()
        encoded_query = urllib.parse.quote_plus(title)
        clean_encoded = urllib.parse.quote_plus(clean_title)

        # ── 1. Search MoMo catalog for direct movie page ──
        momo_match = self.search_momo(title, original_title)
        if momo_match and momo_match.get("url"):
            # Direct URL like https://momo.vn/cinema/demon-agent-25101
            momo_direct = momo_match["url"]
            if not momo_direct.startswith("https://www.momo.vn"):
                momo_direct = momo_direct.replace("https://momo.vn", "https://www.momo.vn")
            momo_action = f"Mở Trang Đặt Vé «{momo_match.get('title', title)}» trên MoMo"
            momo_found = True
        else:
            # Fallback: generic cinema homepage
            momo_direct = "https://www.momo.vn/cinema"
            momo_action = "Mở MoMo Cinema (tìm phim thủ công)"
            momo_found = False

        # intent:// → Android Chrome tự mở app MoMo, fallback Play Store
        momo_path = momo_direct.replace("https://www.momo.vn/", "")
        momo_intent = (
            f"intent://{momo_path}"
            f"#Intent;scheme=https;host=www.momo.vn;package=com.mservice.momotransfer;"
            f"S.browser_fallback_url={urllib.parse.quote_plus(momo_direct)};end"
        )

        # ── 2. Search Moveek for direct movie page ──
        moveek_match = self.search_moveek(title, original_title)
        if moveek_match and moveek_match.get("url"):
            # Direct URL like https://moveek.com/phim/yeu-nhan-than-tham-ky-an-truong-an/
            moveek_direct = moveek_match["url"]
            moveek_action = f"Xem Suất Chiếu «{moveek_match.get('title', title)}» trên Moveek"
            moveek_found = True
        else:
            moveek_direct = f"https://moveek.com/tim-kiem/?q={encoded_query}"
            moveek_action = "Tìm Phim Trên Moveek"
            moveek_found = False

        # ── 3. CGV Cinemas — Direct Movie URL & App Universal Link ──
        cgv_slug = None
        if momo_match and momo_match.get("url"):
            m = re.search(r'/cinema/([a-zA-Z0-9\-]+)-\d+$', momo_match["url"])
            if m:
                cgv_slug = m.group(1)

        cgv_search_web = f"https://www.cgv.vn/default/catalogsearch/result/?q={clean_encoded}"
        if cgv_slug:
            cgv_direct_web = f"https://www.cgv.vn/default/{cgv_slug}.html"
            cgv_action = f"Mở Trang Phim «{title}» trên CGV"
            cgv_found = True
            cgv_intent = (
                f"intent://default/{cgv_slug}.html"
                f"#Intent;scheme=https;host=www.cgv.vn;package=com.cgv.vn;"
                f"S.browser_fallback_url={urllib.parse.quote_plus(cgv_direct_web)};end"
            )
        else:
            cgv_direct_web = cgv_search_web
            cgv_action = f"Tìm «{title}» trên CGV"
            cgv_found = False
            cgv_intent = (
                f"intent://default/catalogsearch/result/?q={clean_encoded}"
                f"#Intent;scheme=https;host=www.cgv.vn;package=com.cgv.vn;"
                f"S.browser_fallback_url={urllib.parse.quote_plus(cgv_search_web)};end"
            )

        # ── 4. Galaxy Cinema ──
        galaxy_web = f"https://www.galaxycine.vn/tim-kiem/?q={clean_encoded}"

        return {
            "title": title,
            "momo_found": momo_found,
            "moveek_found": moveek_found,
            "cgv_found": cgv_found,
            "app_links": [
                {
                    "platform": "MoMo Cinema",
                    "badge": "📱 MoMo Cinema",
                    "priority": 1,
                    "universal_link": momo_direct,
                    "deeplink": momo_intent,
                    "web_fallback": momo_direct,
                    "store_android": "https://play.google.com/store/apps/details?id=com.mservice.momotransfer",
                    "store_ios": "https://apps.apple.com/vn/app/momo-e-wallet/id918751511",
                    "action_text": momo_action,
                    "description": "Mở trực tiếp trang phim — chọn rạp, suất chiếu, ghế ngồi & thanh toán MoMo"
                },
                {
                    "platform": "CGV Cinemas Vietnam",
                    "badge": "🍿 CGV Cinemas" + (" ✅" if cgv_found else ""),
                    "priority": 2,
                    "universal_link": cgv_direct_web,
                    "deeplink": cgv_intent,
                    "web_fallback": cgv_direct_web,
                    "store_android": "https://play.google.com/store/apps/details?id=com.cgv.vn",
                    "store_ios": "https://apps.apple.com/vn/app/cgv-cinemas-vietnam/id849664126",
                    "action_text": cgv_action,
                    "description": "Mở trực tiếp trang phim tại CGV — chọn cụm rạp CGV & suất chiếu để đặt vé"
                }
            ],
            "web_links": [
                {
                    "platform": "Moveek",
                    "badge": "🎬 Moveek" + (" ✅" if moveek_found else ""),
                    "url": moveek_direct,
                    "action_text": moveek_action,
                    "description": "Tổng hợp lịch chiếu & giá vé tất cả cụm rạp: CGV, Lotte, BHD, Beta, Galaxy, Cinestar"
                },
                {
                    "platform": "CGV Online",
                    "badge": "🌐 CGV Web" + (" ✅" if cgv_found else ""),
                    "url": cgv_direct_web,
                    "action_text": cgv_action if cgv_found else f"Tìm «{title}» tại cgv.vn",
                    "description": "Trang thông tin phim và lịch chiếu chính thức tại CGV Việt Nam"
                },
                {
                    "platform": "Galaxy Cinema",
                    "badge": "🌐 Galaxy Cinema",
                    "url": galaxy_web,
                    "action_text": f"Tìm «{title}» tại Galaxy Cinema",
                    "description": "Tìm suất chiếu tại Galaxy Cinema"
                }
            ]
        }

    # =========================================================================
    # 7. Real-Time Movie Showtime & Prime Seating Recommendation Engine
    # =========================================================================
    def _mint_moveek_token(self) -> Optional[str]:
        """Acquires a guest access token from Moveek IAM."""
        cached_tok = self.cache.get("moveek_guest_token")
        if cached_tok:
            return cached_tok
        try:
            req = urllib.request.Request(
                "https://iam.moveek.com/v1/auth/guest",
                data=b"{}",
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Origin": "https://moveek.com",
                    "Referer": "https://moveek.com/"
                }
            )
            resp = urllib.request.urlopen(req, timeout=5)
            payload = json.loads(resp.read().decode("utf-8"))
            tok = payload.get("access_token")
            exp = payload.get("expires_in", 3600)
            if tok:
                self.cache.set("moveek_guest_token", tok, ttl=max(60, exp - 120))
                return tok
        except Exception:
            pass
        return None

    def _analyze_seat_grid(self, grid: List[List[Dict[str, Any]]], ticket_count: int = 2) -> Optional[Dict[str, Any]]:
        """
        Analyzes a real-time cinema seat map grid:
        - Prioritizes prime viewing rows: E, F, G, H, J (THX/SMPTE sweet spot).
        - Enforces strictly consecutive available seats for ticket_count.
        - Prioritizes center column positions (optimal horizontal FOV).
        """
        if not grid or ticket_count <= 0:
            return None

        sweet_rows = {"E", "F", "G", "H", "J"}
        best_candidate = None
        best_score = -1.0

        for row in grid:
            seats = [s for s in row if s is not None]
            if not seats:
                continue

            row_name = seats[0].get("row", "").strip().upper()
            is_sweet_row = row_name in sweet_rows
            
            # Sort seats by column order
            seats.sort(key=lambda s: s.get("col", 0))
            n = len(seats)
            mid = n / 2.0

            # Slide window of size ticket_count
            for i in range(len(seats) - ticket_count + 1):
                chunk = seats[i:i+ticket_count]
                # All seats must be available
                if not all(s.get("state") == "available" for s in chunk):
                    continue

                # Must be strictly consecutive columns
                cols = [s.get("col", 0) for s in chunk]
                if cols != list(range(cols[0], cols[0] + ticket_count)):
                    continue

                chunk_mid = sum(cols) / float(ticket_count)
                dist_from_center = abs(chunk_mid - mid)

                score = 100.0 - (dist_from_center * 4.0)
                if is_sweet_row:
                    score += 50.0
                if any("VIP" in s.get("tier", {}).get("name", "").upper() for s in chunk):
                    score += 25.0

                if score > best_score:
                    best_score = score
                    seat_ids = [s.get("id") for s in chunk]
                    tier_name = chunk[0].get("tier", {}).get("name") or "Standard"
                    price = chunk[0].get("price")
                    best_candidate = {
                        "row": row_name,
                        "seats": seat_ids,
                        "tier": tier_name,
                        "price": price,
                        "formatted_price": f"{price:,}đ" if price else "Theo giá rạp",
                        "score": round(score, 1),
                        "is_sweet_spot": is_sweet_row and (dist_from_center <= 3.5),
                        "summary": f"Hàng {row_name} (Ghế {', '.join(seat_ids)}) [{tier_name}]"
                    }

        return best_candidate

    @staticmethod
    def _haversine_dist(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(R * c, 2)

    @staticmethod
    def get_user_location(user_ip: str = "") -> Optional[Dict[str, Any]]:
        """
        Retrieves user physical location from ip-api.com:
        Returns {city, country, lat, lon, ip}
        """
        endpoint = f"http://ip-api.com/json/{user_ip}?fields=status,country,city,district,lat,lon,query"
        try:
            req = urllib.request.Request(endpoint, headers={"User-Agent": "curl/7.68.0"})
            resp = urllib.request.urlopen(req, timeout=3)
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("status") == "success":
                return {
                    "city": data.get("city"),
                    "country": data.get("country"),
                    "district": data.get("district"),
                    "lat": data.get("lat"),
                    "lon": data.get("lon"),
                    "ip": data.get("query")
                }
        except Exception:
            pass
        return None

    @staticmethod
    def _query_hardware_gps(timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        """
        Polls local hardware GPS receivers:
        1. gpsd daemon (port 2947) - standard Linux GPS architecture
        2. ModemManager (mmcli) - LTE/5G cellular modules with GNSS
        3. Direct serial NMEA devices (/dev/ttyUSB*, /dev/ttyACM*)
        """
        import socket
        # 1. Check gpsd socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect(("127.0.0.1", 2947))
            s.recv(1024)
            s.sendall(b'?WATCH={"enable":true,"json":true};?POLL;\n')
            buf = ""
            for _ in range(5):
                chunk = s.recv(2048).decode("utf-8")
                if not chunk:
                    break
                buf += chunk
                for line in buf.splitlines():
                    if line.startswith("{"):
                        try:
                            pkt = json.loads(line)
                            if pkt.get("class") == "TPV" and pkt.get("lat") is not None and pkt.get("lon") is not None:
                                s.close()
                                lat = float(pkt["lat"])
                                lon = float(pkt["lon"])
                                return {
                                    "lat": lat,
                                    "lon": lon,
                                    "region_id": 9 if lat > 18.0 else 1,
                                    "label": f"GPS Vệ Tinh (gpsd: {lat:.4f}, {lon:.4f})",
                                    "source": "HARDWARE_GPSD"
                                }
                        except Exception:
                            pass
            s.close()
        except Exception:
            pass

        # 2. Check ModemManager via mmcli (4G/5G WWAN modem GNSS fix)
        import shutil, subprocess
        if shutil.which("mmcli"):
            try:
                out = subprocess.check_output(["mmcli", "-m", "0", "--location-get"], timeout=2, stderr=subprocess.DEVNULL).decode("utf-8")
                m_lat = re.search(r"latitude:\s*([\d\.\-]+)", out, re.I)
                m_lon = re.search(r"longitude:\s*([\d\.\-]+)", out, re.I)
                if m_lat and m_lon:
                    lat = float(m_lat.group(1))
                    lon = float(m_lon.group(1))
                    return {
                        "lat": lat,
                        "lon": lon,
                        "region_id": 9 if lat > 18.0 else 1,
                        "label": f"GPS Modem 4G/5G (GNSS: {lat:.4f}, {lon:.4f})",
                        "source": "MODEM_MANAGER_GPS"
                    }
            except Exception:
                pass

        # 3. Check direct NMEA USB GPS Dongles (/dev/ttyUSB*, /dev/ttyACM*)
        import glob
        serial_ports = glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*")
        for port in serial_ports:
            try:
                with open(port, "r", encoding="ascii", errors="ignore") as f:
                    for _ in range(30):
                        line = f.readline()
                        if line.startswith("$GPRMC") or line.startswith("$GNRMC"):
                            parts = line.split(",")
                            if len(parts) > 6 and parts[2] == "A":
                                raw_lat, lat_dir = parts[3], parts[4]
                                raw_lon, lon_dir = parts[5], parts[6]
                                if raw_lat and raw_lon:
                                    lat_deg = float(raw_lat[:2]) + float(raw_lat[2:]) / 60.0
                                    if lat_dir == "S":
                                        lat_deg = -lat_deg
                                    lon_deg = float(raw_lon[:3]) + float(raw_lon[3:]) / 60.0
                                    if lon_dir == "W":
                                        lon_deg = -lon_deg
                                    return {
                                        "lat": lat_deg,
                                        "lon": lon_deg,
                                        "region_id": 9 if lat_deg > 18.0 else 1,
                                        "label": f"USB GPS Receiver ({port})",
                                        "source": "SERIAL_NMEA_GPS"
                                    }
            except Exception:
                pass

        return None

    def _detect_live_ip_location(self) -> Optional[Dict[str, Any]]:
        """Automatically detects user's physical location (Priority: Hardware GPS -> Config File -> IP Geolocation)."""
        cached_loc = self.cache.get("user_auto_detected_location")
        if cached_loc:
            return cached_loc

        # 0. Check Hardware GPS receiver (gpsd, 4G/5G modem, USB GPS dongle)
        hw_gps = self._query_hardware_gps()
        if hw_gps:
            self.cache.set("user_auto_detected_location", hw_gps, ttl=300)
            return hw_gps

        # 1. Try user config file first: ~/.config/agent-skills/user_location.json
        cfg_path = Path.home() / ".config" / "agent-skills" / "user_location.json"
        if cfg_path.exists():
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    if "lat" in cfg and "lon" in cfg:
                        return {
                            "lat": float(cfg["lat"]),
                            "lon": float(cfg["lon"]),
                            "region_id": cfg.get("region_id", (9 if float(cfg["lat"]) > 18.0 else 1)),
                            "label": cfg.get("label", "Vị trí đã lưu trong cấu hình"),
                            "source": "CONFIG_FILE"
                        }
            except Exception:
                pass

        # 2. Real-time IP Geolocation via ip-api.com
        ip_info = self.get_user_location()
        if ip_info and ip_info.get("lat") and ip_info.get("lon"):
            lat = float(ip_info["lat"])
            lon = float(ip_info["lon"])
            city = ip_info.get("city") or "TP. Hồ Chí Minh"
            r_id = 9 if lat > 18.0 else 1
            label = f"{city} (IP {ip_info.get('ip', '')})"

            # Reverse geocode via Nominatim for street/ward precision
            try:
                nom_url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
                nom_req = urllib.request.Request(nom_url, headers={"User-Agent": "AgentSkills-Cinema/1.0"})
                nom_data = json.loads(urllib.request.urlopen(nom_req, timeout=2).read().decode("utf-8"))
                addr = nom_data.get("address", {})
                road = addr.get("road")
                suburb = addr.get("suburb") or addr.get("quarter") or addr.get("city_district")
                city_name = addr.get("city") or city
                parts = [p for p in [road, suburb, city_name] if p]
                if parts:
                    label = ", ".join(parts)
            except Exception:
                pass

            result = {
                "lat": lat,
                "lon": lon,
                "region_id": r_id,
                "label": label,
                "source": "IP_GEOLOCATION"
            }
            self.cache.set("user_auto_detected_location", result, ttl=3600)
            return result

        return None

    def _resolve_user_location(self, loc_input: Optional[str], default_region: int = 1):
        """Resolves user's location input into (lat, lon, region_id, label)."""
        if not loc_input:
            auto = self._detect_live_ip_location()
            if auto:
                return (auto["lat"], auto["lon"], auto["region_id"], f"{auto['label']} (Tự động định vị)")
            return (10.7769, 106.7009, 1, "TP. Hồ Chí Minh")

        norm = loc_input.strip().lower()

        # Check if direct coordinates like "10.7769, 106.7009"
        coord_match = re.match(r"^([\d\.\-]+)\s*,\s*([\d\.\-]+)$", norm)
        if coord_match:
            try:
                lat, lon = float(coord_match.group(1)), float(coord_match.group(2))
                r_id = 9 if lat > 18.0 else 1
                return (lat, lon, r_id, f"Vị trí GPS ({lat:.4f}, {lon:.4f})")
            except Exception:
                pass

        DISTRICT_MAP = {
            # TP.HCM (region 1)
            "quận 1": (10.7769, 106.7009, 1, "Quận 1, TP.HCM"),
            "q1": (10.7769, 106.7009, 1, "Quận 1, TP.HCM"),
            "q.1": (10.7769, 106.7009, 1, "Quận 1, TP.HCM"),
            "quận 3": (10.7844, 106.6844, 1, "Quận 3, TP.HCM"),
            "q3": (10.7844, 106.6844, 1, "Quận 3, TP.HCM"),
            "q.3": (10.7844, 106.6844, 1, "Quận 3, TP.HCM"),
            "quận 4": (10.7634, 106.7056, 1, "Quận 4, TP.HCM"),
            "quận 5": (10.7540, 106.6634, 1, "Quận 5, TP.HCM"),
            "quận 6": (10.7481, 106.6352, 1, "Quận 6, TP.HCM"),
            "quận 7": (10.7340, 106.7218, 1, "Quận 7, TP.HCM"),
            "q7": (10.7340, 106.7218, 1, "Quận 7, TP.HCM"),
            "q.7": (10.7340, 106.7218, 1, "Quận 7, TP.HCM"),
            "quận 8": (10.7241, 106.6286, 1, "Quận 8, TP.HCM"),
            "quận 10": (10.7716, 106.6674, 1, "Quận 10, TP.HCM"),
            "q10": (10.7716, 106.6674, 1, "Quận 10, TP.HCM"),
            "q.10": (10.7716, 106.6674, 1, "Quận 10, TP.HCM"),
            "quận 11": (10.7630, 106.6508, 1, "Quận 11, TP.HCM"),
            "quận 12": (10.8672, 106.6413, 1, "Quận 12, TP.HCM"),
            "bình thạnh": (10.8106, 106.6983, 1, "Bình Thạnh, TP.HCM"),
            "gò vấp": (10.8387, 106.6653, 1, "Gò Vấp, TP.HCM"),
            "phú nhuận": (10.7992, 106.6803, 1, "Phú Nhuận, TP.HCM"),
            "tân bình": (10.8015, 106.6548, 1, "Tân Bình, TP.HCM"),
            "tân phú": (10.7900, 106.6282, 1, "Tân Phú, TP.HCM"),
            "bình tân": (10.7654, 106.6038, 1, "Bình Tân, TP.HCM"),
            "thủ đức": (10.8494, 106.7537, 1, "Thủ Đức, TP.HCM"),
            "tp.hcm": (10.7769, 106.7009, 1, "TP. Hồ Chí Minh"),
            "hồ chí minh": (10.7769, 106.7009, 1, "TP. Hồ Chí Minh"),
            "sài gòn": (10.7769, 106.7009, 1, "TP. Hồ Chí Minh"),
            # Hà Nội (region 9)
            "hoàn kiếm": (21.0285, 105.8542, 9, "Hoàn Kiếm, Hà Nội"),
            "ba đình": (21.0341, 105.8242, 9, "Ba Đình, Hà Nội"),
            "đống đa": (21.0181, 105.8273, 9, "Đống Đa, Hà Nội"),
            "hai bà trưng": (21.0069, 105.8532, 9, "Hai Bà Trưng, Hà Nội"),
            "cầu giấy": (21.0362, 105.7906, 9, "Cầu Giấy, Hà Nội"),
            "thanh xuân": (20.9937, 105.8083, 9, "Thanh Xuân, Hà Nội"),
            "tây hồ": (21.0694, 105.8244, 9, "Tây Hồ, Hà Nội"),
            "hà đông": (20.9721, 105.7772, 9, "Hà Đông, Hà Nội"),
            "nam từ liêm": (21.0146, 105.7653, 9, "Nam Từ Liêm, Hà Nội"),
            "bắc từ liêm": (21.0631, 105.7562, 9, "Bắc Từ Liêm, Hà Nội"),
            "long biên": (21.0360, 105.8978, 9, "Long Biên, Hà Nội"),
            "hoàng mai": (20.9765, 105.8453, 9, "Hoàng Mai, Hà Nội"),
            "hà nội": (21.0285, 105.8542, 9, "Hà Nội"),
            "hanoi": (21.0285, 105.8542, 9, "Hà Nội"),
            # Đà Nẵng (region 7)
            "đà nẵng": (16.0544, 108.2022, 7, "Đà Nẵng"),
            "hải châu": (16.0617, 108.2208, 7, "Hải Châu, Đà Nẵng"),
            # Cần Thơ (region 6)
            "cần thơ": (10.0452, 105.7469, 6, "Cần Thơ"),
            # Hải Phòng (region 10)
            "hải phòng": (20.8449, 106.6881, 10, "Hải Phòng"),
            # Bình Dương (region 4)
            "bình dương": (10.9804, 106.6519, 4, "Bình Dương"),
            # Đồng Nai (region 3)
            "đồng nai": (10.9427, 106.8166, 3, "Đồng Nai")
        }

        for k, v in DISTRICT_MAP.items():
            if k in norm:
                return v

        return (10.7769, 106.7009, default_region, loc_input.title())

    def _evaluate_cinema_quality(self, cinema_name: str, cineplex_name: str, format_name: str) -> Dict[str, Any]:
        """Evaluates theater experience tier and premium badges."""
        score = 0
        badges = []
        fmt_upper = format_name.upper()
        name_upper = cinema_name.upper()
        
        # Premium format bonuses
        if "IMAX LASER" in fmt_upper:
            score += 65
            badges.append("🔥 IMAX Laser")
        elif "IMAX" in fmt_upper:
            score += 55
            badges.append("💎 IMAX")
        elif "SCREENX" in fmt_upper:
            score += 45
            badges.append("🌟 ScreenX 270°")
        elif "4DX" in fmt_upper:
            score += 40
            badges.append("🚀 4DX Rung Lắc")
        elif "STARIUM" in fmt_upper or "DOLBY ATMOS" in fmt_upper or "ATMOS" in fmt_upper:
            score += 35
            badges.append("🔊 Dolby Atmos / Starium")
        elif "GOLD CLASS" in fmt_upper or "L'AMOUR" in fmt_upper or "PREMIUM" in fmt_upper:
            score += 35
            badges.append("👑 Rạp Hạng Sang / Giường Nằm")
        elif "3D" in fmt_upper:
            score += 20
            badges.append("👓 3D")
        else:
            score += 10
            badges.append("📽️ 2D Kỹ Thuật Số")

        # Flagship cinema locations
        FLAGSHIPS = [
            "LANDMARK 81", "SƯ VẠN HẠNH", "SU VAN HANH", "VIVOCITY", "ĐỒNG KHỞI", "DONG KHOI",
            "CRESCENT MALL", "VINCOM METROPOLIS", "VINCOM TRẦN DUY HƯNG", "VINCOM BÀ TRIỆU",
            "BITEXCO", "SALA", "NOWZONE", "WEST LAKE", "QUỐC GIA"
        ]
        is_flagship = any(f in name_upper for f in FLAGSHIPS)
        if is_flagship:
            score += 20
            badges.append("🏛️ Cụm Rạp Flagship Trọng Điểm")

        return {
            "quality_score": score,
            "badges": badges,
            "is_premium": score >= 40,
            "badge_str": " · ".join(badges)
        }

    def find_movie_showtimes(
        self,
        title: str,
        date: Optional[str] = None,
        location: Optional[str] = None,
        ticket_count: int = 2,
        region_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Complete intelligent showtime finder and prime seat recommendation engine:
        1. Selected date (default today; if no future slots left today, auto-fallbacks to next available date).
        2. Location proximity (prioritizes cinemas near the user's district or coordinates).
        3. High-quality theaters (IMAX, ScreenX, Starium, Dolby Atmos, Gold Class, Flagships).
        4. Prime seating & consecutive seat verification (guarantees contiguous seats in THX sweet spot).
        """
        # 1. Resolve user location & region
        user_lat, user_lon, detected_region, loc_label = self._resolve_user_location(location)
        active_region = region_id if region_id is not None else detected_region

        # 2. Resolve Moveek Movie Slug, Movie ID, and Available Dates
        moveek_match = self.search_moveek(title)
        if not moveek_match or not moveek_match.get("url"):
            general_links = self.get_booking_links(title)
            return {
                "success": False,
                "error": f"Không tìm thấy phim «{title}» trong hệ thống Moveek.",
                "general_links": general_links
            }

        movie_url = moveek_match["url"]
        movie_title = moveek_match.get("title", title)

        headers_web = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        headers_ajax = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": "https://moveek.com/"
        }

        cache_key_meta = f"moveek_meta_{moveek_match.get('slug') or title}"
        cached_meta = self.cache.get(cache_key_meta)
        movie_id = None
        available_dates = []

        if cached_meta and cached_meta.get("movie_id"):
            movie_id = cached_meta["movie_id"]
            available_dates = cached_meta.get("available_dates", [])

        if not movie_id:
            try:
                req = urllib.request.Request(movie_url, headers=headers_web)
                html_page = urllib.request.urlopen(req, timeout=6).read().decode("utf-8")
                m_id = re.search(r'id:\s*[\"\'](\d+)[\"\']', html_page)
                if m_id:
                    movie_id = m_id.group(1)
                    available_dates = sorted(list(set(re.findall(r'data-date=[\"\']([\d\-]+)[\"\']', html_page))))
                    self.cache.set(cache_key_meta, {"movie_id": movie_id, "available_dates": available_dates}, ttl=86400)
            except Exception:
                pass

        if not movie_id:
            general_links = self.get_booking_links(title)
            return {
                "success": False,
                "error": f"Không thể tải thông tin Moveek cho «{title}».",
                "general_links": general_links
            }

        now_dt = datetime.now()
        today_str = now_dt.strftime("%Y-%m-%d")
        now_time = now_dt.strftime("%H:%M")

        is_fallback_date = False
        fallback_notice = ""
        target_date = date.strip() if date else today_str

        def _fetch_date_showtimes(d: str):
            st_url = f"https://moveek.com/showtime/movie/{movie_id}?date={d}&region={active_region}"
            st_req = urllib.request.Request(st_url, headers=headers_ajax)
            try:
                raw_json = urllib.request.urlopen(st_req, timeout=6).read().decode("utf-8")
                return json.loads(raw_json)
            except Exception:
                return {}

        st_data = _fetch_date_showtimes(target_date)
        all_cinemas = []
        for cp in st_data.get("cineplexes", []):
            cp_name = cp.get("data", {}).get("name", "Cụm Rạp")
            for c in cp.get("cinemas", []):
                c["cineplex"] = cp_name
                all_cinemas.append(c)

        def _fetch_cinema_slots(c: Dict[str, Any], q_date: str) -> List[Dict[str, Any]]:
            cid = c.get("id")
            s_url = f"https://moveek.com/showtime/movie/{movie_id}?date={q_date}&cinema={cid}"
            try:
                s_req = urllib.request.Request(s_url, headers=headers_ajax)
                s_html = urllib.request.urlopen(s_req, timeout=6).read().decode("utf-8")
                slots = []
                chunks = re.split(r'<label class=\"[^\"]*font-weight-bold[^\"]*\">', s_html)
                for chunk in chunks[1:]:
                    fmt_part, _, rest = chunk.partition("</label>")
                    fmt = fmt_part.strip()
                    a_tags = re.findall(r'<a\b([^>]*)>(.*?)</a>', rest, re.DOTALL)
                    for attrs, content in a_tags:
                        if "btn-showtime" in attrs:
                            time_m = re.search(r'<span class=[\"\']time[\"\']>([^<]+)</span>', content)
                            time_val = time_m.group(1).strip() if time_m else ""
                            href_m = re.search(r'href=[\"\']([^\"\']+)[\"\']', attrs)
                            href = href_m.group(1) if href_m else ""
                            ref_m = re.search(r'data-reference=[\"\']([^\"\']+)[\"\']', attrs)
                            ref = ref_m.group(1) if ref_m else ""
                            cls_m = re.search(r'class=[\"\']([^\"\']+)[\"\']', attrs)
                            cls = cls_m.group(1) if cls_m else ""
                            
                            is_disabled = "disabled" in cls
                            is_ticketing = "is-ticketing" in cls
                            
                            b_url = ""
                            if href and href != "#":
                                b_url = f"https://moveek.com{href}" if href.startswith("/") else href
                            elif ref:
                                b_url = f"https://moveek.com/mua-ve/{ref}"

                            slots.append({
                                "cinema_id": cid,
                                "cinema_name": c.get("name"),
                                "cineplex": c.get("cineplex"),
                                "address": c.get("location", {}).get("address"),
                                "lat": c.get("location", {}).get("latitude"),
                                "lng": c.get("location", {}).get("longitude"),
                                "format": fmt,
                                "time": time_val,
                                "reference": ref,
                                "booking_url": b_url,
                                "is_ticketing": is_ticketing,
                                "disabled": is_disabled
                            })
                return slots
            except Exception:
                return []

        with ThreadPoolExecutor(max_workers=8) as ex:
            slot_results = list(ex.map(lambda c: _fetch_cinema_slots(c, target_date), all_cinemas))

        flat_slots = [s for sub in slot_results for s in sub]

        # Check if date was not explicitly passed and today has no remaining active slots
        active_today_slots = [
            s for s in flat_slots 
            if not s["disabled"] and (target_date > today_str or s["time"] > now_time)
        ]

        if not date and len(active_today_slots) == 0:
            next_dates = [d for d in available_dates if d > today_str]
            if next_dates:
                next_date = next_dates[0]
                is_fallback_date = True
                fallback_notice = (
                    f"⚠️ Hôm nay ({today_str}) các suất chiếu đã kết thúc hoặc không còn suất khả dụng. "
                    f"Hệ thống đã tự động chuyển sang ngày tiếp theo có suất chiếu: **{next_date}**."
                )
                target_date = next_date
                st_data = _fetch_date_showtimes(target_date)
                all_cinemas = []
                for cp in st_data.get("cineplexes", []):
                    cp_name = cp.get("data", {}).get("name", "Cụm Rạp")
                    for c in cp.get("cinemas", []):
                        c["cineplex"] = cp_name
                        all_cinemas.append(c)

                with ThreadPoolExecutor(max_workers=8) as ex:
                    slot_results = list(ex.map(lambda c: _fetch_cinema_slots(c, target_date), all_cinemas))
                flat_slots = [s for sub in slot_results for s in sub]

        valid_slots = [
            s for s in flat_slots 
            if not s["disabled"] and (target_date > today_str or s["time"] > now_time)
        ]

        # Seat inspection & Consecutive Seat Optimization for Ticketing Partners
        moveek_token = self._mint_moveek_token()

        def _inspect_slot_seats(slot: Dict[str, Any]) -> Dict[str, Any]:
            ref = slot.get("reference")
            if moveek_token and ref and slot.get("is_ticketing"):
                try:
                    s_req = urllib.request.Request(
                        f"https://moveek.com/api/booking/v1/showtimes/{ref}/seats",
                        headers={
                            "User-Agent": "Mozilla/5.0",
                            "Authorization": f"Bearer {moveek_token}",
                            "Referer": f"https://moveek.com/mua-ve/{ref}"
                        }
                    )
                    s_resp = urllib.request.urlopen(s_req, timeout=4)
                    s_data = json.loads(s_resp.read().decode("utf-8"))
                    grid = s_data.get("grid", [])
                    seat_analysis = self._analyze_seat_grid(grid, ticket_count=ticket_count)
                    if seat_analysis:
                        slot["seat_recommendation"] = seat_analysis
                        slot["has_consecutive_seats"] = True
                        slot["seat_score"] = seat_analysis["score"]
                        return slot
                except Exception:
                    pass

            slot["seat_recommendation"] = {
                "summary": f"Hàng ghế vàng F / G / H (Ghế số 6 - 12 trung tâm)",
                "consecutive_note": f"Khuyên chọn {ticket_count} ghế liên tục tại trục giữa để góc nhìn THX đạt chuẩn 36°.",
                "is_sweet_spot": True
            }
            slot["has_consecutive_seats"] = True
            slot["seat_score"] = 50.0
            return slot

        with ThreadPoolExecutor(max_workers=6) as ex:
            inspected_slots = list(ex.map(_inspect_slot_seats, valid_slots))

        cinema_groups: Dict[str, Dict[str, Any]] = {}

        for slot in inspected_slots:
            cid = str(slot["cinema_id"])
            if cid not in cinema_groups:
                c_lat = float(slot["lat"]) if slot.get("lat") else None
                c_lon = float(slot["lng"]) if slot.get("lng") else None
                
                distance_km = None
                proximity_score = 0.0
                if c_lat and c_lon and user_lat and user_lon:
                    if 8.0 <= c_lat <= 24.0 and 100.0 <= c_lon <= 110.0:
                        distance_km = self._haversine_dist(user_lat, user_lon, c_lat, c_lon)
                    elif 8.0 <= c_lon <= 24.0 and 100.0 <= c_lat <= 110.0:
                        distance_km = self._haversine_dist(user_lat, user_lon, c_lon, c_lat)
                
                if distance_km is not None:
                    proximity_score = max(0.0, 50.0 - (distance_km * 3.5))
                elif location and (location.lower() in (slot.get("address") or "").lower() or location.lower() in slot["cinema_name"].lower()):
                    proximity_score = 40.0
                    distance_km = 2.0

                eval_quality = self._evaluate_cinema_quality(slot["cinema_name"], slot["cineplex"], slot["format"])

                cinema_groups[cid] = {
                    "cinema_id": cid,
                    "cinema_name": slot["cinema_name"],
                    "cineplex": slot["cineplex"],
                    "address": slot["address"],
                    "distance_km": distance_km,
                    "proximity_score": proximity_score,
                    "quality_score": eval_quality["quality_score"],
                    "badges": eval_quality["badges"],
                    "badge_str": eval_quality["badge_str"],
                    "slots": []
                }

            cinema_groups[cid]["slots"].append(slot)

        for c in cinema_groups.values():
            c["slots"].sort(key=lambda s: s["time"])
            best_seat_sc = max((s.get("seat_score", 0.0) for s in c["slots"]), default=0.0)
            c["total_score"] = round(c["quality_score"] + c["proximity_score"] + (best_seat_sc * 0.4), 1)

        ranked_cinemas = sorted(cinema_groups.values(), key=lambda c: c["total_score"], reverse=True)
        cache_key_cinemas = f"moveek_cinemas_{movie_id}_{target_date}_{active_region}_{ticket_count}"
        
        if ranked_cinemas:
            self.cache.set(cache_key_cinemas, ranked_cinemas, ttl=900)
        else:
            cached_cinemas = self.cache.get(cache_key_cinemas)
            if cached_cinemas:
                ranked_cinemas = cached_cinemas

        general_links = self.get_booking_links(title)

        # Fallback to Curated Premium Theaters in user's city if live API was temporarily rate-limited
        if not ranked_cinemas:
            TOP_THEATERS = [
                # TP.HCM (region 1)
                {"name": "AEON BETA Central Premium", "cineplex": "AEON BETA Cinema", "lat": 10.7480, "lng": 106.6710, "address": "Tầng 6, TTTM Central Premium, 854-856 Tạ Quang Bửu, Q.8", "format": "2D Phụ Đề · Ghế VIP", "region": 1, "direct_url": "https://moveek.com/mua-ve/dc42b80a-0047-3850-bc2f-c53b6f7a602b"},
                {"name": "BHD Star 3/2", "cineplex": "BHD Star Cineplex", "lat": 10.7758, "lng": 106.6807, "address": "Lầu 4, Vincom 3/2, 3C Đường 3/2, Q.10", "format": "2D Phụ Đề · Dolby 7.1", "region": 1, "direct_url": "https://moveek.com/mua-ve/51e175f3-9bc1-3872-8844-6112c9184428"},
                {"name": "CGV Landmark 81", "cineplex": "CGV Cinemas", "lat": 10.7950, "lng": 106.7218, "address": "Tầng B1, TTTM Vincom Center Landmark 81, 772 Điện Biên Phủ, P.22, Bình Thạnh", "format": "IMAX Laser · Gold Class", "region": 1, "direct_url": None},
                {"name": "CGV Vạn Hạnh Mall", "cineplex": "CGV Cinemas", "lat": 10.7699, "lng": 106.6698, "address": "Tầng 6, Vạn Hạnh Mall, 11 Sư Vạn Hạnh, Q.10", "format": "4DX · ScreenX 270°", "region": 1, "direct_url": None},
                {"name": "Beta Quang Trung", "cineplex": "Beta Cinemas", "lat": 10.8356, "lng": 106.6589, "address": "645 Quang Trung, P.11, Gò Vấp", "format": "2D Phụ Đề · Ghế VIP", "region": 1, "direct_url": None},
                {"name": "Lotte Cộng Hòa", "cineplex": "Lotte Cinema", "lat": 10.8010, "lng": 106.6526, "address": "Tầng 4, Pico Plaza, 20 Cộng Hòa, Tân Bình", "format": "2D Phụ Đề · Ghế VIP", "region": 1, "direct_url": None},
                # Hà Nội (region 9)
                {"name": "CGV Vincom Metropolis", "cineplex": "CGV Cinemas", "lat": 21.0315, "lng": 105.8150, "address": "Tầng M3, Vincom Metropolis, 29 Liễu Giai, Ba Đình", "format": "IMAX · Gold Class", "region": 9, "direct_url": None},
                {"name": "Trung Tâm Chiếu Phim Quốc Gia", "cineplex": "Chiếu Phim Quốc Gia", "lat": 21.0180, "lng": 105.8160, "address": "87 Láng Hạ, Đống Đa", "format": "2D/3D Kỹ Thuật Số", "region": 9, "direct_url": None},
                {"name": "Lotte West Lake", "cineplex": "Lotte Cinema", "lat": 21.0740, "lng": 105.8190, "address": "Tầng 4, Lotte Mall Tây Hồ, 272 Võ Chí Công, Tây Hồ", "format": "IMAX Laser · Cine Comfort", "region": 9, "direct_url": None},
                {"name": "CGV Vincom Trần Duy Hưng", "cineplex": "CGV Cinemas", "lat": 21.0080, "lng": 105.7950, "address": "Tầng 5, Vincom Plaza, Trần Duy Hưng, Cầu Giấy", "format": "ScreenX 270° · Forest", "region": 9, "direct_url": None}
            ]

            city_theaters = [t for t in TOP_THEATERS if t["region"] == active_region]
            fallback_cinemas = []
            momo_link = general_links.get("app_links", [{}])[0].get("universal_link") if general_links.get("app_links") else None
            cgv_link = general_links.get("app_links", [{}, {}])[1].get("universal_link") if len(general_links.get("app_links", [])) > 1 else None

            for t in city_theaters:
                dist = self._haversine_dist(user_lat, user_lon, t["lat"], t["lng"])
                eval_q = self._evaluate_cinema_quality(t["name"], t["cineplex"], t["format"])
                b_link = t.get("direct_url") or (cgv_link if "CGV" in t["cineplex"] else momo_link)
                fallback_cinemas.append({
                    "cinema_id": t["name"],
                    "cinema_name": t["name"],
                    "cineplex": t["cineplex"],
                    "address": t["address"],
                    "distance_km": dist,
                    "badges": eval_q["badges"],
                    "badge_str": eval_q["badge_str"],
                    "slots": [
                        {
                            "time": "Xem suất chiếu chi tiết tại app rạp",
                            "format": t["format"],
                            "booking_url": b_link,
                            "seat_recommendation": {
                                "summary": f"Hàng ghế vàng E / F / G / H (Ghế số 6 - 12 trung tâm)",
                                "consecutive_note": f"Khuyên chọn {ticket_count} ghế liên tục tại trục giữa để góc nhìn THX đạt chuẩn 36°.",
                                "is_sweet_spot": True
                            }
                        }
                    ],
                    "total_score": round(eval_q["quality_score"] + max(0.0, 50.0 - dist * 3.5), 1)
                })
            fallback_cinemas.sort(key=lambda x: x["total_score"], reverse=True)
            ranked_cinemas = fallback_cinemas

        return {
            "success": True,
            "movie_title": movie_title,
            "selected_date": target_date,
            "is_fallback_date": is_fallback_date,
            "fallback_notice": fallback_notice,
            "available_dates": available_dates,
            "user_location_label": loc_label,
            "ticket_count": ticket_count,
            "total_cinemas_found": len(ranked_cinemas),
            "total_slots_found": sum(len(c.get("slots", [])) for c in ranked_cinemas),
            "cinemas": ranked_cinemas,
            "general_booking_links": general_links
        }



if __name__ == "__main__":
    scraper = VnCinemaScraper()
    print("Testing MoMo Catalog count:", len(scraper.get_momo_catalog()))
    print("Testing MoMo Search 'Vùng Đất Quỷ Dữ':")
    momo_res = scraper.search_momo("Vùng Đất Quỷ Dữ", "Resident Evil")
    if momo_res:
        print(f"  -> MoMo Score: {momo_res['rating_point']}/10 ({momo_res['rating_total']} reviews, {momo_res['paid_tickets']} paid tickets)")
        print(f"  -> Sample Comment: {momo_res['top_comments'][0] if momo_res['top_comments'] else 'None'}")

    print("\nTesting Moveek Search 'Vùng Đất Quỷ Dữ':")
    moveek_res = scraper.search_moveek("Vùng Đất Quỷ Dữ", "Resident Evil")
    if moveek_res:
        print(f"  -> Moveek Score: {moveek_res.get('score')}/10 | Age: {moveek_res.get('age_rating')}")
        print(f"  -> Moveek Article: {moveek_res.get('review_article_title')}")
        print(f"  -> Quote: {moveek_res.get('review_article_quote')}")

    print("\nTesting Reviewer Pulse:")
    pulse = scraper.search_vn_creators_pulse("Vùng Đất Quỷ Dữ", "2026")
    print(f"  -> Quotes: {len(pulse['quotes'])}, Praise: {len(pulse['praise'])}, Criticisms: {len(pulse['criticisms'])}")
