#!/usr/bin/env python3
"""
project-reporter: Multi-Conversation Orchestrator & Progress Reporter
Inspects SQLite conversation_summaries.db, transcripts, and shared project ledger.
"""

import os
import sys
import json
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime

APP_DATA_DIR = Path.home() / ".gemini" / "antigravity-cli"
DB_PATH = APP_DATA_DIR / "conversation_summaries.db"
BRAIN_DIR = APP_DATA_DIR / "brain"

def get_current_workspace():
    """Detect current workspace directory."""
    cwd = Path.cwd().resolve()
    return str(cwd)

def find_workspace_conversations(workspace_path):
    """Find all conversation summaries matching the given workspace."""
    if not DB_PATH.is_file():
        return []

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Search for workspace URI match
    encoded_ws = workspace_path.replace(" ", "%20")
    query = """
        SELECT conversation_id, title, preview, step_count, last_modified_time, workspace_uris, status
        FROM conversation_summaries
        WHERE workspace_uris LIKE ? OR workspace_uris LIKE ?
        ORDER BY last_modified_time DESC
    """
    cursor.execute(query, (f"%{workspace_path}%", f"%{encoded_ws}%"))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def parse_transcript_summary(conv_id, max_events=10):
    """Parse transcript.jsonl of a conversation for key events, user intents, and completed work."""
    t_file = BRAIN_DIR / conv_id / ".system_generated" / "logs" / "transcript.jsonl"
    if not t_file.is_file():
        return {"user_requests": [], "tools_used": set(), "completed_tasks": [], "modified_files": set()}

    user_requests = []
    tools_used = set()
    modified_files = set()
    commands_run = []

    try:
        with open(t_file, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                    step_type = obj.get("type", "")
                    content = obj.get("content", "")

                    if step_type == "USER_INPUT" and content:
                        clean_content = content.strip().split("\n")[0][:100]
                        if not clean_content.startswith("<"):
                            user_requests.append(clean_content)

                    tool_calls = obj.get("tool_calls", [])
                    for tc in tool_calls:
                        t_name = tc.get("toolAction") or tc.get("toolSummary") or tc.get("name")
                        if t_name:
                            tools_used.add(t_name)
                        
                        args = tc.get("args") or tc.get("arguments") or {}
                        if isinstance(args, dict):
                            cmd = args.get("CommandLine")
                            if cmd:
                                commands_run.append(cmd.strip()[:80])
                            tgt = args.get("TargetFile") or args.get("AbsolutePath")
                            if tgt:
                                clean_name = Path(tgt).name.strip(' "\'')
                                if clean_name:
                                    modified_files.add(clean_name)
                except Exception:
                    continue
    except Exception as e:
        return {"error": str(e), "user_requests": [], "tools_used": set(), "modified_files": set()}

    return {
        "user_requests": user_requests[-max_events:],
        "tools_used": sorted(list(tools_used)),
        "modified_files": sorted(list(modified_files)),
        "commands_sample": commands_run[-5:]
    }

def get_shared_ledger(workspace_path):
    """Load or initialize .agent/project_status.json."""
    ws = Path(workspace_path)
    agent_dir = ws / ".agent"
    status_file = agent_dir / "project_status.json"

    if status_file.is_file():
        try:
            with open(status_file, "r", encoding="utf-8") as f:
                return json.load(f), status_file
        except Exception:
            pass
    return None, status_file

def sync_current_conversation(workspace_path, conv_id=None, note=None):
    """Record current conversation snapshot into the shared project ledger."""
    ws = Path(workspace_path)
    agent_dir = ws / ".agent"
    agent_dir.mkdir(parents=True, exist_ok=True)
    status_file = agent_dir / "project_status.json"

    ledger = {}
    if status_file.is_file():
        try:
            with open(status_file, "r", encoding="utf-8") as f:
                ledger = json.load(f)
        except Exception:
            ledger = {}

    ledger.setdefault("project_name", ws.name)
    ledger.setdefault("updated_at", datetime.now().isoformat())
    ledger.setdefault("conversations", {})
    ledger.setdefault("shared_state", {
        "ports": {},
        "paths": {},
        "active_services": []
    })

    if not conv_id:
        # Detect latest modified conversation
        convs = find_workspace_conversations(workspace_path)
        if convs:
            conv_id = convs[0]["conversation_id"]

    if conv_id:
        t_summary = parse_transcript_summary(conv_id)
        conv_entry = {
            "conversation_id": conv_id,
            "last_synced": datetime.now().isoformat(),
            "latest_requests": t_summary.get("user_requests", [])[-3:],
            "modified_files": t_summary.get("modified_files", []),
            "note": note or "Auto-synced via project-reporter"
        }
        ledger["conversations"][conv_id] = conv_entry

    with open(status_file, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2, ensure_ascii=False)

    print(f"✅ Synced conversation {conv_id} to {status_file}")
    return ledger

def generate_all_report(workspace_path, convs):
    """Generate comprehensive Markdown report across all workspace conversations."""
    ws_name = Path(workspace_path).name
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    md = []
    md.append(f"# 📊 Project Progress Report: {ws_name}")
    md.append(f"> **Generated at**: `{now_str}` | **Workspace**: `{workspace_path}`\n")
    md.append(f"Tìm thấy **{len(convs)} conversation(s)** đã hoạt động trong workspace này.\n")

    md.append("## 🏛️ 1. Ma Trận Các Phiên Làm Việc (Conversation Matrix)\n")
    md.append("| # | Tiêu Đề Phiên | Conversation ID | Lần Sửa Đổi Cuối | Lượt Thao Tác |")
    md.append("|---|---|---|---|---|")

    for idx, c in enumerate(convs, 1):
        cid = c["conversation_id"]
        title = c["title"] or "Untitled"
        steps = c["step_count"]
        # Convert unix epoch or ISO string
        lmt = c["last_modified_time"]
        if isinstance(lmt, (int, float)):
            time_str = datetime.fromtimestamp(lmt).strftime("%Y-%m-%d %H:%M")
        else:
            time_str = str(lmt)[:16]
        
        cid_short = cid[:8] + "..." + cid[-4:]
        md.append(f"| {idx} | **{title}** | [`{cid_short}`](conversation://{cid}) | {time_str} | {steps} steps |")

    md.append("\n---\n")
    md.append("## 🔍 2. Chi Tiết Tiến Độ Từng Phiên (Per-Conversation Breakdown)\n")

    for c in convs:
        cid = c["conversation_id"]
        title = c["title"] or "Untitled"
        md.append(f"### 📍 {title} (`{cid}`)")
        
        t_data = parse_transcript_summary(cid)
        reqs = t_data.get("user_requests", [])
        files = t_data.get("modified_files", [])
        tools = t_data.get("tools_used", [])

        if reqs:
            md.append("**Yêu cầu gần nhất của User:**")
            for r in reqs[-3:]:
                md.append(f"* `{r}`")
        
        if files:
            md.append(f"\n**Files tác động ({len(files)}):** " + ", ".join([f"`{f}`" for f in files[:8]]))

        if tools:
            md.append(f"**Công cụ / Kỹ năng đã dùng:** " + ", ".join([f"`{t}`" for t in tools[:6]]))

        md.append("")

    # Check shared ledger
    ledger, status_file = get_shared_ledger(workspace_path)
    md.append("---\n## 🧭 3. Sổ Cái Trạng Thái Dự Án (Shared Project Ledger)\n")
    if ledger:
        md.append(f"Đã phát hiện file sổ cái trung tâm: `{status_file}`\n")
        shared = ledger.get("shared_state", {})
        if shared.get("ports"):
            md.append("**Port Matrix đã đăng ký:**")
            for svc, port in shared["ports"].items():
                md.append(f"* `{svc}`: `{port}`")
        if shared.get("paths"):
            md.append("\n**Đường dẫn thư viện cốt lõi:**")
            for name, path in shared["paths"].items():
                md.append(f"* `{name}`: `{path}`")
    else:
        md.append(f"Chưa có file `.agent/project_status.json`. Dùng `python3 reporter.py --sync` để tự động khởi tạo.")

    return "\n".join(md)

def generate_single_report(conv_id):
    """Generate detailed breakdown for a single conversation ID."""
    t_data = parse_transcript_summary(conv_id, max_events=30)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    md = [
        f"# 📋 Chi Tiết Conversation: `{conv_id}`",
        f"> **Thời gian xuất**: `{now_str}`\n",
        "### 🎯 Lịch Sử Yêu Cầu Của User:"
    ]
    for r in t_data.get("user_requests", []):
        md.append(f"* {r}")

    md.append("\n### 🛠️ Các File Đã Thay Đổi:")
    for f in t_data.get("modified_files", []):
        md.append(f"* `{f}`")

    md.append("\n### ⚙️ Mẫu Lệnh Đã Thực Thi Gần Nhất:")
    for cmd in t_data.get("commands_sample", []):
        md.append(f"```bash\n{cmd}\n```")

    return "\n".join(md)

def main():
    parser = argparse.ArgumentParser(description="Multi-Conversation Orchestrator & Progress Reporter")
    parser.add_argument("--all", "-a", action="store_true", help="Report on all conversations in current workspace")
    parser.add_argument("--conv", "-c", type=str, help="Report on a specific conversation ID or keyword")
    parser.add_argument("--sync", "-s", action="store_true", help="Sync current conversation into .agent/project_status.json")
    parser.add_argument("--workspace", "-w", type=str, default=None, help="Explicit workspace path")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of Markdown")

    args = parser.parse_args()
    ws_path = args.workspace or get_current_workspace()

    if args.sync:
        sync_current_conversation(ws_path, conv_id=args.conv)
        return

    if args.conv and not args.all:
        # Single conv report
        print(generate_single_report(args.conv))
        return

    # Default to report all in workspace
    convs = find_workspace_conversations(ws_path)
    if not convs:
        # Fallback to home dir or recent convs if workspace path didn't match directly
        convs = find_workspace_conversations("/home/chungnh")

    report_md = generate_all_report(ws_path, convs)
    print(report_md)

if __name__ == "__main__":
    main()
