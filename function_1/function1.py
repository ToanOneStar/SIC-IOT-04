import time
from gpiozero import LED, Buzzer 
from hx711py.hx711 import HX711

# Khởi tạo cảm biến load cell
hx = HX711(dout_pin=5, pd_sck_pin=6)
hx.zero()

# Khởi tạo đèn cảnh báo 
led_alert = LED(17)
buzzer_alert = Buzzer(27)

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

# Thời gian tối đa ngồi cho phép theo mức (tính bằng giây)
MAX_SITTING_TIME = 3600  
MAX_SITTING_TIME_2 = 4200

# Kiểm tra có người ngồi không (trên 40kg)
def is_sitting(weight):
    return weight > 40000   

start_time = None
no_sitting_start_time = None
RESET_TIME = 5 # Thời gian không ngồi tối thiểu để làm mưới bộ đếm 

while True:
    try:
        weight = hx.get_weight_mean(20)
        print(f"Khối lượng: {weight:.2f} g")

        if is_sitting(weight):
            no_sitting_start_time = None # đặt lại bộ đếm trễ nếu có người ngồi 
            if start_time is None:
                start_time = time.time()
            else:
                duration = time.time() - start_time
                print(f"Đã ngồi: {duration:.0f} giây")

                if duration > MAX_SITTING_TIME:
                    led_alert.on()
                else:
                    led_alert.off()
                
                if duration > MAX_SITTING_TIME_2:
                    buzzer_alert.on()
                else:
                    buzzer_alert.off()

        else:
             print("Không có người ngồi.")
             if no_sitting_start_time is None:
                 no_sitting_start_time = time.time()
             elif (time.time() - no_sitting_start_time) > RESET_TIME: #nếu thời gian rời ghế quá 5s thì đặt lại bộ đếm 
                 start_time = None
                 led_alert.off()
                 buzzer_alert.off() 

        time.sleep(0.5)
         
    except KeyboardInterrupt:
        print("Dừng chương trình.")
        led_alert.off()
        buzzer_alert.off()
        break
    