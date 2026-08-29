---
name: translate-subtitle
description: Dịch phụ đề phim chuyên sâu. Hỗ trợ đa cơ sở dữ liệu định danh (TMDb ID, TheTVDB ID, IMDb ID). Tích hợp kho glossary dài hạn, quy tắc theo thể loại phim (Genres), và lệnh fetch tự động từ kho cộng đồng GitHub nchungdev/subtitle-glossary-hub.
---

# Translate Subtitle Skill

Kỹ năng dịch phụ đề chuyên nghiệp, tích hợp kho trí tuệ thuật ngữ cộng đồng mở (Open-Source Community Hub).

## 🚀 Kích Hoạt & Lệnh Fetch Kho Cộng Đồng

### 1. Dịch Phim:
`translate-subtitle <tên_phim/tmdbid/tvdbid/imdbid> <đường_dẫn_subtitle> <ngôn_ngữ_đích>`

### 2. Tự Động Cập Nhật Kho Thuật Ngữ Cộng Đồng:
`python3 <skill_dir>/scripts/fetch_hub.py --all`
* Kéo toàn bộ **Quy tắc Thể loại (Genres)** và **Glossary từng phim (Franchises)** từ kho mở:
  👉 [github.com/nchungdev/subtitle-glossary-hub](https://github.com/nchungdev/subtitle-glossary-hub)

---

## 🏛️ CẤU TRÚC KHO TẬP TRUNG (COMMUNITY HUB ARCHITECTURE)

```text
resources/
├── MASTER_INDEX.json                  # Bộ giải mã ID đa năng (TMDb / TheTVDB / Aliases)
├── genres/                            # 1. QUY TẮC & STYLE THEO THỂ LOẠI
│   ├── mecha-robot/                   # Anime Mecha / Siêu Robot (Karaoke 2 lớp, Romaji)
│   ├── detective-mystery/             # Trinh thám / Hình sự (Pháp y, chứng cứ ngoại phạm)
│   ├── medical-drama/                 # Y khoa / Phẫu thuật (Giải phẫu, phẫu thuật)
│   ├── xianxia-wuxia-historical/      # Cổ trang / Tiên hiệp (Xưng hô Hán-Việt, pháp bảo)
│   └── slice-of-life-folklore/        # Đời thường / Huyền bí (Văn phong triết lý)
│
└── glossaries/                        # 2. BẢNG THUẬT NGỮ THEO TỪNG TÁC PHẨM
    ├── Black_Jack_{tvdb-78864}/       # TV Series
    ├── Black_Jack_The_Movie_1996_{tmdb-54378}/ # Movie
    └── Mashin_Hero_Wataru_{tvdb-227501}/
        ├── glossary.json              # Bộ nhớ dài hạn nhân vật, xưng hô
        ├── ERRORS_AND_PITFALLS.md     # Nhật ký cạm bẫy thực chiến đã sửa
        ├── AUDIT_REPORT.md            # Báo cáo kiểm định toàn vẹn
        ├── WORKFLOW.md                # Quy trình dịch chi tiết
        └── metadata.json
```

---

# PHẦN A — LÕI CHUNG & QUY CHUẨN DỊCH THUẬT

1. **Khởi tạo & Nạp Dữ Liệu:**
   * Tự động tra cứu ID và nạp `glossary.json` + `ERRORS_AND_PITFALLS.md` của phim.
   * Nạp tiếp quy tắc thể loại tương ứng từ `genres/<the_loai>/rules.md`.
2. **Kiểm Định Toàn Vẹn & Xuất Bản:**
   * Đối chiếu 3 chiều: `Gốc ↔ Trung gian ↔ Tiếng Việt`.
   * Đặt tên chuẩn Plex/Jellyfin: `<Tên Phim> - S01E01.vi.ass` & `.vi.srt`.
3. **Bồi Đắp Vĩnh Viễn:**
   * Ghi nhận lỗi mới vào `ERRORS_AND_PITFALLS.md` để đóng góp ngược lại kho cộng đồng.
