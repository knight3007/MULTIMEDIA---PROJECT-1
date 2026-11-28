# G-002.9 Galaxy UI mockup

Prototype tương tác **chỉ để duyệt thiết kế** cho Unity Desktop 2D. Mọi điểm số, pack, tiến độ AI và trạng thái gameplay trong mockup là mô phỏng. Media từ Content Pack 15 từ có `test_only=true`, `needs_review`; không phải dữ liệu gameplay `ready` hay tài sản đã được duyệt để phát hành.

Từ thư mục gốc repo, chạy:

```powershell
python -m http.server 8765 --bind 127.0.0.1
```

Mở `http://127.0.0.1:8765/game/prototypes/g0029_ui_mockup/` trên trình duyệt desktop. Máy chủ chỉ phục vụ tệp cục bộ; mockup không gọi AI, Docker hay dịch vụ ngoài. Cần giữ nguyên cấu trúc thư mục repo để các đường dẫn `../../UXUI/` và `../../../reports/` hoạt động. Không đưa prototype này lên mạng công khai.

Thanh **G-002.9 REVIEW** nằm ngoài khung game 16:9 (không che HUD) và cho phép nhảy S01–S11, đổi EN/JA, so sánh khung hình, hai cách đặt chữ và Full Word / Fill-in-the-Blank, dừng sao, giảm chuyển động, kích hoạt laser/nổ và đặt lại trạng thái. Có thể ẩn thanh này khi chụp màn hình. Ở Gameplay, nhấn Tab để đổi mục tiêu, nhập đáp án rồi Enter để xem hiệu ứng. Ở Full Word, phần đang gõ hiện trên đúng thiên thạch và được giữ riêng cho từng thiên thạch; Text + Image/Text Only hiện chữ đầu, Text + Image hiện thêm ảnh pack. Laser bắn vào thiên thạch đang chọn. Pause/Resume và Flashcard có tương tác mô phỏng. Import và AI Progress chỉ thay đổi giao diện, không đọc/validate workbook hay chạy pipeline. Âm thanh trên Flashcard chỉ phát khi người xem bấm nút; trình duyệt có thể chặn nếu chưa tương tác.

**Nguồn hình/âm:** sprite tàu, thiên thạch, laser, shield, reticle, nút và panel từ Kenney trong `game/UXUI/`; font Noto Sans/Noto Sans JP từ cùng thư viện; ảnh và âm EN/JA của 3 mục trong Content Pack 15 từ tại `reports/EXCEL_15_SMOKE/.../content_pack_v46/`. Tệp gốc không được sao chép hay chỉnh sửa. Background Canvas 2D diễn giải tài liệu `game/background/background_idea.md`; texture Kenney blue không thay thế concept đó.

Mockup không chứng minh khả năng render TextMeshPro, IME của Unity, cân bằng game, tính đúng ngữ nghĩa/âm đọc hay quyền phát hành media. Không có project Unity hoặc gameplay engine nào được tạo trong thư mục này.

## Ảnh rà soát

Thư mục `screenshots/` có 13 ảnh 1920 × 1080 chụp ngày 2026-11-27 bằng Edge headless (`--window-size=1920,1080`, URL có `capture=1&toolbar=0`). Gồm Main Menu, Library, Import Excel, Language Selection (JA), Game Configuration, Meteor Defense EN và JA (bố cục A, Full Word), Pause, Results, Flashcard (JA), Settings, `12_gameplay_en_layout_b.png` và `13_gameplay_ja_fill_layout_b.png` (JA, bố cục B, Fill-in-the-Blank). Bộ ảnh ngày 2026-11-26 trước đó bị giới hạn ở 754 × 440 và đã được thay thế.

Có thể mở thẳng một trạng thái bằng URL, ví dụ `?screen=S07&lang=JA&layout=B&answer=FILL_IN_THE_BLANK&capture=1&toolbar=0`.

## Quyết định

- 2026-11-27: chủ dự án chọn **bố cục A** (nghĩa Việt ở trên, đáp án ở dưới thiên thạch), ghi tại D-029. Bố cục B chỉ còn trong thanh review để so sánh.

## Sửa lỗi ngày 2026-11-27

- Nhãn của nút chính (asset Kenney `button_square_header_large_rectangle.png`) được canh vào dải xanh của asset. Trước đây chữ nằm đè lên đường ranh giữa hai phần nên khó đọc.
- Thanh review được tách ra khỏi khung game. Trước đây nó che ô HP/Wave.
- Reticle dùng bản SVG cùng mẫu (`Vector/Blue/crosshair_color_a.svg`) nên không còn bị mờ khi phóng to. Reticle đặt phía sau thiên thạch.
- Full Word hiển thị phần đang gõ hoặc gợi ý chữ đầu, thay cho chuỗi `_ _ _ _ _ _` cố định.
- Laser nhắm đúng mục tiêu đang chọn. Ô nhập không còn mất focus sau khi trả lời đúng. Tab bỏ qua các thiên thạch đã bị phá.
- Dòng chú thích không còn đè lên chữ hướng dẫn. Mẫu chữ JA không còn bị ngắt dòng giữa từ (ví dụ 食べる).

## Tinh chỉnh UX ngày 2026-11-27 (skill ui-ux-pro-max + emil-design-eng)

- Chuyển màn: mờ dần và nâng nhẹ 8px trong 220ms, chỉ khi đổi màn (không chạy lại khi gõ hoặc khi toast hiện). Khi bật giảm chuyển động thì chỉ còn mờ dần.
- Nút, thẻ lựa chọn và pack: thu nhỏ còn `scale(.97)` khi bấm (140ms, ease-out mạnh), đổi màu nền và viền mượt trong 150ms. Hiệu ứng hover chỉ áp dụng cho thiết bị có chuột.
- Toast xuất hiện có chuyển tiếp ngắn 200ms. Khi nhập sai, viền nhãn của thiên thạch đang chọn chuyển đỏ (không rung, vì đây là thao tác bàn phím lặp lại nhiều).
- Nâng cỡ chữ nhỏ nhất (nhãn HUD, chip, hướng dẫn, chú thích) để ở khung 1366×768 không còn chữ quá nhỏ, khoảng dưới 9px.
- Không chạy `impeccable`, vì launcher của skill này tải binary từ GitHub và cần chủ dự án cho phép trước.

## Sửa theo Impeccable critique ngày 2026-11-27

Kết quả critique lần đầu là 24/40, lưu tại `.impeccable/critique/`. Chủ dự án chọn sửa top 3 vấn đề, ưu tiên trải nghiệm học:

- **[P0] Flashcard:** mặt trước chỉ còn từ, ảnh và nút phát âm; nghĩa tiếng Việt chuyển ra mặt sau với cỡ chữ lớn. Phím Space lật thẻ, ←/→ đổi thẻ.
- **[P1] Áp lực gameplay:** thiên thạch rơi một chiều tới tuyến phòng thủ (JS điều khiển, nên Tab hay toast không làm thiên thạch nhảy về đầu). Gần tới tuyến thì viền chuyển màu hổ phách. Khi chạm tuyến: mất 1 HP (icon mờ đi), viền màn hình nháy đỏ, toast ghi rõ tên thiên thạch, combo về 0. Hết HP thì bản xem thử tự hồi lại. Tốc độ rơi là giá trị mô phỏng, chưa phải cân bằng.
- **[P1] Nút chính:** chuyển sang asset Kenney một mặt `kenney_space-shooter-remastered/PNG/UI/buttonBlue.png` (dùng `border-image`), cao bằng nút phụ cùng hàng.
- Thêm: nhập sai thì toast nói rõ sai ở thiên thạch nào, combo về 0 (theo D-028), và nhãn có thêm chữ "Sai ·" để không chỉ dựa vào màu. Placeholder ô nhập đạt độ tương phản ≥ 4.5:1.
- Chưa làm: lối "Chơi ngay" bỏ qua S06, gom nhãn "mô phỏng" thành một huy hiệu, panel lồng trong Flashcard.
