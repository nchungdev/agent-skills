#!/usr/bin/env python3
"""
Direct SQLite read-only connector for local Plex and Jellyfin databases.
Extracts watch history, in-progress items, unwatched library gems, and user taste profile.
Zero-API, zero-auth, zero DB locking.
"""

import os
import re
import sqlite3
from typing import List, Dict, Any, Optional
from pathlib import Path

PLEX_DEFAULT_DB = "/home/chungnh/appdata/plex/Library/Application Support/Plex Media Server/Plug-in Support/Databases/com.plexapp.plugins.library.db"
JELLYFIN_DEFAULT_DB = "/home/chungnh/appdata/jellyfin/data/data/jellyfin.db"

class PlexReader:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or PLEX_DEFAULT_DB
        self.available = os.path.exists(self.db_path)

    def _get_connection(self):
        if not self.available:
            return None
        # Connect in read-only mode to prevent any locking or WAL interference
        return sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)

    @staticmethod
    def extract_tmdb_id(file_path: str) -> Optional[int]:
        if not file_path:
            return None
        m = re.search(r"\{tmdb-(\d+)\}", file_path, re.IGNORECASE)
        if m:
            try:
                return int(m.group(1))
            except ValueError:
                pass
        return None

    def get_taste_profile(self) -> Dict[str, Any]:
        """Analyzes watched content to build a user taste profile."""
        conn = self._get_connection()
        if not conn:
            return {"genres": [], "actors": [], "directors": [], "total_watched": 0}

        try:
            cur = conn.cursor()
            # Top genres of watched items
            cur.execute("""
                SELECT t.tag, COUNT(*) as cnt
                FROM metadata_item_settings s
                JOIN metadata_items m ON s.guid = m.guid
                JOIN taggings tg ON tg.metadata_item_id = m.id
                JOIN tags t ON t.id = tg.tag_id
                WHERE t.tag_type = 1 AND s.view_count > 0
                GROUP BY t.tag
                ORDER BY cnt DESC
                LIMIT 10;
            """)
            top_genres = [{"genre": r[0], "count": r[1]} for r in cur.fetchall()]

            # Top actors of watched items
            cur.execute("""
                SELECT t.tag, COUNT(*) as cnt
                FROM metadata_item_settings s
                JOIN metadata_items m ON s.guid = m.guid
                JOIN taggings tg ON tg.metadata_item_id = m.id
                JOIN tags t ON t.id = tg.tag_id
                WHERE t.tag_type = 6 AND s.view_count > 0
                GROUP BY t.tag
                ORDER BY cnt DESC
                LIMIT 8;
            """)
            top_actors = [{"actor": r[0], "count": r[1]} for r in cur.fetchall()]

            # Total items watched
            cur.execute("SELECT COUNT(*) FROM metadata_item_settings WHERE view_count > 0;")
            total_watched = cur.fetchone()[0]

            return {
                "genres": top_genres,
                "actors": top_actors,
                "total_watched": total_watched
            }
        except Exception as e:
            return {"error": str(e), "genres": [], "actors": [], "total_watched": 0}
        finally:
            conn.close()

    def get_in_progress(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Returns items currently in progress (watched partially)."""
        conn = self._get_connection()
        if not conn:
            return []

        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT m.id, m.title, m.year, m.metadata_type, s.view_offset, m.duration,
                       s.last_viewed_at, m.summary, p.file, 
                       season.title as season_title, show.title as show_title
                FROM metadata_item_settings s
                JOIN metadata_items m ON s.guid = m.guid
                LEFT JOIN metadata_items season ON m.parent_id = season.id
                LEFT JOIN metadata_items show ON season.parent_id = show.id
                LEFT JOIN media_items mi ON mi.metadata_item_id = m.id
                LEFT JOIN media_parts p ON p.media_item_id = mi.id
                WHERE s.view_offset > 0 
                  AND (m.duration IS NULL OR s.view_offset < (m.duration * 0.92))
                GROUP BY m.id
                ORDER BY s.last_viewed_at DESC
                LIMIT ?;
            """, (limit,))
            
            items = []
            for r in cur.fetchall():
                dur_ms = r[5] or 0
                offset_ms = r[4] or 0
                pct = int((offset_ms / dur_ms * 100)) if dur_ms > 0 else 0
                m_type = "Movie" if r[3] == 1 else "Episode"
                
                show_title = r[10]
                season_title = r[9]
                ep_title = r[1]
                
                if m_type == "Episode" and show_title:
                    display_title = f"{show_title} - {season_title or ''} - {ep_title}"
                    search_title = show_title
                else:
                    display_title = ep_title
                    search_title = ep_title

                file_path = r[8] or ""
                tmdb_id = self.extract_tmdb_id(file_path)

                items.append({
                    "id": r[0],
                    "title": display_title,
                    "search_title": search_title,
                    "year": r[2],
                    "type": m_type,
                    "offset_minutes": offset_ms // 60000,
                    "duration_minutes": dur_ms // 60000,
                    "progress_percent": pct,
                    "last_viewed_at": r[6],
                    "summary": r[7] or "",
                    "file": file_path,
                    "tmdb_id": tmdb_id
                })
            return items
        except Exception:
            return []
        finally:
            conn.close()

    def get_unwatched_library(self, limit: int = 20, min_rating: float = 0.0) -> List[Dict[str, Any]]:
        """Returns top quality movies/shows stored on NAS that the user has NOT watched."""
        conn = self._get_connection()
        if not conn:
            return []

        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT m.id, m.title, m.year, m.rating, m.summary, p.file, m.duration, m.metadata_type
                FROM metadata_items m
                LEFT JOIN metadata_item_settings s ON s.guid = m.guid
                LEFT JOIN media_items mi ON mi.metadata_item_id = m.id
                LEFT JOIN media_parts p ON p.media_item_id = mi.id
                WHERE m.metadata_type IN (1, 2)
                  AND (s.view_count IS NULL OR s.view_count = 0)
                  AND (s.view_offset IS NULL OR s.view_offset = 0)
                  AND p.file IS NOT NULL
                GROUP BY m.id
                ORDER BY m.rating DESC, m.year DESC
                LIMIT ?;
            """, (limit * 2,))

            items = []
            seen_titles = set()
            for r in cur.fetchall():
                title = r[1]
                if not title or title.lower() in seen_titles:
                    continue
                seen_titles.add(title.lower())
                
                rating = float(r[3]) if r[3] is not None else 0.0
                if min_rating > 0 and rating < min_rating:
                    continue

                file_path = r[5] or ""
                tmdb_id = self.extract_tmdb_id(file_path)

                items.append({
                    "id": r[0],
                    "title": title,
                    "year": r[2],
                    "rating": rating if rating > 0 else None,
                    "summary": r[4] or "",
                    "file": file_path,
                    "duration_minutes": (r[6] or 0) // 60000,
                    "type": "Movie" if r[7] == 1 else "Show",
                    "tmdb_id": tmdb_id
                })
                if len(items) >= limit:
                    break
            return items
        except Exception:
            return []
        finally:
            conn.close()

    def search_local(self, query: str, year: Optional[Any] = None, tmdb_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Searches if a movie exists locally on NAS / Plex using strict matching."""
        conn = self._get_connection()
        if not conn:
            return []

        try:
            cur = conn.cursor()

            # 1. Exact match via TMDb ID if available
            if tmdb_id:
                # 1a. Check Plex tags
                cur.execute("""
                    SELECT m.id, m.title, m.year, m.metadata_type, p.file, s.view_count
                    FROM metadata_items m
                    JOIN taggings tg ON tg.metadata_item_id = m.id
                    JOIN tags t ON t.id = tg.tag_id AND t.tag_type = 314
                    LEFT JOIN media_items mi ON mi.metadata_item_id = m.id
                    LEFT JOIN media_parts p ON p.media_item_id = mi.id
                    LEFT JOIN metadata_item_settings s ON s.guid = m.guid
                    WHERE m.metadata_type IN (1, 2) AND t.tag = ?
                    GROUP BY m.id
                    LIMIT 1;
                """, (f"tmdb://{tmdb_id}",))
                row = cur.fetchone()
                if not row:
                    # 1b. Check media_parts file path
                    cur.execute("""
                        SELECT m.id, m.title, m.year, m.metadata_type, p.file, s.view_count
                        FROM metadata_items m
                        JOIN media_items mi ON mi.metadata_item_id = m.id
                        JOIN media_parts p ON p.media_item_id = mi.id
                        LEFT JOIN metadata_item_settings s ON s.guid = m.guid
                        WHERE m.metadata_type IN (1, 2) AND p.file LIKE ?
                        GROUP BY m.id
                        LIMIT 1;
                    """, (f"%{{tmdb-{tmdb_id}}}%",))
                    row = cur.fetchone()
                if row:
                    return [{
                        "id": row[0],
                        "title": row[1],
                        "year": row[2],
                        "type": "Movie" if row[3] == 1 else "Show",
                        "file": row[4] or "",
                        "view_count": row[5] or 0,
                        "watched": (row[5] or 0) > 0
                    }]

            # 2. Strict normalized title matching
            from difflib import SequenceMatcher

            def normalize(s):
                if not s:
                    return ""
                s = s.lower()
                s = re.sub(r"[\(\)\[\]\{\}\:\-\*\.\,\?\_]", " ", s)
                return " ".join(s.split())

            nq = normalize(query)
            if not nq:
                return []

            stop = {"the", "a", "an", "phim", "movie", "tap", "season"}
            q_tokens = set([w for w in nq.split() if w not in stop])

            cur.execute("""
                SELECT m.id, m.title, m.year, m.metadata_type, p.file, s.view_count
                FROM metadata_items m
                LEFT JOIN metadata_item_settings s ON s.guid = m.guid
                LEFT JOIN media_items mi ON mi.metadata_item_id = m.id
                LEFT JOIN media_parts p ON p.media_item_id = mi.id
                WHERE m.metadata_type IN (1, 2)
                GROUP BY m.id;
            """)

            results = []
            target_year = int(year) if year and str(year).isdigit() else None

            for r in cur.fetchall():
                cand_title = r[1]
                cand_year = r[2]
                nt = normalize(cand_title)
                if not nt:
                    continue

                matched = False
                if nq == nt:
                    matched = True
                else:
                    t_tokens = set([w for w in nt.split() if w not in stop])
                    if q_tokens and t_tokens and q_tokens == t_tokens:
                        matched = True
                    else:
                        ratio = SequenceMatcher(None, nq, nt).ratio()
                        if ratio >= 0.85:
                            matched = True

                if matched:
                    if target_year and cand_year and abs(target_year - int(cand_year)) > 1:
                        continue
                    results.append({
                        "id": r[0],
                        "title": r[1],
                        "year": r[2],
                        "type": "Movie" if r[3] == 1 else "Show",
                        "file": r[4] or "",
                        "view_count": r[5] or 0,
                        "watched": (r[5] or 0) > 0
                    })
                    if len(results) >= 2:
                        break

            return results
        except Exception:
            return []
        finally:
            conn.close()

if __name__ == "__main__":
    reader = PlexReader()
    print("Plex DB available:", reader.available)
    if reader.available:
        print("In progress sample:", reader.get_in_progress(2))
