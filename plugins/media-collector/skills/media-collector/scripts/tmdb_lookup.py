#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TMDb Lookup — Tra cứu metadata phim từ The Movie Database API v3.
Hỗ trợ: search by name, lookup by ID, download poster/fanart, generate NFO.

Usage:
  python3 tmdb_lookup.py search "Kindaichi"
  python3 tmdb_lookup.py search "Black Jack" --type movie
  python3 tmdb_lookup.py get tv 1481
  python3 tmdb_lookup.py get movie 54378
  python3 tmdb_lookup.py get movie 54378 --poster --fanart --nfo --output ./output/
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.parse
import urllib.error

ENV_FILE = os.path.expanduser("~/.env")
TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMG_BASE = "https://image.tmdb.org/t/p"


def load_api_key():
    """Load TMDB_API_KEY from ~/.env (dotenv style)."""
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
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"❌ TMDb API error: {e.code} {e.reason}")
        return None
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None


def download_image(url, output_path):
    """Download an image from TMDb."""
    try:
        urllib.request.urlretrieve(url, output_path)
        size_kb = os.path.getsize(output_path) / 1024
        print(f"  📥 Downloaded: {os.path.basename(output_path)} ({size_kb:.0f} KB)")
        return True
    except Exception as e:
        print(f"  ⚠️  Failed to download {url}: {e}")
        return False


def search(query, media_type="multi", api_key=None, language="en-US"):
    """Search TMDb for movies, TV shows, or both."""
    endpoint = f"/search/{media_type}"
    data = api_get(endpoint, {"query": query, "language": language}, api_key)
    if not data or "results" not in data:
        print(f"❌ No results for '{query}'")
        return []

    results = data["results"][:10]
    print(f"\n🔍 TMDb Search Results for '{query}' ({len(results)} found):\n")
    print(f"{'#':<4} {'Type':<8} {'ID':<10} {'Title':<50} {'Year':<6} {'Rating':<6}")
    print("─" * 90)

    for i, r in enumerate(results, 1):
        mtype = r.get("media_type", media_type)
        if mtype == "tv":
            title = r.get("name", "?")
            year = r.get("first_air_date", "")[:4]
        else:
            title = r.get("title", "?")
            year = r.get("release_date", "")[:4]

        rating = r.get("vote_average", 0)
        tmdb_id = r.get("id", "?")
        print(f"{i:<4} {mtype:<8} {tmdb_id:<10} {title:<50} {year:<6} {rating:<6.1f}")

    return results


def get_details(media_type, tmdb_id, api_key=None, language="en-US"):
    """Get full details for a specific movie or TV show."""
    data = api_get(f"/{media_type}/{tmdb_id}", {
        "language": language,
        "append_to_response": "external_ids,credits,keywords"
    }, api_key)

    if not data:
        return None

    ext = data.get("external_ids", {})

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
            "genres": [g["name"] for g in data.get("genres", [])],
            "status": data.get("status"),
            "seasons": data.get("number_of_seasons"),
            "episodes": data.get("number_of_episodes"),
            "studio": [s["name"] for s in data.get("production_companies", [])],
            "poster_path": data.get("poster_path"),
            "backdrop_path": data.get("backdrop_path"),
            "vote_average": data.get("vote_average"),
        }
    else:
        info = {
            "type": "movie",
            "tmdb_id": data["id"],
            "imdb_id": ext.get("imdb_id"),
            "title": data.get("title"),
            "original_title": data.get("original_title"),
            "year": (data.get("release_date") or "")[:4],
            "overview": data.get("overview"),
            "genres": [g["name"] for g in data.get("genres", [])],
            "runtime": data.get("runtime"),
            "studio": [s["name"] for s in data.get("production_companies", [])],
            "poster_path": data.get("poster_path"),
            "backdrop_path": data.get("backdrop_path"),
            "vote_average": data.get("vote_average"),
        }

    # Display
    print(f"\n{'═' * 70}")
    print(f"📺 {info['title']}  ({info['original_title']})")
    print(f"{'═' * 70}")
    print(f"  TMDb ID:  {info['tmdb_id']}")
    if info.get("tvdb_id"):
        print(f"  TVDB ID:  {info['tvdb_id']}")
    if info.get("imdb_id"):
        print(f"  IMDb ID:  {info['imdb_id']}")
    print(f"  Year:     {info['year']}")
    print(f"  Genres:   {', '.join(info['genres'])}")
    print(f"  Rating:   {info.get('vote_average', 'N/A')}")
    if info.get("seasons"):
        print(f"  Seasons:  {info['seasons']}  ({info['episodes']} episodes)")
    if info.get("runtime"):
        print(f"  Runtime:  {info['runtime']} min")
    print(f"  Studio:   {', '.join(info.get('studio', []))}")
    if info.get("overview"):
        print(f"  Synopsis: {info['overview'][:200]}...")
    print()

    return info


def generate_nfo(info, output_dir):
    """Generate Plex/Jellyfin/Kodi-compatible NFO file."""
    os.makedirs(output_dir, exist_ok=True)

    if info["type"] == "tv":
        nfo_file = os.path.join(output_dir, "tvshow.nfo")
        root_tag = "tvshow"
    else:
        nfo_file = os.path.join(output_dir, "movie.nfo")
        root_tag = "movie"

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
    for s in info.get("studio", []):
        lines.append(f'  <studio>{_xml_escape(s)}</studio>')

    if info.get("tmdb_id"):
        lines.append(f'  <uniqueid type="tmdb" default="true">{info["tmdb_id"]}</uniqueid>')
    if info.get("tvdb_id"):
        lines.append(f'  <uniqueid type="tvdb">{info["tvdb_id"]}</uniqueid>')
    if info.get("imdb_id"):
        lines.append(f'  <uniqueid type="imdb">{info["imdb_id"]}</uniqueid>')
    if info.get("vote_average"):
        lines.append(f'  <rating>{info["vote_average"]}</rating>')

    lines.append(f'</{root_tag}>')

    with open(nfo_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"  📄 Generated: {os.path.basename(nfo_file)}")
    return nfo_file


def _xml_escape(s):
    if not s:
        return ""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def download_artwork(info, output_dir):
    """Download poster and fanart/backdrop images."""
    os.makedirs(output_dir, exist_ok=True)
    if info.get("poster_path"):
        download_image(f"{TMDB_IMG_BASE}/w500{info['poster_path']}", os.path.join(output_dir, "poster.jpg"))
    if info.get("backdrop_path"):
        download_image(f"{TMDB_IMG_BASE}/w1280{info['backdrop_path']}", os.path.join(output_dir, "fanart.jpg"))


def main():
    parser = argparse.ArgumentParser(description="TMDb Lookup — Search & fetch movie/TV metadata")
    sub = parser.add_subparsers(dest="command")

    # search
    sp_search = sub.add_parser("search", help="Search TMDb by title")
    sp_search.add_argument("query", help="Search query")
    sp_search.add_argument("--type", default="multi", choices=["multi", "movie", "tv"], help="Media type filter")
    sp_search.add_argument("--lang", default="en-US", help="Language (default: en-US)")

    # get
    sp_get = sub.add_parser("get", help="Get details by TMDb ID")
    sp_get.add_argument("media_type", choices=["movie", "tv"], help="Media type")
    sp_get.add_argument("tmdb_id", type=int, help="TMDb ID")
    sp_get.add_argument("--lang", default="en-US", help="Language")
    sp_get.add_argument("--poster", action="store_true", help="Download poster")
    sp_get.add_argument("--fanart", action="store_true", help="Download fanart/backdrop")
    sp_get.add_argument("--nfo", action="store_true", help="Generate NFO file")
    sp_get.add_argument("--output", "-o", default=".", help="Output directory")
    sp_get.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    api_key = load_api_key()
    if not api_key:
        print("❌ TMDB_API_KEY not found in ~/.env")
        print("   To add it, run:")
        print('   printf "Enter TMDB_API_KEY (typing hidden): " && read -s val && echo && echo "TMDB_API_KEY=$val" >> ~/.env && echo "Saved."')
        print("\n   Get a free API key at: https://www.themoviedb.org/settings/api")
        sys.exit(1)

    if args.command == "search":
        search(args.query, args.type, api_key, args.lang)
    elif args.command == "get":
        info = get_details(args.media_type, args.tmdb_id, api_key, args.lang)
        if info:
            if args.json:
                print(json.dumps(info, ensure_ascii=False, indent=2))
            if args.poster or args.fanart:
                download_artwork(info, args.output)
            if args.nfo:
                generate_nfo(info, args.output)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
