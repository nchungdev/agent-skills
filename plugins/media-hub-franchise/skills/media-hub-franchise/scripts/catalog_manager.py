#!/usr/bin/env python3
import csv
import json
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
RULES_PATH = SKILL_DIR / "rules" / "franchise_rules.json"
CSV_PATH = SKILL_DIR / "data" / "movies.csv"
CATALOG_PATH = SKILL_DIR / "data" / "catalog.json"

def load_rules():
    if not RULES_PATH.exists():
        return {"disambiguation": {}, "umbrella_rules": {}, "keyword_franchises": [], "canonical_name_map": {}}
    with open(RULES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def extract_ids(all_ids_str, root_key_str):
    combined = f"{all_ids_str} {root_key_str}".strip()
    tmdb_matches = re.findall(r'\btmdb-(\d+)\b', combined)
    tvdb_matches = re.findall(r'\btvdb-(\d+)\b', combined)
    imdb_matches = re.findall(r'\b(tt\d+|imdb-tt\d+)\b', combined)
    
    clean_imdb = []
    for m in imdb_matches:
        clean_imdb.append(m.replace("imdb-", ""))
        
    return {
        "tmdb": list(dict.fromkeys(tmdb_matches)),
        "tvdb": list(dict.fromkeys(tvdb_matches)),
        "imdb": list(dict.fromkeys(clean_imdb)),
        "root_key": root_key_str.strip()
    }

def match_keyword(kw, title, text):
    kw_lower = kw.lower().strip()
    clean_title = re.sub(r'\s*\(\d{4}\)', '', title).strip().lower()
    # Các từ đơn thông dụng cần so khớp chính xác tên phim thay vì substring
    if kw_lower in ["secret", "broken", "game", "g@me.", "oldboy", "troy"]:
        return clean_title == kw_lower or title.lower().strip() == kw_lower
    pattern = r'(?i)(?:\b|_)' + re.escape(kw_lower) + r'(?:\b|_)'
    return bool(re.search(pattern, text))

def classify_title(title, folder_plex, all_ids_str, root_key_str, rules):
    text = f"{title} {folder_plex}".lower()
    ids_text = f"{all_ids_str} {root_key_str}".lower()
    
    # 1. BỘ LỌC BẢN CHẤT IP (Disambiguation): Phân tách các tựa phim trùng/gần giống nhưng khác IP
    for base_name, branches in rules.get("disambiguation", {}).items():
        pattern = r'(?i)(?:\b|_)' + re.escape(base_name.lower()) + r'(?:\b|_)'
        if re.search(pattern, text) or re.search(pattern, ids_text):
            for branch in branches:
                m = branch.get("match", {})
                # Check IDs match
                for target_id in m.get("ids", []):
                    if target_id.lower() in ids_text:
                        return branch["franchise"]
                # Check keyword match
                for kw in m.get("keywords", []):
                    if match_keyword(kw, title, text):
                        return branch["franchise"]

    # 2. Umbrella rules (Vũ trụ lớn: Marvel, DC, Ghibli, Shinkai, Higashino Keigo, Super Sentai...)
    for franchise, keywords in rules.get("umbrella_rules", {}).items():
        for kw in keywords:
            if match_keyword(kw, title, text):
                return franchise

    # 3. Keyword-based franchises (Chuỗi theo tên thương hiệu/đồ chơi: Doraemon, One Piece, B-Daman...)
    canonical_map = rules.get("canonical_name_map", {})
    for kw in rules.get("keyword_franchises", []):
        if match_keyword(kw, title, text):
            return canonical_map.get(kw, kw)

    # 4. Heuristic dấu hai chấm (vd: "Ne Zha: ...")
    if ":" in title:
        candidate = title.split(":")[0].strip()
        if len(candidate) > 2 and candidate.lower() not in ["the", "a", "an"]:
            return canonical_map.get(candidate, candidate)

    # 5. Phim độc lập (Standalone)
    clean_title = re.sub(r'\s*\(\d{4}\)', '', title).strip()
    return clean_title

def deduplicate_rows(rows):
    """
    Chống trùng thông minh:
    Gộp các bản ghi thuộc cùng 1 tác phẩm bị chia làm nhiều dòng (do nguồn Jellyfin/Plex/Drive khác nhau)
    nhưng giữ nguyên các bản remake/khác năm (như Doraemon 1980 vs 2006).
    """
    by_title = {}
    for r in rows:
        t = r.get("title", "").strip().lower()
        if not t:
            continue
        by_title.setdefault(t, []).append(r)

    deduped = []
    for t, group in by_title.items():
        if len(group) == 1:
            deduped.append(group[0])
            continue

        # Có nhiều dòng trùng title -> kiểm tra năm
        years = {g.get("year") for g in group if g.get("year")}
        
        # Nếu có nhiều năm khác nhau rõ rệt (vd 1980 và 2006) -> Là phim remake/phần khác -> Giữ riêng
        if len(years) > 1:
            for y in sorted(years):
                sub = [g for g in group if g.get("year") == y]
                merged_item = dict(sub[0])
                for other in sub[1:]:
                    merged_item["all_ids"] = (merged_item.get("all_ids", "") + " " + other.get("all_ids", "")).strip()
                deduped.append(merged_item)
            # Dòng nào không có năm thì gộp vào dòng đầu tiên hoặc giữ riêng
            empty = [g for g in group if not g.get("year")]
            for em in empty:
                deduped.append(em)
        else:
            # Cùng 1 phim xuất hiện ở nhiều server (1 dòng Jellyfin, 1 dòng Plex...) -> GỘP NGUỒN
            merged_item = dict(group[0])
            for other in group[1:]:
                if not merged_item.get("year") and other.get("year"):
                    merged_item["year"] = other["year"]
                if not merged_item.get("folder_plex") and other.get("folder_plex"):
                    merged_item["folder_plex"] = other["folder_plex"]
                merged_item["all_ids"] = (merged_item.get("all_ids", "") + " " + other.get("all_ids", "")).strip()
                if other.get("thuyet_minh_vn") == "1":
                    merged_item["thuyet_minh_vn"] = "1"
                if other.get("sub_langs"):
                    merged_item["sub_langs"] = other["sub_langs"]
                # Gộp sources
                s1 = set((merged_item.get("sources") or "").split("+"))
                s2 = set((other.get("sources") or "").split("+"))
                merged_item["sources"] = "+".join(sorted(filter(None, s1 | s2)))
            deduped.append(merged_item)

    return deduped

def build_catalog(csv_file=None):
    source_csv = Path(csv_file) if csv_file else CSV_PATH
    if not source_csv.exists():
        print(f"Error: CSV file '{source_csv}' not found.")
        sys.exit(1)
        
    rules = load_rules()
    
    with open(source_csv, "r", encoding="utf-8-sig") as f:
        raw_rows = list(csv.DictReader(f))

    # BƯỚC 1: CHỐNG TRÙNG CÁC DÒNG MEDIA
    deduped_rows = deduplicate_rows(raw_rows)
    
    catalog = {}
    for row in deduped_rows:
        title = (row.get("title") or "").strip()
        if not title:
            continue
        folder_plex = (row.get("folder_plex") or "").strip()
        all_ids = (row.get("all_ids") or "").strip()
        root_key = (row.get("root_key") or "").strip()
        
        # BƯỚC 2: PHÂN LOẠI THEO IP & FRANCHISE
        franchise = classify_title(title, folder_plex, all_ids, root_key, rules)
        
        ids = extract_ids(all_ids, root_key)
        episodes = (row.get("episodes") or "").strip()
        media_type = "series" if (episodes.isdigit() and int(episodes) > 1) else (row.get("type", "").strip() or "movie")
        
        item = {
            "title": title,
            "year": (row.get("year") or "").strip(),
            "type": media_type,
            "viet_title": folder_plex,
            "root_key": ids["root_key"],
            "tmdb_ids": ids["tmdb"],
            "tvdb_ids": ids["tvdb"],
            "imdb_ids": ids["imdb"],
            "thuyet_minh_vn": row.get("thuyet_minh_vn") == "1",
            "sub_langs": (row.get("sub_langs") or "").strip(),
            "sources": row.get("sources", "")
        }
        
        if franchise not in catalog:
            catalog[franchise] = []
        catalog[franchise].append(item)

    # Sắp xếp phim trong từng franchise theo năm
    for f_name in catalog:
        catalog[f_name].sort(key=lambda x: (x["year"] if x["year"].isdigit() else "9999", x["title"]))

    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    total_movies = sum(len(v) for v in catalog.values())
    print(f"Build catalog thành công (sau khi chống trùng): {total_movies} tác phẩm trong {len(catalog)} franchise.")

def load_catalog():
    if not CATALOG_PATH.exists():
        build_catalog()
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def list_franchises(sort_by="count"):
    catalog = load_catalog()
    total_movies = sum(len(v) for v in catalog.values())
    print(f"Tổng cộng: {len(catalog)} franchise · {total_movies} phim/series\n")
    
    if sort_by == "alpha":
        items = sorted(catalog.items(), key=lambda x: x[0].lower())
    else:
        items = sorted(catalog.items(), key=lambda x: len(x[1]), reverse=True)
        
    for name, movies in items:
        movies_count = sum(1 for m in movies if m["type"] == "movie")
        series_count = sum(1 for m in movies if m["type"] == "series")
        desc = []
        if movies_count > 0:
            desc.append(f"{movies_count} movie")
        if series_count > 0:
            desc.append(f"{series_count} series")
        print(f"- **{name}** ({len(movies)}) [{', '.join(desc)}]")

def get_franchise(target_name):
    catalog = load_catalog()
    target_lower = target_name.lower().strip()
    
    matches = [k for k in catalog if k.lower() == target_lower]
    if not matches:
        matches = [k for k in catalog if target_lower in k.lower()]
        
    if not matches:
        print(f"Không tìm thấy franchise nào khớp với '{target_name}'.")
        return
        
    for f_name in matches:
        movies = catalog[f_name]
        print(f"## {f_name} ({len(movies)})\n")
        for m in movies:
            year_str = f"({m['year']})" if m['year'] else "(?)"
            type_str = m['type']
            
            id_parts = []
            if m['tmdb_ids']:
                id_parts.append(f"[tmdb-{','.join(m['tmdb_ids'])}]")
            if m['tvdb_ids']:
                id_parts.append(f"[tvdb-{','.join(m['tvdb_ids'])}]")
            if not id_parts and m['root_key']:
                id_parts.append(f"[{m['root_key']}]")
            ids_str = " ".join(id_parts) if id_parts else ""
            
            viet = f" · *{m['viet_title']}*" if m['viet_title'] and m['viet_title'].lower() != m['title'].lower() else ""
            extras = []
            if m.get('thuyet_minh_vn'):
                extras.append("thuyết minh VN")
            if m.get('sub_langs'):
                extras.append(f"sub: {m['sub_langs']}")
            extra_str = f" [{'; '.join(extras)}]" if extras else ""
            
            print(f"- {m['title']} {year_str} · {type_str} · {ids_str}{viet}{extra_str}".replace("  ", " "))
        print()

def categorize_list(titles_or_file):
    rules = load_rules()
    titles = []
    
    p = Path(titles_or_file)
    if p.exists() and p.is_file():
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                l = line.strip().lstrip("-*0123456789. ")
                if l:
                    titles.append(l)
    else:
        titles = [t.strip().lstrip("-*0123456789. ") for t in titles_or_file.split("\n") if t.strip()]

    grouped = {}
    for t in titles:
        franchise = classify_title(t, "", "", "", rules)
        if franchise not in grouped:
            grouped[franchise] = []
        grouped[franchise].append(t)
        
    for f_name, items in sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"### {f_name} ({len(items)})")
        for item in items:
            print(f"- {item}")
        print()

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  catalog_manager.py build [path/to/movies.csv]")
        print("  catalog_manager.py list-franchises [--alpha]")
        print("  catalog_manager.py get-franchise <franchise_name>")
        print("  catalog_manager.py categorize <titles_or_file_path>")
        return

    cmd = sys.argv[1]
    if cmd == "build":
        csv_file = sys.argv[2] if len(sys.argv) > 2 else None
        build_catalog(csv_file)
    elif cmd == "list-franchises":
        sort_mode = "alpha" if "--alpha" in sys.argv else "count"
        list_franchises(sort_mode)
    elif cmd == "get-franchise":
        if len(sys.argv) < 3:
            print("Vui lòng cung cấp tên franchise cần tra cứu.")
            return
        get_franchise(" ".join(sys.argv[2:]))
    elif cmd == "categorize":
        if len(sys.argv) < 3:
            print("Vui lòng cung cấp danh sách tên phim hoặc đường dẫn file.")
            return
        categorize_list(" ".join(sys.argv[2:]))
    else:
        print(f"Lệnh không hợp lệ: {cmd}")

if __name__ == "__main__":
    main()
