import os
import shutil
from pathlib import Path

def purge_local_cache(target_path):
    """Safely purge local staging buffer files."""
    p = Path(target_path)
    if not p.exists():
        return True

    try:
        if p.is_file():
            p.unlink()
            print(f"🗑️ [Auto-Purge] Đã xóa sạch file đệm: {p.name}")
        elif p.is_dir():
            shutil.rmtree(p)
            print(f"🗑️ [Auto-Purge] Đã dọn sạch thư mục đệm: {p.name}")
        return True
    except Exception as e:
        print(f"⚠️ [Auto-Purge] Lỗi khi dọn dẹp: {e}")
        return False
