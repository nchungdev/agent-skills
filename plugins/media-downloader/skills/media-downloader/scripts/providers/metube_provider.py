import json
import urllib.request
import urllib.error
import sys

def add_metube_download(url, subfolder=None, quality="best", metube_url="http://127.0.0.1:8081/add"):
    """
    Send video/stream URL to MeTube container via REST API.
    Tasks immediately appear in MeTube Web GUI (http://192.168.1.37:8081).
    """
    payload = {
        "url": url,
        "quality": quality,
        "format": "any",
        "auto_start": True
    }
    if subfolder:
        payload["folder"] = str(subfolder)

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        metube_url,
        data=data,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            print(f"✅ [MeTube] Đã gửi task tải vào MeTube Web GUI thành công!")
            print(f"🌐 Theo dõi queue và tiến độ trực quan tại: http://192.168.1.37:8081")
            return True
    except urllib.error.HTTPError as e:
        print(f"❌ [MeTube] Lỗi HTTP {e.code}: {e.read().decode('utf-8')}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"❌ [MeTube] Không thể kết nối tới MeTube ({metube_url}): {e}", file=sys.stderr)
        return False
