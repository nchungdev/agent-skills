---
name: distributed-infra
description: Comprehensive self-hosted infrastructure and distributed compute manager. Operates OpenMediaVault 7 NAS architectures, MergerFS storage pools, Docker Compose media automation pipelines, distributed hardware-accelerated Tdarr transcoding nodes, and ephemeral Cloudflare Tunnel (cloudflared) docker integrations with masked token injection.
---

# Distributed Infrastructure & Homelab Operations Skill

Bộ kỹ năng quản trị hạ tầng máy chủ gia đình (Homelab/NAS), cụm Docker Compose và điều phối các trạm tính toán phân tán (Distributed Transcode Nodes).

---

## 🚀 Các Lệnh CLI Cốt Lõi

```bash
# 1. Báo cáo sức khỏe hạ tầng (Infra Report):
python3 <skill_dir>/scripts/infra_cli.py report

# 2. Khởi chạy / Kiểm tra Tdarr Node trên máy cá nhân (Mac/Linux Worker):
python3 <skill_dir>/scripts/node_manager.py start --server-ip "<nas-ip>" --node-name "MacBook-M2"

# 3. Quản trị Docker Compose từ xa trên NAS qua SSH:
ssh user@nas "docker compose -f /srv/docker/docker-compose.yml ps"
ssh user@nas "docker compose -f /srv/docker/docker-compose.yml restart plex"

# 4. Kiểm tra sức khỏe ổ đĩa MergerFS:
ssh user@nas "df -h /srv/mergerfs/MainPool && ls -la /srv/mergerfs/MainPool/Phim"
```

---

## 🚇 1. Cloudflare Tunnel (`cloudflared`) Cho Bất Kỳ Docker Compose Nào

Khi cần đưa các dịch vụ nội bộ (Plex, MeTube, AriaNg, Dashboard) ra internet mà không mở port modem:
1. Người dùng chỉ cần cung cấp token: `eyJh...`
2. Agent tự động chèn service `cloudflared` vào file `docker-compose.yml` bạn chỉ định:
   ```yaml
   cloudflared:
     image: cloudflare/cloudflared:latest
     container_name: cloudflared
     restart: unless-stopped
     command: tunnel --no-autoupdate run --token <TOKEN_DA_MASK>
   ```
3. **Bảo mật tuyệt đối (Masking)**: Trong toàn bộ tin nhắn chat và log terminal, token sẽ được che giấu thành `tunnel --no-autoupdate run --token [REDACTED_CLOUDFLARE_TOKEN]`. Không lưu token vào bất kỳ cơ sở dữ liệu hay sổ cái nào.

---

## 🍏 2. Triển Khai Cụm Transcode Tdarr Node Phân Tán

Tận dụng GPU máy cá nhân (ví dụ Apple Silicon M-series hoặc card NVIDIA) làm Worker Node giải tải cho CPU máy chủ NAS:
* **macOS (VideoToolbox)**: Tận dụng phần cứng HEVC phần cứng cực mạnh trên chip Apple Silicon.
* **Linux (Intel QSV / NVIDIA NVENC)**: Sử dụng `/dev/dri` hoặc `nvidia-container-toolkit`.
* **Path Translators**: Cấu hình ánh xạ thư mục chống lỗi `ENOENT` giữa client và NAS server.

---

## 📊 3. Định Dạng Báo Cáo: `distributed-infra report`

```markdown
### 📊 Báo Cáo Sức Khỏe Hạ Tầng (Infrastructure Dashboard)
> **Thiết bị**: OpenMediaVault 7 NAS (`192.168.1.50`) | **Uptime**: `14 ngày`

| Thành Phần | Hiện Trạng | Tài Nguyên / Chi Tiết |
|---|:---:|---|
| 💾 **MergerFS Pool** | 🟢 Healthy | Đã dùng: `6.6 TB / 8.0 TB` (Còn trống `1.4 TB`) |
| 🐳 **Docker Media Stack** | 🟢 8/8 Running | Plex, Sonarr, Radarr, Prowlarr, Aria2, MeTube |
| 🚀 **Tdarr Cluster** | 🟢 2 Nodes Online | Master (NAS) + Worker Node (MacBook-M2 VideoToolbox) |
| 🚇 **Cloudflare Tunnel** | 🟢 Connected | Socket Active (0 lỗi kết nối) |
```
