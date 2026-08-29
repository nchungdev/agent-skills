# Quy trình dịch phụ đề Wataru — cơ chế đã xây dựng

Tài liệu này ghi lại **cách làm** đã hình thành qua toàn bộ dự án: nguồn lấy từ đâu,
dịch theo quy tắc nào, sai ở đâu thì phát hiện bằng cách nào, và mỗi lần sai thì
glossary được bồi đắp thêm cái gì.

Ba tài liệu anh em, đọc kèm:

| File | Vai trò |
|---|---|
| `wataru-glossary.json` | Bộ nhớ dài hạn — 25 nhóm khoá, 88 mục karaoke, 63 quy đổi bắt buộc, 17 romaji chính thức |
| `LOI-DA-GAP.md` | Nhật ký lỗi, 396 dòng, nhóm A→G9. Mỗi mục = một lỗi đã trả giá |
| `CHO-MO-HO.md` | Hàng đợi chỗ mơ hồ chờ tra cứu (hiện đã xử lý hết) |

---

## 1. Vấn đề gốc: nguồn dịch không phải nguyên tác

Đây là phát hiện định hình toàn bộ quy trình.

Bản `.ass` tiếng Anh của Phần 1/2/3 **không dịch thẳng từ tiếng Nhật**. Nó đi qua chuỗi:

```
Tiếng Nhật (nguyên tác)  →  Tiếng Trung  →  Tiếng Anh (bản ta có)
```

Bằng chứng là những chữ Trung lộ nguyên hình trong bản Anh:

| Bản Anh viết | Thực ra là | Vì sao |
|---|---|---|
| `Ferry` | 渡 = Wataru | 渡 nghĩa là "qua sông/phà" |
| `Fumiko fire` | 火美子 = Himiko | Dịch nghĩa từng chữ 火(fire)美子 |
| `Dragon balls` | 龍神丸 = Ryujinmaru | 丸 bị hiểu thành "viên/quả" |
| `Etc.` | 等 = "Khoan đã" | 等 vừa là "vân vân" vừa là "đợi" |
| `Feed` | 喂 = "Này" (gọi) | 喂 vừa là "cho ăn" vừa là tiếng gọi |
| `a lot of adults` | 大人 = "đại nhân" | 大人 là kính ngữ, không phải "người lớn" |
| `Caixing` | 才行 | Là hư từ ngữ pháp, bị tưởng là tên người |

**Hệ quả về phương pháp:** không bao giờ được coi bản Anh là chuẩn. Nó là *bản sao đời thứ ba*.
Khi một câu tiếng Anh vô nghĩa hoặc một cái tên nghe lạ, phản xạ đúng là
**dịch ngược về chữ Hán rồi truy về tiếng Nhật**, chứ không phải cố dịch cho xuôi.

### 1.1. Bước ngoặt: tìm được mắt xích giữa

Cuối dự án tìm ra thư mục `Plex_Jellyfin_Subtitles/` chứa **216 file phụ đề tiếng Trung**
cho toàn bộ series. Đây chính là **mắt xích Trung** của chuỗi trên. Có nó thì:

- Không phải đoán ngược nữa — đọc thẳng bản Trung là ra nghĩa
- Giải được loạt tên bế tắc suốt nhiều tháng (mục 5.3)
- Nhưng **bản Trung cũng có thể sai** — xem mục 4.3

### 1.2. Thứ bậc nguồn (áp dụng khi các nguồn mâu thuẫn)

```
1. Ảnh tên chính thức trên mashin-eiyuuden-wataru.net   ← cao nhất, thắng mọi suy luận
2. Wikipedia tiếng Nhật / trang nhân vật chính thức
3. Bản phụ đề tiếng Trung (mắt xích gốc)
4. Bản phụ đề tiếng Anh (bản sao đời 3)               ← thấp nhất
```

Quy tắc chốt: **cần ít nhất 2 nguồn Nhật độc lập** mới được đổi hàng loạt một cái tên.

---

## 2. Quy tắc dịch tên riêng

Đây là nơi đã sai nhiều nhất, nên quy tắc được siết dần thành:

### 2.1. Giữ romaji hay dịch Hán-Việt?

| Loại | Xử lý | Ví dụ |
|---|---|---|
| Tên người | **Giữ romaji** | Wataru, Himiko, Shibaraku, Kurama, Tonkararin |
| Tên Mashin | **Giữ romaji** | Ryujinmaru, Senjinmaru, Jyakomaru |
| Tên kiếm | **Giữ romaji** | Ryuuouken, Enryuuken |
| Địa danh đọc âm Nhật | **Giữ romaji** | Soukaizan, Seikaizan, Mashinzan |
| Địa danh/cõi đọc âm Hán | **Dịch Hán-Việt** | Thiên Bộ Giới, Thần Bộ Giới, Tinh Thần Giới |
| **Tên chiêu khi hô to** | **Dịch Hán-Việt + karaoke** | Enryuuken → Viêm Long Quyền |
| Katakana mượn tiếng Anh | Dịch nghĩa | (xét từng ca) |

Nguyên tắc phân biệt: **romaji đọc lên nghe như tiếng Anh thì mới dịch**;
còn lại giữ nguyên.

### 2.2. Quy tắc `_KHOP_SO_AM` — phạm vi rất hẹp

Quy tắc: khi dịch tên sang Hán-Việt, **số âm tiết phải khớp** số âm tiết romaji,
để karaoke chạy đúng nhịp với tiếng hô trong phim.

```
En | ryuu | ken        (3 âm)
Viêm | Long | Quyền    (3 âm)  ✓ khớp
```

> **Từng áp dụng sai quy tắc này.** Có lúc đem nó ra để *rút gọn câu thoại* cho vừa
> số ký tự. Đó là hiểu sai hoàn toàn: quy tắc chỉ dành cho **tên riêng khi hô chiêu**,
> tuyệt đối không dành cho câu thoại thường. Ghi tại `LOI-DA-GAP.md` mục G7.

### 2.3. Một thực thể — nhiều cách viết

Bản Anh thường viết một nhân vật theo nhiều kiểu khác nhau. Phải gom về một mối:

```
Buriburi / BuriBuri          → Puripuri     (51 chỗ)
Jeopardy / Kapidy            → Kakubatteru  (12 chỗ)
No-Fall-Down / Không-Bao-Giờ-Ngã → Marudaruma (28 chỗ)
Jakomaru                     → Jyakomaru    (7 chỗ, theo romaji chính thức)
```

---

## 3. Cơ chế karaoke cho tên chiêu

### 3.1. Cấu trúc hai dòng

Mỗi lần hô chiêu sinh ra **hai dòng Dialogue cùng mốc thời gian**:

```
MarginV 0068 → dòng romaji    {\kf62}Sen\h{\kf62}jin\h{\kf62}maru
MarginV 0040 → dòng Hán-Việt  {\kf62}Chiến\h{\kf62}Thần\h{\kf62}Hoàn
```

### 3.2. Ba cái bẫy kỹ thuật đã dính

**Dấu cách thường bị ASS nuốt.** Phải dùng `\h` (hard space), không dùng dấu cách.

**`\N` KHÔNG reset đồng hồ karaoke.** Nếu để `\N` giữa chừng, các `\kf` sau đó tính giờ
sai hoàn toàn. Bắt buộc **tách thành hai dòng Dialogue riêng**, không xuống dòng bằng `\N`.

**Tách theo CHỮ HÁN, không theo mora tiếng Nhật.** `Ryujinmaru` tách thành
`Ryu|jin|maru` (3 phần, ứng 龍神丸) chứ không phải `Ryu|u|ji|n|ma|ru`.

### 3.3. Hàm sinh karaoke

`_work/build_vi.py` giữ toàn bộ logic. Tên chiêu tra từ glossary (`can_karaoke.bang`, 88 mục);
tên chưa có thì truyền thẳng dạng gạch đứng `'Hoàng|Long|Lôi|Kích|Ba'` qua nhánh `mot_dong`.

Cùng romaji nhưng khác kanji thì phải tách bằng bảng `EXTRA`:

```python
'SeiryuukenHoly': ("Sei|ryuu|ken","Thánh|Long|Kiếm"),  # 聖龍剣 phim 2022
# KHÁC 星龍剣 của P2 — cùng đọc "Seiryuuken"
'EnryuukenKen':   ("En|ryuu|ken","Viêm|Long|Kiếm"),    # 炎龍剣 (kiếm)
# KHÁC 炎龍拳 của P1 (quyền)
```

---

## 4. Cơ chế phát hiện lỗi

Đây là phần cốt lõi. Nguyên tắc bao trùm: **không tin vào cảm giác "chắc xong rồi"**.

### 4.1. Quét máy — nhưng phải quét đúng tín hiệu

Từng viết bộ quét bắt "từ tiếng Anh còn sót" bằng `\b[A-Za-z]{2,}\b`.
Kết quả: **12.654 báo động giả**, vì tiếng Việt không dấu (`qua`, `sao`, `trong`, `cho`)
cũng khớp. Vô dụng.

Tín hiệu **đúng** là **hư từ tiếng Anh** — những từ không thể tồn tại trong tiếng Việt:

```python
EN = {'the','is','are','of','and','to','in','that','this','with','for','you','your',...}
# >= 2 hư từ trong một dòng  →  gần như chắc chắn còn tiếng Anh
```

Đổi sang tín hiệu này: từ 12.654 xuống **86 dòng, 32 câu khác nhau** — và đều là lỗi thật.

**Bài học:** một bộ dò cho ra hàng nghìn kết quả là bộ dò hỏng, không phải bản dịch hỏng.

### 4.2. Đối chiếu ba chiều

Không bao giờ sửa câu chỉ dựa trên bản tiếng Việt. Luôn đặt cạnh nhau:

```
ZH: 什麼         ← mắt xích gốc
EN: What did you say?   ← bản sao đời 3
VI: Ngươi nói cái gì đó?  ← bản dịch của ta
```

Nhờ nhìn đủ ba mà phát hiện `What did you say?` (câu vặn lại đầy thách thức)
bị dịch thành câu hỏi bâng quơ. Sai ở **16 chỗ**, sửa thành "Ngươi vừa nói gì?".

Từng sửa câu mà **không** xem bản gốc, và đã làm hỏng: cắt mất vế nối sang dòng sau,
đổi ngôi thứ nhất thành mệnh lệnh, xoá thói quen tự xưng ngôi thứ ba của Himiko
(một nét tính cách xuất hiện ở 26 dòng).

### 4.3. Nguồn cũng sai — kiểm chéo cả nguồn

Bản Trung ghi công chúa là `布莉布莉` (Buriburi). Bản dịch tiếng Việt bám theo đó — **trung thực**.
Nhưng trang chính thức **và** Wikipedia tiếng Nhật đều ghi `プリプリ姫` (Puripuri).

→ **Chính bản Trung sai.** Sửa 51 chỗ.

Đây là lý do quy tắc "2 nguồn Nhật độc lập" ở mục 1.2 tồn tại.

### 4.4. Xác minh phải đếm lại, không tin lệnh chạy xong

Ba lần bị lừa bởi chính công cụ:

| Lỗi | Biểu hiện | Vì sao |
|---|---|---|
| `sed -i '' 's/\bA\b/B/'` trên macOS | In ra "đã sửa", `mtime` đổi, **nội dung y nguyên** | BSD sed không hiểu `\b`; pattern không khớp nhưng vẫn ghi lại file |
| `perl -CSD -i -pe` với chuỗi tiếng Việt | Không thay gì cả | `-CSD` giải mã đầu vào thành ký tự, mẫu trong script vẫn là byte thô |
| Đếm bằng `grep */*.vi.ass` | Số không đổi sau khi sửa | Glob quét cả `_backup/` vừa tạo |

**Quy tắc rút ra:** mọi phép thay chuỗi tiếng Việt dùng **Python**; xác minh bằng
**đếm lại số lần xuất hiện**, loại trừ thư mục backup. Ghi tại `LOI-DA-GAP.md` G9.

### 4.5. Kiểm toàn vẹn sau mỗi đợt sửa

Chạy cố định, không bỏ qua:

```
số dòng Dialogue trước == sau
số dòng \kf     trước == sau
mọi file còn là UTF-8 hợp lệ
0 chữ Hán còn sót trong dòng thoại (trừ dòng lời hát)
```

### 4.6. Tự động hoá có giới hạn

Từng viết bộ tự nhận diện câu triệu hồi Mashin. Nó gắn cờ **133 dòng ở Phần 3**.
Kiểm mẫu thì toàn là thoại thường: *"Ryujinmaru, ở trên kìa!"*, *"Cẩn thận! Ryujinmaru."*

→ Thu hẹp tự động hoá **chỉ còn tên chiêu**. Triệu hồi thì `_work/tim_trieu_hoi.py`
**chỉ liệt kê ứng viên kèm câu gốc để người đọc**, không bao giờ tự sửa.

**Nguyên tắc:** việc nào máy không phân biệt nổi thì máy chỉ được *đề xuất*, không được *quyết*.

---

## 5. Vòng lặp bồi đắp glossary

Mỗi lỗi đi qua đủ bốn bước, không bỏ bước nào:

```
1. PHÁT HIỆN  →  quét máy, hoặc người đọc thấy gợn
2. TRUY NGUYÊN →  ZH ↔ EN ↔ VI, rồi tra nguồn Nhật
3. SỬA        →  Python thay chuỗi + đếm lại xác minh
4. GHI LẠI    →  glossary (để lần sau đúng) + LOI-DA-GAP.md (để lần sau không tái phạm)
```

Bước 4 là bước hay bị bỏ nhất, và cũng là bước có giá trị nhất.

### 5.1. Glossary lớn dần theo lỗi

| Nhóm khoá | Sinh ra từ |
|---|---|
| `romaji_chinh_thuc` (17 mục) | Sau khi dùng sai `Kennou` thay vì `Kenou` — cần một bảng "nhà sản xuất nói sao" đè lên mọi suy luận |
| `bang_quy_doi_bat_buoc` (63 mục) | Sau khi phát hiện chuỗi dịch máy Trung→Anh |
| `CANH_BAO_TRUNG_ROMAJI` | Sau khi 星龍剣 và 聖龍剣 cùng đọc "Seiryuuken" mà bị ghép nhầm |
| `bien_the_chinh_ta` | Sau khi một nhân vật có 2–3 cách viết trong cùng một phần |
| `ten_chua_giai_duoc` | Chỗ chưa tra ra — ghi lại để không quên, thay vì đoán bừa |
| `ten_ova_majinzan` (11 mục) | Khi dịch OVA, có trường `do_chac` ghi rõ mức tin cậy từng tên |

### 5.2. Ghi cả độ tin cậy, không chỉ ghi kết quả

Bài học từ việc tự chế tên. Mục glossary mới có trường `do_chac`:

```json
{"tieng_trung":"忒娜麗","romaji":"Tenari","tieng_nhat":"(chưa xác minh)",
 "vai_tro":"Cháu gái Tonkararin","do_chac":"thap"}
```

Người đọc sau biết ngay cái nào chắc, cái nào cần tra lại — thay vì tưởng mọi mục đều chắc như nhau.

### 5.3. Ví dụ trọn vòng — `No-Fall-Down`

```
PHÁT HIỆN   Bộ dò hư từ tiếng Anh bắt được 27 dòng còn tên lạ ở Phần 2
TRUY NGUYÊN Bản Trung: 圓球不倒翁
            不倒翁 = con lật đật (đồ chơi bật dậy, không bao giờ đổ)
            → bản Anh dịch NGHĨA ĐEN thành "No-Fall-Down", làm mất trò đùa
              "不倒翁先生 跌倒了" = "ông Lật Đật ngã rồi!"
XÁC MINH    Trang chính thức + Wikipedia Nhật: マルダルマ (Marudaruma)
            マル = 丸 (tròn) + ダルマ = 達磨 (lật đật) → khớp chính xác 圓球不倒翁
SỬA         28 chỗ (gồm 1 biến thể tiếng Việt "Không-Bao-Giờ-Ngã")
GHI LẠI     Vào glossary; đồng thời lộ thêm 3 lỗi cùng cụm:
              Jeopardy/Kapidy → Kakubatteru (角畢迪 = カクバッテル)
              Louis Marcus    → Rui Omakasei (ルイ・オマカセイ)
              Stargate        → Tinh Môn (星門鎮)
```

Một lỗi được truy tới cùng thường kéo theo cả cụm lỗi cùng nguồn gốc.

---

## 6. Những lỗi đã trả giá đắt nhất

Sáu ca dưới đây định hình phần lớn quy tắc hiện tại.

**Tự chế từ Hán-Việt mà tiếng Việt không dùng.** Dịch `Bamboo Panda` thành "Trúc Hùng Miêu".
熊猫 là tiếng Trung; tiếng Việt nói **"gấu trúc"**. Mà cũng thừa, vì "trúc" đã là "bamboo".
Tra ra thì thật sự là **サンチョ・パンダ (Sancho Panda)** — nhại Sancho Panza,
**tên người** → giữ romaji, không dịch gì cả.
→ Sinh quy tắc G6: **tra tên gốc tiếng Nhật TRƯỚC khi tự đặt tên**.

**Dịch sai dấu hiệu.** `バツの字斬り` — バツ là dấu **✗**. Bản Trung viết 叉字斬 (叉 = ✗),
bản Anh ghi "X For Incorrect". Đã dịch thành 十字斬 (✚) — **sai dấu**.
Sửa thành **Xoa Tự Trảm** ở 13 chỗ. Lỗi có từ Phần 1, sống sót qua nhiều đợt rà.

**Ép vần cho kêu.** Dịch khẩu hiệu thành "Cười thật tươi, vui thật đã" — bị nhận xét
"cố vần mà nghe rất cringe". Thay bằng cách nói tự nhiên đã có sẵn ở bản ONA:
**"Cứ cười tươi và vui vẻ nhé!"**
→ Quy tắc: **ưu tiên cách nói tự nhiên hơn là vần điệu**.

**Bịa từ không có trong nguồn.** Gọi nhóm người đón khách là "nhân viên".
Kiểm lại bản Trung: **không hề có** 职员/员工/工作人员/服务员/店员/导游/向导 (đều 0 lần).
Nguồn chỉ dùng 她们 / 各位 / 家伙.
→ Quy tắc: **một từ không có trong nguồn thì không được tự thêm vào**.

**So sánh hai đơn vị không cùng loại.** Đem số ký tự tiếng Việt so với số **chữ Hán**
để đo độ dài câu. Chữ tượng hình khác chữ ghép âm: `快点` (2 chữ) ứng với
"Nhanh lên" (9 ký tự) — phép so sánh vô nghĩa ngay từ đầu.

**Tin chú thích của fansub.** Chú thích trong ngoặc do người làm sub tự thêm, có thể sai.
→ Ghi tại G8: **không dịch theo chú thích, phải tự kiểm chứng**.

---

## 7. Bộ công cụ

| File | Việc |
|---|---|
| `_work/build_vi.py` | Lõi dựng file. Ghép bản dịch vào khung `.ass` gốc, sinh karaoke, chèn style |
| `_work/apply_style_v2.py` | Chuyển dòng đã style sang karaoke. **Idempotent** — bỏ qua dòng đã có `\kf` |
| `_work/gan_trieu_hoi.py` | Gắn karaoke tại `(file, mốc thời gian)` chỉ định từ danh sách người đã duyệt |
| `_work/tim_trieu_hoi.py` | **Chỉ liệt kê** ứng viên triệu hồi kèm câu gốc — không bao giờ tự sửa |
| `_work/dong_bo_style.py` | Bảo đảm mọi style `summon-`/`atk-` đang dùng đều được khai báo trong `[V4+ Styles]` |
| `_work/epNN-vi.py` | Một file cho mỗi tập: `D` (bản dịch) + `SPECIAL` (chiêu thức) + `map_idx()` |

### 7.1. Khuôn một file dịch

```python
D = { 1:"...", 2:"...", ... }         # bản dịch theo số thứ tự dòng thoại
SPECIAL = {                            # chiêu thức cần karaoke
  227:{'style':'summon-senjinmaru','name':'Senjinmaru','kind':'trieu','pre':''},
  242:{'style':'atk-fire','name':'Enryuuken','kind':'chieu','pre':''},
}
def map_idx(d): ...                    # đổi số thứ tự thoại → số dòng trong file gốc
```

`map_idx()` cần thiết vì file nguồn xen kẽ dòng lời hát (`jpoped`/`cnoped`) giữa các
khối thoại, nên số thứ tự thoại **không trùng** số dòng trong file.

### 7.2. Kiểm trước khi dựng

```python
miss = [i for i in range(1, N+1) if i not in D]   # phải rỗng
```

Sót một dòng là câu đó giữ nguyên tiếng Trung trong bản phát hành — lỗi lộ liễu nhất.

---

## 8. Quy trình chuẩn cho một tập mới

```
1. Trích thoại nguồn, xác định ranh giới khối style và số thứ tự dòng
2. Tra glossary MỌI tên riêng xuất hiện — tên chưa có thì tra nguồn Nhật, đừng đoán
3. Dịch, giữ nguyên sắc thái xưng hô của từng nhân vật
4. Khai báo SPECIAL cho tên chiêu hô to
5. Kiểm không sót dòng nào (mục 7.2)
6. Dựng file
7. Kiểm toàn vẹn (mục 4.5)
8. Ghi tên mới vào glossary kèm do_chac
```

## 9. Quy trình audit cuối mỗi phần

```
1. Quét hư từ tiếng Anh (mục 4.1)
2. Quét biến thể chính tả của cùng một tên
3. Đối chiếu với bảng romaji_chinh_thuc
4. Quét mẫu văn dịch cứng, rồi ĐẶT CẠNH BẢN GỐC mới phán xét (mục 4.2)
5. Kiểm toàn vẹn file
6. Cập nhật glossary + LOI-DA-GAP.md
```

Bước 4 phải luôn có phần "đặt cạnh bản gốc". Bộ dò văn phong cho ra **129 dòng nghi vấn**
trên 97 tập, nhưng khi đặt cạnh câu tiếng Anh thì **phần lớn là báo động giả** —
"Cảm ơn tất cả mọi người!" là tiếng Việt hoàn toàn tự nhiên. Sửa theo bộ dò mà không
nhìn bản gốc sẽ làm bản dịch **tệ đi**.

---

## 10. Ba nguyên tắc rút gọn

**Nguồn có thứ bậc, và bậc nào cũng có thể sai.** Bản Anh sai nhiều nhất, bản Trung sai ít hơn,
nguồn Nhật chính thức thắng. Nhưng cần **2 nguồn Nhật độc lập** mới đủ để sửa hàng loạt.

**Máy tìm, người quyết.** Bộ quét dùng để **thu hẹp** từ 30.000 dòng xuống vài chục dòng
đáng nhìn. Quyết định sửa hay không luôn cần đặt bản dịch cạnh bản gốc và đọc bằng mắt.

**Ghi lại quan trọng ngang sửa.** Một lỗi đã sửa mà không ghi vào `LOI-DA-GAP.md`
là một lỗi sẽ tái phạm. Nhiều mục trong nhật ký đã cứu chính mình về sau —
mục C2 về `Kenou` đã cảnh báo đúng cái lỗi mà sau đó vẫn suýt mắc lại.
