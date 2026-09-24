#!/usr/bin/env python3
"""
Media Advisor Master CLI: Homelab Cinema & Series Recommendation Concierge.
Integrates local Plex/Jellyfin SQLite DB, TMDb Theatrical/Streaming trends, and Anti-seeding sentiment.
Outputs beautiful 2-column visual Markdown tables with local poster thumbnails.
"""

import sys
import os
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from advisor_setup import load_config, run_survey
from plex_reader import PlexReader
from sentiment_filter import SentimentFilter
from tmdb_trends import TMDbTrends

def render_movie_card_table(items: List[Dict[str, Any]], title_section: str = "") -> str:
    """Renders items into a 2-column GitHub-Flavored Markdown table with local thumbnails."""
    if not items:
        return "*(Không tìm thấy đề xuất nào phù hợp)*\n"

    lines = []
    if title_section:
        lines.append(f"### {title_section}\n")

    lines.append("| Poster | Thông Tin Chi Tiết & Đánh Giá Thực Tế |")
    lines.append("|:---:|---|")

    for item in items:
        title = item.get("title", "Không rõ")
        year = item.get("year") or (item.get("release_date", "")[:4] if item.get("release_date") else "")
        year_str = f" ({year})" if year else ""
        
        # Poster cell
        poster_local = item.get("poster_local")
        if poster_local and os.path.exists(poster_local):
            poster_html = f'<img src="{poster_local}" width="115" alt="{title}" />'
        else:
            poster_html = "🎬<br>*(No Poster)*"

        # Content lines
        info_lines = []
        info_lines.append(f"**{title}**{year_str}")

        # Rating & Sentiment badge
        rating = item.get("adjusted_rating") or item.get("rating") or item.get("vote_average")
        vote_count = item.get("vote_count", 0)
        badge = item.get("sentiment_badge", "")
        
        rating_part = f"⭐ **{rating:.1f}/10**" if rating else "⭐ *Chưa chấm điểm*"
        if vote_count > 0:
            rating_part += f" ({vote_count:,} lượt đánh giá)"
        if badge:
            rating_part += f" · {badge}"
        info_lines.append(rating_part)

        # NAS / Local Status
        nas_status = item.get("nas_status")
        if nas_status:
            info_lines.append(f"📍 **Kho NAS**: {nas_status}")

        # Progress if in-progress
        progress = item.get("progress_percent")
        if progress is not None:
            off_m = item.get("offset_minutes", 0)
            dur_m = item.get("duration_minutes", 0)
            info_lines.append(f"⏱️ **Tiến độ**: Đã xem {progress}% ({off_m}/{dur_m} phút)")

        # Summary
        summary = item.get("summary") or item.get("overview") or ""
        if summary:
            clean_sum = summary.replace("\n", " ").replace("|", "I").strip()
            if len(clean_sum) > 220:
                clean_sum = clean_sum[:217] + "..."
            info_lines.append(f"📝 {clean_sum}")

        detail_cell = "<br>".join(info_lines)
        lines.append(f"| {poster_html} | {detail_cell} |")

    return "\n".join(lines) + "\n"

def cmd_unwatched(args):
    cfg = load_config()
    plex = PlexReader(cfg.get("plex_db_path"))
    sentiment = SentimentFilter(cfg.get("anti_seeding_min_votes", 300), cfg.get("min_rating", 6.5))
    tmdb = TMDbTrends()

    if not plex.available:
        print("❌ Không tìm thấy Plex Database. Hãy chạy `media-advisor setup` để cấu hình đường dẫn.")
        return

    items = plex.get_unwatched_library(limit=args.limit, min_rating=0.0)
    
    for item in items:
        item["nas_status"] = "🟢 Sẵn sàng xem ngay trên NAS"
        
        # 1. Try resolving via embedded tmdb_id
        t_match = None
        if tmdb.api_key and item.get("tmdb_id"):
            t_match = tmdb.get_details_by_id(item["tmdb_id"], "movie" if item.get("type") == "Movie" else "tv")
        
        # 2. Fallback to title search
        if not t_match and tmdb.api_key:
            res = tmdb.search_multi(item["title"], limit=1)
            if res:
                t_match = res[0]

        if t_match:
            item["poster_local"] = t_match.get("poster_local")
            item["vote_count"] = t_match.get("vote_count", 0)
            item["vote_average"] = t_match.get("vote_average", 0.0)
            s_res = sentiment.analyze_sentiment(item["vote_average"], item["vote_count"], item["title"])
            item["sentiment_badge"] = s_res.get("badge")
            item["adjusted_rating"] = s_res.get("adjusted_rating")

    print(render_movie_card_table(items, f"💎 KHO BÁU BỎ QUÊN TRÊN NAS (Chưa xem, sẵn sàng phát ngay)"))

def cmd_continue(args):
    cfg = load_config()
    plex = PlexReader(cfg.get("plex_db_path"))
    tmdb = TMDbTrends()

    if not plex.available:
        print("❌ Không tìm thấy Plex Database. Hãy chạy `media-advisor setup` để cấu hình đường dẫn.")
        return

    items = plex.get_in_progress(limit=args.limit)
    for item in items:
        item["nas_status"] = "🟢 Sẵn sàng trên NAS"
        
        t_match = None
        if tmdb.api_key and item.get("tmdb_id"):
            t_match = tmdb.get_details_by_id(item["tmdb_id"], "tv" if item.get("type") == "Episode" else "movie")
        
        if not t_match and tmdb.api_key:
            search_query = item.get("search_title") or item["title"]
            res = tmdb.search_multi(search_query, limit=1)
            if res:
                t_match = res[0]

        if t_match:
            item["poster_local"] = t_match.get("poster_local")

    print(render_movie_card_table(items, f"⏯️ TIẾP TỤC THEO DÕI (Đang xem dở trên Plex / Jellyfin)"))

def cmd_theatrical(args):
    cfg = load_config()
    sentiment = SentimentFilter(cfg.get("anti_seeding_min_votes", 300), cfg.get("min_rating", 6.5))
    tmdb = TMDbTrends()
    plex = PlexReader(cfg.get("plex_db_path"))

    if not tmdb.api_key:
        print("❌ Chưa cấu hình TMDB_API_KEY. Hãy chạy `tmdb-catalog setup` để lưu key.")
        return

    theatrical = tmdb.get_theatrical_releases(limit=args.limit)
    for item in theatrical:
        local_matches = plex.search_local(item["title"]) if plex.available else []
        if local_matches:
            item["nas_status"] = f"🟢 ĐÃ CÓ TRÊN NAS: `{local_matches[0]['title']}`"
        else:
            item["nas_status"] = "⚪ Chưa có trên NAS (Có thể dùng `media-downloader` tìm kiếm)"

        s_res = sentiment.analyze_sentiment(item["vote_average"], item["vote_count"], item["title"])
        item["sentiment_badge"] = s_res.get("badge")
        item["adjusted_rating"] = s_res.get("adjusted_rating")

    print(render_movie_card_table(theatrical, f"🍿 ĐANG CHIẾU RẠP & VỪA RA MẮT (Theatrical Releases)"))

def cmd_trending(args):
    cfg = load_config()
    sentiment = SentimentFilter(cfg.get("anti_seeding_min_votes", 300), cfg.get("min_rating", 6.5))
    tmdb = TMDbTrends()
    plex = PlexReader(cfg.get("plex_db_path"))

    if not tmdb.api_key:
        print("❌ Chưa cấu hình TMDB_API_KEY.")
        return

    trending = tmdb.get_trending("all", "week", limit=args.limit)
    for item in trending:
        local_matches = plex.search_local(item["title"]) if plex.available else []
        if local_matches:
            item["nas_status"] = f"🟢 ĐÃ CÓ TRÊN NAS: `{local_matches[0]['title']}`"
        else:
            item["nas_status"] = "⚪ Chưa có trên NAS"

        s_res = sentiment.analyze_sentiment(item["vote_average"], item["vote_count"], item["title"])
        item["sentiment_badge"] = s_res.get("badge")
        item["adjusted_rating"] = s_res.get("adjusted_rating")

    print(render_movie_card_table(trending, f"🔥 XU HƯỚNG NỔI BẬT TRÊN CÁC NỀN TẢNG (Trending Movies & Series)"))

def cmd_report(args):
    cfg = load_config()
    plex = PlexReader(cfg.get("plex_db_path"))
    
    print("## 🧭 BÁO CÁO TỔNG QUAN MEDIA CONCIERGE & KHẨU VỊ PHIM\n")
    if plex.available:
        profile = plex.get_taste_profile()
        genres = ", ".join([f"**{g['genre']}** ({g['count']})" for g in profile.get("genres", [])[:6]])
        actors = ", ".join([f"{a['actor']} ({a['count']})" for a in profile.get("actors", [])[:5]])
        print(f"📊 **Hồ Sơ Xem Phim Nội Bộ (Plex)**:")
        print(f"- Tổng lượt xem: **{profile.get('total_watched', 0)}** tập/phim.")
        print(f"- Thể loại yêu thích hàng đầu: {genres or 'Chưa đủ dữ liệu'}")
        print(f"- Diễn viên hay theo dõi: {actors or 'Chưa đủ dữ liệu'}\n")
    
    print("---")
    args.limit = 3
    cmd_continue(args)
    cmd_unwatched(args)
    cmd_theatrical(args)

def main():
    parser = argparse.ArgumentParser(description="Media Advisor - Cinema & Series Recommendation Concierge")
    subparsers = parser.add_subparsers(dest="command", help="Lệnh thực hiện")

    p_setup = subparsers.add_parser("setup", help="Khảo sát sở thích người dùng và cấu hình hệ thống")
    p_setup.add_argument("--defaults", action="store_true", help="Lưu cấu hình mặc định (khách quan, bao quát toàn bộ)")

    p_unw = subparsers.add_parser("unwatched", help="Đề xuất phim chưa xem trên NAS")
    p_unw.add_argument("--limit", type=int, default=5, help="Số lượng đề xuất")

    p_cont = subparsers.add_parser("continue", help="Đề xuất phim/series đang xem dở")
    p_cont.add_argument("--limit", type=int, default=5, help="Số lượng đề xuất")

    p_theat = subparsers.add_parser("theatrical", help="Đề xuất phim đang chiếu rạp")
    p_theat.add_argument("--limit", type=int, default=5, help="Số lượng đề xuất")

    p_trend = subparsers.add_parser("trending", help="Đề xuất xu hướng thịnh hành")
    p_trend.add_argument("--limit", type=int, default=5, help="Số lượng đề xuất")

    p_rep = subparsers.add_parser("report", help="Báo cáo toàn diện: Gu xem phim + Đang xem dở + Đề xuất")
    p_rep.add_argument("--limit", type=int, default=3, help="Số lượng mỗi mục")

    args = parser.parse_args()

    if not args.command:
        args.command = "report"
        args.limit = 3
        cmd_report(args)
        return

    if args.command == "setup":
        run_survey(non_interactive=args.defaults)
    elif args.command == "unwatched":
        cmd_unwatched(args)
    elif args.command == "continue":
        cmd_continue(args)
    elif args.command == "theatrical":
        cmd_theatrical(args)
    elif args.command == "trending":
        cmd_trending(args)
    elif args.command == "report":
        cmd_report(args)

if __name__ == "__main__":
    main()
