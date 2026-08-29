# Báo cáo audit 4 bộ phim — 27/08/2026

Chạy đủ 6 bước của quy trình audit ghi ở `LOI-DA-GAP.md` mục G.

## Tổng quan

| | Phần 1 (1988) | Phần 2 (1990) | Phần 3 (1997) | Bản 2022 |
|---|---|---|---|---|
| Số tập | 45 | 46 | 51 | 9 |
| Lệch số dòng / timing | **0** | 0 | 1 tập (ep27) | 0 |
| Dòng karaoke `\kf` | **369** | 0 | 0 | 0 |
| Cặp 2 dòng `0068`/`0040` | **có** | không | không | không (dùng MarginV 25) |
| Hán-Việt trong ngoặc (format đã bỏ) | 0 | **120** | 0 | 0 |
| Block style gốc còn nguyên | có | **MẤT — 46/46 file** | có | có |
| Vi phạm bảng quy đổi tên | **0** | 3 | **57** | **0** |
| Romaji sai | 0 | 0 | 2 | 0 |

**Kết luận: chỉ Phần 1 đạt chuẩn. Ba bộ còn lại đều cần dựng lại.**

---

## Phần 2 (1990) — 46 tập

### Lỗi nghiêm trọng: mất block style gốc, cả 46/46 file

File gốc khai báo **11 style**: `Default, Ryo, title1, title2, Dou, Ryu, Sword, text, Ryujinmaru, Autor`.
File `.vi.ass` chỉ còn **30 style mashin** của tôi — **11 style gốc bị ghi đè mất**.

Hậu quả: mọi dòng thoại đều gắn `Style: text` nhưng `text` không còn được khai báo,
nên trình phát rơi về style mặc định — **sai font, sai cỡ, sai màu trên toàn bộ 46 tập**.

Đây là lỗi của script sinh file (`_work/process_s02*.py`) chứ không phải `build_vi.py`.
`build_vi.py` **chèn thêm** style vào block có sẵn, không thay thế.

### Chưa áp quy ước style

- **0 dòng karaoke** — toàn bộ yêu cầu về triệu hồi Mashin / tung chiêu chưa được áp dòng nào
- **120 chỗ** còn dùng format `\N(Hán-Việt)` trong ngoặc — đúng cái format đã bị bỏ

### Tên riêng — 3 chỗ

`Gunamun` ×1 → Kurama · `Zanjinmaru` ×1 → Senjinmaru · `Soujinmaru` ×1 → Kujinmaru

### Không phải lỗi

`Your Fight Jump` (xuất hiện nhiều lần) là **lời bài hát tiếng Anh trong bản gốc**, giữ nguyên là đúng.
23 chỗ `Death` đều thuộc tên riêng `Death Control` / `Death Crush` — **khác** với デス・ゴッド (Tử Thần),
không phải vi phạm.

---

## Phần 3 (1997) — 51 tập

### Tên riêng — 57 chỗ, nhiều nhất trong cả 4 bộ

| Sai | Đúng | Số chỗ |
|---|---|---|
| Zanjinmaru | Senjinmaru | 27 |
| Darkedar | Ankokudar | 11 |
| Doru | Doruku | 9 |
| Tigermaru | Jyakomaru | 4 |
| Dolan | Doran | 3 |
| Jakomaru | Jyakomaru | 2 |
| Tiger | Toraoh / Hổ Vương | 1 |

Lưu ý `Ankokudar` (90 chỗ), `Doruku` (136), `Doran` (83) đã đúng — tức là **cùng một nhân vật
đang được gọi bằng hai tên khác nhau trong cùng một bộ**, đây là lỗi nhất quán chứ không phải dịch sót.

### ep27 — bản dịch làm từ NGUỒN KHÁC

| File | Số dòng | Style dùng |
|---|---|---|
| `ep27.ass` (bản OCR từ VobSub tôi dựng) | 421 | `text` |
| `ep27.vi.ass` (bản dịch có sẵn) | 409 | `wataru krk op1`, có thẻ `{\K668}` |

Hai file **không khớp mốc thời gian nào**. Bản dịch làm từ file sub thứ hai của tập này
(bản có karaoke OP), không phải từ bản OCR. Cần chọn một nguồn rồi dựng lại.

### Chưa áp quy ước style

0 dòng karaoke, 0 dòng chú Hán-Việt nào.

---

## Bản 2022 (七魂の龍神丸) — 9 tập

**Sạch nhất trong ba bộ chưa chuẩn.** 0 vi phạm tên, 0 romaji sai, timing khớp, block style nguyên vẹn.

Đã có **dòng chú Hán-Việt hai dòng** với `\h` và style `atk-*` — nhưng:

- **0 dòng có `\kf`** → chú hiện tĩnh, không có animation quét màu
- Dùng `MarginV = 25` thay vì cặp `0068` / `0040`
- **Chỉ 7 dòng chú trên tổng 9 tập** (1 dòng/tập, tập 1 và 2 không có dòng nào)
  → so với Phần 1 trung bình ~8 dòng/tập. Cần rà lại xem còn bao nhiêu chỗ triệu hồi/tung chiêu bị bỏ sót.

---

## Hai cảnh báo ở Phần 1 — đã kiểm, đều là script báo nhầm

| Cảnh báo | Thực tế |
|---|---|
| ep01 thiếu `\h` trong karaoke | `{\kf60}Ryu{\kf60}jin{\kf59}maru` là **một từ liền**, không có dấu cách nên không cần `\h` |
| ep09 dùng ngoặc | `\N(tiếng Garzi)` là **chú thích ngôn ngữ**, không phải gloss Hán-Việt |

Bài học cho script audit: kiểm `\h` phải loại trường hợp tên một từ; kiểm ngoặc phải loại chú thích thường.

---

## Thứ tự nên làm

1. **Phần 2 — sửa block style trước tiên.** Đây là lỗi làm hỏng hiển thị toàn bộ 46 tập,
   và sửa được bằng script (ghép lại 11 style gốc vào đầu block), không cần dịch lại.
2. **Phần 3 — gộp tên.** 57 chỗ, sửa bằng script theo bảng quy đổi.
3. **Phần 3 ep27 — chọn nguồn** rồi dựng lại.
4. Gắn `SPECIAL` karaoke cho Phần 2, 3, 2022 — việc này phải làm tay từng tập như Phần 1.
5. Bỏ 120 chỗ ngoặc ở Phần 2, chuyển sang cặp hai dòng.


---

## Bổ sung 27/08 — P3 ep27: chốt nguồn

**Thư mục `Mashin Hero Wataru (1988)/` bị cấm tuyệt đối** — không đọc, không copy,
**và không dùng làm nguồn đối chiếu**. Tôi đã vi phạm khi copy `S03E27.en.ass` từ đó sang,
đã hoàn tác hoàn toàn.

Tình trạng thật của ep27:

| | |
|---|---|
| Bản phát hành chính TH97-SUB | cấp ep27 **chỉ dưới dạng VobSub** `.idx`/`.sub` — ep27 là tập DUY NHẤT trong 51 tập có VobSub |
| `ep27.ass` hiện tại | **bản OCR từ VobSub** của tôi, 421 dòng, style `Default/text` — đây là nguồn hợp lệ duy nhất của thư mục 1997 |
| `ep27.vi.ass` | 409 dòng, dịch từ một bản `.ass` khác nay không còn trong thư mục — **khớp 0/409 mốc giờ với nguồn hiện tại** |

**Kết luận: bản dịch ep27 mồ côi, phải dịch lại từ `ep27.ass` (bản OCR).**
Đây là tập duy nhất của P3 chưa có bản dịch hợp lệ. 50 tập còn lại khớp nguồn bình thường.

Lưu ý khi dịch lại: bản OCR đọc từ ảnh nên có thể sai chữ, cần đọc kỹ hơn bản `.ass` thường.
