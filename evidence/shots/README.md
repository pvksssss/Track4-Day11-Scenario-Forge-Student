# Ảnh bằng chứng — 2A202602590

Ảnh chụp thật từ viewer chương 9 trên `evidence/review.html`, không dùng ảnh mẫu
giảng viên. Bảng tham số lấy từ `viewer.json` và cảnh hazard chính xác; chỉ cắt
lề trống do ảnh chụp trình duyệt, không chỉnh tác nhân hay số liệu.

| File | Cảnh | Thời điểm | Xe chính / bóng mờ |
|---|---|---:|---|
| bus-bypass.jpg | B-01 | 12.40 s, frame 248 | baseline / policy chọn |
| crosswalk-block.jpg | C-01 | 20.05 s, frame 401 | baseline / policy chọn |
| policy-fix.jpg | FIX-B-01 | 12.40 s, frame 248 | policy chọn / baseline |
| hazard-bike.jpg | G-EXACT | 4.65 s, frame 93 | baseline / policy chọn |

Viewer làm tròn readout một chữ số thập phân: 20.05 hiển thị 20.1, 4.65 hiển
thị 4.7. Slider được đặt bằng thời điểm đầy đủ. `review-scenes.json` lưu sự
kiện tính lại từ tham số đầy đủ bằng Python.

Exporter ghim baseline vào B-*/C-*, nên hai nhãn “chính sách của bạn/gốc” trong
bảng đọc của chúng phải hiểu theo policy đang ghim. Cảnh FIX-* đổi vai để bảng
so sánh có xe chính là bản sửa và bóng mờ đúng là baseline.
