# Star Background Concept

## 1. Mục tiêu

Thiết kế background động cho web game theo phong cách bầu trời đêm / galaxy xanh đậm, có nhiều ngôi sao chuyển động chậm. Background cần tạo cảm giác có chiều sâu, nhẹ nhàng, không gây mất tập trung khỏi nội dung học.

Ảnh tham chiếu hiện tại dùng làm **art direction**, không nhất thiết dùng trực tiếp làm ảnh nền cuối cùng.

## 2. Ý tưởng chuyển động cốt lõi

Mỗi ngôi sao là một particle độc lập.

### Chuyển động theo trục Y

- Sao rơi chậm từ trên xuống dưới.
- Mỗi sao có tốc độ rơi riêng.
- Khi đi ra khỏi đáy màn hình, sao được đưa trở lại phía trên để tạo vòng lặp vô hạn.
- Không dùng gia tốc rơi tăng mãi theo thời gian vì sẽ khiến sao rơi quá nhanh. Với UI background, vận tốc Y gần như cố định sẽ phù hợp hơn.

Công thức cơ bản:

```text
y += fallSpeed * deltaTime
```

## 3. Phản ứng theo con trỏ chuột

Theo trục X, các ngôi sao không bám trực tiếp vào vị trí con trỏ.

Thay vào đó:

- Con trỏ tạo ra một độ lệch ngang so với tâm màn hình.
- Mỗi sao có một vị trí X cơ sở `baseX`.
- Khi chuột di chuyển, sao dịch chuyển nhẹ sang cùng hướng.
- Chuyển động phải mượt, có quán tính nhẹ.

### Cách đơn giản: Smooth / Lerp

```text
targetX = baseX + mouseInfluence
x += (targetX - x) * smoothing
```

### Cách ưu tiên: Spring + Damping

```text
vx += (targetX - x) * springForce
vx *= damping
x += vx
```

Cách thứ hai tạo cảm giác tốt hơn: khi đổi hướng chuột, sao hơi trễ một nhịp rồi mới đổi hướng, tạo cảm giác quán tính.

## 4. Parallax theo độ sâu

Mỗi sao có một thuộc tính `depth` để mô phỏng khoảng cách tới người xem.

Ví dụ:

```text
depth = 0.2
- sao nhỏ
- rơi rất chậm
- phản ứng với chuột rất ít

depth = 0.6
- sao trung bình
- rơi vừa
- phản ứng vừa

depth = 1.0
- sao lớn / sáng hơn
- rơi nhanh hơn một chút
- phản ứng với chuột rõ nhất
```

Điều này tạo hiệu ứng parallax 3D mà không cần Three.js.

## 5. Cách tính ảnh hưởng của chuột

Chuẩn hóa vị trí chuột theo chiều ngang màn hình:

```ts
const normalizedMouseX =
  (mouseX / window.innerWidth - 0.5) * 2
```

Sau đó:

```ts
star.targetX =
  star.baseX +
  normalizedMouseX *
  MAX_PARALLAX *
  star.depth
```

Khi chuột ở giữa màn hình, sao gần vị trí ban đầu.

Khi chuột sang trái hoặc phải, các lớp sao dịch chuyển theo mức độ khác nhau dựa trên `depth`.

## 6. Twinkle / nhấp nháy nhẹ

Không nên để toàn bộ sao sáng cố định.

Một số sao có thể thay đổi opacity nhẹ theo thời gian:

```ts
opacity =
  baseOpacity +
  Math.sin(time * twinkleSpeed + offset) * 0.15
```

Mục tiêu là tạo cảm giác sống động nhưng không gây nhiễu.

## 7. Sao đặc biệt

Một tỷ lệ nhỏ, khoảng 1–3%, có thể là sao sáng dạng bốn cánh như:

```text
    |
 -- ✦ --
    |
```

Các sao này có thể:

- sáng hơn sao thường
- có glow nhẹ
- twinkle chậm
- xuất hiện thưa để tránh làm background quá rối

## 8. Phân lớp background

Background nên có nhiều lớp:

```text
Layer 0: gradient / nebula
Layer 1: sao xa, rất nhỏ, rất chậm
Layer 2: sao trung bình
Layer 3: sao gần, sáng hơn, parallax mạnh hơn
Layer UI: giao diện game nằm phía trên
```

Gợi ý màu:

- xanh navy rất đậm
- cyan / teal nhẹ
- trắng xanh nhạt
- một ít vàng nhạt ở một số sao

## 9. Cấu trúc dữ liệu particle

Ví dụ TypeScript:

```ts
type Star = {
  x: number
  y: number

  baseX: number

  radius: number
  opacity: number

  fallSpeed: number

  depth: number

  vx: number

  twinkleSpeed: number
  twinkleOffset: number
}
```

Có thể mở rộng thêm:

```ts
type Star = {
  // ...
  isSparkle: boolean
  glowStrength: number
}
```

## 10. Công nghệ triển khai

### Lựa chọn ưu tiên

**React + TypeScript + HTML5 Canvas 2D**

Không cần Three.js ở giai đoạn này.

Lý do:

- hiệu ứng chỉ là particle 2D
- Canvas xử lý hàng trăm particle rất nhẹ
- không cần render hàng trăm `<div>` bằng React mỗi frame
- dễ kiểm soát animation bằng `requestAnimationFrame`

Kiến trúc:

```text
React App
│
├── Game UI (DOM)
│
└── <StarBackground />
    │
    └── Canvas 2D
        ├── particles
        ├── falling
        ├── mouse influence
        ├── inertia
        ├── parallax
        ├── twinkle
        └── glow
```

## 11. Canvas layer

Canvas nên là một layer fullscreen nằm phía sau UI:

```css
position: fixed;
inset: 0;
z-index: -1;
pointer-events: none;
```

Animation dùng:

```ts
requestAnimationFrame()
```

Con trỏ chuột được theo dõi bằng:

```text
pointermove
```

## 12. Nguyên tắc performance

Không nên render mỗi ngôi sao bằng React component riêng.

Không nên có kiểu:

```text
<Star />
<Star />
<Star />
... x 300
```

và update React state mỗi frame.

Nên để React chỉ quản lý việc mount/unmount canvas, còn toàn bộ animation chạy trực tiếp trong Canvas API.

## 13. Hiệu ứng tương tác với gameplay

Có thể liên kết background với sự kiện trong game, nhưng phải rất nhẹ.

Ví dụ khi trả lời đúng:

- một vài sao tăng brightness trong thời gian ngắn
- một shooting star nhỏ xuất hiện
- glow tăng nhẹ rồi trở lại bình thường

Không nên dùng flash mạnh toàn màn hình vì sẽ phá cảm giác dịu của background.

## 14. Tóm tắt concept

Concept cuối cùng:

> Infinite falling star field + horizontal mouse attraction + inertia + depth-based parallax + subtle twinkling.

Phong cách hình ảnh:

> Galaxy / starry night xanh navy - teal, nhiều lớp sao nhỏ, chuyển động chậm và mượt.

Công nghệ ưu tiên:

> Canvas 2D + TypeScript trong React.

Không cần WebGL hoặc Three.js ở giai đoạn đầu.

## 15. Ghi chú triển khai sau này

Khi bắt đầu code, nên tách background thành component độc lập, ví dụ:

```text
web/
└── src/
    └── components/
        └── StarBackground.tsx
```

Component này không nên chứa logic gameplay. Nó chỉ nhận các signal đơn giản nếu cần, ví dụ:

```ts
<StarBackground event="correct-answer" />
```

hoặc thông qua một event/state nhỏ để kích hoạt hiệu ứng đặc biệt.
