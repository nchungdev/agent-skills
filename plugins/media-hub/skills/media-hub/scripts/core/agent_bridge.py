#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent Command Queue & Bridge Module
"""

import os
import json
import time
from pathlib import Path

# Kept alongside the other hub state instead of a hard-coded path on an external
# volume: that directory can be unmounted or removed, and the previous constant
# crashed the whole server at import time when it went away.
def default_queue_file():
    from core.settings import resolve_dirs, load_unified_settings
    return resolve_dirs(load_unified_settings(), create=True)["queue_path"]


QUEUE_FILE = None  # resolved per instance; see default_queue_file()


class AgentBridge:
    def __init__(self, queue_file=None):
        self.queue_file = queue_file or os.environ.get("MEDIA_HUB_QUEUE_FILE") or default_queue_file()
        # Create lazily and never let a bad path take the server down on import.
        try:
            Path(self.queue_file).parent.mkdir(parents=True, exist_ok=True)
            if not os.path.exists(self.queue_file):
                self._save([])
        except Exception as e:
            print(f"[AgentBridge] Không khởi tạo được hàng đợi ({self.queue_file}): {e}")

    def _load(self):
        try:
            with open(self.queue_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save(self, data):
        tmp = f"{self.queue_file}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, self.queue_file)   # atomic; a crash mid-write left a torn file

    def add_command(self, command_text, author="User"):
        queue = self._load()
        cmd_id = int(time.time() * 1000)
        
        # A placeholder only. The real answer is produced by agent_queue_watcher via
        # intent_router and written back with update_response(). This used to invent
        # concrete figures ("49/51 tập - 96.1%", "32 torrents") that were never measured.
        quick_response = "🤖 Đã nhận lệnh, đang xử lý..."

        cmd_item = {
            "id": cmd_id,
            "command": command_text,
            "author": author,
            "status": "pending",
            "response": quick_response,
            "timestamp": time.strftime("%H:%M")
        }
        queue.append(cmd_item)
        self._save(queue)
        return cmd_item

    def update_response(self, cmd_id, response_text, status="done"):
        queue = self._load()
        for item in queue:
            if item.get("id") == cmd_id:
                item["response"] = response_text
                item["status"] = status
                break
        self._save(queue)

    def list_commands(self):
        return self._load()
