#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TMDb Auto-Context & Metadata Resolver for translate-subtitle
Tự động tra cứu bối cảnh, thể loại, dàn nhân vật từ TMDb để:
1. Xác định thể loại và đề xuất style dịch phù hợp
2. Khởi tạo / Bổ sung glossary.json với tên nhân vật chính thức
3. Tạo metadata.json chuẩn định danh TMDb / TheTVDB / IMDb
4. Khởi tạo Two-Tier workspace (PROGRESS.md, AMBIGUITY_LOG.md)

Usage:
  python3 auto_context_resolver.py "Monster" --type tv --output-dir "./Monster_Workspace"
  python3 auto_context_resolver.py 30981 --type tv --output-dir "./Monster_Workspace"
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

# Genre mapping to translate-subtitle style presets
GENRE_TO_STYLE = {
    "Mystery": "detective-mystery",
    "Crime": "detective-mystery",
    "Animation": "default",
    "Action": "classic-cinema",
    "Adventure": "classic-cinema",
    "Sci-Fi & Fantasy": "mecha-robot-karaoke",
    "Science Fiction": "mecha-robot-karaoke",
    "Drama": "classic-cinema",
    "War & Politics": "classic-cinema",
    "History": "xianxia-historical",
    "Comedy": "default",
    "Romance": "default"
}


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
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"❌ TMDb API error: {e}")
        return None


def resolve_media_context(query_or_id, media_type="tv", api_key=None):
    """Resolve full context, cast, and metadata from TMDb."""
    # Check if query_or_id is a numeric ID
    if str(query_or_id).isdigit():
        tmdb_id = int(query_or_id)
    else:
        # Search by query
        search_res = api_get(f"/search/{media_type}", {"query": query_or_id, "language": "en-US"}, api_key)
        if not search_res or not search_res.get("results"):
            print(f"❌ Không tìm thấy phim '{query_or_id}' trên TMDb")
            return None
        tmdb_id = search_res["results"][0]["id"]

    # Fetch full details with credits & external_ids
    details = api_get(f"/{media_type}/{tmdb_id}", {
        "language": "en-US",
        "append_to_response": "credits,external_ids,keywords"
    }, api_key)

    if not details:
        return None

    ext = details.get("external_ids", {})
    credits = details.get("credits", {})
    cast_list = credits.get("cast", [])[:15]

    # Map characters
    characters = {}
    for c in cast_list:
        char_name = c.get("character", "").strip()
        actor_name = c.get("name", "").strip()
        if char_name and char_name not in ["Self", "Narrator"]:
            characters[char_name] = {
                "actor_tmdb": actor_name,
                "vai_tro": "Chính" if len(characters) < 5 else "Phụ"
            }

    genres = [g["name"] for g in details.get("genres", [])]
    
    # Determine best style preset
    recommended_style = "default"
    for g in genres:
        if g in GENRE_TO_STYLE:
            recommended_style = GENRE_TO_STYLE[g]
            break

    # If medical terms in synopsis/title, recommend medical-drama
    synopsis = details.get("overview", "")
    if any(k in synopsis.lower() or k in details.get("name", "").lower() for k in ["surgeon", "doctor", "hospital", "surgery", "disease"]):
        recommended_style = "medical-drama"

    context = {
        "tmdb_id": details["id"],
        "tvdb_id": ext.get("tvdb_id"),
        "imdb_id": ext.get("imdb_id"),
        "type": media_type,
        "title": details.get("name") if media_type == "tv" else details.get("title"),
        "original_title": details.get("original_name") if media_type == "tv" else details.get("original_title"),
        "year": (details.get("first_air_date") or details.get("release_date") or "")[:4],
        "genres": genres,
        "recommended_style": recommended_style,
        "synopsis": synopsis,
        "characters": characters,
        "total_episodes": details.get("number_of_episodes", 1) if media_type == "tv" else 1,
        "total_seasons": details.get("number_of_seasons", 1) if media_type == "tv" else 1
    }

    return context


def init_workspace(context, output_dir):
    """Initialize Two-Tier translation workspace based on TMDb context."""
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "_work"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "_style"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "output"), exist_ok=True)

    # 1. metadata.json
    meta_path = os.path.join(output_dir, "metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(context, f, ensure_ascii=False, indent=2)

    # 2. glossary.json (Pre-populated with TMDb characters)
    gloss_path = os.path.join(output_dir, "glossary.json")
    if not os.path.exists(gloss_path):
        initial_glossary = {
            "meta": {
                "title": context["title"],
                "original_title": context["original_title"],
                "tmdb_id": context["tmdb_id"],
                "tvdb_id": context["tvdb_id"],
                "genres": context["genres"],
                "recommended_style": context["recommended_style"]
            },
            "nhan_vat": context["characters"],
            "address_matrix": {},
            "bang_quy_doi_bat_buoc": {}
        }
        with open(gloss_path, "w", encoding="utf-8") as f:
            json.dump(initial_glossary, f, ensure_ascii=False, indent=2)

    # 3. PROGRESS.md
    prog_path = os.path.join(output_dir, "PROGRESS.md")
    if not os.path.exists(prog_path):
        with open(prog_path, "w", encoding="utf-8") as f:
            f.write(f"# 📋 BẢNG THEO DÕI TIẾN ĐỘ DỊCH — {context['title']} ({context['year']})\n\n")
            f.write(f"> **TMDb ID:** `{context['tmdb_id']}` | **TVDB ID:** `{context['tvdb_id']}` | **Style Đề Xuất:** `{context['recommended_style']}`\n\n")
            f.write("## 📝 Checklist Tiến Độ Từng Tập:\n\n")
            f.write("| Tập | Tên Gốc / Tiêu Đề | Trạng Thái Dịch | Kiểm Định Toàn Vẹn | Lên Plex / NAS |\n")
            f.write("|:---:|:---|:---:|:---:|:---:|\n")
            total_eps = context.get("total_episodes", 1)
            for ep in range(1, min(total_eps + 1, 100)):
                f.write(f"| S01E{ep:02d} | - | ⏳ Chờ dịch | ⏳ Chờ audit | ⏳ Chưa lên |\n")

    # 4. AMBIGUITY_LOG.md
    amb_path = os.path.join(output_dir, "AMBIGUITY_LOG.md")
    if not os.path.exists(amb_path):
        with open(amb_path, "w", encoding="utf-8") as f:
            f.write(f"# ❓ NHẬT KÝ ĐOẠN THOẠI MỜ NGHĨA — {context['title']}\n\n")
            f.write("> *Ghi nhận các đoạn thoại chơi chữ, tiếng lóng, ngữ cảnh mơ hồ cần tham vấn người dịch trước khi chốt vào glossary.*\n\n")
            f.write("| Tập | Timecode | Thoại Gốc (Source) | Phương Án Dịch Tạm Thời | Trạng Thái |\n")
            f.write("|:---:|:---:|:---|:---|:---:|\n")

    print(f"\n🎉 Đã khởi tạo hoàn chỉnh Workspace 2 tầng tại: {output_dir}")
    print(f"  • Title: {context['title']} ({context['year']})")
    print(f"  • Thể loại: {', '.join(context['genres'])}")
    print(f"  • Style gợi ý: --style {context['recommended_style']}")
    print(f"  • Nhân vật TMDb nạp sẵn: {len(context['characters'])} nhân vật")


def main():
    parser = argparse.ArgumentParser(description="TMDb Auto-Context & Metadata Resolver for translate-subtitle")
    parser.add_argument("query", help="Tên phim hoặc TMDb ID")
    parser.add_argument("--type", default="tv", choices=["tv", "movie"], help="Loại phim: tv hoặc movie")
    parser.add_argument("--output-dir", "-o", help="Thư mục workspace cần khởi tạo")
    parser.add_argument("--json", action="store_true", help="In kết quả dạng JSON")

    args = parser.parse_args()

    api_key = load_api_key()
    if not api_key:
        print("❌ TMDB_API_KEY chưa có trong ~/.env")
        sys.exit(1)

    context = resolve_media_context(args.query, args.type, api_key)
    if not context:
        sys.exit(1)

    if args.json:
        print(json.dumps(context, ensure_ascii=False, indent=2))
        return

    print(f"\n══════════════════════════════════════════════════════════════════════")
    print(f"🎬 TMDb Context: {context['title']} ({context['year']})")
    print(f"══════════════════════════════════════════════════════════════════════")
    print(f"  • TMDb ID:       {context['tmdb_id']}")
    print(f"  • TVDB ID:       {context['tvdb_id']}")
    print(f"  • Thể loại:      {', '.join(context['genres'])}")
    print(f"  • Style Gợi Ý:   --style {context['recommended_style']}")
    print(f"  • Quy mô:        {context['total_seasons']} Season, {context['total_episodes']} Tập")
    print(f"  • Dàn nhân vật:  {', '.join(list(context['characters'].keys())[:6])}...")
    print(f"  • Tóm tắt:       {context['synopsis'][:180]}...\n")

    if args.output_dir:
        init_workspace(context, args.output_dir)


if __name__ == "__main__":
    main()
