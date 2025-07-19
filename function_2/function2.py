import time
import csv
from datetime import datetime
from hx711py.hx711 import HX711

# Khởi tạo cảm biến load cell
hx = HX711(dout_pin=5, pd_sck_pin=6)
hx.zero()

# Kiểm tra có người ngồi không 
def is_sitting(weight):
    return weight > 40000

# Thời gian cần đứng dậy tối thiểu để reset lại bộ đếm 
RESET_TIME = 5  

# Tạo file csv ghi lại dữ liệu thười gian ngồi 
log_file = "sit_log.csv"
try:
    with open(log_file, "x", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "Event"])
except FileExistsError:
    pass

# Khởi tạo trạng thái bắt đầu khi chưa có ai ngồi 
was_sitting = False
no_sitting_start_time = None

while True:
    try:
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
                    with open(log_file, "a", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow([timestamp, "Start Sitting"])
                    was_sitting = True
                    no_sitting_start_time = None
        else:
            if was_sitting and no_sitting_start_time is None:
                # Bắt đầu đo thời gian đứng dậy
                no_sitting_start_time = time.time()
            elif was_sitting and (time.time() - no_sitting_start_time > RESET_TIME):
                # Đứng dậy đủ lâu thì kết thúc 
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(log_file, "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([timestamp, "Stop Sitting"])
                was_sitting = False
                no_sitting_start_time = None

        time.sleep(3)

    except KeyboardInterrupt:
        break
