#!/usr/bin/env python3
"""
Media Advisor Master CLI: Homelab Cinema & Series Recommendation Concierge.
Gracefully adapts across 3 modes:
1. Local SQLite Homelab (Zero-API Plex/Jellyfin read-only)
2. Remote Server API (Plex / Jellyfin HTTP)
3. Pure Internet Cinephile (Zero server required, survey-driven & global trends)
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

def render_movie_card_table(items: List[Dict[str, Any]], title_section: str = "", is_internet_mode: bool = False) -> str:
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

        # Platform / NAS Location
        if is_internet_mode:
            providers = item.get("watch_providers", [])
            prov_str = ", ".join(providers) if providers else "Đang cập nhật nền tảng"
            info_lines.append(f"📺 **Nền tảng phát sóng**: {prov_str}")
        else:
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

def is_homelab_active(cfg, plex) -> bool:
    mode = cfg.get("mode", "auto")
    if mode == "internet_only":
        return False
    return plex.available

def cmd_unwatched(args):
    cfg = load_config()
    plex = PlexReader(cfg.get("plex_db_path"))
    sentiment = SentimentFilter(cfg.get("anti_seeding_min_votes", 300), cfg.get("min_rating", 6.5))
    tmdb = TMDbTrends()

    if not is_homelab_active(cfg, plex):
        print("ℹ️ Hệ thống đang hoạt động ở chế độ Internet (không có kết nối Plex/Jellyfin cục bộ).")
        print("💡 Tự động chuyển sang đề xuất tác phẩm kinh điển theo gu khảo sát:")
        cmd_discover(args)
        return

    items = plex.get_unwatched_library(limit=args.limit, min_rating=0.0)
    for item in items:
        item["nas_status"] = "🟢 Sẵn sàng xem ngay trên NAS"
        t_match = None
        if tmdb.api_key and item.get("tmdb_id"):
            t_match = tmdb.get_details_by_id(item["tmdb_id"], "movie" if item.get("type") == "Movie" else "tv")
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

    print(render_movie_card_table(items, f"💎 KHO BÁU BỎ QUÊN TRÊN NAS (Chưa xem, sẵn sàng phát ngay)", is_internet_mode=False))

def cmd_continue(args):
    cfg = load_config()
    plex = PlexReader(cfg.get("plex_db_path"))
    tmdb = TMDbTrends()

    if not is_homelab_active(cfg, plex):
        print("ℹ️ Chế độ Internet không lưu trữ tiến độ xem dở.")
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

    print(render_movie_card_table(items, f"⏯️ TIẾP TỤC THEO DÕI (Đang xem dở trên Plex / Jellyfin)", is_internet_mode=False))

def cmd_theatrical(args):
    cfg = load_config()
    sentiment = SentimentFilter(cfg.get("anti_seeding_min_votes", 300), cfg.get("min_rating", 6.5))
    tmdb = TMDbTrends()
    plex = PlexReader(cfg.get("plex_db_path"))
    has_homelab = is_homelab_active(cfg, plex)

    if not tmdb.api_key:
        print("❌ Chưa cấu hình TMDB_API_KEY. Hãy chạy `tmdb-catalog setup` để lưu key.")
        return

    theatrical = tmdb.get_theatrical_releases(limit=args.limit)
    for item in theatrical:
        if has_homelab:
            local_matches = plex.search_local(item["title"])
            if local_matches:
                item["nas_status"] = f"🟢 ĐÃ CÓ TRÊN NAS: `{local_matches[0]['title']}`"
            else:
                item["nas_status"] = "⚪ Chưa có trên NAS (Có thể dùng `media-downloader` tìm kiếm)"

        s_res = sentiment.analyze_sentiment(item["vote_average"], item["vote_count"], item["title"])
        item["sentiment_badge"] = s_res.get("badge")
        item["adjusted_rating"] = s_res.get("adjusted_rating")

    print(render_movie_card_table(theatrical, f"🍿 ĐANG CHIẾU RẠP & VỪA RA MẮT (Theatrical Releases)", is_internet_mode=not has_homelab))

def cmd_trending(args):
    cfg = load_config()
    sentiment = SentimentFilter(cfg.get("anti_seeding_min_votes", 300), cfg.get("min_rating", 6.5))
    tmdb = TMDbTrends()
    plex = PlexReader(cfg.get("plex_db_path"))
    has_homelab = is_homelab_active(cfg, plex)

    if not tmdb.api_key:
        print("❌ Chưa cấu hình TMDB_API_KEY.")
        return

    trending = tmdb.get_trending("all", "week", limit=args.limit)
    for item in trending:
        if has_homelab:
            local_matches = plex.search_local(item["title"])
            if local_matches:
                item["nas_status"] = f"🟢 ĐÃ CÓ TRÊN NAS: `{local_matches[0]['title']}`"
            else:
                item["nas_status"] = "⚪ Chưa có trên NAS"

        s_res = sentiment.analyze_sentiment(item["vote_average"], item["vote_count"], item["title"])
        item["sentiment_badge"] = s_res.get("badge")
        item["adjusted_rating"] = s_res.get("adjusted_rating")

    print(render_movie_card_table(trending, f"🔥 XU HƯỚNG NỔI BẬT TRÊN CÁC NỀN TẢNG (Trending Movies & Series)", is_internet_mode=not has_homelab))

def cmd_discover(args):
    cfg = load_config()
    sentiment = SentimentFilter(cfg.get("anti_seeding_min_votes", 300), cfg.get("min_rating", 6.8))
    tmdb = TMDbTrends()

    if not tmdb.api_key:
        print("❌ Chưa cấu hình TMDB_API_KEY.")
        return

    genres = cfg.get("preferred_genres", [])
    items = tmdb.discover_by_survey(
        genres=genres,
        min_rating=cfg.get("min_rating", 6.8),
        min_votes=cfg.get("anti_seeding_min_votes", 300),
        limit=args.limit
    )

    for item in items:
        s_res = sentiment.analyze_sentiment(item["vote_average"], item["vote_count"], item["title"])
        item["sentiment_badge"] = s_res.get("badge")
        item["adjusted_rating"] = s_res.get("adjusted_rating")

    genre_str = ", ".join(genres) if genres else "Tất cả thể loại"
    print(render_movie_card_table(items, f"✨ ĐỀ XUẤT THEO GU KHẢO SÁT ({genre_str})", is_internet_mode=True))

def cmd_query(args):
    cfg = load_config()
    sentiment = SentimentFilter(cfg.get("anti_seeding_min_votes", 300), cfg.get("min_rating", 6.5))
    tmdb = TMDbTrends()
    plex = PlexReader(cfg.get("plex_db_path"))
    has_homelab = is_homelab_active(cfg, plex)

    if not tmdb.api_key:
        print("❌ Chưa cấu hình TMDB_API_KEY.")
        return

    query_str = getattr(args, "keyword", "") or ""
    items = tmdb.search_multi(query_str, limit=args.limit)

    for item in items:
        if has_homelab:
            local_matches = plex.search_local(item["title"])
            if local_matches:
                item["nas_status"] = f"🟢 ĐÃ CÓ TRÊN NAS: `{local_matches[0]['title']}`"
            else:
                item["nas_status"] = "⚪ Chưa có trên NAS"

        s_res = sentiment.analyze_sentiment(item["vote_average"], item["vote_count"], item["title"])
        item["sentiment_badge"] = s_res.get("badge")
        item["adjusted_rating"] = s_res.get("adjusted_rating")

    print(render_movie_card_table(items, f"🔍 KẾT QUẢ TÌM KIẾM CHO: '{query_str}'", is_internet_mode=not has_homelab))

def cmd_report(args):
    cfg = load_config()
    plex = PlexReader(cfg.get("plex_db_path"))
    has_homelab = is_homelab_active(cfg, plex)
    
    print("## 🧭 BÁO CÁO TỔNG QUAN MEDIA CONCIERGE & KHẨU VỊ PHIM\n")
    if has_homelab:
        profile = plex.get_taste_profile()
        genres = ", ".join([f"**{g['genre']}** ({g['count']})" for g in profile.get("genres", [])[:6]])
        actors = ", ".join([f"{a['actor']} ({a['count']})" for a in profile.get("actors", [])[:5]])
        print(f"🏠 **Chế độ**: Homelab Native (Plex/Jellyfin Local SQLite ro)")
        print(f"- Tổng lượt xem: **{profile.get('total_watched', 0)}** tập/phim.")
        print(f"- Thể loại yêu thích hàng đầu: {genres or 'Chưa đủ dữ liệu'}")
        print(f"- Diễn viên hay theo dõi: {actors or 'Chưa đủ dữ liệu'}\n")
        print("---")
        args.limit = 3
        cmd_continue(args)
        cmd_unwatched(args)
        cmd_theatrical(args)
    else:
        genres = ", ".join(cfg.get("preferred_genres", [])) or "Tất cả thể loại (Khách quan)"
        regions = ", ".join(cfg.get("preferred_regions", ["ALL"]))
        print(f"🌐 **Chế độ**: Khám Phá Internet Toàn Cầu (Pure Cinephile - Zero Media Server)")
        print(f"- Gu thể loại đã khảo sát: **{genre_str or genres}**")
        print(f"- Khu vực ưu tiên: **{regions}**")
        print(f"- Bộ lọc chống seeding: Điểm >= **{cfg.get('min_rating', 6.8)}**, Vote >= **{cfg.get('anti_seeding_min_votes', 300)}**\n")
        print("---")
        args.limit = 3
        cmd_discover(args)
        cmd_theatrical(args)
        cmd_trending(args)

def main():
    parser = argparse.ArgumentParser(description="Media Advisor - Cinema & Series Recommendation Concierge")
    subparsers = parser.add_subparsers(dest="command", help="Lệnh thực hiện")

    # setup
    p_setup = subparsers.add_parser("setup", help="Khảo sát sở thích người dùng và cấu hình hệ thống")
    p_setup.add_argument("--defaults", action="store_true", help="Lưu cấu hình mặc định (khách quan, bao quát toàn bộ)")

    # unwatched
    p_unw = subparsers.add_parser("unwatched", help="Đề xuất phim chưa xem trên NAS (hoặc theo gu nếu không có NAS)")
    p_unw.add_argument("--limit", type=int, default=5, help="Số lượng đề xuất")

    # continue
    p_cont = subparsers.add_parser("continue", help="Đề xuất phim/series đang xem dở")
    p_cont.add_argument("--limit", type=int, default=5, help="Số lượng đề xuất")

    # theatrical
    p_theat = subparsers.add_parser("theatrical", help="Đề xuất phim đang chiếu rạp")
    p_theat.add_argument("--limit", type=int, default=5, help="Số lượng đề xuất")

    # trending
    p_trend = subparsers.add_parser("trending", help="Đề xuất xu hướng thịnh hành")
    p_trend.add_argument("--limit", type=int, default=5, help="Số lượng đề xuất")

    # discover
    p_disc = subparsers.add_parser("discover", help="Khám phá phim hay từ Internet theo gu khảo sát")
    p_disc.add_argument("--limit", type=int, default=5, help="Số lượng đề xuất")

    # query
    p_query = subparsers.add_parser("query", help="Tìm kiếm và đề xuất theo từ khóa hoặc cảm hứng")
    p_query.add_argument("keyword", type=str, help="Từ khóa hoặc mô tả phim muốn xem")
    p_query.add_argument("--limit", type=int, default=5, help="Số lượng đề xuất")

    # report
    p_rep = subparsers.add_parser("report", help="Báo cáo toàn diện")
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
    elif args.command == "discover":
        cmd_discover(args)
    elif args.command == "query":
        cmd_query(args)
    elif args.command == "report":
        cmd_report(args)

if __name__ == "__main__":
    main()
