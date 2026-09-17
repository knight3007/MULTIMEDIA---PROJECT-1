Thu thập data 
                 SOURCES
                    │
       ┌────────────┼────────────┐
       ↓            ↓            ↓
    JMdict      Openverse      TTS
       │            │            │
       └────────────┼────────────┘
                    ↓
              DATA BUILDER
             (Python script)
                    ↓
          ┌──────────────────┐
          │ STATIC DATASET   │
          ├──────────────────┤
          │ vocabulary       │
          │ definition       │
          │ image            │
          │ audio            │
          └──────────────────┘
                    ↓
                WEB GAME


13/9 đang dừng ở đoạn chuẩn bị data - ảnh hiện tại kh phù hợp đang cài thêm model để cải thiện việc chọn ảnh

17/9 tích hợp tính năng xếp hạng bằng SigLIP và tái cấu trúc các thành phần thu thập dữ liệu
17/9 Tái cấu trúc tệp `collector.py` thành các mô-đun riêng biệt dựa trên chức năng.
17/9 Bổ sung bản thảo ban đầu cho quy trình thu thập dữ liệu âm thanh.
lưu ý ngày 17/9 hình ảnh và cả âm thanh đều chưa phù hợp đang suy nghĩ cho bước tiếp theo ổn định hơn

    