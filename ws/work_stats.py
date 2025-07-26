import sqlite3
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

DB_PATH = "work_monitor.db"

def get_weekly_summary(db_path, days=7):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    start_date = (datetime.now() - timedelta(days=days)).date()
    end_date = datetime.now().date()

    cursor.execute('''
        SELECT 
            DATE(created_date) as work_date,
            SUM(duration) as total_duration,
            AVG(avg_distance) as avg_distance,
            SUM(break_warnings) as total_warnings
        FROM work_sessions
        WHERE created_date BETWEEN ? AND ?
        GROUP BY DATE(created_date)
        ORDER BY created_date
    ''', (start_date, end_date))

    data = cursor.fetchall()
    conn.close()
    return data

def plot_summary(data):
    dates = [d[0] for d in data]
    durations = [(d[1] or 0)/3600 for d in data]  # đổi giây -> giờ
    avg_distances = [d[2] or 0 for d in data]
    break_warnings = [d[3] or 0 for d in data]

    fig, axs = plt.subplots(3, 1, figsize=(10, 12))

    # Biểu đồ 1: Tổng thời gian làm việc theo ngày
    axs[0].bar(dates, durations, color='skyblue')
    axs[0].set_title("Tổng thời gian làm việc (giờ)")
    axs[0].set_ylabel("Giờ")

    # Biểu đồ 2: Khoảng cách trung bình theo ngày
    axs[1].plot(dates, avg_distances, marker='o', color='green')
    axs[1].set_title("Khoảng cách trung bình (cm)")
    axs[1].set_ylabel("cm")

    # Biểu đồ 3: Số lần cảnh báo nghỉ
    axs[2].bar(dates, break_warnings, color='orange')
    axs[2].set_title("Số lần cảnh báo nghỉ")
    axs[2].set_ylabel("Cảnh báo")

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    data = get_weekly_summary(DB_PATH, days=14)  # Lấy dữ liệu 14 ngày gần nhất
    if data:
        plot_summary(data)
    else:
        print("❌ Không có dữ liệu trong khoảng thời gian này!")
