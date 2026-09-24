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
import html
import hashlib
import urllib.request
import urllib.parse
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
