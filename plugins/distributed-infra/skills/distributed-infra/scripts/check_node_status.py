#!/usr/bin/env python3
"""
Tdarr Node Health & Status Monitor CLI
Queries Tdarr Server API (:8265) to inspect connected nodes, active workers, and queue status.
"""

import sys
import json
import urllib.request
import urllib.error

DEFAULT_SERVER_URL = "http://127.0.0.1:8265"

def api_post(endpoint, payload):
    url = f"{DEFAULT_SERVER_URL}{endpoint}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"❌ Error connecting to Tdarr Server at {url}: {e}")
        return None

def main():
    print("==================================================")
    print("       TDARR DISTRIBUTED CLUSTER STATUS           ")
    print("==================================================")

    # 1. Server status
    try:
        with urllib.request.urlopen(f"{DEFAULT_SERVER_URL}/api/v2/status", timeout=3) as resp:
            st = json.loads(resp.read().decode("utf-8"))
            print(f"🖥️  Server Status: {st.get('status')} | Version: {st.get('version')} | Engine: {st.get('serverEngine')}")
    except Exception as e:
        print(f"❌ Cannot contact Tdarr server: {e}")
        sys.exit(1)

    # 2. Query nodes
    nodes = api_post("/api/v2/cruddb", {"data": {"collection": "NodeJSONDB", "mode": "getAll"}})
    if not nodes:
        print("⚠️  No node information returned.")
        return

    print(f"\n📡 Connected Nodes: {len(nodes)}")
    for node in nodes:
        nid = node.get("_id")
        ip = node.get("nodeIP", "unknown")
        paused = node.get("nodePaused", False)
        workers = node.get("workers", {})
        cpu_workers = node.get("transcodecpu", 0)
        gpu_workers = node.get("transcodegpu", 0)
        
        status_icon = "⏸️  PAUSED" if paused else "🟢 ACTIVE"
        print(f"\n  • [{nid}] ({ip}) - {status_icon}")
        print(f"    - Worker Config : CPU Limit = {cpu_workers} | GPU Limit = {gpu_workers}")
        
        active_cnt = len(workers)
        print(f"    - Active Workers: {active_cnt} running")
        for wid, wdata in workers.items():
            file_name = wdata.get("file", "Unknown")
            pct = wdata.get("percentage", 0)
            fps = wdata.get("fps", 0)
            est = wdata.get("eta", "N/A")
            wtype = wdata.get("workerType", "transcode")
            print(f"      ↳ [{wid}] ({wtype}): {pct}% @ {fps} FPS (ETA: {est})")
            print(f"        File: {file_name}")

    print("\n==================================================")

if __name__ == "__main__":
    main()
