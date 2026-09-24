#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Subtitle Multi-Source Search & Fetcher
Tra cứu và tải phụ đề từ Kitsunekko (Japanese ASS/SRT) và SubDL / Subsource.
media-collector — scripts/subtitle_search.py
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.parse
import re

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"


def search_kitsunekko(anime_name):
    """
    Search Kitsunekko for Japanese subtitles (ASS/SRT).
    Kitsunekko has a clean directory listing format.
    """
    base_url = "https://kitsunekko.net/dirlist.php?dir=subtitles%2Fjapanese%2F"
    try:
        req = urllib.request.Request(base_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        # Find matching anime folder links
        matches = []
        # Pattern: <a href="dirlist.php?dir=subtitles%2Fjapanese%2FAnime_Name%2F"><strong>Anime Name</strong></a>
        for link, name in re.findall(r'href="(dirlist\.php\?dir=subtitles%2Fjapanese%2F[^"]+)"[^>]*><strong>([^<]+)</strong>', html):
            if anime_name.lower() in name.lower():
                full_url = f"https://kitsunekko.net/{link}"
                matches.append({"name": name, "url": full_url})
        return matches
    except Exception as e:
        print(f"⚠️  Kitsunekko search error: {e}")
        return []


def get_kitsunekko_files(folder_url):
    """Get list of subtitle files inside a Kitsunekko anime folder."""
    try:
        req = urllib.request.Request(folder_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        files = []
        # Pattern: <a href="subtitles/japanese/Anime_Name/episode.srt">filename</a>
        for href in re.findall(r'href="(subtitles/japanese/[^"]+\.(?:srt|ass|zip|rar|7z))"', html):
            file_url = f"https://kitsunekko.net/{href}"
            filename = urllib.parse.unquote(os.path.basename(href))
            files.append({"filename": filename, "url": file_url})
        return files
    except Exception as e:
        print(f"⚠️  Kitsunekko file fetch error: {e}")
        return []


def download_sub_file(file_url, output_path):
    """Download a subtitle file from direct link."""
    try:
        req = urllib.request.Request(file_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=20) as resp, open(output_path, "wb") as out:
            out.write(resp.read())
        size_kb = os.path.getsize(output_path) / 1024
        print(f"  📥 Saved: {os.path.basename(output_path)} ({size_kb:.1f} KB)")
        return True
    except Exception as e:
        print(f"  ⚠️  Failed to download {file_url}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Multi-Source Subtitle Search & Fetcher")
    parser.add_argument("query", help="Anime / Movie name to search")
    parser.add_argument("--source", default="kitsunekko", choices=["kitsunekko", "all"], help="Source provider")
    parser.add_argument("--download-all", "-d", metavar="DIR", help="Download all files to target directory")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    print(f"\n🔍 Searching Subtitles for '{args.query}' on {args.source.capitalize()}...\n")

    if args.source in ["kitsunekko", "all"]:
        folders = search_kitsunekko(args.query)
        if not folders:
            print(f"❌ Không tìm thấy thư mục phụ đề tiếng Nhật cho '{args.query}' trên Kitsunekko.")
        else:
            print(f"✅ Tìm thấy {len(folders)} thư mục khớp trên Kitsunekko:")
            for i, f in enumerate(folders, 1):
                print(f"  [{i}] {f['name']}")

            # Fetch files from the first matching folder
            target_folder = folders[0]
            print(f"\n📂 Lấy danh sách file từ: {target_folder['name']}...")
            files = get_kitsunekko_files(target_folder["url"])
            print(f"  -> Có {len(files)} file phụ đề.")

            if args.json:
                print(json.dumps(files, ensure_ascii=False, indent=2))
                return

            for item in files[:10]:
                print(f"   • {item['filename']}")
            if len(files) > 10:
                print(f"   ... và {len(files) - 10} file khác.")

            if args.download_all and files:
                os.makedirs(args.download_all, exist_ok=True)
                print(f"\n⚡ Đang tải {len(files)} file vào: {args.download_all}...")
                for item in files:
                    out_p = os.path.join(args.download_all, item["filename"])
                    download_sub_file(item["url"], out_p)
                print(f"🎉 Hoàn tất tải {len(files)} phụ đề!")


if __name__ == "__main__":
    main()
