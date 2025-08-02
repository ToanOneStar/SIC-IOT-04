# ĐÂY LÀ HỆ THỐNG GIÁM SÁT THỜI GIAN NGỒI

Code có đầu vào là dữ liệu được đọc từ HX711 nối với loadcell và có cơ chế cảnh báo bằng đèn LED và loa 

Đoạn mã được thực hiện như sau:
- Bắt đầu khởi tạo các biến. 
- Kiểm tra xem có ai đang ngồi không và đã ngồi bao lâu:
  + Nếu đang ngồi(đứng lên rồi xuống trong khoản thời gian quy định cũng được tính) thì bộ đếm sẽ đếm giờ. Nếu quá giờ quy định sẽ cảnh báo tùy theo mức độ.
  + Ngược lại nếu không có người ngồi sẽ tắt hết cảnh báo và đặt lại bộ đếm.

Kết quả là in ra terminal trạng thái có người ngồi hay không, khối lượng của người đó và thời gian ngồi.
    