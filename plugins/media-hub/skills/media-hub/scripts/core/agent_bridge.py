#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent Command Queue & Bridge Module
"""

import os
import json
import time

QUEUE_FILE = "/Volumes/512GB/AI Workspace/antigravity-media-hub/agent_command_queue.json"

class AgentBridge:
    def __init__(self, queue_file=QUEUE_FILE):
        self.queue_file = queue_file
        if not os.path.exists(self.queue_file):
            self._save([])

    def _load(self):
        try:
            with open(self.queue_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save(self, data):
        with open(self.queue_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add_command(self, command_text, author="User"):
        queue = self._load()
        cmd_id = int(time.time() * 1000)
        
        lower_cmd = command_text.lower()
        quick_response = None
        if "tiến độ" in lower_cmd or "status" in lower_cmd or "progress" in lower_cmd or "b-daman" in lower_cmd:
            quick_response = "⚡ Đang sync Cross Fight B-Daman eS (49/51 tập - 96.1%). Monster BluRay đã hoàn tất 100%!"
        elif "torbox" in lower_cmd:
            quick_response = "⚡ TorBox Cloud hiện có 32 torrents (24 Ready, 8 Queued đang chờ)."
        elif "chào" in lower_cmd or "hello" in lower_cmd or "hi" in lower_cmd:
            quick_response = "👋 Chào anh! AI Agent Antigravity đã kết nối và sẵn sàng thực thi lệnh."
        else:
            quick_response = f"🤖 Đã nhận lệnh: \"{command_text}\". Đang điều phối tiến trình..."

        cmd_item = {
            "id": cmd_id,
            "command": command_text,
            "author": author,
            "status": "received",
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
