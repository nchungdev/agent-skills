#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity Media Hub & Command Center HTTP Server
Serves Web UI on port 8888 and provides REST APIs for live monitoring and command dispatch.
"""

import os
import sys
import json
import time
import shutil
import urllib.parse
import subprocess
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

# Import Core Modules
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from core.torbox_manager import TorBoxManager
from core.monitor import PipelineMonitor
from core.gdrive_manager import GDriveManager
from core.agent_bridge import AgentBridge

# Initialize Core Managers
torbox_mgr = TorBoxManager()
pipeline_mon = PipelineMonitor()
gdrive_mgr = GDriveManager()
agent_bridge = AgentBridge()

CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
config = {"port": 8888, "host": "0.0.0.0"}
if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config.update(json.load(f))
    except Exception:
        pass

PORT = int(config.get("port", 8888))
HOST = str(config.get("host", "0.0.0.0"))

def load_unified_settings():
    """Load unified configuration from environment, ~/.env, and settings.json."""
    settings_path = Path.home() / ".gemini" / "config" / "media_hub_settings.json"
    env_file = Path.home() / ".env"
    
    env_dict = {}
    if env_file.is_file():
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        env_dict[k.strip()] = v.strip().strip('"').strip("'")
        except Exception:
            pass

    cfg = {
        "default_provider": "torbox",
        "max_concurrent_downloads": 2,
        "staging_dir": "/Volumes/512GB/AI Workspace/media_staging",
        "torbox_token": os.environ.get("TORBOX_API_TOKEN") or env_dict.get("TORBOX_API_TOKEN") or env_dict.get("TORBOX_TOKEN") or "",
        "tmdb_api_key": os.environ.get("TMDB_API_KEY") or env_dict.get("TMDB_API_KEY") or "",
        "aria2_rpc_host": "127.0.0.1",
        "aria2_rpc_port": 6800,
        "aria2_rpc_secret": "",
        "nas_host": "",
        "nas_user": "admin",
        "nas_port": 22,
        "nas_path": "/volume1/video/TV Shows",
        "gdrive_remote": "gdrive",
        "gdrive_root": "Phim/TV Shows",
        "sync_targets": ["drive"],
        "sync_transfers": 4,
        "auto_purge": True
    }

    if settings_path.is_file():
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                saved = json.load(f)
                cfg.update(saved)
        except Exception:
            pass

    # Fallback to env if empty
    if not cfg.get("torbox_token"):
        cfg["torbox_token"] = os.environ.get("TORBOX_API_TOKEN") or env_dict.get("TORBOX_API_TOKEN") or env_dict.get("TORBOX_TOKEN") or ""
    if not cfg.get("tmdb_api_key"):
        cfg["tmdb_api_key"] = os.environ.get("TMDB_API_KEY") or env_dict.get("TMDB_API_KEY") or ""

    return cfg

class MediaHubHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _send_html(self, html_content, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html_content.encode("utf-8"))

    def do_HEAD(self):
        self.do_GET()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        # 1. Web UI Root
        if path == "/" or path == "/index.html":
            candidate_paths = [
                os.path.join(BASE_DIR, "templates", "index.html"),
                os.path.join(os.path.dirname(BASE_DIR), "templates", "index.html"),
                "/Volumes/512GB/AI Workspace/antigravity-media-hub/templates/index.html"
            ]
            for tp in candidate_paths:
                if os.path.exists(tp):
                    with open(tp, "r", encoding="utf-8") as f:
                        return self._send_html(f.read())
            return self._send_html("<h1>Antigravity Media Hub</h1><p>Template missing.</p>", status=404)

        # 1.1 Static Assets Routing (/static/...)
        elif path.startswith("/static/"):
            file_rel = path.lstrip("/")
            file_path = os.path.join(BASE_DIR, file_rel)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                content_type = "image/jpeg"
                if file_path.endswith(".png"): content_type = "image/png"
                elif file_path.endswith(".svg"): content_type = "image/svg+xml"
                elif file_path.endswith(".css"): content_type = "text/css"
                elif file_path.endswith(".js"): content_type = "application/javascript"
                with open(file_path, "rb") as f:
                    data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Cache-Control", "public, max-age=86400")
                self.end_headers()
                self.wfile.write(data)
                return
            return self.send_error(404, "Static file not found")

        # 2. REST API: TorBox List
        elif path == "/api/torbox":
            res = torbox_mgr.list_torrents()
            return self._send_json(res)

        # 2.1 REST API: TorBox Download Link
        elif path == "/api/torbox/download_link":
            query_params = urllib.parse.parse_qs(parsed_url.query)
            t_id = query_params.get("id", [""])[0]
            if not t_id:
                return self._send_json({"success": False, "error": "Missing id parameter"})
            res = torbox_mgr.request_download_link(t_id)
            return self._send_json(res)

        # 3. REST API: Live Pipelines Status
        elif path == "/api/pipelines":
            monster = pipeline_mon.get_monster_status()
            multi = pipeline_mon.get_multi_show_status()
            lib_ver = f"M:{monster.get('completed_eps',0)}_MS:{multi.get('current_show','')}:{multi.get('completed_eps',0)}_{gdrive_mgr.get_cache_version()}"
            return self._send_json({"monster": monster, "multi_show": multi, "library_version": lib_ver})

        # 4. REST API: GDrive Shows List
        elif path == "/api/gdrive/shows":
            query_params = urllib.parse.parse_qs(parsed_url.query)
            refresh = query_params.get("refresh", ["0"])[0].lower() in ["1", "true"]
            shows = gdrive_mgr.list_tv_shows(force_refresh=refresh)
            return self._send_json({"shows": shows})

        # 4.1 REST API: GDrive Season Files
        elif path == "/api/gdrive/season_files":
            query_params = urllib.parse.parse_qs(parsed_url.query)
            show = query_params.get("show", [""])[0]
            season = query_params.get("season", [""])[0]
            refresh = query_params.get("refresh", ["0"])[0].lower() in ["1", "true"]
            if not show or not season:
                return self._send_json({"files": []})
            files = gdrive_mgr.get_season_files(show, season, force_refresh=refresh)
            return self._send_json({"files": files})

        # 4.15 REST API: Generate M3U Playlist file for VLC / IINA
        elif path == "/api/playlist.m3u":
            query_params = urllib.parse.parse_qs(parsed_url.query)
            show = query_params.get("show", [""])[0]
            season = query_params.get("season", [""])[0]
            filename = query_params.get("file", [""])[0]
            host = self.headers.get("Host", f"{HOST}:{PORT}")
            proto = "https" if ("trycloudflare" in host or self.headers.get("X-Forwarded-Proto") == "https") else "http"
            
            stream_url = f"{proto}://{host}/api/stream?show={urllib.parse.quote(show)}&season={urllib.parse.quote(season)}&file={urllib.parse.quote(filename)}"
            m3u_content = f"#EXTM3U\n#EXTINF:-1,{filename}\n{stream_url}\n"
            
            self.send_response(200)
            self.send_header("Content-Type", "audio/x-mpegurl; charset=utf-8")
            self.send_header("Content-Disposition", f'attachment; filename="{filename}.m3u"')
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(m3u_content.encode("utf-8"))
            return

        # 4.2 Streaming & Direct Download (/api/stream, /api/download)
        elif path == "/api/stream" or path == "/api/download":
            query_params = urllib.parse.parse_qs(parsed_url.query)
            show = query_params.get("show", [""])[0]
            season = query_params.get("season", [""])[0]
            filename = query_params.get("file", [""])[0]

            if not show or not season or not filename:
                return self.send_error(400, "Missing show, season, or file parameter")

            gdrive_path = f"gdrive:Phim/TV Shows/{show}/{season}/{filename}"
            is_download = (path == "/api/download")
            
            content_type = "video/mp4"
            if filename.endswith(".mkv"): content_type = "video/x-matroska"
            elif filename.endswith(".avi"): content_type = "video/x-msvideo"
            elif filename.endswith(".ass") or filename.endswith(".srt"): content_type = "text/plain; charset=utf-8"

            buffer_mb = 32
            try: buffer_mb = max(4, min(512, int(query_params.get("buffer_mb", ["32"])[0])))
            except Exception: pass

            chunk_size = 256 * 1024
            try:
                chunk_kb = int(query_params.get("chunk_kb", ["256"])[0])
                chunk_size = max(64, min(4096, chunk_kb)) * 1024
            except Exception: pass

            # If web streaming an MKV file, remux/transcode to fragmented MP4 for 100% HTML5 browser compatibility
            if not is_download and (filename.endswith(".mkv") or filename.endswith(".avi")):
                self.send_response(200)
                self.send_header("Content-Type", "video/mp4")
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Disposition", f'inline; filename="{filename}.mp4"')
                self.end_headers()

                rclone_proc = subprocess.Popen([
                    gdrive_mgr.rclone_bin,
                    "--config", gdrive_mgr.rclone_config,
                    f"--buffer-size={buffer_mb}M",
                    "cat", gdrive_path
                ], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

                ffmpeg_bin = "/opt/homebrew/bin/ffmpeg" if os.path.exists("/opt/homebrew/bin/ffmpeg") else "ffmpeg"
                ffmpeg_cmd = [
                    ffmpeg_bin,
                    "-loglevel", "error",
                    "-i", "pipe:0",
                    "-c:v", "libx264",
                    "-preset", "ultrafast",
                    "-tune", "zerolatency",
                    "-pix_fmt", "yuv420p",
                    "-crf", "22",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-movflags", "frag_keyframe+empty_moov+default_base_moof",
                    "-f", "mp4",
                    "pipe:1"
                ]

                ff_proc = subprocess.Popen(ffmpeg_cmd, stdin=rclone_proc.stdout, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                rclone_proc.stdout.close()
                
                try:
                    while True:
                        chunk = ff_proc.stdout.read(chunk_size)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                except Exception:
                    pass
                finally:
                    ff_proc.terminate()
                    rclone_proc.terminate()
                    try: ff_proc.wait(timeout=1)
                    except Exception: ff_proc.kill()
                    try: rclone_proc.wait(timeout=1)
                    except Exception: rclone_proc.kill()
                return

            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Access-Control-Allow-Origin", "*")
            if is_download:
                self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            else:
                self.send_header("Content-Disposition", f'inline; filename="{filename}"')
            self.end_headers()

            rclone_cmd = [
                gdrive_mgr.rclone_bin,
                "--config", gdrive_mgr.rclone_config,
                f"--buffer-size={buffer_mb}M",
                "cat", gdrive_path
            ]
            
            proc = subprocess.Popen(rclone_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            try:
                while True:
                    chunk = proc.stdout.read(chunk_size)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
            except Exception:
                pass
            finally:
                proc.terminate()
                try: proc.wait(timeout=1)
                except Exception: proc.kill()
            return

        # 4.3 REST API: Subtitles List (/api/subtitles)
        elif path == "/api/subtitles":
            query_params = urllib.parse.parse_qs(parsed_url.query)
            show = query_params.get("show", [""])[0]
            season = query_params.get("season", [""])[0]
            filename = query_params.get("file", [""])[0]

            if not show or not season or not filename:
                return self._send_json({"subtitles": []})

            all_files = gdrive_mgr.get_season_files(show, season)
            base_name = os.path.splitext(filename)[0]
            
            subtitles = []
            
            # 1. Look for External / Standalone Subtitles (.ass, .srt, .vtt)
            for f in all_files:
                if (f.endswith(".ass") or f.endswith(".srt") or f.endswith(".vtt")) and (f.startswith(base_name) or base_name.startswith(os.path.splitext(f)[0])):
                    lang = "Phụ đề"
                    f_lower = f.lower()
                    if ".vi." in f_lower or "vietsub" in f_lower or ".vie." in f_lower or ".vn." in f_lower:
                        lang = "🇻🇳 Tiếng Việt"
                    elif ".en." in f_lower or ".eng." in f_lower:
                        lang = "🇬🇧 Tiếng Anh (English)"
                    elif ".ja." in f_lower or ".jpn." in f_lower or ".jap." in f_lower:
                        lang = "🇯🇵 Tiếng Nhật (Japanese)"
                    elif ".zh." in f_lower or ".chi." in f_lower:
                        lang = "🇨🇳 Tiếng Trung"
                    else:
                        lang = f"📄 {os.path.splitext(f)[1].upper().replace('.', '')}"

                    subtitles.append({
                        "type": "external",
                        "label": f"{lang} (File rời)",
                        "file": f,
                        "url": f"/api/subtitle/vtt?show={urllib.parse.quote(show)}&season={urllib.parse.quote(season)}&sub={urllib.parse.quote(f)}"
                    })

            # 2. Add Muxed Subtitle option for MKV files
            if filename.endswith(".mkv"):
                subtitles.append({
                    "type": "muxed",
                    "label": "📦 Phụ đề tích hợp sẵn (Muxed Track 1)",
                    "track_index": 0,
                    "url": f"/api/subtitle/vtt?show={urllib.parse.quote(show)}&season={urllib.parse.quote(season)}&file={urllib.parse.quote(filename)}&muxed=1&track=0"
                })

            return self._send_json({"subtitles": subtitles})

        # 4.4 REST API: Serve Subtitle as WebVTT (/api/subtitle/vtt)
        elif path == "/api/subtitle/vtt":
            query_params = urllib.parse.parse_qs(parsed_url.query)
            show = query_params.get("show", [""])[0]
            season = query_params.get("season", [""])[0]
            sub_file = query_params.get("sub", [""])[0]
            is_muxed = query_params.get("muxed", ["0"])[0] == "1"
            video_file = query_params.get("file", [""])[0]
            track_id = query_params.get("track", ["0"])[0]

            self.send_response(200)
            self.send_header("Content-Type", "text/vtt; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            ffmpeg_bin = "/opt/homebrew/bin/ffmpeg" if os.path.exists("/opt/homebrew/bin/ffmpeg") else "ffmpeg"

            if is_muxed and video_file:
                # Extract muxed subtitle track from MKV
                gdrive_path = f"gdrive:Phim/TV Shows/{show}/{season}/{video_file}"
                rclone_proc = subprocess.Popen([
                    gdrive_mgr.rclone_bin, "--config", gdrive_mgr.rclone_config, "cat", gdrive_path
                ], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

                ff_proc = subprocess.Popen([
                    ffmpeg_bin, "-loglevel", "error", "-i", "pipe:0", "-map", f"0:s:{track_id}", "-f", "webvtt", "pipe:1"
                ], stdin=rclone_proc.stdout, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                rclone_proc.stdout.close()
                
                try:
                    out, _ = ff_proc.communicate(timeout=10)
                    self.wfile.write(out if out else b"WEBVTT\n\n")
                except Exception:
                    self.wfile.write(b"WEBVTT\n\n")
                finally:
                    ff_proc.kill()
                    rclone_proc.kill()
                return
            elif sub_file:
                # Convert external ASS/SRT file to WebVTT
                gdrive_path = f"gdrive:Phim/TV Shows/{show}/{season}/{sub_file}"
                rclone_proc = subprocess.Popen([
                    gdrive_mgr.rclone_bin, "--config", gdrive_mgr.rclone_config, "cat", gdrive_path
                ], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

                ff_proc = subprocess.Popen([
                    ffmpeg_bin, "-loglevel", "error", "-i", "pipe:0", "-f", "webvtt", "pipe:1"
                ], stdin=rclone_proc.stdout, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                rclone_proc.stdout.close()
                
                try:
                    out, _ = ff_proc.communicate(timeout=10)
                    self.wfile.write(out if out else b"WEBVTT\n\n")
                except Exception:
                    self.wfile.write(b"WEBVTT\n\n")
                finally:
                    ff_proc.kill()
                    rclone_proc.kill()
                return
            else:
                self.wfile.write(b"WEBVTT\n\n")
                return

        # 5. REST API: Agent Command Queue
        elif path == "/api/agent/queue":
            queue = agent_bridge.list_commands()
            return self._send_json(queue)

        # 6. REST API: Media Hub Settings (/api/settings)
        elif path == "/api/settings":
            cfg = load_unified_settings()
            return self._send_json(cfg)

        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        
        try:
            req_data = json.loads(body)
        except Exception:
            req_data = {}

        # 1. API: Add Magnet
        if path == "/api/torbox/add":
            magnet = req_data.get("magnet")
            if not magnet:
                return self._send_json({"success": False, "error": "Missing magnet link"}, status=400)
            res = torbox_mgr.add_magnet(magnet)
            return self._send_json(res)

        # 2. API: Delete Torrent
        elif path == "/api/torbox/delete":
            torrent_id = req_data.get("id")
            if not torrent_id:
                return self._send_json({"success": False, "error": "Missing torrent ID"}, status=400)
            res = torbox_mgr.delete_torrent(torrent_id)
            return self._send_json(res)

        # 2.1 API: Control Queued Download (Start / Delete)
        elif path == "/api/torbox/control_queued":
            queued_id = req_data.get("id")
            op = req_data.get("operation", "start")
            if not queued_id:
                return self._send_json({"success": False, "error": "Missing queued ID"}, status=400)
            res = torbox_mgr.control_queued(queued_id, operation=op)
            return self._send_json(res)

        # 3. API: Send Agent Command
        elif path == "/api/agent/command":
            cmd = req_data.get("command")
            if not cmd:
                return self._send_json({"success": False, "error": "Empty command"}, status=400)
            item = agent_bridge.add_command(cmd)
            return self._send_json({"success": True, "command": item})

        # 4. API: Save Media Hub Settings (/api/settings)
        elif path == "/api/settings":
            settings_path = Path.home() / ".gemini" / "config" / "media_hub_settings.json"
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                with open(settings_path, "w", encoding="utf-8") as f:
                    json.dump(req_data, f, indent=2, ensure_ascii=False)
                return self._send_json({"success": True, "message": "Đã lưu cài đặt thành công!"})
            except Exception as e:
                return self._send_json({"success": False, "error": str(e)}, status=500)

        # 5. API: Scan NAS Plex Directories (/api/nas/scan)
        elif path == "/api/nas/scan":
            host = req_data.get("host")
            user = req_data.get("user", "admin")
            port = int(req_data.get("port", 22))
            if not host:
                return self._send_json({"success": False, "error": "Thiếu địa chỉ IP NAS"}, status=400)
            
            common_nas_paths = [
                "/volume1/video/TV Shows", "/volume1/video/Movies",
                "/volume1/Media", "/volume1/Plex",
                "/share/CACHEDEV1_DATA/Multimedia/TV Shows",
                "/share/Multimedia/Plex", "/srv/media"
            ]
            ssh_cmd = ["ssh", "-p", str(port), "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", f"{user}@{host}"]
            remote_script = f"for p in {' '.join(common_nas_paths)}; do if [ -d \"$p\" ]; then echo \"FOUND:$p\"; fi; done"
            
            try:
                res = subprocess.run(ssh_cmd + [remote_script], capture_output=True, text=True, timeout=8)
                found = [line.split(":", 1)[1].strip() for line in res.stdout.splitlines() if line.startswith("FOUND:")]
                return self._send_json({"success": True, "libraries": found})
            except Exception as e:
                return self._send_json({"success": False, "error": f"Không thể kết nối SSH tới NAS: {e}"})

        # 6. API: Check Google Drive Connection (/api/gdrive/check)
        elif path == "/api/gdrive/check":
            remote = req_data.get("remote", "gdrive")
            root = req_data.get("root", "Phim/TV Shows")
            rclone_bin = shutil.which("rclone") or "/opt/homebrew/bin/rclone"
            cmd = [rclone_bin, "lsd", f"{remote}:{root.lstrip('/')}"]
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if res.returncode == 0:
                    return self._send_json({"success": True, "message": f"Kết nối tới {remote}:{root} thành công!"})
                else:
                    return self._send_json({"success": False, "error": res.stderr.strip() or "Lỗi kết nối Rclone"})
            except Exception as e:
                return self._send_json({"success": False, "error": str(e)})

        else:
            self.send_error(404, "Not Found")

def run_server():
    server_address = (HOST, PORT)
    httpd = ThreadingHTTPServer(server_address, MediaHubHandler)
    print("=" * 80)
    print(f"🚀 ANTIGRAVITY MEDIA HUB SERVER IS LIVE ON PORT {PORT}")
    print(f"👉 Local Access: http://localhost:{PORT}")
    print(f"👉 LAN Network:  http://0.0.0.0:{PORT}")
    print("=" * 80)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Media Hub Server...")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
