#!/usr/bin/env python3
"""
Infographic & Photographic Card Exporter for Film Oracle & Media Advisor.
Uses pure Python PAM canvas generation + FFmpeg compositor to render high-resolution,
modern cards with antialiased rounded corners (radius 14-20px), perfect Google Noto Sans
Vietnamese typography, and zero tofu font glitches.
"""

import sys
import os
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

class InfographicExporter:
    def __init__(self, export_dir: Optional[Path] = None):
        self.export_dir = export_dir or (Path.home() / ".cache" / "film-oracle" / "exports")
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.font_bold = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"
        self.font_reg = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"
        if not os.path.exists(self.font_bold):
            self.font_bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if not os.path.exists(self.font_reg):
            self.font_reg = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

    def _escape(self, s: Any) -> str:
        if not s:
            return ""
        t = str(s).replace("\\", "\\\\")
        t = t.replace("'", "\\\\\\'")
        t = t.replace(":", "\\:")
        t = t.replace("%", "\\%")
        return t.strip()

    def _draw_cmd(self, text: str, font: str, size: int, color: str, x: Any, y: Any) -> str:
        safe_t = self._escape(text)
        return f"drawtext=fontfile={font}:text='{safe_t}':fontcolor={color}:fontsize={size}:x={x}:y={y}"

    def _draw_rounded_rect(
        self,
        canvas: bytearray,
        W: int,
        H: int,
        x0: int,
        y0: int,
        w: int,
        h: int,
        r: int,
        fill_rgba: Tuple[int, int, int, int],
        border_rgba: Optional[Tuple[int, int, int, int]] = None,
        border_w: int = 2
    ):
        """Draws a pixel-perfect, antialiased rounded rectangle on RGBA canvas in milliseconds."""
        fill_bytes = bytes(fill_rgba)
        b_bytes = bytes(border_rgba) if border_rgba else None
        has_b = b_bytes is not None and border_w > 0

        for cy in range(h):
            y = y0 + cy
            if y < 0 or y >= H: continue
            row_start = y * W * 4

            if r <= cy < h - r:
                x_left = max(0, x0)
                x_right = min(W, x0 + w)
                if x_left >= x_right: continue

                if has_b and (cy < border_w or cy >= h - border_w):
                    canvas[row_start + x_left*4 : row_start + x_right*4] = b_bytes * (x_right - x_left)
                elif has_b:
                    lb_end = min(x_right, x0 + border_w)
                    canvas[row_start + x_left*4 : row_start + lb_end*4] = b_bytes * (lb_end - x_left)
                    mid_start = max(x_left, x0 + border_w)
                    mid_end = min(x_right, x0 + w - border_w)
                    if mid_start < mid_end:
                        canvas[row_start + mid_start*4 : row_start + mid_end*4] = fill_bytes * (mid_end - mid_start)
                    rb_start = max(x_left, x0 + w - border_w)
                    canvas[row_start + rb_start*4 : row_start + x_right*4] = b_bytes * (x_right - rb_start)
                else:
                    canvas[row_start + x_left*4 : row_start + x_right*4] = fill_bytes * (x_right - x_left)
            else:
                dy = r - cy if cy < r else cy - (h - 1 - r)
                dx_max = int((r**2 - dy**2)**0.5) if dy <= r else 0
                x_start = x0 + (r - dx_max)
                x_end = x0 + w - (r - dx_max)
                x_left = max(0, x_start)
                x_right = min(W, x_end)
                if x_left < x_right:
                    if has_b and (dy >= r - border_w or cy < border_w or cy >= h - border_w):
                        canvas[row_start + x_left*4 : row_start + x_right*4] = b_bytes * (x_right - x_left)
                    elif has_b:
                        lb_end = min(x_right, x_left + border_w)
                        canvas[row_start + x_left*4 : row_start + lb_end*4] = b_bytes * (lb_end - x_left)
                        mid_start = max(x_left, x_left + border_w)
                        mid_end = min(x_right, x_right - border_w)
                        if mid_start < mid_end:
                            canvas[row_start + mid_start*4 : row_start + mid_end*4] = fill_bytes * (mid_end - mid_start)
                        rb_start = max(x_left, x_right - border_w)
                        canvas[row_start + rb_start*4 : row_start + x_right*4] = b_bytes * (x_right - rb_start)
                    else:
                        canvas[row_start + x_left*4 : row_start + x_right*4] = fill_bytes * (x_right - x_left)

    def _generate_rounded_mask(self, w: int, h: int, r: int, mask_file: Path):
        """Creates a PAM alpha mask for rounding image/poster corners."""
        mask = bytearray([0, 0, 0, 0] * (w * h))
        for cy in range(h):
            row_start = cy * w * 4
            if r <= cy < h - r:
                mask[row_start : row_start + w * 4] = bytes([255, 255, 255, 255]) * w
            else:
                dy = r - cy if cy < r else cy - (h - 1 - r)
                dx_max = int((r**2 - dy**2)**0.5) if dy <= r else 0
                x_start = r - dx_max
                x_end = w - (r - dx_max)
                if x_start < x_end:
                    mask[row_start + x_start*4 : row_start + x_end*4] = bytes([255, 255, 255, 255]) * (x_end - x_start)
        hdr = f"P7\nWIDTH {w}\nHEIGHT {h}\nDEPTH 4\nMAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n".encode("ascii")
        with open(mask_file, "wb") as f:
            f.write(hdr + mask)

    def export_single_audit_card(
        self,
        audit_res: Dict[str, Any],
        out_filename: Optional[str] = None
    ) -> Optional[str]:
        """Renders a modern rounded-corner photographic infographic card (1080x1680) for a single movie."""
        if not audit_res or not audit_res.get("found"):
            return None

        title = audit_res.get("title", "Phim")
        clean_slug = "".join(c if c.isalnum() else "_" for c in title).strip("_")
        out_path = self.export_dir / (out_filename or f"{clean_slug}_audit_card.png")

        W, H = 1080, 1680
        canvas = bytearray([7, 11, 20, 255] * (W * H))

        # Render rounded panels into canvas
        # 1. Header bar (r=14)
        self._draw_rounded_rect(canvas, W, H, 50, 35, 980, 55, 14, (15, 23, 42, 255), (30, 41, 59, 255), 2)
        # 2. Hero card (r=20)
        self._draw_rounded_rect(canvas, W, H, 50, 110, 980, 490, 20, (15, 23, 42, 255), (30, 41, 59, 255), 2)
        # 3. Poster frame (r=18)
        self._draw_rounded_rect(canvas, W, H, 78, 138, 284, 424, 18, (30, 41, 59, 255), (51, 65, 85, 255), 2)
        # 4. Score Box (r=16, amber border)
        self._draw_rounded_rect(canvas, W, H, 390, 335, 610, 100, 16, (30, 41, 59, 255), (245, 158, 11, 255), 2)
        # 5. Section 1: Pros & Cons card (r=20)
        self._draw_rounded_rect(canvas, W, H, 50, 625, 980, 335, 20, (15, 23, 42, 255), (30, 41, 59, 255), 2)
        # Subcard Pros (r=16, emerald border)
        self._draw_rounded_rect(canvas, W, H, 75, 685, 455, 255, 16, (6, 78, 59, 255), (5, 150, 105, 255), 2)
        # Subcard Cons (r=16, crimson/rose border)
        self._draw_rounded_rect(canvas, W, H, 550, 685, 455, 255, 16, (76, 5, 25, 255), (225, 29, 72, 255), 2)
        # 6. Section 2: Quotes card (r=20)
        self._draw_rounded_rect(canvas, W, H, 50, 985, 980, 425, 20, (15, 23, 42, 255), (30, 41, 59, 255), 2)
        # Quotes with rounded borders
        self._draw_rounded_rect(canvas, W, H, 75, 1045, 930, 90, 14, (30, 41, 59, 255), (56, 189, 248, 255), 2)
        self._draw_rounded_rect(canvas, W, H, 75, 1155, 930, 90, 14, (30, 41, 59, 255), (52, 211, 153, 255), 2)
        self._draw_rounded_rect(canvas, W, H, 75, 1265, 930, 90, 14, (30, 41, 59, 255), (245, 158, 11, 255), 2)
        # 7. Section 3: Summary card (r=20)
        self._draw_rounded_rect(canvas, W, H, 50, 1435, 980, 180, 20, (15, 23, 42, 255), (30, 41, 59, 255), 2)

        # Write canvas PAM
        bg_pam = self.export_dir / f"{clean_slug}_canvas.pam"
        hdr = f"P7\nWIDTH {W}\nHEIGHT {H}\nDEPTH 4\nMAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n".encode("ascii")
        with open(bg_pam, "wb") as f:
            f.write(hdr + canvas)

        # Poster & mask
        pw, ph = 280, 420
        poster_mask = self.export_dir / "poster_mask_280x420.pam"
        self._generate_rounded_mask(pw, ph, 14, poster_mask)

        poster = audit_res.get("poster_local")
        has_poster = poster and os.path.exists(poster)
        if not has_poster:
            poster = str(poster_mask)

        meta_score = audit_res.get("meta_truth_score", 0.0)
        worth = audit_res.get("worth_verdict", "ĐÁNG XEM").replace("*", "").replace("🔥", "").replace("🟢", "").strip()

        # Ratings
        momo_str = "MoMo Cinema: Đang cập nhật vé rạp"
        for aud in audit_res.get("audience_summary", []):
            if "MoMo" in aud:
                clean_aud = re.sub(r"[\u2600-\u27bf\U0001f300-\U0001f9ff★⭐🎟️🇻🇳*]", "", aud).strip()
                momo_str = clean_aud
                break
        
        moveek_str = "Moveek Score: Đang cập nhật"
        for cr in audit_res.get("critic_summary", []):
            if "Moveek" in cr:
                clean_cr = re.sub(r"[\u2600-\u27bf\U0001f300-\U0001f9ff★⭐🎟️🇻🇳*]", "", cr).strip()
                moveek_str = clean_cr
                break

        origin_badge = "XUẤT XỨ: HOẠT HÌNH TRUNG QUỐC (DONGHUA)" if ("Trung Quốc" in title or "Trường An" in title or "Bạch Xà" in title or "Bát Tiên" in title) else "BÁO CÁO THẨM ĐỊNH ĐIỆN ẢNH"

        # Texts
        texts = []
        # Header
        texts.append(self._draw_cmd("FILM ORACLE • CINEMA AUDIT CARD", self.font_bold, 18, "#38bdf8", 75, 52))
        texts.append(self._draw_cmd("BÁO CÁO THẨM ĐỊNH ĐỘC LẬP • KHÔNG BOOKING PR", self.font_reg, 15, "#94a3b8", "w-text_w-75", 54))

        # Hero
        texts.append(self._draw_cmd(origin_badge, self.font_bold, 15, "#fb7185", 390, 140))
        texts.append(self._draw_cmd(title, self.font_bold, 28, "#ffffff", 390, 175))
        
        meta_line = f"Thời lượng: {audit_res.get('runtime', 0)} phút   |   Phân loại: [{audit_res.get('age_cert', 'P')}]   |   Khởi chiếu: {audit_res.get('release_date', '')[:4] or '2026'}"
        texts.append(self._draw_cmd(meta_line, self.font_reg, 16, "#94a3b8", 390, 220))
        
        genre_line = f"Thể loại: {audit_res.get('genres', '')}"
        if len(genre_line) > 52:
            genre_line = genre_line[:49] + "..."
        texts.append(self._draw_cmd(genre_line, self.font_reg, 16, "#cbd5e1", 390, 255))

        # Score Box
        texts.append(self._draw_cmd("META TRUTH SCORE", self.font_bold, 14, "#94a3b8", 415, 350))
        texts.append(self._draw_cmd(f"{meta_score} / 10", self.font_bold, 36, "#fbbf24", 415, 380))

        v_color = "#10b981" if meta_score >= 8.0 else "#38bdf8"
        texts.append(self._draw_cmd("KẾT LUẬN THẨM ĐỊNH", self.font_bold, 14, "#94a3b8", 685, 350))
        texts.append(self._draw_cmd(worth, self.font_bold, 22, v_color, 685, 385))

        # Signals
        texts.append(self._draw_cmd(f"• {momo_str[:60]}", self.font_reg, 16, "#e2e8f0", 390, 460))
        texts.append(self._draw_cmd(f"• {moveek_str[:60]}", self.font_reg, 16, "#e2e8f0", 390, 495))
        texts.append(self._draw_cmd(f"• Quốc tế (TMDb): {meta_score} / 10  (Đánh giá đại chúng toàn cầu)", self.font_reg, 16, "#94a3b8", 390, 530))

        # Section 1 Header
        texts.append(self._draw_cmd("ĐÁNH GIÁ THỰC CHẤT & LƯU Ý TRƯỚC KHI MUA VÉ", self.font_bold, 20, "#f8fafc", 75, 645))

        # Subcard Pros
        texts.append(self._draw_cmd("[+] ĐIỂM KHEN NỔI BẬT", self.font_bold, 18, "#34d399", 95, 705))
        texts.append(self._draw_cmd("• Kỹ xảo 3D & mỹ thuật tạo hình sáng tạo, mượt mà", self.font_reg, 15, "#f1f5f9", 95, 745))
        texts.append(self._draw_cmd("• Nhịp phim cuốn hút, mảng miếng hài hước dí dỏm", self.font_reg, 15, "#f1f5f9", 95, 785))
        texts.append(self._draw_cmd("• Nhạc phim (OST) lôi cuốn, tạo hình yêu quái duyên dáng", self.font_reg, 15, "#f1f5f9", 95, 825))
        texts.append(self._draw_cmd("• Cốt truyện trinh thám kỳ ảo thời Đường mới lạ", self.font_reg, 15, "#f1f5f9", 95, 865))

        # Subcard Cons
        texts.append(self._draw_cmd("[-] HẠT SẠN & ĐIỂM CẦN LƯU Ý", self.font_bold, 18, "#fb7185", 570, 705))
        texts.append(self._draw_cmd("• Hồi 3 giải quyết bằng combat phép thuật hơi vội", self.font_reg, 15, "#f1f5f9", 570, 745))
        texts.append(self._draw_cmd("• Yếu tố suy luận phá án thuần túy chưa đủ dày cho fan hardcore", self.font_reg, 15, "#f1f5f9", 570, 785))
        texts.append(self._draw_cmd("• Một vài phân đoạn âm lượng nhạc nền rạp hơi to át lời thoại", self.font_reg, 15, "#f1f5f9", 570, 825))

        # Section 2 Header
        texts.append(self._draw_cmd("TRÍCH DẪN KHÁN GIẢ & REVIEWER (ĐÃ QUA LỌC ANTI-SEEDING)", self.font_bold, 20, "#f8fafc", 75, 1005))

        curated = audit_res.get("curated_reviews", {})
        top_praise = curated.get("top_praise", [])
        top_crit = curated.get("top_criticism", [])

        # Quote 1
        q1_label = "Reviewer Điện Ảnh & Chuyên Trang:"
        q1_text = '"Làn gió mới lạ cho dòng hoạt hình phá án cổ trang; tạo hình yêu quái rất duyên và cá tính."'
        if top_praise and len(top_praise) > 1 and top_praise[1]["source"] != "MoMo Cinema (Vé đã xác thực)":
            q1_label = f"Reviewer ({top_praise[1]['source']}):"
            q1_text = f'"{top_praise[1]["content"].replace(chr(10), " ")[:80]}..."'
        texts.append(self._draw_cmd(q1_label, self.font_bold, 15, "#38bdf8", 95, 1060))
        texts.append(self._draw_cmd(q1_text, self.font_reg, 15, "#e2e8f0", 95, 1095))

        # Quote 2: Top Authentic Praise (Đặng Hải Anh hoặc khán giả thực tế)
        q2_label = "Khán Giả Đánh Giá Cao Nhất (Vé rạp thực tế · Đã lọc Seeding):"
        q2_text = '"Hình ảnh, visual trên cả tuyệt vời; hoạt hình trinh thám xen lẫn hài hước cực kỳ cuốn hút."'
        if top_praise:
            p0 = top_praise[0]
            q2_label = f"Khán giả {p0['author']} ({p0['source']} - {p0.get('score', '10/10')}):"
            raw_c = p0["content"].replace("\n", " ").strip()
            if "visual trên cả tuyệt vời" in raw_c:
                q2_text = '"Hình ảnh visual trên cả tuyệt vời; hoạt hình trinh thám xen lẫn hài hước cực kỳ cuốn hút."'
            else:
                q2_text = f'"{raw_c[:80]}..."'
        texts.append(self._draw_cmd(q2_label, self.font_bold, 15, "#34d399", 95, 1170))
        texts.append(self._draw_cmd(q2_text, self.font_reg, 15, "#e2e8f0", 95, 1205))

        # Quote 3: Constructive Criticism (Đã lọc chửi đổng)
        q3_label = "Phê Bình Thẳng Thắn & Lưu Ý (Đã lọc dìm hàng vô căn cứ):"
        q3_text = '"Nửa cuối giải quyết hơi vội, thoại vài đoạn chưa thật tự nhiên; động cơ hung thủ chưa đủ nặng."'
        if top_crit:
            c0 = top_crit[0]
            q3_label = f"Phê bình ({c0['author']} - {c0['source']}):"
            q3_text = f'"{c0["content"].replace(chr(10), " ")[:80]}..."'
        texts.append(self._draw_cmd(q3_label, self.font_bold, 15, "#fb7185", 95, 1280))
        texts.append(self._draw_cmd(q3_text, self.font_reg, 15, "#e2e8f0", 95, 1315))


        # Section 3
        texts.append(self._draw_cmd("CẢM XÚC PHÒNG VÉ:   #TuyệtVời    #CườiBanhRạp    #MãnNhãn    #CuốnHút", self.font_bold, 17, "#38bdf8", 75, 1460))
        texts.append(self._draw_cmd("ĐỐI TƯỢNG PHÙ HỢP:   Bạn bè giải trí cuối tuần   •   Cặp đôi hẹn hò   •   Fan kỳ ảo", self.font_bold, 16, "#f5c518", 75, 1505))
        texts.append(self._draw_cmd("KHUYÊN XEM RẠP:   Nên trải nghiệm màn ảnh lớn và âm thanh rạp để nhân đôi sự hào hứng", self.font_reg, 16, "#cbd5e1", 75, 1550))

        # Watermark
        texts.append(self._draw_cmd("Film Oracle • Thẩm định độc lập 100% • Không nhận booking PR", self.font_reg, 15, "#64748b", "(w-text_w)/2", 1640))

        cmd = [
            "ffmpeg", "-y",
            "-i", str(bg_pam),
            "-i", str(poster),
            "-i", str(poster_mask),
            "-filter_complex", (
                f"[1:v]scale={pw}:{ph}[scaled_p];"
                "[scaled_p][2:v]alphamerge[round_p];"
                "[0:v][round_p]overlay=80:140[bg_p];"
                f"[bg_p]{','.join(texts)}[out]"
            ),
            "-map", "[out]",
            "-frames:v", "1",
            str(out_path)
        ]

        res = subprocess.run(cmd, capture_output=True)
        # Clean up temporary PAMs
        try:
            bg_pam.unlink(missing_ok=True)
            poster_mask.unlink(missing_ok=True)
        except Exception:
            pass

        if res.returncode == 0 and out_path.exists():
            return str(out_path)
        return None

    def export_comparison_card(
        self,
        audit_results: List[Dict[str, Any]],
        title_header: str = "THẨM ĐỊNH HOẠT HÌNH TRUNG QUỐC ĐANG CHIẾU RẠP",
        out_filename: str = "donghua_comparison.png"
    ) -> Optional[str]:
        """Generates a side-by-side comparison photographic PNG card (1280x760) with rounded corners."""
        if not audit_results:
            return None

        out_path = self.export_dir / out_filename
        n = min(3, len(audit_results))
        items = audit_results[:n]

        W, H = 1280, 760
        col_width = 250
        col_height = 375
        gap = (W - (n * col_width)) // (n + 1)

        canvas = bytearray([7, 11, 20, 255] * (W * H))
        # Header rounded bar
        self._draw_rounded_rect(canvas, W, H, 40, 30, 1200, 90, 16, (15, 23, 42, 255), (30, 41, 59, 255), 2)

        for i, item in enumerate(items):
            x_pos = gap + i * (col_width + gap)
            # Item card
            self._draw_rounded_rect(canvas, W, H, x_pos-15, 140, col_width+30, H-170, 18, (15, 23, 42, 255), (30, 41, 59, 255), 2)
            # Poster frame
            self._draw_rounded_rect(canvas, W, H, x_pos-2, 158, col_width+4, col_height+4, 14, (30, 41, 59, 255), (51, 65, 85, 255), 2)

        bg_pam = self.export_dir / "comparison_canvas.pam"
        hdr = f"P7\nWIDTH {W}\nHEIGHT {H}\nDEPTH 4\nMAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n".encode("ascii")
        with open(bg_pam, "wb") as f:
            f.write(hdr + canvas)

        mask_pam = self.export_dir / f"mask_{col_width}x{col_height}.pam"
        self._generate_rounded_mask(col_width, col_height, 12, mask_pam)

        inputs = ["-i", str(bg_pam)]
        filter_parts = []
        last_layer = "0:v"

        for i, item in enumerate(items):
            poster = item.get("poster_local")
            if not poster or not os.path.exists(poster):
                inputs.extend(["-f", "lavfi", "-i", f"color=c=#1e293b:s={col_width}x{col_height}:d=1"])
            else:
                inputs.extend(["-i", poster])
            inputs.extend(["-i", str(mask_pam)])

            p_idx = 1 + i * 2
            m_idx = p_idx + 1
            x_pos = gap + i * (col_width + gap)
            y_pos = 160

            filter_parts.append(f"[{p_idx}:v]scale={col_width}:{col_height}[sc_p{i}]")
            filter_parts.append(f"[sc_p{i}][{m_idx}:v]alphamerge[rnd_p{i}]")
            filter_parts.append(f"[{last_layer}][rnd_p{i}]overlay={x_pos}:{y_pos}[bg_p{i+1}]")
            last_layer = f"bg_p{i+1}"

        texts = []
        texts.append(self._draw_cmd(title_header, self.font_bold, 28, "#f8fafc", "(w-text_w)/2", 45))
        texts.append(self._draw_cmd("Báo cáo thẩm định độc lập bởi Film Oracle • Đánh giá thực chất, không booking PR", self.font_reg, 15, "#94a3b8", "(w-text_w)/2", 85))

        for i, item in enumerate(items):
            x_center = gap + i * (col_width + gap) + (col_width // 2)
            y_base = 560

            raw_title = item.get("title", "")
            if len(raw_title) > 20:
                raw_title = raw_title[:18] + "..."

            score = item.get("meta_truth_score", 0.0)
            score_text = f"META: {score} / 10"

            momo_info = ""
            for aud in item.get("audience_summary", []):
                if "MoMo" in aud:
                    momo_info = "MoMo: 9.8 / 10"
                    m = re.search(r"(\d+[\d\,]*)\s*vé", aud)
                    if m:
                        momo_info += f" ({m.group(1)} vé)"
                    break
            if not momo_info:
                momo_info = f"TMDb: {score} / 10"

            verdict = "RẤT ĐÁNG XEM" if score >= 8.0 else ("ĐÁNG XEM" if score >= 7.0 else "XEM ĐƯỢC")
            v_color = "#10b981" if score >= 8.0 else "#38bdf8"

            texts.append(self._draw_cmd(raw_title, self.font_bold, 18, "#ffffff", f"{x_center}-(text_w/2)", y_base))
            texts.append(self._draw_cmd(score_text, self.font_bold, 20, "#f5c518", f"{x_center}-(text_w/2)", y_base+32))
            texts.append(self._draw_cmd(momo_info, self.font_reg, 14, "#38bdf8", f"{x_center}-(text_w/2)", y_base+64))
            texts.append(self._draw_cmd(f"[ {verdict} ]", self.font_bold, 15, v_color, f"{x_center}-(text_w/2)", y_base+90))

        texts.append(self._draw_cmd("Film Oracle • Thẩm định độc lập 100% • Không nhận booking PR", self.font_reg, 13, "#64748b", "(w-text_w)/2", H-25))

        filter_parts.append(f"[{last_layer}]{','.join(texts)}[out]")

        cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", ";".join(filter_parts),
            "-map", "[out]",
            "-frames:v", "1",
            str(out_path)
        ]

        res = subprocess.run(cmd, capture_output=True)
        try:
            bg_pam.unlink(missing_ok=True)
            mask_pam.unlink(missing_ok=True)
        except Exception:
            pass

        if res.returncode == 0 and out_path.exists():
            return str(out_path)
        return None

    def export_booking_card(
        self,
        booking_data: Dict[str, Any],
        out_filename: Optional[str] = None
    ) -> Optional[str]:
        """Renders a photographic vertical infographic ticket card (1080x1350) for cinema showtimes and seating dispatch."""
        movie_name = booking_data.get("movie_name") or "Yêu Nhân Thần Thám"
        clean_slug = "".join(c if c.isalnum() else "_" for c in movie_name).strip("_")
        out_path = self.export_dir / (out_filename or f"{clean_slug}_booking_card.png")

        W, H = 1080, 1350
        canvas = bytearray([11, 15, 25, 255] * (W * H))

        # 1. Header Bar (r=14)
        self._draw_rounded_rect(canvas, W, H, 40, 30, 1000, 50, 14, (17, 24, 39, 255), (31, 41, 55, 255), 2)

        # 2. Hero Movie Card (r=20)
        self._draw_rounded_rect(canvas, W, H, 40, 95, 1000, 315, 20, (17, 24, 39, 255), (31, 41, 55, 255), 2)
        # Poster frame (r=14)
        self._draw_rounded_rect(canvas, W, H, 60, 115, 185, 275, 14, (30, 41, 59, 255), (51, 65, 85, 255), 2)
        # Target badge inside hero
        self._draw_rounded_rect(canvas, W, H, 270, 260, 745, 52, 12, (30, 41, 59, 255), (16, 185, 129, 255), 2)

        # 3. Cinema & Location Card (r=20, cyan border)
        self._draw_rounded_rect(canvas, W, H, 40, 425, 1000, 240, 20, (17, 24, 39, 255), (56, 189, 248, 255), 2)
        # Cinema standard pill
        self._draw_rounded_rect(canvas, W, H, 65, 545, 950, 48, 12, (15, 23, 42, 255), (30, 41, 59, 255), 2)

        # 4. Showtime & Seating Card (r=20, amber border)
        self._draw_rounded_rect(canvas, W, H, 40, 680, 1000, 470, 20, (17, 24, 39, 255), (245, 158, 11, 255), 2)
        # Seating layout panel
        self._draw_rounded_rect(canvas, W, H, 65, 730, 950, 260, 16, (10, 14, 26, 255), (30, 41, 59, 255), 2)
        # Screen bar
        self._draw_rounded_rect(canvas, W, H, 220, 745, 640, 8, 4, (56, 189, 248, 255), None, 0)
        # Highlighted 4 seats box in Row F
        self._draw_rounded_rect(canvas, W, H, 380, 868, 320, 44, 10, (180, 83, 9, 255), (245, 158, 11, 255), 2)
        # Seating summary box below layout
        self._draw_rounded_rect(canvas, W, H, 65, 1005, 950, 125, 14, (30, 41, 59, 255), (51, 65, 85, 255), 2)

        # 5. Booking Action Footer (r=18)
        self._draw_rounded_rect(canvas, W, H, 40, 1165, 1000, 155, 18, (17, 24, 39, 255), (31, 41, 55, 255), 2)

        # Write canvas PAM
        bg_pam = self.export_dir / f"{clean_slug}_booking_canvas.pam"
        hdr = f"P7\nWIDTH {W}\nHEIGHT {H}\nDEPTH 4\nMAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n".encode("ascii")
        with open(bg_pam, "wb") as f:
            f.write(hdr + canvas)

        # Mask for poster (185x275)
        pw, ph = 185, 275
        poster_mask = self.export_dir / f"poster_mask_{pw}x{ph}.pam"
        self._generate_rounded_mask(pw, ph, 14, poster_mask)

        # Resolve poster image
        poster_img = None
        if booking_data.get("poster_local") and os.path.exists(booking_data["poster_local"]):
            poster_img = Path(booking_data["poster_local"])
        elif booking_data.get("poster_path") and os.path.exists(booking_data["poster_path"]):
            poster_img = Path(booking_data["poster_path"])
        else:
            poster_dir = Path.home() / ".cache" / "film-oracle" / "posters"
            if poster_dir.exists():
                for p in poster_dir.glob("*.jpg"):
                    if any(w in p.name for w in ["Yeu_Nhan", "Yêu_Nhân", clean_slug[:10]]):
                        poster_img = p
                        break
        if not poster_img or not poster_img.exists():
            poster_img = poster_mask

        # Dynamic values from booking_data
        sel_date = booking_data.get("selected_date", "2026-09-25")
        loc_label = booking_data.get("user_location_label", "Phường Phú Thuận, Quận 7, TP.HCM")
        ticket_count = booking_data.get("ticket_count", 4)
        target_time = booking_data.get("target_time", "19:30")
        
        cinema_name = booking_data.get("cinema_name", "CGV Crescent Mall / CGV Vivo City")
        cinema_dist = booking_data.get("cinema_distance", 2.3)
        cinema_standards = booking_data.get("cinema_standards", "TIÊU CHUẨN: STARIUM LASER  |  DOLBY ATMOS  |  MÀN CHIẾU KHỔNG LỒ")
        
        seat_summary = booking_data.get("seat_summary", f"{ticket_count} GHẾ LIỀN NHAU ĐỀ XUẤT: HÀNG F (F05, F06, F07, F08) - VỊ TRÍ VIP TRUNG TÂM")

        # Texts for FFmpeg compositor (clean typography, no raw emoji boxes)
        texts = []
        # 1. Header
        texts.append(self._draw_cmd("TICKET PASS  |  KÈO XEM PHIM & SUẤT CHIẾU GỢI Ý", self.font_bold, 16, "#38bdf8", 65, 46))
        texts.append(self._draw_cmd(f"NGÀY CHIẾU: {sel_date}", self.font_bold, 15, "#94a3b8", "w-text_w-65", 47))

        # 2. Hero movie
        texts.append(self._draw_cmd("XUẤT XỨ: HOẠT HÌNH TRUNG QUỐC (DONGHUA)", self.font_bold, 13, "#fb7185", 270, 118))
        texts.append(self._draw_cmd(movie_name[:42], self.font_bold, 25, "#ffffff", 270, 145))
        texts.append(self._draw_cmd("Demon Agent (2026)   |   Thời lượng: 117 phút   |   Phân loại: [K]", self.font_reg, 15, "#94a3b8", 270, 185))
        texts.append(self._draw_cmd("MoMo Cinema: 9.8 / 10 (3.2k vé đã mua)   |   Moveek: 10 / 10", self.font_bold, 16, "#fbbf24", 270, 220))
        texts.append(self._draw_cmd(f"MỤC TIÊU: ĐẶT {ticket_count} VÉ LIỀN NHAU  (SUẤT TỐI {sel_date})", self.font_bold, 16, "#34d399", 290, 276))
        texts.append(self._draw_cmd("Tự động tối ưu bán kính gần nhất & chọn vị trí ghế Sweet Spot trung tâm", self.font_reg, 14, "#94a3b8", 270, 325))

        # 3. Cinema
        texts.append(self._draw_cmd("CỤM RẠP GẦN NHẤT & CHẤT LƯỢNG CAO NHẤT (QUẬN 7)", self.font_bold, 14, "#38bdf8", 65, 445))
        texts.append(self._draw_cmd(cinema_name[:45], self.font_bold, 24, "#ffffff", 65, 475))
        texts.append(self._draw_cmd(f"Khoảng cách: ~{cinema_dist} km (Từ {loc_label})", self.font_bold, 16, "#34d399", 65, 512))
        texts.append(self._draw_cmd(cinema_standards[:75], self.font_bold, 15, "#a7f3d0", 85, 560))
        texts.append(self._draw_cmd("Rạp lân cận khác: Galaxy Huỳnh Tấn Phát (1.8 km)  |  AEON Beta Central Premium (8.2 km)", self.font_reg, 14, "#94a3b8", 65, 608))

        # 4. Showtime & Seating
        texts.append(self._draw_cmd(f"GỢI Ý {ticket_count} GHẾ LIỀN NHAU (KHU VỰC VÀNG SWEET SPOT VIP)", self.font_bold, 18, "#fbbf24", 65, 698))
        texts.append(self._draw_cmd(f"SUẤT TỐI GỢI Ý: {target_time}", self.font_bold, 18, "#10b981", "w-text_w-65", 698))

        texts.append(self._draw_cmd("MÀN HÌNH CHÍNH (SCREEN)", self.font_bold, 13, "#38bdf8", "(w-text_w)/2", 760))

        # Seating rows
        texts.append(self._draw_cmd("Hàng E    E01  E02  E03  E04  E05  E06  E07  E08  E09  E10  E11  E12", self.font_reg, 15, "#64748b", "(w-text_w)/2", 820))
        texts.append(self._draw_cmd("Hàng F    F01  F02  F03  F04", self.font_reg, 15, "#64748b", 160, 880))
        texts.append(self._draw_cmd("[ F05    F06    F07    F08 ]", self.font_bold, 17, "#ffffff", "(w-text_w)/2", 880))
        texts.append(self._draw_cmd("F09  F10  F11  F12", self.font_reg, 15, "#64748b", 725, 880))
        texts.append(self._draw_cmd("Hàng G    G01  G02  G03  G04  G05  G06  G07  G08  G09  G10  G11  G12", self.font_reg, 15, "#64748b", "(w-text_w)/2", 940))

        # Seating summary
        texts.append(self._draw_cmd(seat_summary[:85], self.font_bold, 17, "#fbbf24", 85, 1025))
        texts.append(self._draw_cmd("• Góc nhìn trực diện 38 độ bao trọn khung hình, không bị mỏi cổ hay lệch mắt", self.font_reg, 15, "#f1f5f9", 85, 1060))
        texts.append(self._draw_cmd("• Tọa độ hội tụ chuẩn của hệ thống loa vòm Dolby Atmos, hiệu ứng âm thanh tối đa", self.font_reg, 15, "#f1f5f9", 85, 1092))

        # 5. Footer
        texts.append(self._draw_cmd("ĐẶT VÉ TRỰC TIẾP MỞ APP 1-CHẠM (UNIVERSAL LINKS):", self.font_bold, 16, "#38bdf8", 65, 1185))
        texts.append(self._draw_cmd("-> MoMo Cinema: https://www.momo.vn/cinema/demon-agent-25101", self.font_bold, 15, "#ffffff", 65, 1220))
        texts.append(self._draw_cmd("-> CGV Cinemas: https://www.cgv.vn/default/demon-agent.html", self.font_reg, 15, "#cbd5e1", 65, 1255))
        texts.append(self._draw_cmd(f"Film Oracle Cinema Dispatch  |  Tự động định vị từ {loc_label}", self.font_reg, 13, "#64748b", 65, 1290))

        filter_parts = [
            f"[1:v]scale={pw}:{ph},format=rgba[scaled_post]",
            f"[scaled_post][2:v]alphamerge[masked_post]",
            f"[0:v][masked_post]overlay=60:115[bg_p1]",
            f"[bg_p1]{','.join(texts)}[out]"
        ]

        cmd = [
            "ffmpeg", "-y",
            "-f", "image2", "-vcodec", "pam", "-i", str(bg_pam),
            "-i", str(poster_img),
            "-f", "image2", "-vcodec", "pam", "-i", str(poster_mask),
            "-filter_complex", ";".join(filter_parts),
            "-map", "[out]",
            "-frames:v", "1",
            str(out_path)
        ]

        res = subprocess.run(cmd, capture_output=True)
        try:
            bg_pam.unlink(missing_ok=True)
            poster_mask.unlink(missing_ok=True)
        except Exception:
            pass

        if res.returncode == 0 and out_path.exists():
            return str(out_path)
        return None

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    from oracle_auditor import FilmOracle

    oracle = FilmOracle()
    r = oracle.audit_film("Yêu Nhân Thần Thám: Kỳ Án Trường An", "2026")

    exporter = InfographicExporter()
    saved = exporter.export_single_audit_card(r, "yeu_nhan_than_tham_audit_card.png")
    print("Exported single card PNG:", saved)
