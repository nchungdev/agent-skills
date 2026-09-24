import os
import json
import urllib.request
import urllib.parse
import urllib.error
import re

PROWLARR_URL = os.environ.get("PROWLARR_URL", "http://localhost:9696")
PROWLARR_API_KEY = os.environ.get("PROWLARR_API_KEY", "")
if not PROWLARR_API_KEY and os.path.exists(os.path.expanduser("~/.env")):
    with open(os.path.expanduser("~/.env")) as f:
        for line in f:
            if line.startswith("PROWLARR_API_KEY="):
                PROWLARR_API_KEY = line.strip().split("=", 1)[1].strip("\"'")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

opener = urllib.request.build_opener(NoRedirect)

def resolve_magnet(download_url):
    """Resolve Prowlarr download redirect to real magnet link."""
    if not download_url:
        return None
    if download_url.startswith("magnet:"):
        return download_url
    try:
        opener.open(download_url)
    except urllib.error.HTTPError as e:
        loc = e.headers.get("Location")
        if loc and loc.startswith("magnet:"):
            return loc
    except Exception:
        pass
    return download_url

def search_prowlarr(query, quality=None, limit=20):
    """Search Prowlarr indexers and return clean torrent releases with magnets."""
    encoded_q = urllib.parse.quote(query)
    url = f"{PROWLARR_URL}/api/v1/search?query={encoded_q}"
    req = urllib.request.Request(url, headers={"X-Api-Key": PROWLARR_API_KEY})
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"❌ Prowlarr API error: {e}")
        return []

    results = []
    for item in data:
        title = item.get("title", "")
        size_mb = round(item.get("size", 0) / (1024 * 1024), 1)
        seeders = item.get("seeders", 0)
        indexer = item.get("indexer", "Unknown")
        dl_url = item.get("downloadUrl")
        mag_url = item.get("magnetUrl")

        # Filter by quality if requested
        if quality:
            tokens = quality.lower().split()
            title_lower = title.lower()
            if not all(t in title_lower for t in tokens):
                continue

        results.append({
            "title": title,
            "size_mb": size_mb,
            "seeders": seeders,
            "indexer": indexer,
            "download_url": dl_url,
            "magnet_url": mag_url
        })

    # Sort descending by seeders
    results.sort(key=lambda x: x["seeders"], reverse=True)
    return results[:limit]
