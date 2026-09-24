#!/usr/bin/env python3
"""
Media Advisor Master CLI: Homelab Cinema & Series Recommendation Concierge.
Gracefully adapts across 3 modes:
1. Local SQLite Homelab (Zero-API Plex/Jellyfin read-only)
2. Remote Server API (Plex Token / Jellyfin API Key)
3. Pure Internet Cinephile (Zero server required, survey-driven & global trends)
Outputs beautiful 2-column visual Markdown tables with local poster thumbnails.
"""

import sys
import os
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from advisor_setup import load_config, run_survey
from plex_reader import PlexReader
from media_server_client import PlexApiClient, JellyfinApiClient
from sentiment_filter import SentimentFilter
from tmdb_trends import TMDbTrends
from social_buzz_radar import SocialBuzzRadar
from vn_cinema_scraper import VnCinemaScraper

def get_media_backend(cfg: Dict[str, Any]) -> Tuple[str, Any]:
    """
    Returns ('remote_plex' | 'remote_jellyfin' | 'local_sqlite' | 'internet', backend_instance)
    """
    mode = cfg.get("mode", "auto")
    if mode == "internet_only":
        return "internet", None

    # Check remote server API configuration
    if mode == "remote" or (cfg.get("remote_url") and cfg.get("remote_token")):
        stype = cfg.get("server_type", "plex")
        if stype == "jellyfin":
            return "remote_jellyfin", JellyfinApiClient(cfg["remote_url"], cfg["remote_token"])
        else:
            return "remote_plex", PlexApiClient(cfg["remote_url"], cfg["remote_token"])

    # Fallback to local SQLite reader if available
    plex_local = PlexReader(cfg.get("plex_db_path"))
    if plex_local.available:
        return "local_sqlite", plex_local

    return "internet", None

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

        # Domestic Vietnamese Cinema & Reviewer signal if present
        vn_cinema = item.get("vn_cinema")
        if vn_cinema:
            info_lines.append(f"🇻🇳 **Đánh giá trong nước**: {vn_cinema}")

        # Buzz Score if present
        buzz_score = item.get("buzz_score")
        if buzz_score is not None:
            reasons = item.get("buzz_reasons", [])
            reasons_str = f" ({', '.join(reasons)})" if reasons else ""
            info_lines.append(f"🔥 **Độ thảo luận MXH**: **{buzz_score}/100**{reasons_str}")

        # Platform / NAS Location
        if is_internet_mode:
            providers = item.get("watch_providers", [])
            prov_str = ", ".join(providers) if providers else "Đang cập nhật nền tảng"
            info_lines.append(f"📺 **Nền tảng phát sóng**: {prov_str}")
        else:
            nas_status = item.get("nas_status")
            if nas_status:
                info_lines.append(f"📍 **Kho Media**: {nas_status}")

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
    btype, backend = get_media_backend(cfg)
    sentiment = SentimentFilter(cfg.get("anti_seeding_min_votes", 300), cfg.get("min_rating", 6.5))
    tmdb = TMDbTrends()

    if btype == "internet":
        print("ℹ️ Hệ thống đang hoạt động ở chế độ Internet (không có kết nối Plex/Jellyfin).")
        print("💡 Tự động chuyển sang đề xuất tác phẩm kinh điển theo gu khảo sát:")
        cmd_discover(args)
        return

    if btype == "local_sqlite":
        items = backend.get_unwatched_library(limit=args.limit, min_rating=0.0)
    elif btype in ("remote_plex", "remote_jellyfin"):
        items = backend.get_unwatched(limit=args.limit)
    else:
        items = []

    for item in items:
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

    print(render_movie_card_table(items, f"💎 KHO BÁU BỎ QUÊN TRÊN SERVER (Chưa xem, sẵn sàng phát ngay)", is_internet_mode=False))

def cmd_continue(args):
    cfg = load_config()
    btype, backend = get_media_backend(cfg)
    tmdb = TMDbTrends()

    if btype == "internet":
        print("ℹ️ Chế độ Internet không lưu trữ tiến độ xem dở.")
        return

    items = backend.get_in_progress(limit=args.limit)
    for item in items:
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

    print(render_movie_card_table(items, f"⏯️ TIẾP TỤC THEO DÕI (Đang xem dở trên Server)", is_internet_mode=False))

def cmd_theatrical(args):
    cfg = load_config()
    sentiment = SentimentFilter(cfg.get("anti_seeding_min_votes", 300), cfg.get("min_rating", 6.5))
    tmdb = TMDbTrends()
    btype, backend = get_media_backend(cfg)
    has_server = (btype != "internet")

    if not tmdb.api_key:
        print("❌ Chưa cấu hình TMDB_API_KEY. Hãy chạy `tmdb-catalog setup` để lưu key.")
        return

    vn_scraper = VnCinemaScraper()
    theatrical = tmdb.get_theatrical_releases(limit=args.limit)
    for item in theatrical:
        # Check MoMo & Moveek domestic data
        momo_match = vn_scraper.search_momo(item["title"], item.get("original_title"))
        if momo_match:
            pts = momo_match.get("rating_point")
            paid = momo_match.get("paid_tickets", 0)
            if paid > 0 or pts is not None:
                pt_str = f"⭐ **{pts}/10**" if pts is not None else ""
                paid_str = f"({paid:,} vé đã mua)" if paid > 0 else "(Sắp chiếu / Đang mở bán)"
                item["vn_cinema"] = f"🎟️ MoMo Cinema: {pt_str} {paid_str}".strip()

        moveek_match = vn_scraper.search_moveek(item["title"], item.get("original_title"))
        if moveek_match and moveek_match.get("score") is not None:
            vn_prev = item.get("vn_cinema", "")
            mv_str = f"Moveek: {moveek_match['score']}/10"
            item["vn_cinema"] = f"{vn_prev} · {mv_str}" if vn_prev else f"🎬 {mv_str}"

        if btype == "local_sqlite":
            rel_year = item.get("release_date", "")[:4] if item.get("release_date") else None
            local_matches = backend.search_local(item["title"], year=rel_year, tmdb_id=item.get("tmdb_id"))
            if not local_matches and item.get("original_title") and item["original_title"] != item["title"]:
                local_matches = backend.search_local(item["original_title"], year=rel_year)
            if local_matches:
                item["nas_status"] = f"🟢 ĐÃ CÓ TRÊN SERVER: `{local_matches[0]['title']}`"
            else:
                item["nas_status"] = "⚪ Chưa có trên Server (Có thể dùng `media-downloader` tìm kiếm)"
        elif has_server:
            item["nas_status"] = "⚪ Có thể tìm và tải về Server"

        s_res = sentiment.analyze_sentiment(item["vote_average"], item["vote_count"], item["title"])
        item["sentiment_badge"] = s_res.get("badge")
        item["adjusted_rating"] = s_res.get("adjusted_rating")

    print(render_movie_card_table(theatrical, f"🍿 ĐANG CHIẾU RẠP & VỪA RA MẮT (Theatrical Releases)", is_internet_mode=not has_server))

def cmd_trending(args):
    cfg = load_config()
    sentiment = SentimentFilter(cfg.get("anti_seeding_min_votes", 300), cfg.get("min_rating", 6.5))
    tmdb = TMDbTrends()
    btype, backend = get_media_backend(cfg)
    has_server = (btype != "internet")

    if not tmdb.api_key:
        print("❌ Chưa cấu hình TMDB_API_KEY.")
        return

    trending = tmdb.get_trending("all", "week", limit=args.limit)
    for item in trending:
        if btype == "local_sqlite":
            rel_year = item.get("release_date", "")[:4] if item.get("release_date") else None
            local_matches = backend.search_local(item["title"], year=rel_year, tmdb_id=item.get("tmdb_id"))
            if not local_matches and item.get("original_title") and item["original_title"] != item["title"]:
                local_matches = backend.search_local(item["original_title"], year=rel_year)
            if local_matches:
                item["nas_status"] = f"🟢 ĐÃ CÓ TRÊN SERVER: `{local_matches[0]['title']}`"
            else:
                item["nas_status"] = "⚪ Chưa có trên Server"
        elif has_server:
            item["nas_status"] = "⚪ Có thể tìm và tải về Server"

        s_res = sentiment.analyze_sentiment(item["vote_average"], item["vote_count"], item["title"])
        item["sentiment_badge"] = s_res.get("badge")
        item["adjusted_rating"] = s_res.get("adjusted_rating")

    print(render_movie_card_table(trending, f"🔥 XU HƯỚNG NỔI BẬT TRÊN CÁC NỀN TẢNG (Trending Movies & Series)", is_internet_mode=not has_server))

def cmd_buzz(args):
    cfg = load_config()
    sentiment = SentimentFilter(cfg.get("anti_seeding_min_votes", 300), cfg.get("min_rating", 6.5))
    tmdb = TMDbTrends()
    btype, backend = get_media_backend(cfg)
    has_server = (btype != "internet")

    if not tmdb.api_key:
        print("❌ Chưa cấu hình TMDB_API_KEY.")
        return

    print("📡 Đang kích hoạt Radar quét thảo luận MoMo Cinema, Moveek, YouTube Review & TikTok Trends...")
    radar = SocialBuzzRadar()
    signals = radar.get_social_signals()
    entities = signals.get("extracted_entities", {})
    momo_hot = signals.get("momo_hot", {})

    trending = tmdb.get_trending("all", "day", limit=15)
    buzz_items = []
    for item in trending:
        title = item.get("title", "")
        orig_title = item.get("original_title", "")
        buzz_score = 50
        buzz_reasons = ["Xu hướng 24h"]

        # 1. Domestic MoMo / Moveek detection
        momo_match = radar.vn_scraper.search_momo(title, orig_title)
        if momo_match:
            pts = momo_match.get("rating_point")
            paid = momo_match.get("paid_tickets", 0)
            if paid > 0 or pts is not None:
                buzz_score += 35
                paid_label = f"{paid:,} vé" if paid > 0 else "Mới mở bán"
                buzz_reasons.append(f"Hot MoMo ({paid_label})")
                pt_str = f"⭐ **{pts}/10**" if pts is not None else ""
                paid_str = f"({paid:,} vé đã thanh toán)" if paid > 0 else "(Sắp chiếu / Đang mở bán)"
                item["vn_cinema"] = f"🎟️ MoMo Cinema: {pt_str} {paid_str}".strip()

        moveek_match = radar.vn_scraper.search_moveek(title, orig_title)
        if moveek_match and moveek_match.get("score") is not None:
            buzz_score += 20
            buzz_reasons.append("Hot Moveek")
            vn_prev = item.get("vn_cinema", "")
            mv_str = f"Moveek: {moveek_match['score']}/10"
            item["vn_cinema"] = f"{vn_prev} · {mv_str}" if vn_prev else f"🎬 {mv_str}"

        # 2. General entity match
        if not momo_match:
            for entity in entities:
                if entity.lower() in title.lower() or title.lower() in entity.lower():
                    buzz_score += 25
                    buzz_reasons.append(f"Hot Thảo Luận: {entity}")
                    break

        s_res = sentiment.analyze_sentiment(item["vote_average"], item["vote_count"], title)
        item["sentiment_badge"] = s_res.get("badge")
        item["adjusted_rating"] = s_res.get("adjusted_rating")

        if s_res.get("is_genuine"):
            buzz_score += 15
            buzz_reasons.append("Đánh giá thực chất")

        item["buzz_score"] = min(100, buzz_score)
        item["buzz_reasons"] = buzz_reasons

        if btype == "local_sqlite":
            rel_year = item.get("release_date", "")[:4] if item.get("release_date") else None
            local_matches = backend.search_local(title, year=rel_year, tmdb_id=item.get("tmdb_id"))
            if not local_matches and item.get("original_title") and item["original_title"] != title:
                local_matches = backend.search_local(item["original_title"], year=rel_year)
            if local_matches:
                item["nas_status"] = f"🟢 ĐÃ CÓ TRÊN SERVER: `{local_matches[0]['title']}`"
            else:
                item["nas_status"] = "⚪ Chưa có trên Server"
        elif has_server:
            item["nas_status"] = "⚪ Có thể tìm và tải về Server"

        buzz_items.append(item)

    buzz_items.sort(key=lambda x: x.get("buzz_score", 0), reverse=True)
    print(render_movie_card_table(buzz_items[:args.limit], f"🔥 BÙNG NỔ THẢO LUẬN & CHỐNG SEEDING (Social Buzz Radar: Reddit + YouTube + TikTok)", is_internet_mode=not has_server))

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
    btype, backend = get_media_backend(cfg)
    has_server = (btype != "internet")

    if not tmdb.api_key:
        print("❌ Chưa cấu hình TMDB_API_KEY.")
        return

    query_str = getattr(args, "keyword", "") or ""
    items = tmdb.search_multi(query_str, limit=args.limit)

    for item in items:
        if btype == "local_sqlite":
            rel_year = item.get("release_date", "")[:4] if item.get("release_date") else None
            local_matches = backend.search_local(item["title"], year=rel_year, tmdb_id=item.get("tmdb_id"))
            if not local_matches and item.get("original_title") and item["original_title"] != item["title"]:
                local_matches = backend.search_local(item["original_title"], year=rel_year)
            if local_matches:
                item["nas_status"] = f"🟢 ĐÃ CÓ TRÊN SERVER: `{local_matches[0]['title']}`"
            else:
                item["nas_status"] = "⚪ Chưa có trên Server"
        elif has_server:
            item["nas_status"] = "⚪ Có thể tìm kiếm và lưu vào Server"

        s_res = sentiment.analyze_sentiment(item["vote_average"], item["vote_count"], item["title"])
        item["sentiment_badge"] = s_res.get("badge")
        item["adjusted_rating"] = s_res.get("adjusted_rating")

    print(render_movie_card_table(items, f"🔍 KẾT QUẢ TÌM KIẾM CHO: '{query_str}'", is_internet_mode=not has_server))

def cmd_report(args):
    cfg = load_config()
    btype, backend = get_media_backend(cfg)
    
    print("## 🧭 BÁO CÁO TỔNG QUAN MEDIA CONCIERGE & KHẨU VỊ PHIM\n")
    if btype == "local_sqlite":
        profile = backend.get_taste_profile()
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
    elif btype in ("remote_plex", "remote_jellyfin"):
        stitle = "Plex Media Server" if btype == "remote_plex" else "Jellyfin Server"
        print(f"📡 **Chế độ**: Remote Server API ({stitle} tại `{cfg.get('remote_url')}`)")
        print(f"- Kết nối: REST API qua Token/API Key đã xác thực.")
        print("---")
        args.limit = 3
        cmd_continue(args)
        cmd_unwatched(args)
        cmd_theatrical(args)
    else:
        genres = ", ".join(cfg.get("preferred_genres", [])) or "Tất cả thể loại (Khách quan)"
        regions = ", ".join(cfg.get("preferred_regions", ["ALL"]))
        print(f"🌐 **Chế độ**: Khám Phá Internet Toàn Cầu (Pure Cinephile - Zero Media Server)")
        print(f"- Gu thể loại đã khảo sát: **{genres}**")
        print(f"- Khu vực ưu tiên: **{regions}**")
        print(f"- Bộ lọc chống seeding: Điểm >= **{cfg.get('min_rating', 6.8)}**, Vote >= **{cfg.get('anti_seeding_min_votes', 300)}**\n")
        print("---")
        args.limit = 3
        cmd_discover(args)
        cmd_theatrical(args)
        cmd_trending(args)

def cmd_share(args):
    """Exports a rounded-corner photographic infographic PNG card for a movie or comparison."""
    title = args.title
    compare_titles = args.compare

    oracle_script = Path(__file__).parents[4] / "film-oracle" / "skills" / "film-oracle" / "scripts"
    if oracle_script.exists():
        sys.path.insert(0, str(oracle_script))
    
    from oracle_auditor import FilmOracle
    from infographic_exporter import InfographicExporter

    oracle = FilmOracle()
    exporter = InfographicExporter()

    if compare_titles:
        all_titles = [title] + compare_titles
        print(f"🎨 Đang tổng hợp và tạo ảnh so sánh Infographic cho {len(all_titles)} phim...")
        audits = [oracle.audit_film(t) for t in all_titles]
        out_file = exporter.export_comparison_card(audits)
        if out_file:
            print(f"\n📸 ĐÃ XUẤT ẢNH SO SÁNH (PNG): {out_file}")
            print("💡 Ảnh được thiết kế bo góc tinh tế, font tiếng Việt chuẩn, sẵn sàng chia sẻ!")
        else:
            print("❌ Lỗi khi xuất ảnh so sánh.")
        return

    print(f"🔍 Đang thẩm định và tạo thẻ Infographic Card cho '{title}'...")
    audit = oracle.audit_film(title)
    out_file = exporter.export_single_audit_card(audit)
    if out_file:
        print(f"\n📸 ĐÃ XUẤT INFOGRAPHIC CARD (PNG): {out_file}")
        print(f"★ Điểm Meta Truth Score: {audit.get('meta_truth_score', 0)}/10")
        print(f"🎯 Phán quyết: {audit.get('worth_verdict')}")
        print("💡 Ảnh được thiết kế bo góc tinh tế, font tiếng Việt chuẩn, sẵn sàng chia sẻ lên Zalo/MXH/Story!")
    else:
        print("❌ Không thể tạo infographic card cho phim này.")

def main():
    parser = argparse.ArgumentParser(description="Media Advisor - Cinema & Series Recommendation Concierge")
    subparsers = parser.add_subparsers(dest="command", help="Lệnh thực hiện")

    # setup
    p_setup = subparsers.add_parser("setup", help="Khảo sát sở thích người dùng và cấu hình hệ thống")
    p_setup.add_argument("--defaults", action="store_true", help="Lưu cấu hình mặc định (khách quan, bao quát toàn bộ)")

    # unwatched
    p_unw = subparsers.add_parser("unwatched", help="Đề xuất phim chưa xem trên Server (hoặc theo gu nếu chế độ Internet)")
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

    # buzz
    p_buzz = subparsers.add_parser("buzz", help="Radar quét bùng nổ thảo luận MXH (Reddit + YouTube + TikTok) và chống seeding")
    p_buzz.add_argument("--limit", type=int, default=5, help="Số lượng đề xuất")

    # discover
    p_disc = subparsers.add_parser("discover", help="Khám phá phim hay từ Internet theo gu khảo sát")
    p_disc.add_argument("--limit", type=int, default=5, help="Số lượng đề xuất")

    # query
    p_query = subparsers.add_parser("query", help="Tìm kiếm và đề xuất theo từ khóa hoặc cảm hứng")
    p_query.add_argument("keyword", type=str, help="Từ khóa hoặc mô tả phim muốn xem")
    p_query.add_argument("--limit", type=int, default=5, help="Số lượng đề xuất")

    # share
    p_share = subparsers.add_parser("share", help="Xuất ảnh Photographic Infographic Card (PNG) bo góc để chia sẻ")
    p_share.add_argument("title", type=str, help="Tên phim cần tạo ảnh chia sẻ")
    p_share.add_argument("--compare", nargs="+", help="Các phim khác để so sánh song song trong cùng 1 ảnh")

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
    elif args.command == "buzz":
        cmd_buzz(args)
    elif args.command == "discover":
        cmd_discover(args)
    elif args.command == "query":
        cmd_query(args)
    elif args.command == "share":
        cmd_share(args)
    elif args.command == "report":
        cmd_report(args)

if __name__ == "__main__":
    main()
