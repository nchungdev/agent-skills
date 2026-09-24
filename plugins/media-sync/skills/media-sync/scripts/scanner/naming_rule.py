import re
from pathlib import Path

def sanitize_title(title):
    # Remove torrent junk tags
    junk_patterns = [
        r"\[.*?\]", r"\(1080p.*?\)", r"\(720p.*?\)",
        r"\b(?:480|576|720|1080|2160)[pi]\b", r"\b(?:4K|UHD)\b",
        r"x264.*", r"x265.*",
        r"BDRip.*", r"WEB-DL.*", r"BluRay.*", r"HEVC.*", r"AAC.*", r"DUAL.*"
    ]
    cleaned = title
    for p in junk_patterns:
        cleaned = re.sub(p, " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip().strip("-").strip()

def format_plex_episode(show_title, year=None, tvdb_id=None, season=1, episode=1, ext="mp4", quality="1080p BluRay"):
    """Format file path following standard Plex/TVDB hierarchy."""
    clean_show = sanitize_title(show_title)
    year_str = f" ({year})" if year else ""
    tvdb_str = f" {{tvdb-{tvdb_id}}}" if tvdb_id else ""
    
    show_folder = f"{clean_show}{year_str}{tvdb_str}"
    season_folder = f"Season {season:02d}"
    filename = f"{clean_show} - S{season:02d}E{episode:02d} - [{quality}].{ext.lstrip('.')}"
    
    return Path("TV Shows") / show_folder / season_folder / filename
