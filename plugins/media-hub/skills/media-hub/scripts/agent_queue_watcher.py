#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent Command Queue Watcher Daemon
Notifies Antigravity AI immediately when a user dispatches a command from Web UI
"""

import os
import json
import time

QUEUE_FILE = "/Volumes/512GB/AI Workspace/antigravity-media-hub/agent_command_queue.json"

def watch_queue():
    print("🚀 Agent Queue Watcher Daemon started...", flush=True)
    last_seen_ids = set()
    
    # Initialize seen IDs
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                queue = json.load(f)
                for item in queue:
                    if item.get("status") == "done":
                        last_seen_ids.add(item.get("id"))
        except Exception:
            pass

    while True:
        try:
            if os.path.exists(QUEUE_FILE):
                with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                    queue = json.load(f)
                    
                pending_items = [item for item in queue if item.get("status") == "pending" and item.get("id") not in last_seen_ids]
                for item in pending_items:
                    cmd_id = item.get("id")
                    cmd_text = item.get("command")
                    last_seen_ids.add(cmd_id)
                    print(f"🔔 [AGENT_TRIGGER] Lệnh mới từ Web UI (ID: {cmd_id}): \"{cmd_text}\"", flush=True)
        except Exception:
            pass
        time.sleep(2)

if __name__ == "__main__":
    watch_queue()
