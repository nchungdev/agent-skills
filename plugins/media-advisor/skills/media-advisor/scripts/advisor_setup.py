#!/usr/bin/env python3
"""
Media Advisor interactive user survey and environment configuration.
Supports 3 Operating Modes:
1. Local Homelab SQLite (Zero-API Plex/Jellyfin read-only)
2. Remote Server API (Plex Token / Jellyfin API Key) with live validation
3. Pure Internet Cinephile (No media server needed, survey-driven & global trends)
"""

import os
import sys
import json
import getpass
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))
from media_server_client import PlexApiClient, JellyfinApiClient, mask_token

DEFAULT_CONFIG = {
    "mode": "auto",                  # "auto", "internet_only", "remote"
    "server_type": "plex",           # "plex" or "jellyfin"
    "plex_db_path": "/home/chungnh/appdata/plex/Library/Application Support/Plex Media Server/Plug-in Support/Databases/com.plexapp.plugins.library.db",
    "jellyfin_db_path": "/home/chungnh/appdata/jellyfin/data/data/jellyfin.db",
    "remote_url": "",
    "remote_token": "",
    "preferred_genres": [],          # Empty = all genres welcome
    "excluded_genres": [],
    "preferred_regions": ["ALL"],     # ALL, US, KR, JP, CN, VN
    "max_duration_minutes": 0,       # 0 = unlimited
    "min_rating": 6.8,               # TMDb / IMDb minimum rating
    "anti_seeding_min_votes": 300,   # Minimum vote count to defeat PR/seeding bots
    "streaming_providers": ["Netflix", "Apple TV+", "HBO Max", "Disney+", "Amazon Prime"],
    "auto_taste_profiling": True
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
    
    if Path.cwd() != Path.home():
        (Path.cwd() / ".agent").mkdir(parents=True, exist_ok=True)
        with open(workspace_cfg, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        saved.append(str(workspace_cfg))

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
        print("⚡ Đang lưu cấu hình mặc định (tự động nhận diện, khách quan, bao quát toàn bộ)...")
        saved = save_config(cfg)
        print(f"✅ Đã lưu cấu hình tại: {', '.join(saved)}")
        return cfg

    # 1. Choose Operating Mode
    print("\n--- 🖥️ CHỌN PHƯƠNG THỨC HOẠT ĐỘNG ---")
    print("1. Tự động (Ưu tiên Plex/Jellyfin trên máy nếu có, nếu không tự chuyển sang Internet) [Mặc định]")
    print("2. Kết nối Remote Server qua API Key / Token (Plex hoặc Jellyfin từ xa)")
    print("3. Chỉ dùng dữ liệu Internet (Không dùng Plex/Jellyfin, khám phá phim rạp & OTT theo gu)")
    mode_opt = input("Chọn chế độ (1-3, Enter = 1): ").strip()

    if mode_opt == "2":
        cfg["mode"] = "remote"
        print("\n--- 📡 CẤU HÌNH KẾT NỐI API KEY TỚI SERVER TỪ XA ---")
        stype = input("Loại máy chủ [1: Plex, 2: Jellyfin] (mặc định 1): ").strip()
        cfg["server_type"] = "jellyfin" if stype == "2" else "plex"

        default_url = "http://127.0.0.1:32400" if cfg["server_type"] == "plex" else "http://127.0.0.1:8096"
        url = input(f"Địa chỉ Server URL [{default_url}]: ").strip() or default_url
        cfg["remote_url"] = url

        existing_token = cfg.get("remote_token")
        if existing_token:
            print(f"Token hiện tại: {mask_token(existing_token)}")
            change = input("Có muốn đổi Token/API Key mới không? (y/N): ").strip().lower()
            if change == "y":
                token = getpass.getpass("Nhập Token / API Key mới (ký tự sẽ ẩn): ").strip()
                if token:
                    cfg["remote_token"] = token
        else:
            token = getpass.getpass(f"Nhập {'Plex Token' if cfg['server_type'] == 'plex' else 'Jellyfin API Key'} (ký tự sẽ ẩn): ").strip()
            cfg["remote_token"] = token

        # Verify API connectivity live!
        print(f"🔍 Đang kiểm tra kết nối API tới {url}...")
        if cfg["server_type"] == "plex":
            client = PlexApiClient(url, cfg["remote_token"])
            if client.verify():
                print(f"✅ Kết nối thành công tới Plex Media Server! Token: {mask_token(cfg['remote_token'])}")
            else:
                print("⚠️ Cảnh báo: Không thể xác thực với Plex Server. Vẫn sẽ lưu cấu hình.")
        else:
            client = JellyfinApiClient(url, cfg["remote_token"])
            if client.verify():
                print(f"✅ Kết nối thành công tới Jellyfin Server! API Key: {mask_token(cfg['remote_token'])}")
            else:
                print("⚠️ Cảnh báo: Không thể xác thực với Jellyfin Server. Vẫn sẽ lưu cấu hình.")

    elif mode_opt == "3":
        cfg["mode"] = "internet_only"
        print("🌐 Đã chọn: Chế độ Internet Toàn Cầu (Pure Cinephile). Bỏ qua hoàn toàn Plex/Jellyfin.")
    else:
        cfg["mode"] = "auto"
        default_plex = cfg.get("plex_db_path", "")
        if os.path.exists(default_plex):
            print(f"🟢 Tìm thấy Local Plex Database: {default_plex}")
        else:
            print("ℹ️ Không tìm thấy Plex Database cục bộ. Sẽ dùng Internet Mode nếu cần.")

    # 2. Taste Survey - Preferred Genres
    print("\n--- 🎬 KHẢO SÁT GU XEM PHIM ---")
    print("1. Tất cả thể loại (Mặc định - Khách quan, tự do)")
    print("2. Ưu tiên: Hành động / Phiêu lưu / Sci-Fi")
    print("3. Ưu tiên: Anime / Hoạt hình Nhật Bản")
    print("4. Ưu tiên: Trinh thám / Giật gân / Tâm lý tội phạm")
    print("5. Ưu tiên: Hài hước / Gia đình / Chữa lành")
    genre_opt = input("Chọn mục (1-5 hoặc nhập tên tự do, Enter bỏ qua): ").strip()
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

    # 3. Excluded Genres
    print("\nBạn có muốn loại trừ thể loại nào không? (ví dụ: Kinh dị, Tình cảm...)")
    exc = input("Thể loại bỏ qua (Enter để không bỏ qua gì): ").strip()
    if exc:
        cfg["excluded_genres"] = [g.strip() for g in exc.split(",")]
    else:
        cfg["excluded_genres"] = []

    # 4. Preferred Region / Language
    print("\n--- 🌍 KHU VỰC & ĐIỆN ẢNH ---")
    print("1. Toàn cầu (Âu Mỹ, Châu Á, v.v. - Mặc định)")
    print("2. Hollywood / Âu Mỹ")
    print("3. Nhật Bản / Anime")
    print("4. Hàn Quốc (K-Drama / K-Movie)")
    print("5. Trung Quốc (C-Drama / Điện ảnh Hoa Ngữ)")
    reg_opt = input("Chọn khu vực (1-5, Enter để chọn Toàn cầu): ").strip()
    region_map = {"1": ["ALL"], "2": ["US", "GB"], "3": ["JP"], "4": ["KR"], "5": ["CN", "HK", "TW"]}
    cfg["preferred_regions"] = region_map.get(reg_opt, ["ALL"])

    # 5. Duration Budget
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

    # 6. Anti-Seeding Filter
    print("\n--- 🛡️ BỘ LỌC CHỐNG SEEDING & ĐÁNH GIÁ ẢO ---")
    print("Mặc định: Phải có tối thiểu 300 lượt đánh giá thực tế và điểm số >= 6.8.")
    min_vote = input("Số lượt đánh giá tối thiểu [300]: ").strip()
    if min_vote.isdigit():
        cfg["anti_seeding_min_votes"] = int(min_vote)
    
    min_rat = input("Điểm đánh giá tối thiểu [6.8]: ").strip()
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
    print("💡 Giờ bạn có thể chạy: `media-advisor report` hoặc `media-advisor discover` để nhận đề xuất!")
    return cfg

if __name__ == "__main__":
    run_survey()
