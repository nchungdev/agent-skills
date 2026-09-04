#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TMDb API v3 Standalone Client & Metadata Engine
tmdb-lookup skill — scripts/tmdb_client.py
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.parse
import urllib.error

from hub_paths import output_for

ENV_FILE = os.path.expanduser("~/.env")
TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMG_BASE = "https://image.tmdb.org/t/p"


def load_api_key():
    """Load TMDB_API_KEY from ~/.env."""
    if not os.path.exists(ENV_FILE):
        return None
    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("TMDB_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def api_get(path, params=None, api_key=None):
    """Make a GET request to TMDb API."""
    if params is None:
        params = {}
    params["api_key"] = api_key
    url = f"{TMDB_BASE}{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "Antigravity-TMDb/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"❌ TMDb API Error: {e.code} {e.reason}")
        return None
    except Exception as e:
        print(f"❌ Request Failed: {e}")
        return None


def search(query, media_type="multi", api_key=None, language="en-US"):
    """Search TMDb by query."""
    endpoint = f"/search/{media_type}"
    data = api_get(endpoint, {"query": query, "language": language}, api_key)
    if not data or "results" not in data:
        print(f"❌ Không tìm thấy kết quả cho '{query}'")
        return []

    results = data["results"][:10]
    print(f"\n🔍 Kết quả tìm kiếm TMDb cho '{query}' ({len(results)} kết quả):\n")
    print(f"{'#':<4} {'Type':<8} {'TMDb ID':<10} {'Title':<45} {'Năm':<6} {'Điểm':<6}")
    print("─" * 85)

    for i, r in enumerate(results, 1):
        mtype = r.get("media_type", media_type)
        if mtype == "tv":
            title = r.get("name", "?")
            year = (r.get("first_air_date") or "")[:4]
        else:
            title = r.get("title", "?")
            year = (r.get("release_date") or "")[:4]

        rating = r.get("vote_average", 0)
        tmdb_id = r.get("id", "?")
        t_short = title[:43] + ".." if len(title) > 43 else title
        print(f"{i:<4} {mtype:<8} {tmdb_id:<10} {t_short:<45} {year:<6} {rating:<6.1f}")

    return results


def search_collection(query, api_key=None, language="en-US"):
    """Tim TMDb Collection theo ten (vd 'Fast and Furious Collection').

    Dung khi mot phim KHONG co san field collection nhung tra web xac
    dinh duoc no thuoc mot franchise -- tra nguoc xem TMDb da co san
    collection do chua (chi TMDb chua GAN phim nay vao, khong phai la
    collection chua ton tai).
    """
    data = api_get("/search/collection", {"query": query, "language": language}, api_key)
    if not data or "results" not in data:
        return []
    return data["results"]


def get_collection(collection_id, api_key=None, language="en-US"):
    """Lay chi tiet mot TMDb Collection: ten + toan bo phim (parts) thuoc no."""
    data = api_get(f"/collection/{collection_id}", {"language": language}, api_key)
    if not data:
        return None
    parts = [
        {
            "tmdb_id": p.get("id"),
            "title": p.get("title"),
            "year": (p.get("release_date") or "")[:4],
        }
        for p in data.get("parts", [])
    ]
    return {
        "id": data.get("id"),
        "name": data.get("name"),
        "overview": data.get("overview"),
        "parts": parts,
    }


def find_by_external_id(external_id, source="tvdb_id", api_key=None, language="en-US"):
    """Resolve a TMDb ID from another database's ID (TheTVDB, IMDb, ...).

    Dung khi ban dau chi co tvdb_id/imdb_id, chua co tmdb_id -- vd
    franchise-classifier skill nhan dau vao la tvdb_id cua mot series.
    """
    data = api_get(f"/find/{external_id}", {
        "external_source": source,
        "language": language,
    }, api_key)
    if not data:
        return None
    return {
        "movie_results": data.get("movie_results", []),
        "tv_results": data.get("tv_results", []),
    }


def get_details(media_type, tmdb_id, api_key=None, language="en-US"):
    """Get complete metadata, external IDs, and cast for a show/movie."""
    data = api_get(f"/{media_type}/{tmdb_id}", {
        "language": language,
        "append_to_response": "external_ids,credits,keywords"
    }, api_key)

    if not data:
        return None

    ext = data.get("external_ids", {})
    credits = data.get("credits", {})
    cast_raw = credits.get("cast", [])[:15]

    characters = []
    for c in cast_raw:
        char_name = c.get("character", "").strip()
        actor_name = c.get("name", "").strip()
        if char_name:
            characters.append({
                "character": char_name,
                "actor": actor_name
            })

    genres = [g["name"] for g in data.get("genres", [])]
    studios = [s["name"] for s in data.get("production_companies", [])]

    if media_type == "tv":
        info = {
            "type": "tv",
            "tmdb_id": data["id"],
            "tvdb_id": ext.get("tvdb_id"),
            "imdb_id": ext.get("imdb_id"),
            "title": data.get("name"),
            "original_title": data.get("original_name"),
            "year": (data.get("first_air_date") or "")[:4],
            "overview": data.get("overview"),
            "genres": genres,
            "seasons": data.get("number_of_seasons"),
            "episodes": data.get("number_of_episodes"),
            "studios": studios,
            "characters": characters,
            "poster_path": data.get("poster_path"),
            "backdrop_path": data.get("backdrop_path"),
            "vote_average": data.get("vote_average"),
        }
    else:
        collection = data.get("belongs_to_collection")
        info = {
            "type": "movie",
            "tmdb_id": data["id"],
            "imdb_id": ext.get("imdb_id"),
            "title": data.get("title"),
            "original_title": data.get("original_title"),
            "year": (data.get("release_date") or "")[:4],
            "overview": data.get("overview"),
            "genres": genres,
            "runtime": data.get("runtime"),
            "studios": studios,
            "characters": characters,
            "poster_path": data.get("poster_path"),
            "backdrop_path": data.get("backdrop_path"),
            "vote_average": data.get("vote_average"),
            # TMDb chi co khai niem "collection" cho PHIM LE, khong co cho
            # series -- franchise-classifier skill dung field nay lam nguon
            # dang tin cay nhat truoc khi phai suy luan bang AI.
            "collection": {
                "id": collection.get("id"),
                "name": collection.get("name"),
            } if collection else None,
        }

    return info


def print_info(info):
    """Pretty print metadata."""
    print(f"\n{'═' * 75}")
    print(f"🎬 {info['title']}  ({info['original_title']}) [{info['year']}]")
    print(f"{'═' * 75}")
    print(f"  • TMDb ID:       {info['tmdb_id']}")
    if info.get("tvdb_id"):
        print(f"  • TheTVDB ID:    {info['tvdb_id']}")
    if info.get("imdb_id"):
        print(f"  • IMDb ID:       {info['imdb_id']}")
    print(f"  • Thể loại:      {', '.join(info['genres'])}")
    print(f"  • Đánh giá:      ⭐ {info.get('vote_average', 'N/A')}/10")
    if info.get("seasons"):
        print(f"  • Quy mô:        {info['seasons']} Mùa ({info['episodes']} Tập)")
    if info.get("runtime"):
        print(f"  • Thời lượng:    {info['runtime']} phút")
    if info.get("studios"):
        print(f"  • Studio:        {', '.join(info['studios'])}")
    if info.get("collection"):
        print(f"  • Collection:    {info['collection']['name']} (id {info['collection']['id']})")
    if info.get("characters"):
        chars_str = ", ".join([f"{c['character']} ({c['actor']})" for c in info['characters'][:5]])
        print(f"  • Dàn nhân vật:  {chars_str}...")
    if info.get("overview"):
        print(f"  • Tóm tắt:       {info['overview'][:180]}...")
    print()


def generate_nfo(info, output_dir):
    """Generate NFO file."""
    os.makedirs(output_dir, exist_ok=True)
    root_tag = "tvshow" if info["type"] == "tv" else "movie"
    nfo_file = os.path.join(output_dir, f"{root_tag}.nfo")

    lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        f'<{root_tag}>',
        f'  <title>{_xml_escape(info["title"])}</title>',
        f'  <originaltitle>{_xml_escape(info.get("original_title", ""))}</originaltitle>',
        f'  <year>{info.get("year", "")}</year>',
        f'  <plot>{_xml_escape(info.get("overview", ""))}</plot>',
    ]
    for g in info.get("genres", []):
        lines.append(f'  <genre>{_xml_escape(g)}</genre>')
    for s in info.get("studios", []):
        lines.append(f'  <studio>{_xml_escape(s)}</studio>')

    if info.get("tmdb_id"):
        lines.append(f'  <uniqueid type="tmdb" default="true">{info["tmdb_id"]}</uniqueid>')
    if info.get("tvdb_id"):
        lines.append(f'  <uniqueid type="tvdb">{info["tvdb_id"]}</uniqueid>')
    if info.get("imdb_id"):
        lines.append(f'  <uniqueid type="imdb">{info["imdb_id"]}</uniqueid>')
    if info.get("vote_average"):
        lines.append(f'  <rating>{info["vote_average"]}</rating>')

    for c in info.get("characters", []):
        lines.append('  <actor>')
        lines.append(f'    <name>{_xml_escape(c["actor"])}</name>')
        lines.append(f'    <role>{_xml_escape(c["character"])}</role>')
        lines.append('  </actor>')

    lines.append(f'</{root_tag}>')

    with open(nfo_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"  📄 Đã tạo file NFO: {os.path.basename(nfo_file)}")


def download_artwork(info, output_dir):
    """Download poster and fanart images."""
    os.makedirs(output_dir, exist_ok=True)
    if info.get("poster_path"):
        url = f"{TMDB_IMG_BASE}/w500{info['poster_path']}"
        dst = os.path.join(output_dir, "poster.jpg")
        _download_file(url, dst, "poster.jpg")
    if info.get("backdrop_path"):
        url = f"{TMDB_IMG_BASE}/w1280{info['backdrop_path']}"
        dst = os.path.join(output_dir, "fanart.jpg")
        _download_file(url, dst, "fanart.jpg")


def _download_file(url, output_path, label):
    try:
        urllib.request.urlretrieve(url, output_path)
        sz_kb = os.path.getsize(output_path) / 1024
        print(f"  🖼️  Đã tải: {label} ({sz_kb:.0f} KB)")
    except Exception as e:
        print(f"  ⚠️  Không tải được {label}: {e}")


def _xml_escape(s):
    if not s:
        return ""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def main():
    parser = argparse.ArgumentParser(description="TMDb API v3 Standalone Client & Metadata Engine")
    sub = parser.add_subparsers(dest="command")

    # Search
    p_search = sub.add_parser("search", help="Tìm kiếm phim theo tên")
    p_search.add_argument("query", help="Từ khóa tìm kiếm")
    p_search.add_argument("--type", default="multi", choices=["multi", "movie", "tv"], help="Loại nội dung")
    p_search.add_argument("--lang", default="en-US", help="Ngôn ngữ")

    # Get
    p_get = sub.add_parser("get", help="Lấy chi tiết theo TMDb ID")
    p_get.add_argument("media_type", choices=["movie", "tv"], help="Loại nội dung: movie hoặc tv")
    p_get.add_argument("tmdb_id", type=int, help="TMDb ID")
    p_get.add_argument("--lang", default="en-US", help="Ngôn ngữ")
    p_get.add_argument("--poster", action="store_true", help="Tải poster.jpg")
    p_get.add_argument("--fanart", action="store_true", help="Tải fanart.jpg")
    p_get.add_argument("--nfo", action="store_true", help="Tạo file NFO chuẩn Plex/Jellyfin")
    p_get.add_argument("--output", "-o", default=None,
                       help="Thư mục xuất (mặc định: workspace curation của phim)")
    p_get.add_argument("--json", action="store_true", help="In ra JSON")

    # Find (resolve TMDb ID from an external database ID)
    p_find = sub.add_parser("find", help="Tra cứu TMDb ID từ ID hệ thống khác (TheTVDB/IMDb)")
    p_find.add_argument("external_id", help="Giá trị ID nguồn khác, vd 74599")
    p_find.add_argument("--source", default="tvdb_id",
                         choices=["imdb_id", "tvdb_id", "facebook_id", "instagram_id", "twitter_id"],
                         help="Hệ thống ID nguồn (mặc định: tvdb_id)")
    p_find.add_argument("--lang", default="en-US", help="Ngôn ngữ")
    p_find.add_argument("--json", action="store_true", help="In ra JSON")

    # Search Collection (tìm TMDb Collection theo tên)
    p_sc = sub.add_parser("search-collection", help="Tìm TMDb Collection theo tên franchise")
    p_sc.add_argument("query", help="Tên franchise, vd 'Fast and Furious'")
    p_sc.add_argument("--lang", default="en-US", help="Ngôn ngữ")
    p_sc.add_argument("--json", action="store_true", help="In ra JSON")

    # Collection (lấy chi tiết + danh sách phim thuộc 1 collection)
    p_col = sub.add_parser("collection", help="Lấy chi tiết một TMDb Collection theo ID")
    p_col.add_argument("collection_id", type=int, help="TMDb Collection ID")
    p_col.add_argument("--lang", default="en-US", help="Ngôn ngữ")
    p_col.add_argument("--json", action="store_true", help="In ra JSON")

    args = parser.parse_args()

    api_key = load_api_key()
    if not api_key:
        print("❌ Chưa tìm thấy TMDB_API_KEY trong ~/.env")
        sys.exit(1)

    if args.command == "search":
        search(args.query, args.type, api_key, args.lang)
    elif args.command == "get":
        info = get_details(args.media_type, args.tmdb_id, api_key, args.lang)
        if info:
            if args.json:
                print(json.dumps(info, ensure_ascii=False, indent=2))
            else:
                print_info(info)
            # Default to the title's curation workspace: "." would scatter
            # poster.jpg / tvshow.nfo wherever the agent happened to be run.
            out = args.output or output_for(
                info.get("title") or info.get("name") or str(args.tmdb_id),
                kind=args.media_type)
            if args.poster or args.fanart:
                download_artwork(info, out)
            if args.nfo:
                generate_nfo(info, out)
    elif args.command == "find":
        result = find_by_external_id(args.external_id, args.source, api_key, args.lang)
        if result is None:
            sys.exit(1)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            hits = result["movie_results"] + result["tv_results"]
            if not hits:
                print(f"❌ Không tìm thấy TMDb match cho {args.source}={args.external_id}")
            for r in result["movie_results"]:
                print(f"🎬 movie  tmdb_id={r['id']}  {r.get('title')} ({(r.get('release_date') or '')[:4]})")
            for r in result["tv_results"]:
                print(f"📺 tv     tmdb_id={r['id']}  {r.get('name')} ({(r.get('first_air_date') or '')[:4]})")
    elif args.command == "search-collection":
        results = search_collection(args.query, api_key, args.lang)
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            if not results:
                print(f"❌ Không tìm thấy Collection nào khớp '{args.query}'")
            for r in results:
                print(f"📦 collection_id={r['id']}  {r.get('name')}")
    elif args.command == "collection":
        info = get_collection(args.collection_id, api_key, args.lang)
        if info is None:
            sys.exit(1)
        if args.json:
            print(json.dumps(info, ensure_ascii=False, indent=2))
        else:
            print(f"\n📦 {info['name']} (collection_id {info['id']}) — {len(info['parts'])} phim:")
            for p in info["parts"]:
                print(f"  🎬 tmdb_id={p['tmdb_id']}  {p['title']} ({p['year']})")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
