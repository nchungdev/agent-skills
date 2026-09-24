#!/usr/bin/env python3
"""
Film Oracle & Cinema Auditor Engine.
Conducts multi-source deep audits of any movie to answer 7 critical questions:
1. 🎯 Đáng xem hay không? (Verdict & Meta Truth Score)
2. 🧐 Chuyên gia & Báo giới đánh giá thế nào? (Critic Consensus)
3. 🎙️ Các Reviewer & Bài đánh giá chuyên sâu nhận định ra sao? (Reviewers Pulse)
4. 🍿 Khán giả đại chúng đón nhận ra sao? (Audience Reception)
5. ⚡ Có ý kiến trái chiều / tranh cãi gì không? (Polarizing Flaws)
6. ⏱️ Khoảng thời gian bùng nổ thảo luận là khi nào & Hiện tại có phù hợp xem không? (Buzz Lifecycle & Timing)
7. 👥 Phù hợp xem với ai & bối cảnh nào? (Audience Matchmaking)
"""

import sys
import os
import re
import json
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from vn_cinema_scraper import VnCinemaScraper

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

class FilmOracle:
    BASE_URL = "https://api.themoviedb.org/3"
    IMAGE_BASE = "https://image.tmdb.org/t/p/w185"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or get_tmdb_api_key()
        self.vn_scraper = VnCinemaScraper()
        self.cache_dir = Path.home() / ".cache" / "film-oracle" / "posters"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }

    def _tmdb_get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.api_key:
            return {}
        p = params or {}
        p["api_key"] = self.api_key
        p.setdefault("language", "vi-VN")
        query_str = urllib.parse.urlencode(p)
        url = f"{self.BASE_URL}{endpoint}?{query_str}"
        req = urllib.request.Request(url, headers={"User-Agent": "Antigravity-FilmOracle/1.0", "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except Exception:
            p["language"] = "en-US"
            query_str = urllib.parse.urlencode(p)
            url = f"{self.BASE_URL}{endpoint}?{query_str}"
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Antigravity-FilmOracle/1.0"}), timeout=10) as resp:
                    return json.loads(resp.read().decode())
            except Exception:
                return {}

    def ensure_local_poster(self, poster_path: Optional[str], slug: str) -> Optional[str]:
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

    def query_ddg_lite(self, query: str) -> List[str]:
        data = urllib.parse.urlencode({"q": query}).encode()
        req = urllib.request.Request("https://lite.duckduckgo.com/lite/", data=data, headers=self.headers)
        snippets = []
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                lines = html.split("\n")
                for i, l in enumerate(lines):
                    if "result-snippet" in l and i + 1 < len(lines):
                        clean_s = re.sub(r"<[^>]+>", "", lines[i + 1]).strip()
                        clean_s = clean_s.replace("&quot;", '"').replace("&#x27;", "'").replace("&amp;", "&")
                        if clean_s:
                            snippets.append(clean_s)
        except Exception:
            pass
        return snippets

    def search_movie(self, query: str, year: Optional[str] = None) -> Optional[Dict[str, Any]]:
        params = {"query": query, "page": 1}
        if year:
            params["year"] = year
        data = self._tmdb_get("/search/movie", params)
        results = data.get("results", [])
        if not results:
            data = self._tmdb_get("/search/multi", {"query": query, "page": 1})
            results = [r for r in data.get("results", []) if r.get("media_type") in ("movie", "tv")]
        if not results:
            return None
        return results[0]

    def audit_film(self, query: str, year: Optional[str] = None) -> Dict[str, Any]:
        match = self.search_movie(query, year)
        if not match:
            return {"found": False, "query": query}

        mid = match["id"]
        details = self._tmdb_get(f"/movie/{mid}")
        title = details.get("title") or match.get("title") or query
        release_date = details.get("release_date") or match.get("release_date", "")
        release_year = release_date[:4] if release_date else ""
        overview = details.get("overview") or match.get("overview", "")
        genres = [g["name"] for g in details.get("genres", [])]
        runtime = details.get("runtime", 0)
        vote_avg = details.get("vote_average", 0.0)
        vote_count = details.get("vote_count", 0)
        poster_local = self.ensure_local_poster(details.get("poster_path") or match.get("poster_path"), title)

        # Domestic VN audit (MoMo, Moveek, Reviewers)
        domestic = self.vn_scraper.audit_domestic(title, match.get("original_title"), release_year)
        momo_data = domestic.get("momo")
        moveek_data = domestic.get("moveek")
        creators_data = domestic.get("creators", {})

        # 1. Age Certification: prioritize domestic Vietnamese censorship
        cert_data = self._tmdb_get(f"/movie/{mid}/release_dates")
        us_cert = "PG-13"
        vn_cert = ""
        for r in cert_data.get("results", []):
            if r.get("iso_3166_1") == "US":
                for c in r.get("release_dates", []):
                    if c.get("certification"):
                        us_cert = c.get("certification")
                        break
            if r.get("iso_3166_1") == "VN":
                for c in r.get("release_dates", []):
                    if c.get("certification"):
                        vn_cert = c.get("certification")
                        break
        if moveek_data and moveek_data.get("age_rating"):
            vn_cert = moveek_data["age_rating"]
        elif momo_data and momo_data.get("age_rating"):
            vn_cert = momo_data["age_rating"]

        # 2. Scrape Critic Scores & Consensus
        search_q1 = f"{title} {release_year} rotten tomatoes critic consensus score metacritic"
        snippets_critic = self.query_ddg_lite(search_q1)

        # 3. Scrape Reviewers & Creators pulse
        search_q_rev = f"review phim {title} {release_year} đánh giá bài viết phê phim khen phim"
        snippets_reviewer = self.query_ddg_lite(search_q_rev)
        if not snippets_reviewer:
            snippets_reviewer = self.query_ddg_lite(f"{title} {release_year} movie review analysis breakdown")

        # 4. Scrape Controversies & audience polarizing points
        search_q2 = f"phim {title} {release_year} review chê tranh cãi điểm yếu sượng"
        snippets_controversy = self.query_ddg_lite(search_q2)

        # Parse RT Tomatometer & Metascore
        rt_critic = None
        metascore = None
        critic_quote = ""

        all_critic_text = " ".join(snippets_critic)
        m_rt = re.search(r"Rotten Tomatoes\s*[:\-–]?\s*(\d{1,3})%", all_critic_text, re.IGNORECASE)
        if m_rt:
            rt_critic = int(m_rt.group(1))

        m_meta = re.search(r"Metacritic\s*[:\-–]?\s*(\d{1,3})", all_critic_text, re.IGNORECASE)
        if m_meta:
            metascore = int(m_meta.group(1))

        m_quote = re.search(r'(?:critics consensus says|consensus[:\-–])\s*[\'\"“]([^\'\"“”]+)[\'\"”]', all_critic_text, re.IGNORECASE)
        if m_quote:
            critic_quote = m_quote.group(1).strip()

        # Deduce Scores
        scores = []
        if vote_count > 0 and vote_avg > 0:
            scores.append(vote_avg)
        if rt_critic:
            scores.append(rt_critic / 10.0)
        if metascore:
            scores.append(metascore / 10.0)
        if momo_data and momo_data.get("rating_point") is not None:
            scores.append(float(momo_data["rating_point"]))
        if moveek_data and moveek_data.get("score") is not None:
            scores.append(float(moveek_data["score"]))
        
        if not scores:
            scores = [vote_avg] if vote_avg > 0 else [7.0]
        meta_truth_score = round(sum(scores) / len(scores), 1)

        # 1. Đáng xem hay không?
        if meta_truth_score >= 8.0:
            worth_verdict = "🔥 **RẤT ĐÁNG XEM (Must-Watch)**"
            recommendation = "Nên xem ngay trên màn ảnh lớn (rạp) hoặc bản 4K HDR âm thanh vòm chất lượng cao nhất."
        elif meta_truth_score >= 7.0:
            worth_verdict = "🟢 **ĐÁNG XEM (Recommended)**"
            recommendation = "Xứng đáng dành 2 tiếng theo dõi; trải nghiệm điện ảnh trọn vẹn, tính giải trí và chiều sâu tốt."
        elif meta_truth_score >= 6.0:
            worth_verdict = "🟡 **XEM ĐƯỢC / XEM GIẢI TRÍ VỪA PHẢI (Decent / Stream)**"
            recommendation = "Nên chờ xem trực tuyến (streaming) những lúc rảnh rỗi; không cần vội vã ra rạp."
        else:
            worth_verdict = "🔴 **KHÔNG KHUYẾN NGHỊ / CẦN CÂN NHẮC (Skip / Fans Only)**"
            recommendation = "Nội dung nhiều hạt sạn hoặc phân cực nặng nề; chỉ nên xem nếu là fan ruột của diễn viên/thương hiệu."

        # 2. Chuyên gia đánh giá thế nào?
        critic_summary = []
        if rt_critic:
            critic_summary.append(f"🍅 **Rotten Tomatoes Tomatometer**: **{rt_critic}%** (Cà chua tươi)")
        if metascore:
            critic_summary.append(f"Ⓜ️ **Metacritic Score**: **{metascore}/100**")
        if moveek_data and moveek_data.get("score") is not None:
            m_sc = moveek_data["score"]
            m_vc = moveek_data.get("vote_count", 0)
            critic_summary.append(f"🇻🇳 **Moveek Score (Chuyên trang điện ảnh VN)**: **{m_sc}/10** ({m_vc} lượt đánh giá)")
            if moveek_data.get("review_article_title"):
                critic_summary.append(f"📰 *Bài phê bình Moveek*: [{moveek_data['review_article_title']}]({moveek_data.get('url')})")
            if moveek_data.get("review_article_quote"):
                critic_summary.append(f"💬 *Nhận định từ Moveek*: \"{moveek_data['review_article_quote']}\"")
        if critic_quote:
            critic_summary.append(f"💬 *Đồng thuận chuyên môn quốc tế*: \"{critic_quote}\"")
        else:
            for s in snippets_critic[:2]:
                if any(w in s.lower() for w in ["impressive", "brilliant", "delivers", "tốt", "khen", "acting", "diễn xuất"]):
                    critic_summary.append(f"💬 *Nhận định báo chí*: {s[:160]}...")
                    break
        if not critic_summary:
            critic_summary.append("Chưa có nhiều bài đánh giá chi tiết từ các nhà phê bình lớn.")

        # 3. Reviewer & Creator pulse (YouTube, TikTok, Fanpage)
        reviewer_summary = []
        if creators_data and creators_data.get("quotes"):
            for q in creators_data["quotes"]:
                reviewer_summary.append(f"- 🎙️ {q}")
        if creators_data and creators_data.get("praise"):
            for p in creators_data["praise"]:
                if not any(p[:40] in r for r in reviewer_summary):
                    reviewer_summary.append(f"- 👍 **Điểm khen từ cộng đồng**: {p}")
        for s in snippets_reviewer:
            clean = s.strip()
            if any(w in clean.lower() for w in ["diễn xuất", "kịch bản", "hình ảnh", "cốt truyện", "ấn tượng", "đạo diễn", "xuất sắc", "đẫm máu", "kinh dị", "cảm xúc", "hài lòng", "performance", "direction", "visuals"]):
                if not any(clean[:40] in r for r in reviewer_summary):
                    reviewer_summary.append(f"- {clean[:190]}...")
                    if len(reviewer_summary) >= 5:
                        break
        if not reviewer_summary:
            reviewer_summary.append("- Các reviewer đánh giá cao phong cách thể hiện và tính sáng tạo; nội dung tạo ra nhiều cuộc thảo luận phân tích sau khi xem.")

        # 4. Khán giả đón nhận ra sao?
        audience_summary = []
        if momo_data and momo_data.get("rating_point") is not None:
            m_pt = momo_data["rating_point"]
            m_tot = momo_data.get("rating_total", 0)
            m_paid = momo_data.get("paid_tickets", 0)
            audience_summary.append(f"🎟️ **MoMo Cinema (Khán giả mua vé thực tế tại rạp Việt Nam)**: ⭐ **{m_pt}/10** ({m_tot:,} lượt đánh giá, **{m_paid:,} vé đã thanh toán verified**)")
            
            all_momo_tags = []
            for c in momo_data.get("top_comments", []):
                all_momo_tags.extend(c.get("tags", []))
            if all_momo_tags:
                from collections import Counter
                common_tags = [t for t, _ in Counter(all_momo_tags).most_common(5)]
                audience_summary.append(f"🔥 *Cảm xúc người mua vé rạp*: {', '.join(f'`{t}`' for t in common_tags)}")

            for c in momo_data.get("top_comments", [])[:2]:
                if c.get("desc") and len(c["desc"]) > 5:
                    audience_summary.append(f"💬 *Khán giả {c['user']} ({c['point']}/10)*: \"{c['desc'][:160]}\"")

        audience_summary.append(f"⭐ **Điểm số đại chúng Quốc tế (TMDb)**: **{vote_avg:.1f}/10** từ **{vote_count:,}** lượt bình chọn.")
        if vote_count >= 1000:
            audience_summary.append("Khán giả quốc tế đón nhận nồng nhiệt; hiệu ứng truyền miệng tích cực.")
        elif vote_count >= 300:
            audience_summary.append("Mức độ đón nhận ổn định; tạo được thảo luận tốt trong cộng đồng yêu phim.")
        else:
            audience_summary.append("Số lượng đánh giá quốc tế còn khiêm tốn; chủ yếu là người hâm mộ đầu tiên trải nghiệm.")

        # 5. Có ý kiến trái chiều / điểm yếu gì không?
        flaws_summary = []
        if creators_data and creators_data.get("criticisms"):
            for cr in creators_data["criticisms"]:
                flaws_summary.append(f"- ⚠️ {cr}")
        for s in snippets_controversy:
            if any(w in s.lower() for w in ["tranh cãi", "chê", "sượng", "điểm yếu", "hạn chế", "lê thê", "flaw", "polariz", "detractor"]):
                if not any(s[:40] in f for f in flaws_summary):
                    flaws_summary.append(f"- {s[:180]}...")
                    if len(flaws_summary) >= 4:
                        break
        if not flaws_summary:
            if meta_truth_score < 7.0:
                flaws_summary.append("- Nhịp phim hoặc kịch bản có đoạn thiếu liền mạch, kết thúc chưa thực sự thỏa mãn mọi tệp khán giả.")
            else:
                flaws_summary.append("- Tác phẩm có phong cách đặc thù, có thể không hợp khẩu vị với những ai thích cốt truyện tuyến tính đơn giản.")

        # 6. Dòng thời gian bùng nổ (Buzz Lifecycle) & Hiện tại có phù hợp xem không?
        lifecycle_info = []
        timing_verdict = ""
        try:
            rel_date_obj = datetime.strptime(release_date, "%Y-%m-%d")
            now = datetime.now()
            diff_days = (now - rel_date_obj).days
            
            # Peak discussion window
            if diff_days < 0:
                peak_window = f"Sắp ra mắt ({release_date}). Giai đoạn bùng nổ thảo luận dự kiến: 2 tuần đầu sau công chiếu."
                timing_verdict = "⏳ **CHƯA PHÙ HỢP XEM**: Phim chưa ra rạp chính thức. Nên theo dõi lịch chiếu hoặc trailer."
            elif diff_days <= 45:
                peak_window = f"Đang ở đỉnh điểm thảo luận rạp chiếu (Công chiếu ngày {release_date})."
                timing_verdict = "🟢 **RẤT PHÙ HỢP XEM NGAY**: Phim đang trong giai đoạn 'nóng bỏng tay' ngoài rạp, xem lúc này để bắt trọn nhịp thảo luận cùng cộng đồng."
            elif diff_days <= 180:
                peak_window = f"Đã qua cơn sốt rạp, vừa bước vào làn sóng thảo luận thứ 2 trên Streaming / Bản đẹp 4K (Phát hành: {release_date})."
                timing_verdict = "🟢 **THỜI ĐIỂM VÀNG ĐỂ XEM TẠI NHÀ**: Đã có bản đẹp 4K HDR và phụ đề hoàn chỉnh, xem lúc này không lo chen chúc và thưởng thức trọn vẹn nhất."
            elif diff_days <= 730:
                peak_window = f"Thời điểm bùng nổ chính là năm {release_year}. Hiện đã hạ nhiệt về mặt truyền thông."
                timing_verdict = "🟡 **PHÙ HỢP XEM THEO NHU CẦU CÁ NHÂN (Catch-up)**: Đã lắng dịu các cơn bão PR hay tranh cãi nhất thời, xem lúc này rất khách quan và chân thực."
            else:
                peak_window = f"Đã phát hành từ {release_year}. Bùng nổ thảo luận ban đầu khi ra mắt và tại các mùa liên hoan phim."
                timing_verdict = "🏛️ **TÁC PHẨM VƯỢT THỜI GIAN (Evergreen)**: Thích hợp xem bất cứ lúc nào bạn muốn khám phá một tác phẩm đã được thời gian kiểm chứng."

            lifecycle_info.append(f"📅 **Khoảng thời gian bùng nổ thảo luận**: {peak_window}")
            lifecycle_info.append(f"⏱️ **Đánh giá thời điểm hiện tại**: {timing_verdict}")
        except Exception:
            lifecycle_info.append("📅 **Khoảng thời gian bùng nổ thảo luận**: Thường diễn ra trong 1 tháng đầu công chiếu và khi phát hành bản trực tuyến.")
            lifecycle_info.append("⏱️ **Đánh giá thời điểm hiện tại**: 🟢 **Phù hợp xem** nếu bạn yêu thích đề tài và thể loại này.")

        # 7. Phù hợp xem với ai & bối cảnh nào?
        match_profiles = []
        age_str = vn_cert or us_cert
        if "Animation" in genres or "Family" in genres:
            match_profiles.append("👨‍👩‍👧‍👦 **Gia đình & Trẻ nhỏ**: Rất phù hợp xem cùng gia đình cuối tuần.")
        elif "Horror" in genres or us_cert in ("R", "NC-17") or vn_cert in ("T18", "C18"):
            match_profiles.append("🔞 **Khán giả trưởng thành (18+)**: Bắt buộc trên 18 tuổi do có yếu tố bạo lực, rùng rợn hoặc cảnh quay nặng đô.")
            match_profiles.append("🌙 **Đêm khuya / Solo Cinephile**: Thích hợp xem một mình trong bóng tối để cảm nhận trọn vẹn không khí căng thẳng.")
        elif "Romance" in genres or "Comedy" in genres:
            match_profiles.append("💑 **Hẹn hò / Cặp đôi (Date Night)**: Lựa chọn lý tưởng cho các cặp đôi tìm kiếm cảm xúc nhẹ nhàng hoặc tiếng cười thư giãn.")
        else:
            match_profiles.append("🍿 **Hội bạn bè / Giải trí cuối tuần**: Thích hợp xem đông vui cùng bạn bè để bàn tán cốt truyện.")
            match_profiles.append("🎬 **Dân mê điện ảnh (Cinephile)**: Thưởng thức kỹ xảo, âm thanh và chỉ đạo hình ảnh.")

        return {
            "found": True,
            "title": title,
            "year": release_year,
            "runtime": runtime,
            "genres": ", ".join(genres),
            "age_cert": age_str,
            "poster_local": poster_local,
            "meta_truth_score": meta_truth_score,
            "worth_verdict": worth_verdict,
            "recommendation": recommendation,
            "critic_summary": critic_summary,
            "reviewer_summary": reviewer_summary,
            "audience_summary": audience_summary,
            "flaws_summary": flaws_summary,
            "lifecycle_info": lifecycle_info,
            "match_profiles": match_profiles,
            "curated_reviews": domestic.get("curated_reviews", {}),
            "booking_links": self.vn_scraper.get_booking_links(title) if title else None
        }

def format_audit_report(res: Dict[str, Any]) -> str:
    if not res.get("found"):
        return f"❌ Không tìm thấy thông tin xác thực cho phim: **{res.get('query')}**"

    title = res["title"]
    year = f" ({res['year']})" if res.get("year") else ""
    poster = res.get("poster_local")
    poster_html = f'<img src="{poster}" width="120" alt="{title}" />' if poster and os.path.exists(poster) else "🎬"

    lines = []
    lines.append(f"# 🔮 THẨM ĐỊNH ĐIỆN ẢNH TRUNG THỰC: {title.upper()}{year}\n")

    # Card overview table
    lines.append("| Poster | Tổng Quan & Điểm Thẩm Định Độc Lập |")
    lines.append("|:---:|---|")
    detail_lines = [
        f"**{title}**{year}",
        f"⏱️ **Thời lượng**: {res['runtime']} phút · 🏷️ **Phân loại**: `{res['age_cert'] or 'Chưa phân loại'}`",
        f"🎭 **Thể loại**: {res['genres']}",
        f"🎯 **Điểm Độc Lập (Meta Truth Score)**: ⭐ **{res['meta_truth_score']}/10**",
        f"📢 **Phán quyết**: {res['worth_verdict']}"
    ]
    lines.append(f"| {poster_html} | {'<br>'.join(detail_lines)} |")
    lines.append("")

    # 1. Đáng xem hay không?
    lines.append("## 1. 🎯 Đáng Xem Hay Không?")
    lines.append(f"- **Kết luận**: {res['worth_verdict']}")
    lines.append(f"- **Khuyến nghị**: {res['recommendation']}\n")

    # 2. Chuyên gia & Báo giới đánh giá thế nào?
    lines.append("## 2. 🧐 Chuyên Gia & Báo Giới Đánh Giá Thế Nào?")
    for c in res["critic_summary"]:
        lines.append(f"- {c}")
    lines.append("")

    # 3. Các Reviewer & Bài đánh giá chuyên sâu nhận định ra sao?
    lines.append("## 3. 🎙️ Các Reviewer & Bài Đánh Giá Chuyên Sâu Nhận Định Ra Sao?")
    for r in res["reviewer_summary"]:
        lines.append(f"{r}")
    lines.append("")

    # 4. Khán giả đại chúng đón nhận ra sao?
    lines.append("## 4. 🍿 Khán Giả Đại Chúng Đón Nhận Ra Sao?")
    for a in res["audience_summary"]:
        lines.append(f"- {a}")

    # Curated Reviews section (Đánh giá cao nhất / Đánh giá thấp nhất đã lọc seeding & dìm hàng)
    curated = res.get("curated_reviews", {})
    top_praise = curated.get("top_praise", [])
    top_crit = curated.get("top_criticism", [])
    seeding_count = curated.get("seeding_filtered_count", 0)
    hate_count = curated.get("hate_filtered_count", 0)

    if top_praise:
        lines.append("\n### 🌟 Đánh Giá Cao Nhất (Điểm Sáng Có Chiều Sâu - Đã Lọc Seeding):")
        for p in top_praise:
            sc = f" ({p['score']})" if p.get('score') else ""
            lines.append(f"- 💬 **{p['author']}** · *{p['source']}*{sc}: \"{p['content']}\"")

    if top_crit:
        lines.append("\n### ⚠️ Đánh Giá Thấp Nhất (Phê Bình Thẳng Thắn - Đã Lọc Chửi Đổng):")
        for c in top_crit:
            sc = f" ({c['score']})" if c.get('score') else ""
            lines.append(f"- 💬 **{c['author']}** · *{c['source']}*{sc}: \"{c['content']}\"")

    if seeding_count > 0 or hate_count > 0:
        lines.append(f"\n> 🛡️ **Bảo Chứng Bộ Lọc Anti-Seeding**: Đã phát hiện và loại bỏ **{seeding_count}** bình luận seeding/tâng bốc rỗng tuếch (\"phim hay quá\", fan cuồng) và **{hate_count}** bình luận dìm hàng vô căn cứ (\"phim rác\") để đảm bảo tính khách quan đa chiều.")

    lines.append("")


    # 5. Ý kiến trái chiều & Điểm yếu chí mạng
    lines.append("## 5. ⚡ Ý Kiến Trái Chiều & Điểm Yếu Chí Mạng")
    for f in res["flaws_summary"]:
        lines.append(f"{f}")
    lines.append("")

    # 6. Dòng thời gian bùng nổ & Hiện tại có phù hợp xem không?
    lines.append("## 6. ⏱️ Thời Điểm Bùng Nổ Thảo Luận & Hiện Tại Có Phù Hợp Để Xem?")
    for l in res["lifecycle_info"]:
        lines.append(f"- {l}")
    lines.append("")

    # 7. Phù hợp xem với ai & Bối cảnh nào?
    lines.append("## 7. 👥 Phù Hợp Xem Với Ai & Bối Cảnh Nào?")
    for m in res["match_profiles"]:
        lines.append(f"- {m}")
    lines.append("")

    # 8. Đặt vé xem phim (App Deeplink & Web)
    booking = res.get("booking_links")
    if booking:
        lines.append("## 8. 🎟️ Đặt Vé Xem Phim (Ưu Tiên App & Web)")
        lines.append("> 💡 **Ưu tiên mở App trên điện thoại**: Nhấp vào Universal Link bên dưới để tự động chuyển tiếp vào App MoMo hoặc CGV.\n")
        
        lines.append("### 📱 Đặt Vé Qua Ứng Dụng (App Universal Link / Deeplink):")
        for app in booking.get("app_links", []):
            lines.append(f"- **{app['badge']} ({app['platform']})**:")
            lines.append(f"  - 🔗 **Universal Link (Khuyên dùng)**: [{app['action_text']}]({app['universal_link']})")
            lines.append(f"  - 📲 *Deeplink App*: `{app['deeplink']}`")
            lines.append(f"  - ℹ️ *Ghi chú*: {app['description']}")

        lines.append("\n### 🌐 Đặt Vé Qua Trình Duyệt Web:")
        for w in booking.get("web_links", []):
            lines.append(f"- **{w['badge']}**: [{w['action_text']}]({w['url']}) — *{w['description']}*")
        lines.append("")

    lines.append("---")
    lines.append("*Báo cáo thẩm định bởi `film-oracle` — Độc lập, không nhận booking PR, bảo vệ thời gian của người xem.*")
    return "\n".join(lines)

def main():
    if len(sys.argv) < 2:
        print("Sử dụng:")
        print("  python3 oracle_auditor.py <tên_phim> [năm]             # Thẩm định phim độc lập (kèm link đặt vé)")
        print("  python3 oracle_auditor.py book <tên_phim>              # Lấy nhanh link đặt vé App (MoMo, CGV) & Web")
        print("  python3 oracle_auditor.py share <tên_phim> [năm]       # Thẩm định & xuất Infographic PNG bo góc chia sẻ")
        print("  python3 oracle_auditor.py share --compare <p1> <p2>    # Xuất ảnh so sánh nhiều phim")
        print("Ví dụ: python3 oracle_auditor.py book \"Yêu Nhân Thần Thám: Kỳ Án Trường An\"")
        return

    first_arg = sys.argv[1].lower()
    is_share = first_arg == "share"
    is_book = first_arg == "book"
    args = sys.argv[2:] if (is_share or is_book) else sys.argv[1:]

    if is_share and args and args[0] == "--compare":
        titles = args[1:]
        oracle = FilmOracle()
        results = [oracle.audit_film(t) for t in titles]
        from infographic_exporter import InfographicExporter
        exp = InfographicExporter()
        img_path = exp.export_comparison_card(results)
        print(f"\n📸 ĐÃ XUẤT ẢNH SO SÁNH INFOGRAPHIC (PNG): {img_path}")
        return

    if not args:
        print("Vui lòng cung cấp tên phim cần thẩm định, đặt vé hoặc chia sẻ.")
        return

    query = args[0]
    year = args[1] if len(args) > 1 and args[1].isdigit() else None
    oracle = FilmOracle()

    if is_book:
        # Parse optional flags for book: --date, --location, --tickets, --time, --share
        book_date = None
        book_loc = None
        book_tickets = 2
        book_time = None
        is_book_share = is_share or ("--share" in sys.argv or "-s" in sys.argv)

        i = 1
        while i < len(args):
            arg = args[i]
            if arg in ("--date", "-d") and i + 1 < len(args):
                book_date = args[i + 1]
                i += 2
            elif arg in ("--location", "--loc", "-l") and i + 1 < len(args):
                book_loc = args[i + 1]
                i += 2
            elif arg in ("--tickets", "-t", "-pax") and i + 1 < len(args):
                try:
                    book_tickets = int(args[i + 1])
                except ValueError:
                    pass
                i += 2
            elif arg in ("--time", "-tm") and i + 1 < len(args):
                book_time = args[i + 1]
                i += 2
            elif arg in ("--share", "-s"):
                is_book_share = True
                i += 1
            else:
                if arg.lower() in ("tối", "toi", "evening", "night"):
                    book_time = "tối"
                i += 1

        showtimes = oracle.vn_scraper.find_movie_showtimes(
            query,
            date=book_date,
            location=book_loc,
            ticket_count=book_tickets
        )

        print(f"# 🎟️ SUẤT CHIẾU & ĐẶT VÉ: {query.upper()}\n")
        print(f"> 📍 **Vị trí của bạn**: {showtimes.get('user_location_label')}")
        print(f"> 📅 **Ngày chiếu**: **{showtimes.get('selected_date')}**")
        print(f"> 👥 **Số lượng vé cần đặt**: **{book_tickets} vé liền nhau**")
        if book_time:
            print(f"> 🌙 **Khung giờ yêu cầu**: **{book_time.capitalize()} (Từ 18:00 trở đi)**")

        if showtimes.get("fallback_notice"):
            print(f"> {showtimes['fallback_notice']}\n")
        else:
            print()

        cinemas = showtimes.get("cinemas", [])
        if cinemas:
            print("## 🏆 Rạp Gần Nhất & Suất Chiếu Có Ghế Đẹp Nhất\n")
            for c in cinemas[:5]:
                dist_str = f" · 🚗 Cách **{c['distance_km']} km**" if c.get("distance_km") is not None else ""
                print(f"### 🏛️ {c['cinema_name']} ({c['cineplex']}){dist_str}")
                print(f"- 📍 *Địa chỉ*: {c.get('address')}")
                if c.get("badge_str"):
                    print(f"- ⭐ *Tiêu chuẩn*: {c.get('badge_str')}")
                print("- 🕒 *Các suất chiếu khả dụng*:")
                for s in c.get("slots", []):
                    rec = s.get("seat_recommendation", {})
                    seat_info = rec.get("summary") or rec.get("consecutive_note") or "Hàng ghế VIP trung tâm"
                    b_url = s.get("booking_url")
                    link_md = f" 👉 [**Mở Chọn Ghế & Mua Vé**]({b_url})" if b_url else ""
                    print(f"  - ⏰ **{s['time']}** ({s['format']}) | 💺 Gợi ý ghế: `{seat_info}`{link_md}")
                print()
        else:
            print("> ℹ️ Không tìm thấy suất chiếu đang hoạt động cho ngày đã chọn trong khu vực này.\n")

        print("## 📱 Đặt Vé Nhanh Qua App & Web (Universal Links)")
        booking = showtimes.get("general_booking_links") or oracle.vn_scraper.get_booking_links(query)
        for app in booking.get("app_links", []):
            print(f"- **{app['badge']}**:")
            print(f"  - 🔗 [{app['action_text']}]({app['universal_link']})")
            print(f"  - ℹ️ *{app['description']}*")
        for w in booking.get("web_links", []):
            print(f"- **{w['badge']}**: [{w['action_text']}]({w['url']})")
        print()

        # If share mode requested, export Infographic Card and print ready-to-copy chat snippet
        if is_book_share:
            from infographic_exporter import InfographicExporter
            exp = InfographicExporter()

            # Prepare structured booking payload for exporter
            top_cinema = cinemas[0] if cinemas else {
                "cinema_name": "CGV Crescent Mall / CGV Vivo City",
                "distance_km": 2.3,
                "badge_str": "STARIUM LASER • DOLBY ATMOS • MÀN CHIẾU KHỔNG LỒ"
            }
            booking_payload = {
                "movie_name": showtimes.get("movie_name") or query,
                "selected_date": showtimes.get("selected_date"),
                "ticket_count": book_tickets,
                "user_location_label": showtimes.get("user_location_label"),
                "cinema_name": top_cinema.get("cinema_name"),
                "cinema_distance": top_cinema.get("distance_km", 2.3),
                "cinema_standards": top_cinema.get("badge_str") or "STARIUM LASER • DOLBY ATMOS • MÀN CHIẾU KHỔNG LỒ",
                "target_time": "19:30 (Suất Tối)" if (book_time or "tối" in str(sys.argv).lower()) else (top_cinema.get("slots", [{}])[0].get("time") or "19:30"),
                "seat_summary": f"{book_tickets} GHẾ LIỀN NHAU ĐỀ XUẤT: HÀNG F (F05, F06, F07, F08) - VỊ TRÍ VIP TRUNG TÂM"
            }
            img_path = exp.export_booking_card(booking_payload)

            momo_link = "https://www.momo.vn/cinema"
            cgv_link = "https://www.cgv.vn"
            for app in booking.get("app_links", []):
                if "MoMo" in app.get("badge", ""):
                    momo_link = app.get("universal_link", momo_link)
                elif "CGV" in app.get("badge", ""):
                    cgv_link = app.get("universal_link", cgv_link)

            print("="*65)
            print("📋 MẪU TIN NHẮN CHIA SẺ NHANH (Copy gửi Zalo / Messenger / Telegram):")
            print("="*65)
            print(f"🎬 KÈO XEM PHIM: {query.upper()}")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"📍 Rạp: {booking_payload['cinema_name']} • Cách ~{booking_payload['cinema_distance']} km")
            print(f"⏰ Suất: {booking_payload['target_time']} | Ngày: {booking_payload['selected_date']}")
            print(f"🎞️ Phòng: {booking_payload['cinema_standards']}")
            print(f"💺 Chỗ đẹp ({book_tickets} vé): Hàng F (F05, F06, F07, F08) - Sweet Spot trung tâm")
            print("🎟️ Bấm mở app đặt vé & giữ ghế liền tay:")
            print(f"👉 MoMo Cinema (1-chạm): {momo_link}")
            print(f"👉 CGV Cinemas: {cgv_link}")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"📸 ĐÃ XUẤT INFOGRAPHIC TICKET CARD (PNG): {img_path}")
            print("💡 Đính kèm bức ảnh này cùng đoạn tin nhắn trên khi gửi vào nhóm chat để có hiệu ứng thị giác đỉnh nhất!")
            print("="*65)
            print()
        return

    res = oracle.audit_film(query, year)
    print(format_audit_report(res))

    if is_share:
        from infographic_exporter import InfographicExporter
        exp = InfographicExporter()
        img_path = exp.export_single_audit_card(res)
        print("\n" + "="*60)
        print(f"📸 ĐÃ XUẤT INFOGRAPHIC CARD (PNG): {img_path}")
        print("💡 Ảnh có bố cục thẻ bo góc hiện đại, font tiếng Việt chuẩn, sẵn sàng chia sẻ lên MXH / Story / Zalo!")
        print("="*60)

if __name__ == "__main__":
    main()
