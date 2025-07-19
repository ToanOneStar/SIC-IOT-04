# ĐÂY LÀ HỆ THỐNG GHI LẠI THỜI GIAN NGỒI 

Code có dữ liệu đầu vào như ở chức năng 1, nó đếm thời gian bắt đầu và kết thúc ngồi và ghi lại vào 1 file csv.

Đoạn mã thực hiện như sau:
- Bắt đầu khởi tạo các biến
- Tạo 1 file csv nếu chương trình chạy lần đầu.
- Cơ chế của vòng lặp chính:
  + Nếu đã có người ngồi thì kiểm tra 2 trường hợp:
     > Nếu trước đó chưa có người ngồi (was_sitting = False) thì kiểm tra xem trước 5s người đó người đó đang ngồi hay không, nếu có thì vẫn tính là người đó ngồi liên tục còn không thì tính là phiên ngồi mới và reset lại bộ đếm.
     > Nếu trước đó đã có người ngồi rồi thì có nghĩa là người đó đang ngồi liên tục.
  + Nếu trước đó không có người ngồi thì kiểm tra xem thời gian không có người ngồi đã quá 5s chưa, nếu quá rồi thì kết thúc phiên ngồi.

Kết quả là ghi dữ liệu ra file csv có 2 thành phần là thời gian và trạng thái.