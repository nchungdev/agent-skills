#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nyaa Search & Scraper — Tìm kiếm torrent anime/phim Nhật từ Nyaa.si.
Hỗ trợ: search by keyword, filter category/resolution/trusted, download .torrent, extract magnet link.
media-collector — scripts/nyaa_search.py
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import re

NYAA_RSS_BASE = "https://nyaa.si/?page=rss"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"


def search_nyaa_rss(query, category="1_2", filter_trusted="0"):
    """
    Search Nyaa using RSS feed (fast, clean, and reliable).
    Categories:
      1_2: Anime - English-translated
      1_4: Anime - Raw
      1_0: Anime - All
      0_0: All categories
    Filter:
      0: No filter
      1: No remakes
      2: Trusted only
    """
    params = {
        "q": query,
        "c": category,
        "f": filter_trusted
    }
    url = f"{NYAA_RSS_BASE}&{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read()
            root = ET.fromstring(content)
            
            items = []
            # Nyaa RSS items inside channel
            for item in root.findall("./channel/item"):
                title = item.find("title").text if item.find("title") is not None else ""
                link = item.find("link").text if item.find("link") is not None else ""
                guid = item.find("guid").text if item.find("guid") is not None else ""
                pubDate = item.find("pubDate").text if item.find("pubDate") is not None else ""
                
                # Nyaa custom tags
                size = ""
                seeders = "0"
                leechers = "0"
                downloads = "0"
                info_hash = ""
                
                for child in item:
                    tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    if tag == "size":
                        size = child.text
                    elif tag == "seeders":
                        seeders = child.text
                    elif tag == "leechers":
                        leechers = child.text
                    elif tag == "downloads":
                        downloads = child.text
                    elif tag == "infoHash":
                        info_hash = child.text

                # Build magnet link from info_hash if available
                magnet = ""
                if info_hash:
                    tr_list = [
                        "http://nyaa.tracker.wf:7777/announce",
                        "udp://open.stealth.si:80/announce",
                        "udp://tracker.opentrackr.org:1337/announce",
                        "udp://tracker.torrent.eu.org:451/announce"
                    ]
                    tr_params = "".join([f"&tr={urllib.parse.quote(tr)}" for tr in tr_list])
                    magnet = f"magnet:?xt=urn:btih:{info_hash}&dn={urllib.parse.quote(title)}{tr_params}"

                items.append({
                    "title": title,
                    "download_url": link,
                    "page_url": guid,
                    "size": size,
                    "seeders": int(seeders) if seeders.isdigit() else 0,
                    "leechers": int(leechers) if leechers.isdigit() else 0,
                    "downloads": downloads,
                    "info_hash": info_hash,
                    "magnet": magnet,
                    "date": pubDate
                })
            return items
    except Exception as e:
        print(f"❌ Nyaa search error: {e}")
        return []


def download_torrent_file(download_url, output_path):
    """Download .torrent file from Nyaa link."""
    try:
        req = urllib.request.Request(download_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=20) as resp, open(output_path, "wb") as out:
            out.write(resp.read())
        size_kb = os.path.getsize(output_path) / 1024
        print(f"  📥 Saved torrent: {os.path.basename(output_path)} ({size_kb:.1f} KB)")
        return True
    except Exception as e:
        print(f"  ⚠️  Failed to download .torrent: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Nyaa.si Torrent Search & Scraper")
    parser.add_argument("query", help="Keyword to search (e.g. 'Monster 1080p BDRip')")
    parser.add_argument("--category", "-c", default="1_2", choices=["1_2", "1_4", "1_0", "0_0"],
                        help="Category: 1_2 (Anime Eng-translated), 1_4 (Anime Raw), 1_0 (All Anime), 0_0 (All)")
    parser.add_argument("--trusted", "-t", action="store_true", help="Filter trusted uploads only")
    parser.add_argument("--limit", "-n", type=int, default=10, help="Max results to display")
    parser.add_argument("--download-top", "-d", metavar="DIR", help="Download top seed .torrent to directory")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    filter_val = "2" if args.trusted else "0"
    results = search_nyaa_rss(args.query, args.category, filter_val)

    if not results:
        print(f"❌ Không tìm thấy kết quả Nyaa cho '{args.query}'")
        return

    # Sort by seeders descending
    results.sort(key=lambda x: x["seeders"], reverse=True)
    displayed = results[:args.limit]

    if args.json:
        print(json.dumps(displayed, ensure_ascii=False, indent=2))
        return

    print(f"\n🔍 Nyaa Search Results for '{args.query}' ({len(results)} found, top {len(displayed)}):\n")
    print(f"{'#':<3} {'Seeds':<7} {'Leech':<7} {'Size':<12} {'Title':<60}")
    print("─" * 95)

    for i, item in enumerate(displayed, 1):
        t_short = item["title"][:58] + ".." if len(item["title"]) > 58 else item["title"]
        print(f"{i:<3} 🟢 {item['seeders']:<5} 🔴 {item['leechers']:<5} {item['size']:<12} {t_short:<60}")

    if args.download_top and displayed:
        top_item = displayed[0]
        os.makedirs(args.download_top, exist_ok=True)
        safe_name = re.sub(r'[^\w\-_\. ]', '_', top_item["title"])[:80] + ".torrent"
        out_path = os.path.join(args.download_top, safe_name)
        print(f"\n⚡ Downloading top seed torrent: {top_item['title']}")
        download_torrent_file(top_item["download_url"], out_path)
        if top_item.get("magnet"):
            print(f"🧲 Magnet Link:\n{top_item['magnet']}\n")


if __name__ == "__main__":
    main()
