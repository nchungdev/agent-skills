#!/usr/bin/env python3
"""
Media Advisor interactive user survey and environment configuration.
Discovers local Plex/Jellyfin SQLite databases and surveys user preferences.
"""

import os
import sys
import json
from pathlib import Path

DEFAULT_CONFIG = {
    "plex_db_path": "/home/chungnh/appdata/plex/Library/Application Support/Plex Media Server/Plug-in Support/Databases/com.plexapp.plugins.library.db",
    "jellyfin_db_path": "/home/chungnh/appdata/jellyfin/data/data/jellyfin.db",
    "preferred_genres": [],          # Empty = all genres welcome
    "excluded_genres": [],
    "preferred_regions": ["ALL"],     # ALL, US, KR, JP, CN, VN
    "max_duration_minutes": 0,       # 0 = unlimited
    "min_rating": 6.5,               # TMDb / IMDb minimum rating
    "anti_seeding_min_votes": 300,   # Minimum vote count to defeat PR/seeding bots
    "streaming_providers": ["Netflix", "Apple TV+", "HBO Max", "Disney+", "Amazon Prime"],
    "auto_taste_profiling": True     # Auto-learn from Plex watch history
}

def get_config_paths():
    workspace_cfg = Path.cwd() / ".agent" / "advisor_config.json"
    user_cfg = Path.home() / ".config" / "media-advisor" / "config.json"
    return workspace_cfg, user_cfg

def load_config():
    workspace_cfg, user_cfg = get_config_paths()
    if workspace_cfg.exists():
        try:
            with open(workspace_cfg, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                res = DEFAULT_CONFIG.copy()
                res.update(cfg)
                return res
        except Exception:
            pass
    if user_cfg.exists():
        try:
            with open(user_cfg, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                res = DEFAULT_CONFIG.copy()
                res.update(cfg)
                return res
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(cfg):
    workspace_cfg, user_cfg = get_config_paths()
    saved = []
    
    # Save to workspace if in a git/agent workspace
    if Path.cwd() != Path.home():
        (Path.cwd() / ".agent").mkdir(parents=True, exist_ok=True)
        with open(workspace_cfg, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        saved.append(str(workspace_cfg))

    # Always save to user config directory
    user_cfg.parent.mkdir(parents=True, exist_ok=True)
    with open(user_cfg, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    saved.append(str(user_cfg))

    return saved

def run_survey(non_interactive=False):
    print("🎯 Khảo Sát Thiết Lập Media Advisor (Cinema & Series Concierge)")
    print("==============================================================")
    cfg = load_config()

    if non_interactive or "--defaults" in sys.argv:
        print("⚡ Đang lưu cấu hình mặc định (khách quan, bao quát toàn bộ, không giới hạn)...")
        saved = save_config(cfg)
        print(f"✅ Đã lưu cấu hình tại: {', '.join(saved)}")
        return cfg

    # 1. Plex DB detection
    default_plex = cfg.get("plex_db_path", "")
    if os.path.exists(default_plex):
        print(f"🟢 Tìm thấy Plex Database: {default_plex}")
    else:
        print(f"🟡 Không tìm thấy Plex DB tại: {default_plex}")
    ans = input(f"Đường dẫn Plex DB [{default_plex}]: ").strip()
    if ans:
        cfg["plex_db_path"] = ans

    # 2. Jellyfin DB detection
    default_jf = cfg.get("jellyfin_db_path", "")
    if os.path.exists(default_jf):
        print(f"🟢 Tìm thấy Jellyfin Database: {default_jf}")
    ans = input(f"Đường dẫn Jellyfin DB [{default_jf}]: ").strip()
    if ans:
        cfg["jellyfin_db_path"] = ans

    # 3. Taste Survey - Preferred Genres
    print("\n--- 🎬 KHẢO SÁT GU XEM PHIM ---")
    print("1. Tất cả thể loại (Mặc định - Khách quan)")
    print("2. Ưu tiên: Hành động / Phiêu lưu / Sci-Fi")
    print("3. Ưu tiên: Anime / Hoạt hình Nhật Bản")
    print("4. Ưu tiên: Trinh thám / Giật gân / Tâm lý tội phạm")
    print("5. Ưu tiên: Hài hước / Gia đình / Chữa lành")
    genre_opt = input("Chọn mục (1-5 hoặc gõ tự do, Enter để bỏ qua): ").strip()
    if genre_opt == "2":
        cfg["preferred_genres"] = ["Action", "Adventure", "Science Fiction"]
    elif genre_opt == "3":
        cfg["preferred_genres"] = ["Animation", "Anime"]
    elif genre_opt == "4":
        cfg["preferred_genres"] = ["Mystery", "Thriller", "Crime"]
    elif genre_opt == "5":
        cfg["preferred_genres"] = ["Comedy", "Family"]
    elif genre_opt and genre_opt != "1":
        cfg["preferred_genres"] = [g.strip() for g in genre_opt.split(",")]
    else:
        cfg["preferred_genres"] = []

    # 4. Excluded Genres
    print("\nBạn có muốn loại trừ thể loại nào không? (ví dụ: Kinh dị, Tình cảm...)")
    exc = input("Thể loại bỏ qua (Enter để không bỏ qua gì): ").strip()
    if exc:
        cfg["excluded_genres"] = [g.strip() for g in exc.split(",")]
    else:
        cfg["excluded_genres"] = []

    # 5. Preferred Region / Language
    print("\n--- 🌍 KHU VỰC & QUỐC GIA ---")
    print("1. Toàn cầu (Âu Mỹ, Châu Á, v.v. - Mặc định)")
    print("2. Hollywood / Âu Mỹ")
    print("3. Nhật Bản / Anime")
    print("4. Hàn Quốc (K-Drama / K-Movie)")
    print("5. Trung Quốc (C-Drama / Điện ảnh Hoa Ngữ)")
    reg_opt = input("Chọn khu vực (1-5, Enter để chọn Toàn cầu): ").strip()
    region_map = {"1": ["ALL"], "2": ["US", "GB"], "3": ["JP"], "4": ["KR"], "5": ["CN", "HK", "TW"]}
    cfg["preferred_regions"] = region_map.get(reg_opt, ["ALL"])

    # 6. Duration Budget
    print("\n--- ⏱️ THỜI LƯỢNG MONG MUỐN ---")
    print("1. Không giới hạn thời lượng (Mặc định)")
    print("2. Phim ngắn / Vừa phải (< 90 phút)")
    print("3. Phim tiêu chuẩn (< 120 phút)")
    dur_opt = input("Chọn thời lượng (1-3): ").strip()
    if dur_opt == "2":
        cfg["max_duration_minutes"] = 90
    elif dur_opt == "3":
        cfg["max_duration_minutes"] = 120
    else:
        cfg["max_duration_minutes"] = 0

    # 7. Anti-Seeding Filter
    print("\n--- 🛡️ BỘ LỌC CHỐNG SEEDING & ĐÁNH GIÁ ẢO ---")
    print("Mặc định: Phải có tối thiểu 300 lượt đánh giá thực tế và điểm số >= 6.5.")
    min_vote = input("Số lượt đánh giá tối thiểu [300]: ").strip()
    if min_vote.isdigit():
        cfg["anti_seeding_min_votes"] = int(min_vote)
    
    min_rat = input("Điểm đánh giá tối thiểu [6.5]: ").strip()
    try:
        if min_rat:
            cfg["min_rating"] = float(min_rat)
    except ValueError:
        pass

    saved = save_config(cfg)
    print("\n" + "=" * 60)
    print("🎉 Khảo sát hoàn tất! Cấu hình đã được lưu an toàn tại:")
    for p in saved:
        print(f"  📁 {p}")
    print("💡 Giờ bạn có thể chạy: `media-advisor unwatched` hoặc `media-advisor theatrical` để nhận đề xuất!")
    return cfg

if __name__ == "__main__":
    run_survey()
