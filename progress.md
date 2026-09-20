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

-- Hướng tới một LLM có sẵn để sử lý


20/9 sau khi kiểm tra candidate thì cho thầy đầu ra không ổn định kh phù hợp với mong muốn
đang tìm kiếm một nguồn vào khác ổn định hơn

20/9 đổi hướng - chỉ lấy 100 từ để làm baseline để đánh giá để làm phần advance 
thử qwen cho việc cải thiện input để query
ImageSearchProvider
│
├── DuckDuckGoProvider --> sử dụng cái này
20/9 hướng mới: sử dụng một model suy luận LLM - Qwen3 1.7B để làm trước phần query chuẩn bị cho việc tìm data ảnh
vấn đề hiện tại là cần chỉnh sửa promt để model đưa ra kết quả query trước phần đánh giá 
phần suy luận đang quá chậm cần cải thiện 
tối ưu lại scope - lấy 100 làm chuẩn -> làm sao cho data đạt 100/100 để làm baseline cho phần advance

suy nghỉ được một background hợp lý cho phần web

20/9 vẫn còn loay hoay việc suy luận - test_qwen.py và query_generator đang hoạt động không tốt - check list 20/9 trong schedule chưa được hoàng thành 

list nhìn tổng thể ngày hôm nay vẻ ra được 
100 vocabulary
      ↓
Qwen3 1.7B
      ↓
concept / sense / visual intent
      ↓
Query Generator <-- đang ở đây
      ↓
DuckDuckGo
      ↓
metadata filter
      ↓
5–8 thumbnails
      ↓
SigLIP
      ↓
top 3
      ↓
download best original
      ↓
crop 1:1
      ↓
768×768
      ↓
flashcard image