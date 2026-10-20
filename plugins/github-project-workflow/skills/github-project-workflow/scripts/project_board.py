#!/usr/bin/env python3
"""
Universal Rate-Limit Resilient CLI for GitHub Projects (v2) and Local Spec Synchronization.

Key Optimizations against GitHub API / GraphQL Rate Limits:
1. Zero-API Local List: `list` reads from local task specs and backlog doc by default (0 API calls).
   Pass `--remote` only when an explicit full sync from GitHub Project v2 is required.
2. Persistent Schema & Item-ID Cache (`.local-artifacts/project_board_cache.json`):
   Caches Project field IDs, option IDs, and task-to-item mappings to avoid repeated schema queries.
3. Single-Issue Targeted Lookup: Fetches specific ProjectV2 item IDs via 1-point issue GraphQL
   queries instead of expensive 150-item fan-out queries.
4. Local-First & Outbox Queue (`.local-artifacts/project_board_outbox.json`):
   Spec status is updated immediately locally. If GraphQL is rate-limited or offline, mutations
   are queued in the local outbox and can be flushed in batch via `sync`.
5. Configuration Flexibility:
   Auto-discovers project configuration from `.github/project.json`, `.agents/project.json`,
   git remote origin, environment variables, or CLI arguments.
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone

# Canonical status definitions
CANONICAL_STATUS = {
    "backlog": "Backlog",
    "todo": "Todo",
    "in progress": "In Progress",
    "in_progress": "In Progress",
    "done": "Done",
    "released": "Released",
}

LOCAL_SPEC_STATUS = {
    "Backlog": "Backlog",
    "Todo": "TODO",
    "In Progress": "IN_PROGRESS",
    "Done": "DONE",
    "Released": "RELEASED",
}


def run_gh(cmd, check=True):
    """Run a gh CLI command and return (returncode, stdout, stderr)."""
    res = subprocess.run(cmd, capture_output=True, text=True)
    if check and res.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{res.stderr.strip()}")
    return res.returncode, res.stdout.strip(), res.stderr.strip()


def detect_git_repo():
    """Extract (owner, repo) from git remote origin if available."""
    try:
        res = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            check=False,
        )
        url = res.stdout.strip()
        if not url:
            return None, None
        # Handle SSH: git@github.com:owner/repo.git
        ssh_match = re.search(r"github\.com[:/]([^/]+)/([^/\.]+)(?:\.git)?$", url)
        if ssh_match:
            return ssh_match.group(1), ssh_match.group(2)
    except Exception:
        pass
    return None, None


def find_config_file():
    """Locate project configuration file in standard repository locations."""
    candidates = [
        os.path.join(".github", "project.json"),
        os.path.join(".agents", "project.json"),
        os.path.join(".agents", "workflow.json"),
        "project.json",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def resolve_config(args=None):
    """
    Resolve configuration from:
    1. CLI args
    2. Config file (.github/project.json, etc.)
    3. Environment variables
    4. Git remote detection & filesystem fallbacks
    """
    config = {
        "owner": None,
        "repo": None,
        "project_number": None,
        "project_id": None,
        "tasks_dir": None,
        "backlog_doc": None,
        "cache_dir": ".local-artifacts",
    }

    # 1. Read config file if present
    cfg_file = getattr(args, "config", None) or find_config_file()
    if cfg_file and os.path.exists(cfg_file):
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                file_cfg = json.load(f)
                config.update({k: v for k, v in file_cfg.items() if v is not None})
        except Exception as e:
            print(f"[WARN] Failed to read config file {cfg_file}: {e}", file=sys.stderr)

    # 2. Read environment variables
    env_mappings = {
        "owner": "GH_PROJECT_OWNER",
        "repo": "GH_PROJECT_REPO",
        "project_number": "GH_PROJECT_NUMBER",
        "project_id": "GH_PROJECT_ID",
        "tasks_dir": "GH_TASKS_DIR",
        "backlog_doc": "GH_BACKLOG_DOC",
        "cache_dir": "GH_CACHE_DIR",
    }
    for key, env_var in env_mappings.items():
        val = os.environ.get(env_var)
        if val:
            config[key] = val

    # 3. CLI flag overrides
    if args:
        for key in config.keys():
            arg_val = getattr(args, key, None)
            if arg_val is not None:
                config[key] = arg_val

    # 4. Auto-detect owner and repo from git if still missing
    if not config["owner"] or not config["repo"]:
        git_owner, git_repo = detect_git_repo()
        if not config["owner"]:
            config["owner"] = git_owner
        if not config["repo"]:
            config["repo"] = git_repo

    # 5. Detect tasks_dir
    if not config["tasks_dir"]:
        for d in ["docs/v1-tasks", "docs/tasks", "tasks", ".tasks"]:
            if os.path.isdir(d):
                config["tasks_dir"] = d
                break
        if not config["tasks_dir"]:
            config["tasks_dir"] = "docs/tasks"

    # 6. Detect backlog_doc
    if not config["backlog_doc"]:
        for doc in ["docs/V1-BACKLOG.md", "docs/BACKLOG.md", "BACKLOG.md"]:
            if os.path.isfile(doc):
                config["backlog_doc"] = doc
                break
        if not config["backlog_doc"]:
            config["backlog_doc"] = "docs/BACKLOG.md"

    return config


def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, data):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def normalize_board_status(raw_status):
    cleaned = (raw_status or "").strip().lower()
    return CANONICAL_STATUS.get(cleaned, raw_status.strip() or "Backlog")


def get_cache_paths(config):
    cache_dir = config.get("cache_dir", ".local-artifacts")
    cache_path = os.path.join(cache_dir, "project_board_cache.json")
    outbox_path = os.path.join(cache_dir, "project_board_outbox.json")
    return cache_path, outbox_path


def parse_backlog_issue_map(backlog_doc):
    """Parse backlog markdown doc to map TASK-ID -> issue number without any API call."""
    mapping = {}
    if not backlog_doc or not os.path.exists(backlog_doc):
        return mapping
    with open(backlog_doc, "r", encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^\|\s*([A-Za-z0-9_-]+)\s*\|\s*\[#(\d+)\]", line.strip())
            if m:
                mapping[m.group(1).upper()] = int(m.group(2))
    return mapping


def parse_local_specs(tasks_dir, backlog_doc):
    """Read all markdown spec files in tasks_dir and return structured task records."""
    issue_map = parse_backlog_issue_map(backlog_doc)
    tasks = []
    pattern = os.path.join(tasks_dir, "*.md")
    for path in sorted(glob.glob(pattern)):
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            continue
        lines = content.splitlines()
        title = lines[0].lstrip("# ").strip() if lines else os.path.basename(path)
        # Extract task_id from title or filename
        task_id = None
        id_match = re.match(r"^([A-Za-z0-9]+-\d+)", title)
        if id_match:
            task_id = id_match.group(1).upper()
        else:
            base_match = re.match(r"^([A-Za-z0-9]+-\d+)", os.path.basename(path))
            task_id = base_match.group(1).upper() if base_match else os.path.splitext(os.path.basename(path))[0].upper()

        phase_m = re.search(r"^(?:Phase|Priority):\s*(.+)$", content, re.M | re.I)
        status_m = re.search(r"^Status:\s*(.+)$", content, re.M | re.I)
        phase = phase_m.group(1).strip() if phase_m else "P0"
        raw_status = status_m.group(1).strip() if status_m else "Backlog"
        board_status = normalize_board_status(raw_status)
        tasks.append(
            {
                "task_id": task_id,
                "issue_number": issue_map.get(task_id, "?"),
                "status": board_status,
                "raw_status": raw_status,
                "phase": phase,
                "title": title,
                "spec_path": path,
            }
        )

    def sort_key(t):
        digits = re.sub(r"\D", "", t["task_id"])
        return int(digits) if digits else 999999

    tasks.sort(key=sort_key)
    return tasks


def get_rate_limit_info():
    """Query GitHub API rate limit status without consuming quota."""
    rc, out, _ = run_gh(["gh", "api", "rate_limit"], check=False)
    if rc != 0:
        return None
    try:
        res = json.loads(out).get("resources", {})
        core = res.get("core", {})
        gql = res.get("graphql", {})
        return {
            "core_remaining": core.get("remaining", 0),
            "core_limit": core.get("limit", 5000),
            "core_reset": core.get("reset", 0),
            "gql_remaining": gql.get("remaining", 0),
            "gql_limit": gql.get("limit", 5000),
            "gql_reset": gql.get("reset", 0),
        }
    except Exception:
        return None


def spawn_auto_sync_daemon(config, target_reset_ts):
    """Spawn a detached background process to automatically push queued tasks once rate limit recovers."""
    cache_dir = config.get("cache_dir", ".local-artifacts")
    pid_file = os.path.join(cache_dir, "auto_sync.pid")
    log_file = os.path.join(cache_dir, "auto_sync.log")

    # Check if an existing daemon is alive
    if os.path.exists(pid_file):
        try:
            with open(pid_file, "r") as f:
                old_pid = int(f.read().strip())
            os.kill(old_pid, 0)
            return old_pid
        except (ProcessLookupError, ValueError):
            pass
        except PermissionError:
            return None

    os.makedirs(cache_dir, exist_ok=True)
    cmd = [
        sys.executable,
        os.path.abspath(__file__),
        "daemon",
        "--until", str(int(target_reset_ts)),
        "--cache-dir", cache_dir,
    ]
    if config.get("tasks_dir"):
        cmd.extend(["--tasks-dir", config["tasks_dir"]])
    if config.get("backlog_doc"):
        cmd.extend(["--backlog-doc", config["backlog_doc"]])
    if config.get("owner"):
        cmd.extend(["--owner", config["owner"]])
    if config.get("repo"):
        cmd.extend(["--repo", config["repo"]])
    if config.get("project_number"):
        cmd.extend(["--project", str(config["project_number"])])
    if config.get("project_id"):
        cmd.extend(["--project-id", config["project_id"]])

    try:
        log_fp = open(log_file, "a", encoding="utf-8")
        proc = subprocess.Popen(
            cmd,
            stdout=log_fp,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            close_fds=True,
        )
        with open(pid_file, "w") as f:
            f.write(str(proc.pid))
        return proc.pid
    except Exception as e:
        print(f"[WARN] Không thể khởi động background auto-sync daemon: {e}")
        return None


def enqueue_outbox(entry, config, outbox_path):
    """Save an unexecuted mutation to the local outbox and schedule background auto-sync upon quota reset."""
    outbox = load_json(outbox_path, [])
    # Deduplicate by task_id + action
    outbox = [
        item
        for item in outbox
        if not (item.get("task_id") == entry.get("task_id") and item.get("action") == entry.get("action"))
    ]
    entry["queued_at"] = datetime.now(timezone.utc).isoformat()
    outbox.append(entry)
    save_json(outbox_path, outbox)

    # Determine when rate limit resets
    rl = get_rate_limit_info()
    reset_ts = rl.get("gql_reset", 0) if rl else 0
    if not reset_ts or reset_ts <= time.time():
        reset_ts = time.time() + 300
    target_ts = reset_ts + 5
    wait_secs = max(5, int(target_ts - time.time()))
    reset_str = datetime.fromtimestamp(reset_ts).strftime("%H:%M:%S")

    print(f"📦 [LOCAL SAVED] Đã lưu task vào hàng đợi cục bộ ({outbox_path}): {entry['action']} {entry['task_id']} -> {entry.get('status')}")
    pid = spawn_auto_sync_daemon(config, target_ts)
    if pid:
        print(f"🚀 [AUTO-SYNC DAEMON] Tiến trình ngầm (PID {pid}) đang chờ rate-limit reset lúc {reset_str} (còn ~{wait_secs}s) để tự động đẩy lên GitHub.")


def flush_outbox_entries(config):
    """Flush pending outbox entries to GitHub Project and remote repository."""
    cache_path, outbox_path = get_cache_paths(config)
    outbox = load_json(outbox_path, [])
    if not outbox:
        return 0

    cache = load_json(cache_path, {})
    remaining = []
    project_id = config.get("project_id")
    owner = config.get("owner")
    repo = config.get("repo")
    repo_slug = f"{owner}/{repo}" if owner and repo else None
    flushed_count = 0

    for entry in outbox:
        try:
            action = entry.get("action")
            if action == "move":
                task_id = entry["task_id"]
                target_status = entry["status"]
                status_field_id, status_options, _, _ = get_project_fields(config, cache, cache_path)
                item_id = resolve_project_item_id(task_id, config, cache, cache_path)
                if not item_id:
                    raise RuntimeError(f"Missing item_id for {task_id}")
                mutation = f"""
                mutation {{
                  updateProjectV2ItemFieldValue(input: {{
                    projectId: "{project_id}", itemId: "{item_id}", fieldId: "{status_field_id}",
                    value: {{ singleSelectOptionId: "{status_options[target_status]}" }}
                  }}) {{ projectV2Item {{ id }} }}
                }}
                """
                run_gh(["gh", "api", "graphql", "-f", f"query={mutation}"])
                print(f"Flushed move: {task_id} -> {target_status}")
                flushed_count += 1

            elif action == "attach_issue":
                task_id = entry["task_id"]
                issue_url = entry["issue_url"]
                phase_code = entry.get("phase", "P0")
                board_status = entry["status"]

                status_field_id, status_options, phase_field_id, phase_options = get_project_fields(config, cache, cache_path)
                _, issue_json, _ = run_gh(["gh", "issue", "view", issue_url, "--json", "id,number"])
                issue_data = json.loads(issue_json)
                issue_node_id = issue_data["id"]
                issue_num = issue_data.get("number")

                add_q = f"""
                mutation {{
                  addProjectV2ItemById(input: {{ projectId: "{project_id}", contentId: "{issue_node_id}" }}) {{
                    item {{ id }}
                  }}
                }}
                """
                _, add_out, _ = run_gh(["gh", "api", "graphql", "-f", f"query={add_q}"])
                item_id = json.loads(add_out)["data"]["addProjectV2ItemById"]["item"]["id"]
                cache.setdefault("items", {})[task_id] = {"item_id": item_id, "issue_number": issue_num}
                save_json(cache_path, cache)

                upd_mutations = [
                    f"""setStatus: updateProjectV2ItemFieldValue(input: {{
                        projectId: "{project_id}", itemId: "{item_id}", fieldId: "{status_field_id}",
                        value: {{ singleSelectOptionId: "{status_options[board_status]}" }}
                    }}) {{ projectV2Item {{ id }} }}"""
                ]
                if phase_field_id and phase_options and phase_code in phase_options:
                    upd_mutations.append(
                        f"""setPhase: updateProjectV2ItemFieldValue(input: {{
                            projectId: "{project_id}", itemId: "{item_id}", fieldId: "{phase_field_id}",
                            value: {{ singleSelectOptionId: "{phase_options[phase_code]}" }}
                        }}) {{ projectV2Item {{ id }} }}"""
                    )
                upd_q = f"mutation {{ {' '.join(upd_mutations)} }}"
                run_gh(["gh", "api", "graphql", "-f", f"query={upd_q}"])
                print(f"Flushed attach_issue: {task_id} -> Project #{config.get('project_number')}")
                flushed_count += 1

            elif action == "push":
                task_id = entry["task_id"]
                spec_path = entry["spec_file"]
                board_status = entry["status"]
                with open(spec_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                header = content.splitlines()[0].lstrip("# ").strip()
                phase_match = re.search(r"^(?:Phase|Priority):\s*([^\n\r]+)", content, re.M | re.I)
                phase_code = phase_match.group(1).split("—")[0].strip() if phase_match else "P0"

                cmd = ["gh", "issue", "create", "--title", header, "--body", content]
                if repo_slug:
                    cmd.extend(["--repo", repo_slug])
                if phase_code:
                    cmd.extend(["--label", phase_code])
                rc, issue_url, err = run_gh(cmd, check=False)
                if rc != 0:
                    raise RuntimeError(f"Could not create issue: {err}")

                status_field_id, status_options, phase_field_id, phase_options = get_project_fields(config, cache, cache_path)
                _, issue_json, _ = run_gh(["gh", "issue", "view", issue_url, "--json", "id,number"])
                issue_data = json.loads(issue_json)
                issue_node_id = issue_data["id"]
                issue_num = issue_data.get("number")

                add_q = f"""
                mutation {{
                  addProjectV2ItemById(input: {{ projectId: "{project_id}", contentId: "{issue_node_id}" }}) {{
                    item {{ id }}
                  }}
                }}
                """
                _, add_out, _ = run_gh(["gh", "api", "graphql", "-f", f"query={add_q}"])
                item_id = json.loads(add_out)["data"]["addProjectV2ItemById"]["item"]["id"]
                cache.setdefault("items", {})[task_id] = {"item_id": item_id, "issue_number": issue_num}
                save_json(cache_path, cache)

                upd_mutations = [
                    f"""setStatus: updateProjectV2ItemFieldValue(input: {{
                        projectId: "{project_id}", itemId: "{item_id}", fieldId: "{status_field_id}",
                        value: {{ singleSelectOptionId: "{status_options[board_status]}" }}
                    }}) {{ projectV2Item {{ id }} }}"""
                ]
                if phase_field_id and phase_options and phase_code in phase_options:
                    upd_mutations.append(
                        f"""setPhase: updateProjectV2ItemFieldValue(input: {{
                            projectId: "{project_id}", itemId: "{item_id}", fieldId: "{phase_field_id}",
                            value: {{ singleSelectOptionId: "{phase_options[phase_code]}" }}
                        }}) {{ projectV2Item {{ id }} }}"""
                    )
                upd_q = f"mutation {{ {' '.join(upd_mutations)} }}"
                run_gh(["gh", "api", "graphql", "-f", f"query={upd_q}"])
                print(f"Flushed push: {task_id} -> Issue created & attached to Project #{config.get('project_number')}")
                flushed_count += 1
            else:
                remaining.append(entry)
        except Exception as exc:
            print(f"Still deferred ({entry.get('task_id')}): {str(exc).splitlines()[-1]}")
            remaining.append(entry)

    save_json(outbox_path, remaining)
    return flushed_count


def opportunistic_auto_sync(config):
    """Automatically check and flush outbox if rate limits have recovered."""
    cache_path, outbox_path = get_cache_paths(config)
    if not os.path.exists(outbox_path):
        return
    outbox = load_json(outbox_path, [])
    if not outbox:
        return

    rl = get_rate_limit_info()
    if rl and rl.get("gql_remaining", 0) > 5 and rl.get("core_remaining", 0) > 5:
        flushed = flush_outbox_entries(config)
        if flushed > 0:
            print(f"⚡ [AUTO-SYNC] Đã tự động đồng bộ {flushed} tác vụ từ outbox lên GitHub Project.")


def get_project_fields(config, cache, cache_path):
    """Return cached Project field IDs or fetch once via lightweight GraphQL."""
    fields = cache.get("fields")
    if fields and fields.get("status_field_id") and fields.get("status_options"):
        return (
            fields["status_field_id"],
            fields["status_options"],
            fields.get("phase_field_id"),
            fields.get("phase_options", {}),
        )

    project_id = config.get("project_id")
    if not project_id:
        raise ValueError("Missing project_id in config. Run `project_board.py init` or set in .github/project.json")

    query = f"""
    query {{
      node(id: "{project_id}") {{
        ... on ProjectV2 {{
          fields(first: 20) {{
            nodes {{
              ... on ProjectV2SingleSelectField {{
                id
                name
                options {{ id name }}
              }}
            }}
          }}
        }}
      }}
    }}
    """
    rc, out, err = run_gh(["gh", "api", "graphql", "-f", f"query={query}"], check=False)
    if rc != 0:
        raise RuntimeError(err or out)

    nodes = json.loads(out)["data"]["node"]["fields"]["nodes"]
    status_field = next((f for f in nodes if f and f.get("name") in ("Status", "status")), None)
    if not status_field:
        raise RuntimeError("Status field not found on GitHub Project")

    phase_field = next((f for f in nodes if f and f.get("name") in ("Phase", "phase", "Priority")), None)

    parsed = {
        "status_field_id": status_field["id"],
        "status_options": {opt["name"]: opt["id"] for opt in status_field["options"]},
        "phase_field_id": phase_field["id"] if phase_field else None,
        "phase_options": {opt["name"].split(" ")[0]: opt["id"] for opt in phase_field["options"]} if phase_field else {},
        "cached_at": int(time.time()),
    }
    cache["fields"] = parsed
    save_json(cache_path, cache)
    return (
        parsed["status_field_id"],
        parsed["status_options"],
        parsed["phase_field_id"],
        parsed["phase_options"],
    )


def resolve_project_item_id(task_id, config, cache, cache_path):
    """Resolve ProjectV2Item ID for task_id using cache first, then 1-point issue lookup."""
    items_cache = cache.setdefault("items", {})
    if task_id in items_cache and items_cache[task_id].get("item_id"):
        return items_cache[task_id]["item_id"]

    issue_map = parse_backlog_issue_map(config.get("backlog_doc"))
    issue_num = issue_map.get(task_id)
    owner = config.get("owner")
    repo = config.get("repo")
    project_id = config.get("project_id")

    if issue_num and owner and repo and project_id:
        query = f"""
        query {{
          repository(owner: "{owner}", name: "{repo}") {{
            issue(number: {issue_num}) {{
              id
              projectItems(first: 5) {{
                nodes {{
                  id
                  project {{ id }}
                }}
              }}
            }}
          }}
        }}
        """
        rc, out, _ = run_gh(["gh", "api", "graphql", "-f", f"query={query}"], check=False)
        if rc == 0:
            data = json.loads(out).get("data", {}).get("repository", {}).get("issue")
            if data:
                for node in data.get("projectItems", {}).get("nodes", []):
                    if node.get("project", {}).get("id") == project_id:
                        items_cache[task_id] = {"item_id": node["id"], "issue_number": issue_num}
                        save_json(cache_path, cache)
                        return node["id"]
    return None


def update_local_spec_status(task_id, board_status, tasks_dir):
    pattern = os.path.join(tasks_dir, f"{task_id}*.md")
    matches = glob.glob(pattern)
    if not matches:
        spec_path = os.path.join(tasks_dir, f"{task_id}.md")
        if not os.path.exists(spec_path):
            return
        matches = [spec_path]

    mapped = LOCAL_SPEC_STATUS.get(board_status, board_status.upper())
    for spec_path in matches:
        with open(spec_path, "r", encoding="utf-8") as f:
            text = f.read()
        updated = re.sub(r"^Status:\s*.*$", f"Status: {mapped}", text, flags=re.M | re.I)
        with open(spec_path, "w", encoding="utf-8") as f:
            f.write(updated)
        print(f"Updated local spec {spec_path} -> Status: {mapped}")


def cmd_list(args):
    config = resolve_config(args)
    opportunistic_auto_sync(config)
    cache_path, outbox_path = get_cache_paths(config)

    if not args.remote:
        tasks = parse_local_specs(config["tasks_dir"], config["backlog_doc"])
        if args.status:
            target = normalize_board_status(args.status).lower()
            tasks = [
                t
                for t in tasks
                if t["status"].lower() == target
                or (target == "todo" and t["raw_status"].strip().upper() == "TODO")
            ]
        for t in tasks:
            num = t["issue_number"]
            phase_short = t["phase"].split("—")[0].strip()
            print(f"#{str(num):<3} | {t['status']:<12} | {phase_short:<6} | {t['title']}")
        outbox = load_json(outbox_path, [])
        suffix = f" (Pending outbox sync: {len(outbox)})" if outbox else " (0 GitHub API calls used)"
        print(f"\nTotal: {len(tasks)} task(s){suffix}")
        return

    # Remote listing requested
    project_number = config.get("project_number")
    owner = config.get("owner")
    if not project_number or not owner:
        print(f"[WARN] Missing project_number or owner. Falling back to local specs:\n")
        args.remote = False
        return cmd_list(args)

    rc, out, err = run_gh(
        ["gh", "project", "item-list", str(project_number), "--owner", owner, "--limit", "150", "--format", "json"],
        check=False,
    )
    if rc != 0:
        print(f"[WARN] Remote Project query unavailable ({err.splitlines()[-1] if err else 'error'}). Falling back to local specs:\n")
        args.remote = False
        return cmd_list(args)

    data = json.loads(out)
    items = data.get("items", [])
    cache = load_json(cache_path, {})
    items_cache = cache.setdefault("items", {})
    for i in items:
        title = i.get("title", "")
        m = re.match(r"^([A-Za-z0-9]+-\d+)", title)
        if m:
            tid = m.group(1).upper()
            items_cache[tid] = {
                "item_id": i.get("id"),
                "issue_number": i.get("content", {}).get("number"),
            }
    save_json(cache_path, cache)

    if args.status:
        items = [i for i in items if i.get("status", "").lower() == args.status.lower()]
    for i in items:
        num = i.get("content", {}).get("number", "?")
        status = i.get("status", "None")
        phase = i.get("phase", "")
        print(f"#{num:<3} | {status:<12} | {phase:<22} | {i.get('title')}")
    print(f"\nTotal: {len(items)} task(s) (synced to local cache)")


def cmd_move(args):
    config = resolve_config(args)
    opportunistic_auto_sync(config)
    cache_path, outbox_path = get_cache_paths(config)
    task_id = args.task_id.upper()
    target_status = normalize_board_status(args.status)

    # 1. Local-First: Update spec file immediately
    update_local_spec_status(task_id, target_status, config["tasks_dir"])

    # 2. Remote update (GraphQL)
    cache = load_json(cache_path, {})
    try:
        project_id = config.get("project_id")
        if not project_id:
            raise RuntimeError("Missing project_id in config")
        status_field_id, status_options, _, _ = get_project_fields(config, cache, cache_path)
        if target_status not in status_options:
            raise SystemExit(f"Invalid status '{target_status}'. Valid options: {list(status_options.keys())}")
        item_id = resolve_project_item_id(task_id, config, cache, cache_path)
        if not item_id:
            raise RuntimeError(f"Item ID for {task_id} not cached and remote lookup unavailable")

        mutation = f"""
        mutation {{
          updateProjectV2ItemFieldValue(input: {{
            projectId: "{project_id}"
            itemId: "{item_id}"
            fieldId: "{status_field_id}"
            value: {{ singleSelectOptionId: "{status_options[target_status]}" }}
          }}) {{
            projectV2Item {{ id }}
          }}
        }}
        """
        rc, _, err = run_gh(["gh", "api", "graphql", "-f", f"query={mutation}"], check=False)
        if rc != 0:
            raise RuntimeError(err)
        print(f"Moved {task_id} -> [{target_status}] on GitHub Project #{config.get('project_number')} (1 GraphQL point)")
    except Exception as exc:
        print(f"[RATE-LIMIT / SCOPE GUARD] Deferred GitHub Project update ({str(exc).splitlines()[-1]}).")
        enqueue_outbox({"action": "move", "task_id": task_id, "status": target_status}, config, outbox_path)


def cmd_push(args):
    config = resolve_config(args)
    opportunistic_auto_sync(config)
    cache_path, outbox_path = get_cache_paths(config)
    spec_path = args.spec_file
    if not os.path.exists(spec_path):
        raise SystemExit(f"Spec file not found: {spec_path}")

    with open(spec_path, "r", encoding="utf-8") as f:
        content = f.read().strip()
    header = content.splitlines()[0].lstrip("# ").strip()
    id_m = re.match(r"^([A-Za-z0-9]+-\d+)", header)
    task_id = id_m.group(1).upper() if id_m else os.path.splitext(os.path.basename(spec_path))[0].upper()

    phase_match = re.search(r"^(?:Phase|Priority):\s*([^\n\r]+)", content, re.M | re.I)
    phase_code = phase_match.group(1).split("—")[0].strip() if phase_match else "P0"
    board_status = normalize_board_status(args.status)

    update_local_spec_status(task_id, board_status, config["tasks_dir"])
    owner = config.get("owner")
    repo = config.get("repo")
    repo_slug = f"{owner}/{repo}" if owner and repo else None

    # Step 1: Create GitHub Issue via REST (uses REST quota)
    cmd = ["gh", "issue", "create", "--title", header, "--body", content]
    if repo_slug:
        cmd.extend(["--repo", repo_slug])
    if phase_code:
        cmd.extend(["--label", phase_code])

    rc, issue_url, err = run_gh(cmd, check=False)
    if rc != 0:
        print(f"[RATE-LIMIT GUARD] Could not create remote issue right now ({err.splitlines()[-1] if err else 'error'}).")
        enqueue_outbox({"action": "push", "task_id": task_id, "spec_file": spec_path, "status": board_status}, config, outbox_path)
        return

    print(f"Created GitHub Issue for {task_id} -> {issue_url}")
    issue_num_m = re.search(r"/issues/(\d+)$", issue_url.strip())
    issue_num = int(issue_num_m.group(1)) if issue_num_m else None

    # Step 2: Add to Project v2 if available
    cache = load_json(cache_path, {})
    try:
        project_id = config.get("project_id")
        if not project_id:
            raise RuntimeError("Missing project_id in config")
        status_field_id, status_options, phase_field_id, phase_options = get_project_fields(config, cache, cache_path)
        _, issue_json, _ = run_gh(["gh", "issue", "view", issue_url, "--json", "id"])
        issue_node_id = json.loads(issue_json)["id"]

        add_q = f"""
        mutation {{
          addProjectV2ItemById(input: {{ projectId: "{project_id}", contentId: "{issue_node_id}" }}) {{
            item {{ id }}
          }}
        }}
        """
        _, add_out, _ = run_gh(["gh", "api", "graphql", "-f", f"query={add_q}"])
        item_id = json.loads(add_out)["data"]["addProjectV2ItemById"]["item"]["id"]
        cache.setdefault("items", {})[task_id] = {"item_id": item_id, "issue_number": issue_num}
        save_json(cache_path, cache)

        upd_mutations = [
            f"""setStatus: updateProjectV2ItemFieldValue(input: {{
                projectId: "{project_id}", itemId: "{item_id}", fieldId: "{status_field_id}",
                value: {{ singleSelectOptionId: "{status_options[board_status]}" }}
            }}) {{ projectV2Item {{ id }} }}"""
        ]
        if phase_field_id and phase_options and phase_code in phase_options:
            upd_mutations.append(
                f"""setPhase: updateProjectV2ItemFieldValue(input: {{
                    projectId: "{project_id}", itemId: "{item_id}", fieldId: "{phase_field_id}",
                    value: {{ singleSelectOptionId: "{phase_options[phase_code]}" }}
                }}) {{ projectV2Item {{ id }} }}"""
            )

        upd_q = f"mutation {{ {' '.join(upd_mutations)} }}"
        run_gh(["gh", "api", "graphql", "-f", f"query={upd_q}"])
        print(f"Synced {task_id} ({board_status}) to GitHub Project #{config.get('project_number')}")
    except Exception as exc:
        print(f"[RATE-LIMIT / SCOPE GUARD] Issue created ({issue_url}), Project board card queued ({str(exc).splitlines()[-1]}).")
        enqueue_outbox(
            {
                "action": "attach_issue",
                "task_id": task_id,
                "issue_url": issue_url,
                "phase": phase_code,
                "status": board_status,
            },
            config,
            outbox_path,
        )


def cmd_sync(args):
    config = resolve_config(args)
    flushed = flush_outbox_entries(config)
    cache_path, outbox_path = get_cache_paths(config)
    outbox = load_json(outbox_path, [])
    if not outbox and flushed == 0:
        print("Outbox is empty — all local task statuses are in sync.")
    elif not outbox:
        print(f"All {flushed} pending outbox tasks successfully synced to GitHub Project!")
    else:
        print(f"Synced {flushed} task(s). {len(outbox)} task(s) remaining in outbox.")


def cmd_daemon(args):
    """Background daemon that sleeps until rate limit reset timestamp, then auto-pushes outbox."""
    config = resolve_config(args)
    cache_path, outbox_path = get_cache_paths(config)
    target_ts = getattr(args, "until", 0)
    cache_dir = config.get("cache_dir", ".local-artifacts")
    pid_file = os.path.join(cache_dir, "auto_sync.pid")

    try:
        while time.time() < target_ts:
            outbox = load_json(outbox_path, [])
            if not outbox:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Outbox is empty. Daemon exiting cleanly.")
                return
            chunk = min(15, max(1, target_ts - time.time()))
            time.sleep(chunk)

        # Rate-limit window passed. Give GitHub API a 3-second buffer to update counters.
        time.sleep(3)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Rate-limit reset time reached. Flushing outbox...")
        flushed = flush_outbox_entries(config)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Finished auto-sync: {flushed} tasks synced.")
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Daemon error: {e}")
    finally:
        if os.path.exists(pid_file):
            try:
                os.remove(pid_file)
            except Exception:
                pass


def cmd_rate_limit(args):
    config = resolve_config(args)
    cache_path, outbox_path = get_cache_paths(config)
    rc, out, err = run_gh(["gh", "api", "rate_limit"], check=False)
    outbox = load_json(outbox_path, [])
    cache = load_json(cache_path, {})
    if rc != 0:
        print(f"GitHub API unreachable: {err}")
        return
    res = json.loads(out).get("resources", {})
    core = res.get("core", {})
    gql = res.get("graphql", {})
    reset_ts = gql.get("reset", 0)
    reset_str = datetime.fromtimestamp(reset_ts).strftime("%H:%M:%S") if reset_ts else "N/A"
    print(f"REST (core)   : {core.get('remaining', '?')}/{core.get('limit', '?')} remaining")
    print(f"GraphQL       : {gql.get('remaining', '?')}/{gql.get('limit', '?')} remaining (resets at {reset_str})")
    print(f"Cached items  : {len(cache.get('items', {}))} task(s)")
    print(f"Pending outbox: {len(outbox)} mutation(s)")


def cmd_report(args):
    """Render a clean Markdown status report of the project, tasks, rate limits, and outbox."""
    config = resolve_config(args)
    opportunistic_auto_sync(config)
    cache_path, outbox_path = get_cache_paths(config)
    tasks = parse_local_specs(config["tasks_dir"], config["backlog_doc"])
    outbox = load_json(outbox_path, [])
    cache = load_json(cache_path, {})

    # Check API rate limits
    rc, out, _ = run_gh(["gh", "api", "rate_limit"], check=False)
    core_rem, core_lim = "?", "?"
    gql_rem, gql_lim = "?", "?"
    reset_str = "N/A"
    if rc == 0:
        res = json.loads(out).get("resources", {})
        core = res.get("core", {})
        gql = res.get("graphql", {})
        core_rem, core_lim = core.get("remaining", "?"), core.get("limit", "?")
        gql_rem, gql_lim = gql.get("remaining", "?"), gql.get("limit", "?")
        reset_ts = gql.get("reset", 0)
        reset_str = datetime.fromtimestamp(reset_ts).strftime("%H:%M:%S") if reset_ts else "N/A"

    # Group tasks by canonical status
    groups = {s: [] for s in ["Backlog", "Todo", "In Progress", "Done", "Released"]}
    for t in tasks:
        st = t["status"]
        if st not in groups:
            groups[st] = []
        groups[st].append(t)

    owner = config.get("owner", "N/A")
    repo = config.get("repo", "N/A")
    p_num = config.get("project_number", "N/A")
    p_id = config.get("project_id", "Not set")

    lines = [
        "# 📊 GitHub Project Workflow Report",
        "",
        f"- **Repository**: `{owner}/{repo}`",
        f"- **Project Board**: `#{p_num}` (Node ID: `{p_id}`)",
        f"- **Spec Directory**: `{config['tasks_dir']}`",
        "",
        "## 🚦 API Rate-Limit Status",
        f"- **REST Core**: `{core_rem}/{core_lim}` remaining",
        f"- **GraphQL**: `{gql_rem}/{gql_lim}` remaining (resets at `{reset_str}`)",
        f"- **Pending Outbox**: `{len(outbox)}` mutations deferred",
        f"- **Cached Items**: `{len(cache.get('items', {}))}` tasks in local schema cache",
        "",
        "## 📋 Task Breakdown by Status",
        "| Status | Count | Tasks |",
        "|---|:---:|---|",
    ]

    for status_name, task_list in groups.items():
        if not task_list:
            continue
        task_preview = ", ".join(f"`{t['task_id']}`" for t in task_list[:6])
        if len(task_list) > 6:
            task_preview += f" ... (+{len(task_list) - 6} more)"
        lines.append(f"| **{status_name}** | {len(task_list)} | {task_preview} |")

    lines.append("")
    lines.append(f"**Total Tracked Tasks**: {len(tasks)}")
    print("\n".join(lines))


def cmd_init(args):
    """Initialize project configuration in .github/project.json."""
    config = resolve_config(args)
    owner = args.owner or config["owner"]
    repo = args.repo or config["repo"]
    project_number = args.project_number or config["project_number"]

    if not owner or not repo:
        print("Error: Could not auto-detect owner/repo. Please specify --owner and --repo.", file=sys.stderr)
        sys.exit(1)

    project_id = config.get("project_id")
    if project_number and not project_id:
        print(f"Querying GitHub GraphQL for Project #{project_number} Node ID (owner: {owner})...")
        q = f"""
        query {{
          user(login: "{owner}") {{
            projectV2(number: {project_number}) {{ id title }}
          }}
          organization(login: "{owner}") {{
            projectV2(number: {project_number}) {{ id title }}
          }}
        }}
        """
        rc, out, _ = run_gh(["gh", "api", "graphql", "-f", f"query={q}"], check=False)
        if rc == 0:
            data = json.loads(out).get("data", {})
            user_proj = data.get("user", {}).get("projectV2") if data.get("user") else None
            org_proj = data.get("organization", {}).get("projectV2") if data.get("organization") else None
            proj = user_proj or org_proj
            if proj:
                project_id = proj["id"]
                print(f"Found Project: '{proj.get('title')}' (Node ID: {project_id})")

    out_cfg = {
        "owner": owner,
        "repo": repo,
        "project_number": str(project_number) if project_number else None,
        "project_id": project_id,
        "tasks_dir": config.get("tasks_dir") or "docs/tasks",
        "backlog_doc": config.get("backlog_doc") or "docs/BACKLOG.md",
        "cache_dir": config.get("cache_dir") or ".local-artifacts",
    }
    target_path = os.path.join(".github", "project.json")
    save_json(target_path, out_cfg)
    print(f"\nSaved configuration to {target_path}:")
    print(json.dumps(out_cfg, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="Universal Rate-Limit Resilient CLI for GitHub Projects (v2) and Spec Workflow",
    )
    parser.add_argument("--config", help="Path to custom project.json config file")
    parser.add_argument("--owner", help="GitHub repo or project owner")
    parser.add_argument("--repo", help="GitHub repository name")
    parser.add_argument("--project", dest="project_number", help="GitHub Project number")
    parser.add_argument("--project-id", dest="project_id", help="GitHub Project Node ID (PVT_...)")
    parser.add_argument("--tasks-dir", help="Directory containing task spec markdown files")
    parser.add_argument("--backlog-doc", help="Path to backlog markdown document")
    parser.add_argument("--cache-dir", help="Directory for cache and outbox JSON files")

    sub = parser.add_subparsers(dest="cmd", required=True)

    # list
    p_list = sub.add_parser("list", help="List tasks (0 API calls by default; pass --remote for live query)")
    p_list.add_argument("--status", help="Filter by status (Backlog, Todo, In Progress, Done, Released)")
    p_list.add_argument("--remote", action="store_true", help="Query GitHub Project v2 directly and refresh cache")
    p_list.set_defaults(func=cmd_list)

    # move
    p_move = sub.add_parser("move", help="Move a task to a status column (Local-First + 1-pt GraphQL / Outbox)")
    p_move.add_argument("task_id", help="Task ID, e.g. TNG-01 or FEAT-12")
    p_move.add_argument("status", help="Target status: Backlog, Todo, In Progress, Done, Released")
    p_move.set_defaults(func=cmd_move)

    # push
    p_push = sub.add_parser("push", help="Create issue from spec file and attach to Project v2")
    p_push.add_argument("spec_file", help="Path to spec markdown file, e.g. docs/tasks/TASK-01.md")
    p_push.add_argument("--status", default="Backlog", help="Initial status (default: Backlog)")
    p_push.set_defaults(func=cmd_push)

    # sync
    p_sync = sub.add_parser("sync", help="Flush queued outbox mutations to GitHub Project v2")
    p_sync.set_defaults(func=cmd_sync)

    # rate-limit
    p_rl = sub.add_parser("rate-limit", help="Check GitHub REST/GraphQL quota and local cache/outbox status")
    p_rl.set_defaults(func=cmd_rate_limit)

    # report
    p_rep = sub.add_parser("report", help="Render Markdown status report of project, tasks, rate limits, and outbox")
    p_rep.set_defaults(func=cmd_report)

    # daemon
    p_daemon = sub.add_parser("daemon", help="Background daemon to auto-sync when rate limit resets")
    p_daemon.add_argument("--until", type=float, required=True, help="Epoch timestamp to sleep until")
    p_daemon.set_defaults(func=cmd_daemon)

    # init
    p_init = sub.add_parser("init", help="Initialize or generate .github/project.json config file")
    p_init.set_defaults(func=cmd_init)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
