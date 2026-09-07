# Cạm Bẫy Thực Chiến & Bài Học Kinh Nghiệm (Errors & Pitfalls)

Tài liệu này tổng hợp các cạm bẫy thực chiến đúc kết từ việc căn chỉnh phụ đề frame-perfect trên hàng trăm tập phim thực tế.

---

## 1. Hiện Tượng Quá Tải Đầu Đọc HDD Khi Trích Xuất Sóng Âm (Disk Head Thrashing)
* **Triệu chứng:** Khi dùng `ThreadPoolExecutor(max_workers=3)` hoặc chạy nhiều lệnh FFmpeg cùng lúc trên máy chủ NAS / ổ cứng HDD cơ khí, tốc độ đọc giảm nghiêm trọng từ $150\text{ MB/s}$ xuống chỉ còn $3 - 5\text{ MB/s}$, một tập phim mất tới $50\text{s} - 60\text{s}$ thay vì $3\text{s} - 12\text{s}$.
* **Nguyên nhân cốt lõi:** Ổ đĩa HDD cơ khí chỉ có 1 cụm đầu đọc vật lý. Khi 3 tiến trình FFmpeg cùng lúc seek vào các vị trí khác nhau trên đĩa, đầu đọc phải nhảy qua lại liên tục (Head Thrashing).
* **Giải pháp chuẩn:** 
  * Trên ổ cứng HDD hoặc Storage Pool (MergerFS / Unraid): **Bắt buộc chạy tuần tự từng file (`max_workers=1`)**.
  * Chế độ đọc tuần tự (Sequential I/O) giúp đạt trọn vẹn băng thông tối đa của đĩa, rút ngắn thời gian xử lý toàn bộ mùa phim xuống mức tối thiểu.
  * Chỉ dùng đa luồng khi dữ liệu nằm hoàn toàn trên ổ cứng NVMe / SSD.

---

## 2. Bẫy Tên Style Hội Thoại Trong File ASS Của Các Đội Fansub
* **Triệu chứng:** Script chạy báo thành công nhưng chỉ căn chỉnh được $1 - 3$ câu thoại, bỏ sót $99\%$ hội thoại còn lại trong phim.
* **Nguyên nhân:** Các đội fansub (đặc biệt là sub tiếng Hoa hoặc sub anime cũ) sử dụng nhiều tên style khác nhau cho thoại chính:
  * Phổ biến: `Default`
  * Bản mở rộng Aegisub: `*Default` (có dấu hoa thị phía trước)
  * Bản dịch TVB/fansub: `text`, `Main`, `Default-Italic`
* **Giải pháp chuẩn:** 
  * Bộ lọc style phải quét đồng thời cả `Default`, `*Default`, `text`, `Main`.
  * Không bao giờ giả định file ASS chỉ dùng duy nhất 1 style `Default`.

---

## 3. Khóa Bảo Vệ KFX Animation & Bài Hát (Style Lock Protocol)
* **Triệu chứng:** Lời bài hát Opening/Ending bị lệch nhịp sau khi căn chỉnh, hoặc hiệu ứng chiêu thức (KFX zoom/pop) bị mất nhịp hô của nhân vật.
* **Nguyên nhân:** Âm thanh bài hát có nhạc đệm (BGM) lớn khiến bộ phát hiện giọng nói VAD bắt nhầm tiếng trống/beat thành tiếng người, làm trôi dạt timestamp của các câu hát vốn đã được timing karaoke chuẩn từ trước.
* **Giải pháp chuẩn:**
  * Khóa tuyệt đối mọi style mang tiền tố:
    * Nhạc phim: `Song-OP`, `Song-ED`, `Song-*`
    * Bảng tựa đề: `title*`
    * Chiêu thức hoạt họa: `summon-*`, `atk-*`, `transform-*`
  * Chỉ can thiệp vào các câu thoại đối thoại thông thường của nhân vật.

---

## 4. Xử Lý Đường Dẫn Media Chứa Tag TVDB / TMDb (`{tvdb-...}`)
* **Triệu chứng:** Báo lỗi `NameError: name 'tvdb' is not defined` hoặc `KeyError` khi chạy Python script.
* **Nguyên nhân:** Tên thư mục media tuân thủ quy chuẩn Plex/Jellyfin thường chứa `{tvdb-227501}`, `{tmdb-19612}`. Trong Python f-string (`f"..."`), dấu ngoặc nhọn `{...}` bị hiểu nhầm là biểu thức tính toán.
* **Giải pháp chuẩn:**
  * Tuyệt đối không nhúng đường dẫn trực tiếp vào f-string.
  * Sử dụng `os.path.join()`, `pathlib.Path()`, hoặc chuỗi thường không có tiền tố `f`.
  * Trong lệnh shell `python3 -c '...'`, luôn bọc nháy đơn và truyền đường dẫn qua `sys.argv`.

---

## 5. Quy Tắc Thời Lượng Tối Thiểu (Minimum Duration Rule)
* **Triệu chứng:** Phụ đề chớp tắt quá nhanh (dưới 0.5s) khiến người xem không kịp đọc chữ hoặc gây cảm giác giật mắt.
* **Nguyên nhân:** Trong phân cảnh nhân vật chỉ thốt ra một từ ngắn ("Hả?", "A!", "Khoan đã!"), VAD chỉ phát hiện sóng âm trong 0.2s - 0.3s.
* **Giải pháp chuẩn:**
  * Áp dụng công thức an toàn: `new_end = max(new_start + min_duration, original_end)`.
  * Luôn duy trì `min_duration` tối thiểu $1.2\text{s}$ cho mọi câu thoại ngắn để đảm bảo trải nghiệm đọc tự nhiên nhất.
