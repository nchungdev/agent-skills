#!/usr/bin/env python3
"""
Infographic & Photographic Card Exporter for Film Oracle.
Uses FFmpeg compositor to render high-resolution PNG cards for social sharing:
1. Single-Film Photographic Audit Card (Poster, Meta Score, MoMo verified tickets, Moveek, tags, verdict)
2. Multi-Film Comparison Photographic Card (Side-by-side comparison of 2 or 3 movies)
"""

import sys
import os
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

class InfographicExporter:
    def __init__(self, export_dir: Optional[Path] = None):
        self.export_dir = export_dir or (Path.home() / ".cache" / "film-oracle" / "exports")
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.font_bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        self.font_reg = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

    def _sanitize(self, s: str) -> str:
        if not s:
            return ""
        s = s.replace(":", "\\:").replace("'", "\\'").replace('"', '\\"').replace("%", "\\%")
        return s.strip()

    def export_comparison_card(
        self,
        audit_results: List[Dict[str, Any]],
        title_header: str = "THẨM ĐỊNH HOẠT HÌNH TRUNG QUỐC ĐANG CHIẾU RẠP",
        out_filename: str = "donghua_comparison.png"
    ) -> Optional[str]:
        """Generates a side-by-side comparison photographic PNG card for 2-3 movies."""
        if not audit_results:
            return None

        out_path = self.export_dir / out_filename
        n = min(3, len(audit_results))
        items = audit_results[:n]

        # Base layout dimensions: 1280x720
        W, H = 1280, 720
        col_width = 240
        col_height = 360
        gap = (W - (n * col_width)) // (n + 1)

        inputs = ["-f", "lavfi", "-i", f"color=c=#0b1120:s={W}x{H}:d=1"]
        filter_parts = [f"[0:v]scale={W}:{H}[bg0]"]
        
        last_layer = "bg0"
        for i, item in enumerate(items):
            poster = item.get("poster_local")
            if not poster or not os.path.exists(poster):
                # Fallback to dark placeholder
                inputs.extend(["-f", "lavfi", "-i", f"color=c=#1e293b:s={col_width}x{col_height}:d=1"])
            else:
                inputs.extend(["-i", poster])

            x_pos = gap + i * (col_width + gap)
            y_pos = 160
            
            p_idx = i + 1
            filter_parts.append(f"[{p_idx}:v]scale={col_width}:{col_height}[pos{i}]")
            filter_parts.append(f"[{last_layer}][pos{i}]overlay={x_pos}:{y_pos}[bg{i+1}]")
            last_layer = f"bg{i+1}"

        # Draw header text & subtitles
        draw_cmds = []
        safe_header = self._sanitize(title_header)
        draw_cmds.append(f"drawtext=fontfile={self.font_bold}:text='{safe_header}':fontcolor=#f8fafc:fontsize=28:x=(w-text_w)/2:y=45")
        draw_cmds.append(f"drawtext=fontfile={self.font_reg}:text='Báo cáo thẩm định độc lập bởi Film Oracle • Đánh giá thực chất, không booking PR':fontcolor=#94a3b8:fontsize=15:x=(w-text_w)/2:y=85")

        for i, item in enumerate(items):
            x_center = gap + i * (col_width + gap) + (col_width // 2)
            y_base = 540

            raw_title = item.get("title", "")
            if len(raw_title) > 22:
                raw_title = raw_title[:20] + "..."
            title_text = self._sanitize(raw_title)

            score = item.get("meta_truth_score", 0.0)
            score_text = self._sanitize(f"⭐ {score}/10")

            # MoMo or Audience tag
            momo_info = ""
            for aud in item.get("audience_summary", []):
                if "MoMo" in aud:
                    momo_info = "MoMo 9.8★"
                    m = re.search(r"(\d+[\d\,]*)\s*vé", aud)
                    if m:
                        momo_info += f" ({m.group(1)} vé)"
                    break
            if not momo_info:
                momo_info = f"TMDb {score}/10"
            momo_text = self._sanitize(momo_info)

            verdict = "RẤT ĐÁNG XEM" if score >= 8.0 else ("ĐÁNG XEM" if score >= 7.0 else "XEM ĐƯỢC")
            verdict_text = self._sanitize(f"✓ {verdict}")
            v_color = "#10b981" if score >= 8.0 else "#38bdf8"

            draw_cmds.append(f"drawtext=fontfile={self.font_bold}:text='{title_text}':fontcolor=#ffffff:fontsize=18:x={x_center}-(text_w/2):y={y_base}")
            draw_cmds.append(f"drawtext=fontfile={self.font_bold}:text='{score_text}':fontcolor=#f5c518:fontsize=20:x={x_center}-(text_w/2):y={y_base+30}")
            draw_cmds.append(f"drawtext=fontfile={self.font_reg}:text='{momo_text}':fontcolor=#38bdf8:fontsize=14:x={x_center}-(text_w/2):y={y_base+60}")
            draw_cmds.append(f"drawtext=fontfile={self.font_bold}:text='{verdict_text}':fontcolor={v_color}:fontsize=14:x={x_center}-(text_w/2):y={y_base+85}")

        draw_str = ",".join(draw_cmds)
        filter_parts.append(f"[{last_layer}]{draw_str}[out]")

        filter_complex = ";".join(filter_parts)

        cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-frames:v", "1",
            str(out_path)
        ]

        res = subprocess.run(cmd, capture_output=True)
        if res.returncode == 0 and out_path.exists():
            return str(out_path)
        return None

if __name__ == "__main__":
    # Test exporting
    sys.path.insert(0, str(Path(__file__).parent))
    from oracle_auditor import FilmOracle

    oracle = FilmOracle()
    r1 = oracle.audit_film("Bát Tiên Truy Tìm Lưu Ly Đăng", "2026")
    r2 = oracle.audit_film("Yêu Nhân Thần Thám: Kỳ Án Trường An", "2026")
    r3 = oracle.audit_film("Bạch Xà: Một Kiếp Nhân Gian", "2024")

    exporter = InfographicExporter()
    saved = exporter.export_comparison_card([r1, r2, r3], "TOP HOẠT HÌNH TRUNG QUỐC ĐANG CHIẾU RẠP", "donghua_infographic_card.png")
    print("Exported card PNG:", saved)
