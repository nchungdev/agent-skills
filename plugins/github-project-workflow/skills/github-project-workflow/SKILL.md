---
name: github-project-workflow
description: Quản lý vòng đời task và đồng bộ GitHub Project v2 chống cạn kiệt rate-limit: danh sách local zero-API, bộ đệm schema/item-id, tra cứu 1-point và hàng đợi outbox offline. Kèm quy trình 4 bước chuẩn (Tạo task, Do task, Code review gate, Release).
---

# GitHub Project Workflow Skill

Kỹ năng quản lý vòng đời task, đặc tả kỹ thuật (spec-driven development) và đồng bộ trạng thái hai chiều với **GitHub Projects (v2)**, được thiết kế chuyên biệt để **chống cạn kiệt hạn ngạch GitHub API/GraphQL Rate Limit** cho AI Agent và nhà phát triển.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 📂 TẦNG NỘI BỘ DỰ ÁN (LOCAL-FIRST & ZERO-API)                               │
│    ├── 📄 docs/tasks/TASK-*.md   -> Đặc tả chi tiết từng task (Spec files)  │
│    ├── 📑 docs/BACKLOG.md        -> Bảng phân bổ task & ánh xạ Issue ID     │
│    └── ⚡ CLI `list`              -> Đọc trực tiếp từ ổ cứng (0 API CALLS)  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ (1 GraphQL Point / REST)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🛡️ TẦNG BẢO VỆ RATE-LIMIT (CACHE & OFFLINE OUTBOX)                         │
│    ├── 🗄️ project_board_cache.json  -> Cache Field ID, Option ID, Item ID   │
│    ├── 📮 project_board_outbox.json -> Hàng đợi đột biến khi rate-limited    │
│    └── 🔄 CLI `sync`                -> Flush hàng đợi sau khi hồi quota     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ ☁️ GITHUB PROJECTS (v2) KANBAN BOARD                                         │
│    Backlog ──▶ Todo ──▶ In Progress ──▶ Done ──▶ Released                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Các Cơ Chế Chống Cạn Kiệt Rate-Limit (Anti-Rate-Limit Defenses)

1. **Zero-API Local List (`list`)**:
   - Mặc định, lệnh `list` đọc trực tiếp danh sách task từ thư mục spec (`docs/tasks/*.md` hoặc `docs/v1-tasks/*.md`) và file backlog — **tiêu tốn đúng 0 điểm API**.
   - Chỉ dùng `--remote` khi thật sự cần kéo toàn bộ snapshot mới từ GitHub Project.
2. **Persistent Schema & Item Cache**:
   - Lưu trữ `ProjectV2SingleSelectField` ID và ánh xạ `TASK_ID -> item_id` tại `.local-artifacts/project_board_cache.json`.
   - Loại bỏ hoàn toàn việc gọi `gh project field-list` và `gh project item-list --limit 150` ở mỗi lần đổi trạng thái task (tiết kiệm hàng trăm điểm GraphQL).
3. **Single-Issue Targeted Lookup**:
   - Khi cần tìm Item ID của một task chưa cache, script chỉ tra cứu 1 issue cụ thể qua GraphQL (tốn **1 điểm** duy nhất thay vì quét toàn bộ 150 item).
4. **Tự Động Lưu Local & Push Lại Sau Khi Hết Rate Limit (Auto-Save & Background Retry Daemon)**:
   - Khi chuyển trạng thái task hoặc tạo issue, nếu gặp lỗi mạng, mã `429 (Rate Limit)` hoặc `403 (Abuse/Secondary Rate Limit)`:
     - **Lưu cục bộ ngay lập tức**: Cập nhật file spec trên ổ cứng và ghi nhận thao tác vào `project_board_outbox.json` để tiến trình công việc của Agent không bao giờ bị nghẽn.
     - **Tự động khởi chạy Daemon ngầm (`daemon`)**: Script tự động tra cứu mốc thời gian quota hồi phục (`reset_ts`) và kích hoạt một tiến trình nền detached (`project_board.py daemon --until <ts>`). Tiến trình này sẽ ngủ cho đến đúng thời điểm GitHub cấp lại quota, tự động thức dậy, đẩy toàn bộ thay đổi lên GitHub Project và thoát an toàn.
     - **Đồng bộ cơ hội (Opportunistic Auto-Sync)**: Mỗi khi bất kỳ lệnh CLI nào (`list`, `move`, `push`, `report`) được thực thi sau khi quota đã hồi, script sẽ tự động xả sạch các task còn đọng trong outbox.
5. **Tách Biệt REST & GraphQL**:
   - Lệnh `push` tạo issue qua REST (`gh issue create` — dùng hạn ngạch REST 5.000 req/giờ độc lập) trước khi gắn card vào Project qua GraphQL.

---

## 🛠️ Cấu Hình & Khởi Tạo Dự Án

### 1. Tự động khởi tạo cấu hình (`init`)
Chạy lệnh khởi tạo ngay tại thư mục gốc của repository:

```bash
python3 <skill_dir>/scripts/project_board.py init --project <PROJECT_NUMBER>
```

Script sẽ:
- Tự động nhận diện `owner` và `repo` từ `git remote origin`.
- Tự động truy vấn GraphQL lấy Node ID dạng `PVT_kw...` của GitHub Project #`<PROJECT_NUMBER>`.
- Ghi cấu hình vào `.github/project.json`.

### 2. File cấu hình `.github/project.json` mẫu
Nếu muốn cấu hình thủ công hoặc tùy biến thư mục:

```json
{
  "owner": "nchungdev",
  "repo": "my-awesome-project",
  "project_number": "5",
  "project_id": "PVT_kwHOAsegYM4BnkpP",
  "tasks_dir": "docs/tasks",
  "backlog_doc": "docs/BACKLOG.md",
  "cache_dir": ".local-artifacts"
}
```

> **Thứ tự ưu tiên nạp cấu hình**: CLI flags (`--owner`, `--repo`, `--project`...) > `.github/project.json` / `.agents/project.json` > Biến môi trường (`GH_PROJECT_OWNER`, `GH_PROJECT_REPO`, `GH_PROJECT_NUMBER`, `GH_PROJECT_ID`...) > Tự động dò `git remote`.

---

## 🔄 4 Vòng Đời Task Chuẩn (Standard Task Workflow)

### Bước 1: Tạo task (`Tạo task`)
1. Nghiên cứu yêu cầu, thống nhất kiến trúc và chia nhỏ sub-tasks.
2. Viết tài liệu đặc tả (spec) tại `docs/tasks/<TASK_ID>.md`:
   ```markdown
   # TASK-01 — Triển khai Module A
   Status: Backlog
   Priority: P0
   ```
3. Đẩy lên Backlog của GitHub Project:
   ```bash
   python3 <skill_dir>/scripts/project_board.py push docs/tasks/TASK-01.md --status "Backlog"
   ```

### Bước 2: Thực thi task (`Do task`)
1. Đọc task cần làm từ cột `Todo`:
   ```bash
   python3 <skill_dir>/scripts/project_board.py list --status "Todo"
   ```
2. Chuyển task sang `In Progress`:
   ```bash
   python3 <skill_dir>/scripts/project_board.py move TASK-01 "In Progress"
   ```
3. Tiến hành implement mã nguồn.
4. Chạy Unit Test và Test trên môi trường/thiết bị thực tế:
   - Nếu **thất bại**: Giữ nguyên ở `In Progress`, sửa lỗi và ghi nhận bằng chứng kiểm thử.
   - Nếu **vượt qua**: Tiến hành bước Code Review Gate.

### Bước 3: Code Review Gate & Hoàn thành (`Done`)
1. Chạy linter, format code, kiểm tra tính toàn vẹn (SOLID, Clean Architecture, Conventions).
2. Chuyển task sang `Done`:
   ```bash
   python3 <skill_dir>/scripts/project_board.py move TASK-01 "Done"
   ```

### Bước 4: Đóng phiên bản (`Release`)
1. Gom các task hoàn thành, đóng tag/commit phiên bản mới.
2. Chuyển các task đã phát hành sang `Released`:
   ```bash
   python3 <skill_dir>/scripts/project_board.py move TASK-01 "Released"
   ```

---

## 📖 Bảng Lệnh CLI Chi Tiết

| Lệnh | Mục đích | API Quota sử dụng |
|---|---|---|
| `python3 <skill_dir>/scripts/project_board.py list` | Liệt kê toàn bộ task từ spec cục bộ | **0 điểm** (Zero-API) |
| `python3 <skill_dir>/scripts/project_board.py list --status "Todo"` | Lọc task theo trạng thái | **0 điểm** (Zero-API) |
| `python3 <skill_dir>/scripts/project_board.py list --remote` | Kéo dữ liệu tươi từ GitHub Project và cập nhật cache | 1 điểm GraphQL |
| `python3 <skill_dir>/scripts/project_board.py move <ID> "<Status>"` | Cập nhật spec cục bộ + di chuyển card trên Board | 1 điểm GraphQL (hoặc 0 nếu đẩy vào Outbox) |
| `python3 <skill_dir>/scripts/project_board.py push <spec-file>` | Tạo GitHub Issue qua REST và gắn card vào Project | 1 REST + 1 GraphQL |
| `python3 <skill_dir>/scripts/project_board.py sync` | Xả toàn bộ hàng đợi outbox offline lên GitHub | 1 điểm / mutation |
| `python3 <skill_dir>/scripts/project_board.py rate-limit` | Kiểm tra hạn ngạch REST/GraphQL còn lại và độ dài outbox | 1 điểm REST |
| `python3 <skill_dir>/scripts/project_board.py init --project <N>` | Khởi tạo file cấu hình `.github/project.json` | 1 điểm GraphQL |

---

## 💡 Lời Khuyên Cho AI Agent Khi Làm Việc

- **Luôn kiểm tra `rate-limit` trước khi chạy batch**: Chạy `project_board.py rate-limit` nếu nghi ngờ mạng chập chờn hoặc vừa thực hiện nhiều tác vụ.
- **Không ngần ngại khi outbox kích hoạt**: Nếu terminal báo `[RATE-LIMIT / SCOPE GUARD] Deferred GitHub Project update`, đừng lo lắng! File spec cục bộ đã được cập nhật chính xác trạng thái, Agent có thể tiếp tục công việc coding ngay mà không cần đợi.
- **Quy chuẩn định danh task**: Nên dùng định dạng `<PREFIX>-<NUMBER>` (ví dụ `TNG-01`, `FEAT-42`, `CORE-101`) trong tiêu đề file markdown để script tự động nhận diện và sắp xếp khoa học.
