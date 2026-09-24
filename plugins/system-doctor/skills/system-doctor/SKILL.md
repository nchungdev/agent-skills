---
name: system-doctor
description: Autonomous system optimizer and SRE diagnostic engine (CleanMyMac X meets Site Reliability Engineering). Auto-detects device signatures in 0.1s (macOS, Linux Server/NAS, Workstation) without manual flags to clean OS/developer caches, purge inactive RAM, kill runaway CPU hogs, hunt port conflicts (Aria2, Plex, Prowlarr), inspect Docker crashloops, and execute 1-click auto-healing.
---

# System Doctor (Autonomous System Optimizer & SRE Diagnostics)

Bộ kỹ năng kết hợp giữa tư duy dọn dẹp, tăng tốc của **CleanMyMac X** và năng lực chẩn đoán cấp cứu của **Kỹ sư SRE / Homelab Sysadmin**. Hoạt động đa nền tảng trên macOS, Linux Desktop, Linux Server/NAS và Windows WSL.

---

## ⚡ Tự Động Nhận Diện Thiết Bị (Zero-Config Device Auto-Detection)

Không cần gõ bất kỳ cờ lệnh nào như `--nas` hay `--mac`. Trong **0.1 giây đầu tiên**, `system-doctor` tự động đọc chữ ký hệ thống:
* **macOS (Apple Silicon M-series / Intel)**: Tự kích hoạt module kiểm tra Pin, đo quạt, purge RAM, dọn Xcode `DerivedData`, Homebrew và Application Support leftovers.
* **Linux Media NAS / Homelab Server**: Tự phát hiện MergerFS, OMV và quét ma trận cổng media (`6800`, `9696`, `7878`, `32400`), kiểm tra quyền đọc ghi `1000:1000` và GPU Intel QSV/NVENC.
* **Linux Desktop / Workstation**: Quét nhật ký `journalctl`, package manager cache (npm, pip, cargo, docker).

---

## 🚀 Các Lệnh CLI Cốt Lõi

```bash
# 1. Quét sức khỏe toàn diện 2 tầng (Smart Scan):
python3 <skill_dir>/scripts/doctor.py scan

# 2. Dọn sạch rác hệ thống & developer cache an toàn:
python3 <skill_dir>/scripts/doctor.py clean

# 3. Chẩn đoán và đề xuất đơn thuốc sửa lỗi (Doctor):
python3 <skill_dir>/scripts/doctor.py doctor
```

---

## 🏛️ Hai Tầng Khám Chữa Bệnh

### 🏢 TẦNG 1: HỆ ĐIỀU HÀNH & BỘ NHỚ (Phong cách CleanMyMac X)
* **🧹 Dọn rác Developer & Caches**: Dọn build cache Docker, dangling images, pip, npm, yarn, gradle, và Xcode `DerivedData` (thường giải phóng từ 15GB đến 50GB).
* **⚡ Tối ưu RAM & Bắt tiến trình treo**: Phát hiện các tiến trình ăn 100% CPU liên tục làm nóng máy, giải phóng Inactive RAM.
* **📂 Thợ săn tệp lớn**: Quét tìm các file `.iso`, `.zip`, `.dmg`, video thô bị bỏ quên trong thư mục `Downloads` > 30 ngày.
* **🗑️ Gỡ cài đặt tận gốc**: Quét sạch các file tàn dư (`Application Support`, `Preferences`, `Caches`) sau khi xóa ứng dụng.

---

### 🖥️ TẦNG 2: HẠ TẦNG & DỊCH VỤ HOMELAB (Phong cách SRE Doctor)
* **🔌 Săn xung đột cổng (Port Conflict Hunter)**: Quét toàn bộ các port media: `6800` (Aria2), `9696` (Prowlarr), `7878` (Radarr), `8989` (Sonarr), `32400` (Plex), `8081` (MeTube). Chỉ đích danh PID nếu có xung đột.
* **💾 Phẫu thuật ổ cứng & Mount point**: Phát hiện nếu pool MergerFS bị rụng, kiểm tra cạn kiệt Inode (`df -i`) và sửa lỗi quyền file thuộc `root` làm Docker không ghi được.
* **🐳 Khám nghiệm Docker (Crash Forensics)**: Bắt các container bị `CrashLoopBackOff`, bóc tách log lỗi tìm nguyên nhân gốc rễ (RCA) và dịch sang tiếng Việt.
* **🚀 Kiểm tra GPU Transcode**: Kiểm tra file thiết bị `/dev/dri/renderD128` (Intel QSV) hoặc `nvidia-smi` (NVIDIA NVENC).
* **🔑 Khám API & Cloudflare Tunnel**: Test sống/chết của TMDb API key, TorBox token và kết nối socket của Cloudflare Tunnel.

---

## 🩹 Cơ Chế 1-Click Auto-Heal

Khi Agent phát hiện sự cố, nó xuất bảng chẩn đoán kèm **Đơn Thuốc (Remediation)**. Người dùng chỉ cần gõ `system-doctor clean` hoặc yêu cầu: *"Sửa các lỗi trên giùm tôi"*, Agent sẽ tự động xử lý và kiểm tra lại hệ thống đạt trạng thái 🟢 Healthy 100%.
