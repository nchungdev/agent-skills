---
name: translate-subtitle
description: Dịch phụ đề phim chuyên sâu. Lõi chung áp dụng cho mọi ngôn ngữ nguồn, kèm mô-đun riêng cho nguồn CJK (Nhật/Trung/Hàn) xử lý tên riêng, Hán-Việt và karaoke tên chiêu. Có quy trình audit và cơ chế bồi đắp glossary qua từng lần dịch.
---

# Translate Subtitle Skill

Kỹ năng dịch phụ đề, đúc từ một dự án dịch 152 tập + 5 OVA + 1 phim lẻ.

> **Đọc mục 0 trước.** Skill này có phần dùng cho mọi phim, và phần **chỉ đúng khi
> nguồn là tiếng Nhật/CJK**. Áp dụng nhầm phần sau vào phim Âu-Mỹ sẽ ra kết quả vô nghĩa.

## 🚀 Kích hoạt

`translate-subtitle <tên_phim/tmdbid/tvdbid/imdbid> <đường_dẫn_subtitle> <ngôn_ngữ_đích>`

---

## 0. Xác định ngôn ngữ nguồn TRƯỚC KHI làm gì khác

Phải phân biệt **hai thứ khác nhau**, vì chúng quyết định hai việc khác nhau:

| | Là gì | Quyết định |
|---|---|---|
| **Ngôn ngữ nguyên tác** | Phim được sản xuất bằng tiếng gì | Chọn mô-đun (phần B/C), tra tên riêng ở đâu |
| **Ngôn ngữ file phụ đề đang có** | File nguồn ta cầm trong tay viết bằng tiếng gì | Biết nó là bản gốc hay bản qua trung gian |

Hai thứ này **thường không trùng nhau**. Ví dụ thật: anime Nhật, nhưng file `.ass` ta có
là tiếng Anh dịch từ bản Trung — nguyên tác là Nhật, file nguồn là Anh đời thứ ba.

### 0.1. Nhận dạng ngôn ngữ nguyên tác

Chạy theo thứ tự, dừng khi có kết quả chắc:

**a) Metadata âm thanh của file video** — tin cậy nhất nếu có:

```bash
ffprobe -v error -select_streams a \
  -show_entries stream=index:stream_tags=language,title \
  -of csv=p=0 "phim.mkv"
```

**b) Trường `original_language` từ TMDB/TVDB/IMDb** nếu người dùng đưa ID.

**c) Suy từ tên file / nhóm phát hành**: `[AI-Raws]`, `[DBD-Raws]`, `[SubsPlease]` → nguồn Nhật;
tên gốc trong tên file (`魔神英雄伝`, `기생충`) chỉ thẳng ngôn ngữ.

**d) Hỏi người dùng** nếu ba cách trên không dứt khoát. **Đừng đoán** — chọn sai mô-đun
là hỏng toàn bộ cách xử lý tên riêng.

### 0.2. Nhận dạng ngôn ngữ của chính file phụ đề

Nhận theo **hệ chữ viết** trong dòng thoại (bỏ qua dòng lời hát):

```python
import re
def nhan_dang(text):
    if re.search(r'[ぁ-んァ-ヶ]', text):  return 'Nhật'    # có kana
    if re.search(r'[가-힣]',   text):     return 'Hàn'     # có hangul
    if re.search(r'[一-鿿]', text):
        # chỉ có chữ Hán, không kana/hangul -> tiếng Trung
        phon = set('这为个来对说时门题实产')   # giản thể đặc trưng
        trad = set('這為個來對說時門題實產')   # phồn thể đặc trưng
        sp = sum(c in phon for c in text); st = sum(c in trad for c in text)
        return 'Trung giản thể' if sp > st else 'Trung phồn thể'
    if re.search(r'[ก-๙]', text):        return 'Thái'
    if re.search(r'[Ѐ-ӿ]', text):        return 'Nga'
    return _he_latin(text)

VN_DAU = 'ăâđêôơưàáảãạầấẩẫậằắẳẵặèéẻẽẹềếểễệìíỉĩịòóỏõọồốổỗộờớởỡợùúủũụừứửữựỳýỷỹỵ'
EN_HUTU = {'the','is','are','of','and','to','in','that','this','with','for','you','your',
           'was','were','have','has','not','but','from','what','when','which','they'}

def _he_latin(text):
    # He Latin: phan biet bang mat do dau phu va hu tu dac trung
    low = text.lower()
    co_dau = sum(c in VN_DAU for c in low)
    tu     = re.findall(r"[a-z']+", low)
    hu_tu  = sum(w in EN_HUTU for w in tu)
    if co_dau > len(text) * 0.03: return 'Việt'
    if hu_tu  > len(tu)   * 0.08: return 'Anh'
    return 'hệ Latin — chưa rõ, hỏi người dùng'
```

**Nhánh Latin không nhận ra bằng hệ chữ được**, vì tiếng Anh, Việt, Pháp, Tây Ban Nha
dùng chung bảng chữ cái. Phải phân biệt bằng **mật độ dấu phụ** và **hư từ đặc trưng**.
Ngôn ngữ ngoài hai cái trên thì trả về "chưa rõ" và **hỏi người dùng** —
đoán bừa còn tệ hơn thừa nhận không biết.

**Cạm bẫy:** file `.chi.ass` không đảm bảo nội dung là tiếng Trung, và một file có thể
**trộn nhiều ngôn ngữ** (thoại tiếng Trung nhưng lời bài hát để nguyên tiếng Nhật).
Vì vậy phải **thống kê theo dòng**, không chỉ đọc vài dòng đầu:

```python
kana = sum(1 for d in dong_thoai if re.search(r'[ぁ-んァ-ヶ]', d))
han  = sum(1 for d in dong_thoai
           if re.search(r'[一-鿿]', d) and not re.search(r'[ぁ-んァ-ヶ]', d))
```

> Ca thật: file tên `.chi.ass` mở ra dòng đầu là tiếng Nhật. Thống kê cả file mới rõ:
> **308 dòng chỉ chữ Hán / 24 dòng có kana** — thoại là tiếng Trung, lời hát giữ nguyên
> tiếng Nhật. Nếu chỉ nhìn dòng đầu sẽ kết luận sai hoàn toàn.

### 0.3. Chọn mô-đun theo kết quả

| Nguyên tác | Áp dụng |
|---|---|
| **Nhật** | Lõi chung (1–5) **+** Mô-đun CJK (6) **+** Mô-đun Nhật (7) |
| **Trung / Hàn** | Lõi chung **+** Mô-đun CJK (6). **Bỏ** mục 7 |
| **Khác** (Âu-Mỹ, Thái, Ấn…) | **Chỉ** lõi chung (1–5). **Bỏ** mục 6 và 7 |

Với nguyên tác ngoài CJK: tên riêng **giữ nguyên chính tả gốc**, không phiên âm,
không Hán-Việt, không karaoke hai lớp. Thứ bậc nguồn ở mục 2 thay
"Wikipedia tiếng Nhật" bằng **Wikipedia/CSDL bằng chính ngôn ngữ nguyên tác**.

### 0.4. Ghi kết luận vào glossary ngay

```json
"ngon_ngu": {
  "nguyen_tac": "Nhật",
  "cach_xac_dinh": "ffprobe: audio stream tag jpn + tên nhóm phát hành [AI-Raws]",
  "file_nguon": "Trung phồn thể (thoại) + Nhật (lời hát)",
  "la_ban_qua_trung_gian": false,
  "mo_dun_ap_dung": ["loi_chung", "cjk", "nhat"]
}
```

Ghi lại để lần chạy sau — và người khác — không phải xác định lại, và biết được
bản dịch đã dựa trên giả định nào.


---

### 0.5. HỎI người dùng: phim có cần bộ style & karaoke không?

**Đây là trục riêng, độc lập với ngôn ngữ.** Phim truyền hình Trung Quốc và phim người đóng
Nhật đều là nguồn CJK nhưng **không có chiêu thức nào để hô**. Ngay trong anime, thể loại
đời thường cũng chẳng có gì để gắn karaoke.

Bộ style ASS (`summon-*`, `atk-*`) và karaoke hai lớp **chỉ đáng làm khi phim thực sự có**:

- Tên chiêu / tuyệt kỹ được **hô to** thành tiếng
- Câu **triệu hồi** hoặc **biến thân** lặp lại theo mô-típ
- Tên riêng cần hiện **song song hai lớp** (phiên âm + nghĩa)

Điển hình: anime shounen chiến đấu, mecha, tokusatsu (Super Sentai, Kamen Rider), phim tu tiên.

**PHẢI hỏi người dùng, đừng tự quyết:**

> "Phim này có tên chiêu thức / câu triệu hồi được hô to không? Nếu có, tôi sẽ dựng bộ style
> ASS riêng và karaoke hai lớp cho chúng. Nếu không, tôi chỉ dịch thoại thường —
> nhanh hơn và file gọn hơn."

| Trả lời | Áp dụng |
|---|---|
| **Có** | Làm đủ: `_style/`, bảng tên chiêu trong glossary, mục 6.3–6.5, khối `SPECIAL` |
| **Không** | **Bỏ** `_style/`, bỏ 6.3–6.5, `SPECIAL = {}`. Chỉ dịch thoại |
| **Không chắc** | Quét thử: tìm dòng thoại ngắn, viết hoa, lặp lại nhiều tập → đưa danh sách cho người dùng xem rồi mới quyết |

Ghi kết luận vào glossary cùng chỗ với mục 0.4:

```json
"che_ban": {
  "can_karaoke_chieu_thuc": true,
  "ly_do": "anime mecha, có câu triệu hồi Mashin và tên chiêu hô to mỗi tập",
  "the_loai": "anime mecha"
}
```

> **Đừng dựng style khi phim không cần.** Nó làm file phồng lên, thêm chỗ để sai, và
> không đem lại gì cho người xem. Nhưng cũng đừng bỏ qua khi phim có — mất hẳn một
> lớp thông tin mà khán giả thể loại này mong đợi.

# PHẦN A — LÕI CHUNG (mọi ngôn ngữ nguồn)

## 1. Khởi tạo workspace

- `glossary.json` — bộ nhớ dài hạn
- `LOI-DA-GAP.md` — nhật ký lỗi, mỗi mục là một lỗi đã trả giá
- `_style/` — file style ASS *(chỉ tạo nếu mục 0.5 kết luận là CÓ)*
- `_work/` — file gốc, script Python, file dịch từng tập
- `translated/` — kết quả

## 2. Thứ bậc nguồn — và cảnh giác bản dịch qua trung gian

Nhiều bản phụ đề tiếng Anh trên mạng **không dịch thẳng từ nguyên tác** mà qua một
ngôn ngữ trung gian. Bản qua trung gian là **bản sao đời thứ ba**, sai lệch tích luỹ.

**Dấu hiệu nhận biết:** tên riêng bị dịch *nghĩa* thay vì phiên âm; xuất hiện từ vô nghĩa
trong ngữ cảnh; một nhân vật có nhiều cách viết khác nhau.

```
1. Trang chính thức của phim (ảnh tên, tài liệu nhà sản xuất)  ← thắng mọi suy luận
2. Wikipedia/CSDL bằng CHÍNH ngôn ngữ gốc của phim
3. Phụ đề bằng ngôn ngữ gốc, hoặc ngôn ngữ trung gian gần gốc
4. Phụ đề tiếng Anh qua trung gian                             ← thấp nhất
```

**Quy tắc chốt:** cần **≥ 2 nguồn độc lập cấp 1–2** mới được đổi hàng loạt một cái tên.

> Nguồn cấp 3 cũng sai được. Bản Trung ghi công chúa là `布莉布莉` (Buriburi), bản dịch
> bám theo — trung thực nhưng sai. Trang chính thức **và** Wikipedia Nhật đều ghi
> `プリプリ姫` (Puripuri). Phải sửa 51 chỗ.

### 2.1. Kết tinh nguồn cấp 1 thành bảng tra riêng

Đây là cấu trúc quan trọng nhất. Đừng để thông tin cấp 1 nằm rải rác trong ghi chú —
gom vào **một bảng chuyên dụng** trong glossary:

```json
"ten_chinh_thuc": {
  "_nguon": "Ảnh tên trên website chính thức — ưu tiên hơn mọi suy luận",
  "bang": [
    {"goc":"邪虎丸","chinh_thuc":"JYAKOMARU","truoc_ghi":"Jakomaru — SỬA"},
    {"goc":"空神丸","chinh_thuc":"KUJINMARU","truoc_ghi":"Kuujinmaru — SỬA"}
  ]
}
```

Trường `truoc_ghi` ghi dạng **sai đã từng dùng** → cho phép quét tự động tìm chỗ còn sót.
Bảng này đã bắt được 3 lỗi mà suy luận thuần tuý không thể phát hiện.

## 3. Cấu trúc glossary

Tối thiểu cần các nhóm sau (dự án thật đã lên tới 25 nhóm):

| Nhóm | Chứa gì |
|---|---|
| `boi_canh` | Bối cảnh, cốt truyện |
| `nhan_vat` | Nhân vật, quan hệ |
| `address_matrix` | **Ai gọi ai bằng gì** — phải giữ đúng sắc thái gốc |
| `ten_chinh_thuc` | Bảng nguồn cấp 1 (mục 2.1) |
| `bang_quy_doi_bat_buoc` | Mọi chuyển đổi đã chốt, dạng sai → dạng đúng |
| `bien_the_chinh_ta` | Một thực thể nhiều cách viết |
| `ten_chua_giai_duoc` | Hàng đợi chưa tra ra — ghi lại thay vì đoán bừa |

**Mọi mục tên riêng phải có `"do_chac": "cao" | "trung" | "thap"`.**
Người đọc sau biết ngay cái nào chắc, cái nào cần tra lại.

## 4. Quy tắc nội dung

- **Không bịa từ không có trong nguồn.** Nghi ngờ thì đếm: nếu nguồn không hề chứa
  khái niệm đó, không được tự thêm.
- **Không ép vần cho kêu.** Vần gượng nghe rất giả. Ưu tiên cách nói tự nhiên.
- **Không tự ghép từ mà ngôn ngữ đích không dùng.**
- **Giữ trò chơi chữ.** Dịch nghĩa đen làm mất trò đùa là dịch hỏng.
- **Giữ nét tính cách trong lời thoại** (tự xưng ngôi thứ ba, tật nói lặp…).
- **Không rút gọn câu theo số ký tự.** Rút gọn làm gãy vế nối sang dòng sau,
  đổi ngôi, mất từ trả lời. Ưu tiên **nghĩa**, không phải độ dài.

## 5. Audit & kiểm toàn vẹn

### 5.1. Quét — nhưng phải quét đúng tín hiệu

Bộ dò cho ra **hàng nghìn kết quả là bộ dò hỏng**, không phải bản dịch hỏng.

> Quét "từ tiếng Anh còn sót" bằng `\b[A-Za-z]{2,}\b` cho ra **12.654 báo động giả**,
> vì tiếng Việt không dấu (`qua`, `sao`, `trong`) cũng khớp.
> Đổi sang quét **hư từ tiếng Anh** (`the, is, are, of, and, that, you, your`… — những từ
> không thể tồn tại trong tiếng Việt), ngưỡng ≥ 2 từ/dòng: còn **86 dòng**, đều là lỗi thật.

### 5.2. Đối chiếu ba chiều — bắt buộc trước khi sửa

Không bao giờ sửa câu chỉ dựa trên bản dịch. Luôn đặt cạnh nhau:
`nguồn gốc ↔ nguồn trung gian ↔ bản dịch`.

Bộ dò văn phong cho **129 dòng nghi vấn** trên 97 tập, nhưng khi đặt cạnh bản gốc thì
**phần lớn là báo động giả**. Sửa theo bộ dò mà không nhìn bản gốc sẽ làm bản dịch **tệ đi**.

### 5.3. Máy tìm, người quyết

Công cụ dò chỉ được **liệt kê ứng viên kèm câu gốc**, tuyệt đối không tự sửa.

> Bộ tự nhận diện câu triệu hồi gắn cờ 133 dòng — kiểm ra toàn thoại thường
> (*"Ryujinmaru, ở trên kìa!"*). Chỉ tự động hoá phần máy phân biệt được chắc chắn.

### 5.4. Thay chuỗi và xác minh

**Dùng Python cho mọi phép thay chuỗi có ký tự ngoài ASCII.** Hai cách sau âm thầm thất bại:

| Cách | Vì sao hỏng |
|---|---|
| `sed -i '' 's/\bA\b/B/'` (macOS) | BSD sed không hiểu `\b`. Pattern không khớp nhưng **vẫn ghi lại file** → `mtime` đổi, tưởng đã sửa |
| `perl -CSD -i -pe` với chuỗi Unicode | `-CSD` giải mã đầu vào thành ký tự, mẫu trong script vẫn là byte thô → không khớp |

**Xác minh bằng đếm lại số lần xuất hiện**, không tin lệnh chạy xong.
**Loại trừ thư mục backup khi đếm** — glob `*/*.ass` quét cả bản sao vừa tạo nên số
không đổi, gây tưởng nhầm là sửa hụt.

### 5.5. Kiểm sót dòng TRƯỚC khi dựng

```python
miss = [i for i in range(1, N+1) if i not in D]   # phải rỗng
```

Sót một dòng là câu đó **giữ nguyên tiếng nguồn** trong bản phát hành.

### 5.6. Kiểm toàn vẹn SAU khi dựng

```
số dòng Dialogue   trước == sau
số thẻ \kf         trước == sau
mọi file còn là UTF-8 hợp lệ
0 ký tự ngôn ngữ nguồn còn sót trong dòng thoại
```

### 5.7. Đặt tên file đầu ra

Để Plex/Jellyfin tự nhận, tên phụ đề phải **khớp chính xác basename của file video**:

```
Ten Phim (Nam) - S01E01.mkv
Ten Phim (Nam) - S01E01.vi.ass     ← đúng
ten-phim.vi.ass                    ← SAI, sẽ không được nhận
```

## 5.8. Vòng lặp bồi đắp

```
PHÁT HIỆN → TRUY NGUYÊN → SỬA → GHI LẠI
```

Bước **GHI LẠI** hay bị bỏ nhất và có giá trị nhất: glossary (để lần sau đúng)
+ `LOI-DA-GAP.md` (để lần sau không tái phạm). Lỗi đã sửa mà không ghi là lỗi sẽ tái phạm.

---

# PHẦN B — MÔ-ĐUN CJK (chỉ khi nguồn là Nhật/Trung/Hàn)

> **Bỏ toàn bộ phần B nếu phim không phải nguồn CJK.**

## 6. Tên riêng và Hán-Việt

### 6.1. Giữ nguyên hay dịch Hán-Việt?

| Loại | Xử lý |
|---|---|
| Tên người | **Giữ phiên âm gốc** (romaji/pinyin) |
| Tên robot/mecha, vũ khí | **Giữ phiên âm gốc** |
| Địa danh đọc theo âm bản ngữ | **Giữ phiên âm gốc** |
| Địa danh/cõi đọc theo âm Hán | **Dịch Hán-Việt** |
| **Tên chiêu khi hô to** | **Hán-Việt + karaoke** (mục 6.3) |

Nguyên tắc phân biệt: **phiên âm đọc lên nghe như tiếng Anh thì mới dịch nghĩa**; còn lại giữ.

### 6.2. Một thực thể, nhiều cách viết

Bản qua trung gian thường viết một nhân vật theo nhiều kiểu. Phải gom về một mối
và ghi vào `bien_the_chinh_ta`.

### 6.3. Karaoke hai lớp cho tên chiêu

> **Chỉ làm nếu mục 0.5 kết luận là CÓ.** Phim không có chiêu thức hô to thì bỏ qua 6.3–6.5.

Hai dòng `Dialogue` **cùng mốc thời gian**:

```
MarginV 0068  →  {\kf62}Sen\h{\kf62}jin\h{\kf62}maru      (phiên âm, chữ to)
MarginV 0040  →  {\kf62}Chiến\h{\kf62}Thần\h{\kf62}Hoàn   (Hán-Việt, chữ nhỏ, mờ)
```

Ba bẫy kỹ thuật:

1. **`\N` KHÔNG reset đồng hồ karaoke.** Để `\N` giữa chừng là các `\kf` sau tính giờ sai
   hoàn toàn → **bắt buộc tách hai dòng Dialogue riêng**.
2. **Dấu cách thường bị ASS nuốt** → luôn dùng `\h`.
3. **Tách theo CHỮ HÁN, không theo mora.** `Ryu|jin|maru` (3 phần, ứng 龍神丸),
   không phải `Ryu|u|ji|n|ma|ru`.

### 6.4. Quy tắc khớp số âm — phạm vi rất hẹp

Khi dịch **tên chiêu** sang Hán-Việt, số âm tiết phải khớp phiên âm để karaoke đúng nhịp:

```
En | ryuu | ken       (3 âm)
Viêm | Long | Quyền   (3 âm)   ✓
```

> ⚠️ **Chỉ dùng cho tên riêng khi hô chiêu. TUYỆT ĐỐI không dùng để rút gọn câu thoại.**
> Áp nhầm sẽ phá bản dịch: gãy vế nối, đổi ngôi, mất từ trả lời.

### 6.5. Cùng phiên âm, khác chữ Hán

Bẫy hay gặp. Phải tách bằng bảng riêng trong code dựng:

```python
EXTRA = {
 'SeiryuukenHoly': ("Sei|ryuu|ken", "Thánh|Long|Kiếm"),  # 聖龍剣
 'SeiryuukenStar': ("Sei|ryuu|ken", "Tinh|Long|Kiếm"),   # 星龍剣 — KHÁC
}
```

Ghi cảnh báo vào glossary để lần sau không ghép nhầm cặp.

## 7. Mô-đun riêng cho nguồn NHẬT

### 7.1. Giải mã dấu vết Nhật → Trung → Anh

Khi bản Anh đi qua tiếng Trung, chữ Trung lộ nguyên hình. Bảng nhận dạng:

| Bản Anh viết | Thực ra là | Vì sao |
|---|---|---|
| `Ferry` | 渡 = Wataru | 渡 nghĩa "qua sông/phà" |
| `Fumiko fire` | 火美子 = Himiko | Dịch từng chữ 火(fire)美子 |
| `Dragon balls` | 龍神丸 = Ryujinmaru | 丸 bị hiểu thành "viên/quả" |
| `Etc.` | 等 = "Khoan đã" | 等 vừa là "vân vân" vừa là "đợi" |
| `Feed` | 喂 = "Này" (gọi) | 喂 vừa là "cho ăn" vừa là tiếng gọi |
| `a lot of adults` | 大人 = "đại nhân" | 大人 là kính ngữ, không phải "người lớn" |
| `Caixing` | 才行 | **Hư từ ngữ pháp**, không phải tên người |

Gặp câu tiếng Anh vô nghĩa hoặc tên nghe lạ: **dịch ngược về chữ Hán rồi truy về tiếng Nhật**,
đừng cố dịch cho xuôi.

> Ca mẫu trọn vòng: `No-Fall-Down` (27 chỗ) → bản Trung `圓球不倒翁` → `不倒翁` là **con lật đật**
> → bản Anh dịch nghĩa đen, làm mất trò đùa "ông Lật Đật ngã rồi!" → trang chính thức +
> Wikipedia Nhật: **マルダルマ (Marudaruma)**, マル=丸(tròn)+ダルマ=達磨(lật đật), khớp chính xác.
> Truy tới cùng một lỗi thường lòi ra cả cụm lỗi cùng nguồn gốc.

### 7.2. Tên đọc âm Nhật vs âm Hán

`Soukaizan`, `Mashinzan` → giữ romaji. `天部界`, `神部界` → Thiên Bộ Giới, Thần Bộ Giới.

---

# PHẦN C — CHẾ BẢN

## 8. Ánh xạ số thứ tự dòng

File `.ass` thường **xen kẽ dòng lời hát** (OP/ED) giữa các khối thoại, nên
**số thứ tự thoại ≠ số dòng trong file**. Bắt buộc có hàm ánh xạ:

```python
def map_idx(d):
    """Thoại #1..274 -> dòng 27..300 ; #275..284 -> dòng 323..332"""
    return 26 + d if d <= 274 else 322 + (d - 274)
```

Xác định ranh giới bằng cách quét mốc đổi `style` trong file gốc. Bỏ qua bước này là lệch toàn bộ.

## 9. Khuôn file dịch một tập

```python
D = { 1:"...", 2:"...", ... }          # bản dịch theo số thứ tự thoại
SPECIAL = {                             # tên chiêu cần karaoke (chỉ nguồn CJK)
  227:{'style':'summon-senjinmaru','name':'Senjinmaru','kind':'trieu','pre':''},
}
def map_idx(d): ...
VI = {map_idx(k): v for k, v in D.items()}
```

## 10. Hoàn thiện

Lưu vào `translated/` theo quy tắc đặt tên ở mục 5.7. Báo cáo cho người dùng:
cách xưng hô đã chốt, tên riêng mới thêm vào glossary kèm `do_chac`, và kết quả audit.

---

## Ba nguyên tắc rút gọn

1. **Nguồn có thứ bậc, và bậc nào cũng có thể sai.** Cần ≥ 2 nguồn độc lập cấp cao
   mới sửa hàng loạt.
2. **Máy tìm, người quyết.** Bộ quét dùng để thu hẹp phạm vi, không dùng để quyết định.
3. **Ghi lại quan trọng ngang sửa.** Lỗi không ghi vào `LOI-DA-GAP.md` là lỗi sẽ tái phạm.
