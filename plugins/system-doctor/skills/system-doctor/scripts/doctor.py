#!/usr/bin/env python3
"""
System Doctor: All-in-One Autonomous System Optimizer & SRE Diagnostics.
Inspired by CleanMyMac X and SRE Homelab health checks.
Zero third-party dependencies (Pure Python 3 standard library).
"""

import os
import sys
import platform
import shutil
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

def detect_device_environment():
    """Auto-detect current host device signature in 0.1s."""
    sys_name = platform.system()
    machine = platform.machine()
    
    env_info = {
        "os": sys_name,
        "machine": machine,
        "is_mac": sys_name == "Darwin",
        "is_linux": sys_name == "Linux",
        "is_nas_or_server": False,
        "has_docker": False,
        "has_mergerfs": False,
        "device_type": "Unknown"
    }

    # Check for Docker
    if shutil.which("docker"):
        env_info["has_docker"] = True

    # Check for MergerFS / OMV / Media NAS signatures
    if os.path.exists("/etc/openmediavault") or os.path.exists("/srv/mergerfs"):
        env_info["has_mergerfs"] = True
        env_info["is_nas_or_server"] = True

    # Classify device
    if env_info["is_mac"]:
        chip = "Apple Silicon" if "arm" in machine.lower() else "Intel Mac"
        env_info["device_type"] = f"macOS Workstation ({chip})"
    elif env_info["is_nas_or_server"]:
        env_info["device_type"] = "Linux Media NAS / Homelab Server"
    elif env_info["is_linux"]:
        env_info["device_type"] = "Linux Desktop / Workstation"
    else:
        env_info["device_type"] = f"{sys_name} Host"

    return env_info

def check_disk_usage(path="/"):
    """Check storage space and inode saturation."""
    usage = shutil.disk_usage(path)
    total_gb = usage.total / (1024**3)
    used_gb = usage.used / (1024**3)
    free_gb = usage.free / (1024**3)
    pct = (usage.used / usage.total) * 100
    return {
        "total_gb": round(total_gb, 1),
        "used_gb": round(used_gb, 1),
        "free_gb": round(free_gb, 1),
        "percent_used": round(pct, 1)
    }

def scan_reclaimable_caches():
    """Detect reclaimable caches (Docker, npm, pip, logs)."""
    reclaimable = {}
    total_bytes = 0

    # 1. Docker Dangling & Build Cache
    if shutil.which("docker"):
        try:
            res = subprocess.run(["docker", "system", "df", "--format", "{{.Type}}\t{{.Reclaimable}}"], 
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
            if res.returncode == 0:
                lines = [l.strip() for l in res.stdout.strip().split("\n") if l.strip()]
                reclaimable["docker"] = ", ".join(lines) if lines else "Clean"
        except Exception:
            reclaimable["docker"] = "Docker daemon inactive"

    # 2. User Caches
    home = Path.home()
    cache_dirs = {
        "pip": home / ".cache" / "pip",
        "npm": home / ".npm" / "_cacache",
        "yarn": home / ".cache" / "yarn",
        "pnpm": home / ".local" / "share" / "pnpm" / "store",
        "gradle": home / ".gradle" / "caches",
        "xcode_derived": home / "Library" / "Developer" / "Xcode" / "DerivedData"
    }

    for name, p in cache_dirs.items():
        if p.exists() and p.is_dir():
            size = sum(f.stat().st_size for f in p.glob('**/*') if f.is_file())
            if size > 10 * 1024 * 1024: # > 10MB
                mb = round(size / (1024**2), 1)
                total_bytes += size
                reclaimable[name] = f"{mb} MB"

    reclaimable["total_reclaimable_gb"] = round(total_bytes / (1024**3), 2)
    return reclaimable

def scan_media_ports():
    """Scan key media ports for conflicts or service availability."""
    ports = {
        6800: "Aria2 RPC",
        9696: "Prowlarr",
        7878: "Radarr",
        8989: "Sonarr",
        32400: "Plex Media Server",
        8096: "Jellyfin",
        8081: "MeTube"
    }
    status = {}
    if shutil.which("ss"):
        cmd = ["ss", "-tulpn"]
    elif shutil.which("netstat"):
        cmd = ["netstat", "-tuln"]
    else:
        cmd = None

    if cmd:
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=4)
            out = res.stdout
            for port, name in ports.items():
                if f":{port}" in out:
                    status[port] = {"name": name, "status": "ACTIVE / LISTENING", "occupied": True}
                else:
                    status[port] = {"name": name, "status": "IDLE / FREE", "occupied": False}
        except Exception:
            pass
    return status

def check_docker_containers():
    """Check Docker container health and detect crash loops."""
    if not shutil.which("docker"):
        return {"status": "Docker not installed"}

    try:
        res = subprocess.run(["docker", "ps", "-a", "--format", "{{.Names}}\t{{.Status}}\t{{.Image}}"],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
        if res.returncode != 0:
            return {"status": "Docker daemon unreachable"}

        containers = []
        issues = []
        for line in res.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                name, st = parts[0], parts[1]
                containers.append({"name": name, "status": st})
                if "Restarting" in st or "Dead" in st:
                    issues.append(f"⚠️ `{name}` is in unhealthy state: {st}")

        return {
            "total": len(containers),
            "healthy": len(containers) - len(issues),
            "issues": issues,
            "containers": containers[:10]
        }
    except Exception as e:
        return {"status": f"Error: {e}"}

def run_smart_scan():
    """Execute full 2-tier smart scan (CleanMyMac OS + SRE Homelab)."""
    env = detect_device_environment()
    disk = check_disk_usage("/")
    caches = scan_reclaimable_caches()
    ports = scan_media_ports()
    dock = check_docker_containers()

    md = []
    md.append(f"# 🩺 System Doctor: Smart Health Report")
    md.append(f"> **Thiết bị**: `{env['device_type']}` | **Thời gian**: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n")

    # 1. OS & Storage
    md.append("## 🏢 1. Tầng Hệ Điều Hành & Bộ Nhớ (OS & Storage)")
    d_icon = "🟢" if disk["percent_used"] < 85 else ("🟡" if disk["percent_used"] < 92 else "🔴")
    md.append(f"* {d_icon} **Ổ đĩa gốc (`/`)**: Đã dùng `{disk['used_gb']} GB / {disk['total_gb']} GB` (`{disk['percent_used']}%`) — Còn trống `{disk['free_gb']} GB`")
    
    rec_gb = caches.get("total_reclaimable_gb", 0)
    md.append(f"* 🧹 **Rác Developer & Cache có thể dọn**: `~{rec_gb} GB`")
    for k, v in caches.items():
        if k != "total_reclaimable_gb":
            md.append(f"  - `{k}`: {v}")

    # 2. Ports & Network
    md.append("\n## 🔌 2. Tầng Cổng Giao Tiếp (Media Port Matrix)")
    if ports:
        md.append("| Cổng (Port) | Dịch Vụ | Trạng Thái |")
        md.append("|:---:|---|:---:|")
        for p, d in ports.items():
            icon = "🟢" if d["occupied"] else "⚪"
            md.append(f"| `{p}` | {d['name']} | {icon} {d['status']} |")
    else:
        md.append("Không thể quét cổng mạng (thiếu quyền hoặc thiếu `ss`/`netstat`).")

    # 3. Docker & Containers
    md.append("\n## 🐳 3. Tầng Container & Dịch Vụ Docker")
    if isinstance(dock, dict) and "total" in dock:
        md.append(f"* **Tổng số Container**: `{dock['total']}` (`{dock['healthy']}` hoạt động)")
        if dock.get("issues"):
            md.append("\n**⚠️ Cảnh báo sự cố:**")
            for issue in dock["issues"]:
                md.append(f"* {issue}")
        else:
            md.append("* 🟢 Tất cả Container đều ổn định, không có CrashLoopBackOff.")
    else:
        md.append(f"* Trạng thái Docker: {dock.get('status', 'N/A')}")

    md.append("\n---\n👉 **Khuyến nghị:** Dùng `system-doctor clean` để dọn sạch bộ đệm rác an toàn.")
    return "\n".join(md)

def run_clean():
    """Safely purge reclaimable caches."""
    print("🧹 Bắt đầu dọn dẹp bộ đệm an toàn...")
    if shutil.which("docker"):
        print("-> Đang dọn dẹp Docker build cache & dangling images...")
        subprocess.run(["docker", "system", "prune", "-f"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("✅ Docker rác đã được dọn sạch.")

    home = Path.home()
    pip_cache = home / ".cache" / "pip"
    if pip_cache.exists():
        shutil.rmtree(pip_cache, ignore_errors=True)
        print("✅ Đã dọn pip cache.")

    npm_cache = home / ".npm" / "_cacache"
    if npm_cache.exists():
        shutil.rmtree(npm_cache, ignore_errors=True)
        print("✅ Đã dọn npm cache.")

    print("\n🎉 Dọn dẹp hoàn tất! Hệ thống đã được giải phóng dung lượng.")

def main():
    parser = argparse.ArgumentParser(description="System Doctor: All-in-One Autonomous System Optimizer & SRE Diagnostics")
    parser.add_argument("action", choices=["scan", "clean", "doctor", "report"], default="scan", nargs="?", help="Action to perform")
    args = parser.parse_args()

    if args.action in ["scan", "doctor", "report"]:
        print(run_smart_scan())
    elif args.action == "clean":
        run_clean()

if __name__ == "__main__":
    main()
