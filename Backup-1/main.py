import cv2
import cvzone
from cvzone.FaceMeshModule import FaceMeshDetector
import requests
import time
import threading

# Cấu hình ESP32
ESP32_IP = "192.168.1.6"  # Thay bằng IP của ESP32
ESP32_PORT = 80


class EyeDistanceMonitor:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Can't open camera.")
            exit()

        self.detector = FaceMeshDetector(maxFaces=1)
        self.last_alert_time = 0
        self.alert_interval = 2  # Gửi cảnh báo mỗi 2 giây

    def send_to_esp32(self, distance, is_warning):
        """Gửi dữ liệu đến ESP32"""
        try:
            url = f"http://{ESP32_IP}:{ESP32_PORT}/update"
            data = {
                'distance': distance,
                'warning': 1 if is_warning else 0
            }
            response = requests.post(url, json=data, timeout=1)
            if response.status_code == 200:
                print(f"Sent: {distance}cm, Warning: {is_warning}")
        except Exception as e:
            print(f"Error data: {e}")

    def run(self):
        while True:
            success, img = self.cap.read()
            if not success or img is None:
                print("Can't access img from camera")
                continue

            img, faces = self.detector.findFaceMesh(img, draw=False)

            if faces:
                face = faces[0]
                pointLeft = face[145]
                pointRight = face[374]
                w, _ = self.detector.findDistance(pointLeft, pointRight)

                # Tính khoảng cách
                W = 6.3  # khoảng cách thật giữa 2 điểm mắt (cm)
                f = 840  # tiêu cự đã hiệu chỉnh
                d = (W * f) / w

                # Kiểm tra cảnh báo
                is_warning = d < 50
                current_time = time.time()

                # Hiển thị trên màn hình
                color = (0, 0, 255) if is_warning else (0, 255, 0)
                status = "CANH BAO!" if is_warning else "OK"

                cvzone.putTextRect(img, f'Khoang cach: {int(d)}cm',
                                   (face[10][0] - 100, face[10][1] - 50),
                                   scale=2, colorR=color)
                cvzone.putTextRect(img, status,
                                   (face[10][0] - 100, face[10][1] - 10),
                                   scale=2, colorR=color)

                # Gửi dữ liệu đến ESP32 (không quá thường xuyên)
                if current_time - self.last_alert_time > self.alert_interval:
                    self.send_to_esp32(int(d), is_warning)
                    self.last_alert_time = current_time

                print(f"Distance: {d:.2f} cm - {status}")

            cv2.imshow("Eye Distance Monitor", img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    monitor = EyeDistanceMonitor()
    monitor.run()