# Thống kê & Phân tích thói quen làm việc

## 📌Đoạn code thực hiện như sau:
- Dùng **SQLite** đọc dữ liệu từ `work_monitor.db`
- Truy vấn dữ liệu trong `work_sessions.db` để lấy các thuộc tính: ngày làm việc, tổng thời gian làm việc (giây), khoảng cách trung bình trong ngày và tổng số cảnh báo trong ngày
- Vẽ **biểu đồ thống kê**:
  - Tổng thời gian làm việc theo ngày
  - Khoảng cách trung bình theo ngày
  - Số lần cảnh báo nghỉ

## 🛠️ Cài đặt
- Thư viện:
  ```bash
  pip install matplotlib 
