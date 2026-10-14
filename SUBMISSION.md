# Phạm Văn Kiên — 2A202602590

Bài làm gồm `lab11/*.py`, `hazard.json`, `REPORT.md`, kết quả chạy đầy đủ trong
`evidence/` và ảnh chụp thật trong `evidence/shots/`.

## Chạy lại

```powershell
python -m pip install -r requirements.txt
python -m pytest -q
python run_lab.py all
python prepare_review.py
python write_report.py
python verify_submission.py --zip
```

`run_lab.py` đọc nguyên MSSV `2A202602590` ở dòng đầu báo cáo và truyền qua
`LAB11_MSSV`, biến môi trường chính thức của pipeline. Cách này giữ đúng chuỗi
MSSV để suy ra thị trấn B và seed, vì parser của `run_all.py` chỉ chấp nhận chữ số.
Không sửa `run_all.py`, `avsim/`, `tests/`, `viewer/` hoặc các policy ứng viên gốc.
Lệnh tương đương khi chấm:

```powershell
$env:LAB11_MSSV = '2A202602590'
python run_all.py all
```

Mở `evidence/review.html#lab` để xem dữ liệu của bài làm offline, không phải dữ
liệu mẫu của giảng viên. Trang này dùng nguyên mã viewer, nạp `viewer.json` qua
file JavaScript cục bộ do `prepare_review.py` tạo. Các nút `FIX-*` có xe chính là
policy đã chọn và bóng mờ là policy gốc; `G-EXACT` là cảnh chính xác trong hazard.
`review-scenes.json` lưu thời điểm sự kiện tính lại từ đầy đủ tham số.

`hazard.json: exposure` là giả định vận hành minh họa có giải thích và phân tích
độ nhạy trong báo cáo; chưa được hiệu chỉnh bằng dữ liệu giao thông thật.
Kết quả không phải chứng nhận an toàn ngoài đời.

Chỉ dùng ngân sách đầy đủ để nộp; không dùng `--quick`. Các thử nghiệm thiết kế
hazard được tách khỏi kết quả chính thức. Sau khi chạy lại, cần chụp lại ảnh nếu
đổi MSSV, hazard hoặc thuật toán. `evidence/` được bỏ khỏi danh sách ignore để
được đưa vào bài nộp. Không cần đưa file ZIP vào Git.
