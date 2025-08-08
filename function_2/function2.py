import time
import json
from datetime import datetime
from hx711py.hx711 import HX711
import os

# Khởi tạo cảm biến load cell
hx = HX711(dout_pin=5, pd_sck_pin=6)
hx.set_scale_ratio(1) # Đặt tỷ lệ ban đầu

# Hiệu chỉnh trọng lượng 
def calibrate_hx711():
    print("Bắt đầu hiệu chỉnh cảm biến HX711.")
    input("Đảm bảo cảm biến không có trọng lượng nào và nhấn Enter để zero...")
    hx.zero()
    print("Đã zero cảm biến.")
    time.sleep(1)

    known_weight_gram = float(input("Đặt một vật có trọng lượng đã biết (bằng gram) lên cảm biến và nhập giá trị: "))
    input("Nhấn Enter khi đã đặt vật lên cảm biến...")

    current_weight = hx.get_weight_mean(20)
    ratio = current_weight / known_weight_gram
    hx.set_scale_ratio(ratio)

    print(f"Giá trị đo được: {current_weight} (trọng lượng thực: {known_weight_gram}g)")
    print(f"Tỷ lệ hiệu chỉnh đã được đặt: {ratio}")
    print(f"Kiểm tra: {hx.get_weight_mean(20):.2f}g")
    
    return hx.get_scale_ratio()

# Thực hiện hiệu chỉnh và lấy tỷ lệ
scale_ratio = calibrate_hx711()

# Kiểm tra có người ngồi không
def is_sitting(weight):
    # Sử dụng ngưỡng trọng lượng sau khi đã hiệu chỉnh, ví dụ: 40kg = 40000g
    return weight > 40000

# Thời gian cần đứng dậy tối thiểu để reset lại bộ đếm
RESET_TIME = 5

# Tạo file json ghi lại dữ liệu thời gian ngồi
log_file = "sit_log.json"

# Nếu file chưa tồn tại thì tạo file rỗng với cấu trúc list
if not os.path.exists(log_file):
    with open(log_file, "w") as f:
        json.dump([], f)

# Khởi tạo trạng thái ban đầu khi chưa có ai ngồi
was_sitting = False
no_sitting_start_time = None

while True:
    try:
        # Lấy trọng lượng đã được hiệu chỉnh
        weight = hx.get_weight_mean(20)

        if is_sitting(weight):
            if not was_sitting:
                # Nếu đứng lên ngồi xuống trong 5s vẫn tính là đang ngồi
                if no_sitting_start_time and (time.time() - no_sitting_start_time <= RESET_TIME):
                    was_sitting = True
                    no_sitting_start_time = None
                else:
                    # reset lại dữ liệu cho lần ngồi mới
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    with open(log_file, "r+") as f:
                        data = json.load(f)
                        data.append({"Timestamp": timestamp, "Event": "Start Sitting"})
                        f.seek(0)
                        json.dump(data, f, indent=4)
                    was_sitting = True
                    no_sitting_start_time = None
        else:
            if was_sitting and no_sitting_start_time is None:
                # Bắt đầu đo thời gian đứng dậy
                no_sitting_start_time = time.time()
            elif was_sitting and (time.time() - no_sitting_start_time > RESET_TIME):
                # Đứng dậy đủ lâu thì kết thúc
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(log_file, "r+") as f:
                    data = json.load(f)
                    data.append({"Timestamp": timestamp, "Event": "Stop Sitting"})
                    f.seek(0)
                    json.dump(data, f, indent=4)
                was_sitting = False
                no_sitting_start_time = None

        time.sleep(0.5)

    except KeyboardInterrupt:
        print("Chương trình dừng lại.")
        break