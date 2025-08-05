from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime, timedelta
from distance_utils import DistanceCamera
from flask import Flask, send_from_directory
import atexit
from collections import defaultdict
import threading
import time
import os

app = Flask(__name__)

DB_PATH = 'work_sessions.db'
SAFE_DISTANCE_CM = 50
BREAK_REMINDER_MINUTES = 5  # Thời gian nhắc nghỉ (phút)

# Khởi tạo camera
camera = DistanceCamera(cam_id=0, safe_distance=SAFE_DISTANCE_CM)

def init_db():
    """Khởi tạo database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TEXT NOT NULL,
            end_time TEXT,
            duration TEXT,
            avg_distance TEXT,
            break_warnings INTEGER DEFAULT 0,
            distance_warning BOOLEAN DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

# Biến lưu trữ session hiện tại
current_session = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/api/history')
def api_history():
    """API lấy lịch sử làm việc"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM sessions ORDER BY start_time DESC')
    sessions = cursor.fetchall()
    conn.close()
    
    history_data = []
    for s in sessions:
        history_data.append({
            'id': s[0],
            'start_time': s[1],
            'end_time': s[2] if s[2] else '',
            'duration': s[3] if s[3] else '',
            'avg_distance': s[4] if s[4] else '0cm',
            'break_warnings': s[5] if s[5] else 0,
            'distance_warning': bool(s[6]) if s[6] is not None else False
        })
    
    return jsonify(history_data)

@app.route('/audio/<path:filename>')
def serve_audio(filename):
    try:
        return send_from_directory('audio', filename)
    except FileNotFoundError:
        return "Audio file not found", 404

def get_available_audio_files():
    audio_dir = 'audio'
    if os.path.exists(audio_dir):
        return [f for f in os.listdir(audio_dir) if f.endswith(('.mp3', '.wav', '.ogg'))]
    return []

@app.route('/api/chart_data')
def api_chart_data():
    """API lấy dữ liệu cho biểu đồ cột theo ngày"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM sessions WHERE start_time IS NOT NULL ORDER BY start_time')
    sessions = cursor.fetchall()
    conn.close()
    
    daily_data = defaultdict(lambda: {
        'sessions': 0,
        'total_minutes': 0,
        'total_distance': 0,
        'distance_warnings': 0,
        'break_warnings': 0
    })
    
    for session in sessions:
        try:
            date_str = session[1].split(' ')[0]
            
            duration = session[3] if session[3] else '0m'
            minutes = 0
            if 'h' in duration:
                hours = int(duration.split('h')[0])
                minutes += hours * 60
                remaining = duration.split('h')[1].strip()
                if 'm' in remaining:
                    minutes += int(remaining.replace('m', ''))
            elif 'm' in duration:
                minutes = int(duration.replace('m', ''))
            
            avg_distance = session[4] if session[4] else '0cm'
            distance = float(avg_distance.replace('cm', '')) if avg_distance else 0
            
            daily_data[date_str]['sessions'] += 1
            daily_data[date_str]['total_minutes'] += minutes
            daily_data[date_str]['total_distance'] += distance
            daily_data[date_str]['distance_warnings'] += 1 if session[6] else 0
            daily_data[date_str]['break_warnings'] += session[5] if session[5] else 0
            
        except (ValueError, IndexError, AttributeError) as e:
            print(f"Error parsing session data: {e}")
            continue
    
    chart_data = []
    for date, data in sorted(daily_data.items()):
        avg_distance = data['total_distance'] / data['sessions'] if data['sessions'] > 0 else 0
        
        chart_data.append({
            'date': date,
            'sessions': data['sessions'],
            'total_hours': round(data['total_minutes'] / 60, 1),
            'total_minutes': data['total_minutes'],
            'avg_distance': round(avg_distance, 1),
            'distance_warnings': data['distance_warnings'],
            'break_warnings': data['break_warnings']
        })
    
    return jsonify(chart_data)

@app.route('/api/check_break_reminder')
def check_break_reminder():
    """
    API kiểm tra thông báo nghỉ ngơi.
    - Logic tính thời gian làm việc hiệu quả sau break gần nhất.
    - Trả về should_break = True chỉ khi đủ 5 phút.
    """
    global current_session
    
    if current_session is None:
        return jsonify({'active': False, 'should_break': False})
    
    last_reset_time = current_session.get('last_break_taken_time', 
                                          datetime.strptime(current_session['start_time'], '%Y-%m-%d %H:%M:%S'))
    
    current_time = datetime.now()
    work_duration = (current_time - last_reset_time).total_seconds() / 60  # phút
    
    should_break = work_duration >= BREAK_REMINDER_MINUTES
    
    return jsonify({
        'active': True,
        'work_duration': round(work_duration, 1),
        'should_break': should_break,
        'break_warnings': current_session['break_warnings'],
        'next_break_in': max(0, BREAK_REMINDER_MINUTES - work_duration)
    })

@app.route('/start_work', methods=['POST'])
def start_work():
    """Bắt đầu phiên làm việc"""
    global current_session
    
    if current_session is not None:
        return jsonify({'success': False, 'error': 'Work session already started'})
    
    start_time = datetime.now()
    current_session = {
        'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
        'distances': [],
        'break_warnings': 0,
        'last_break_taken_time': start_time
    }
    
    try:
        camera.start_monitoring(server_url="http://localhost:5000", interval=3)
        print("🎥 Bắt đầu giám sát camera")
    except Exception as e:
        print(f"⚠️ Không thể khởi động camera: {e}")
    
    return jsonify({
        'success': True, 
        'start_time': current_session['start_time'],
        'break_reminder_minutes': BREAK_REMINDER_MINUTES
    })

@app.route('/stop_work', methods=['POST'])
def stop_work():
    """Kết thúc phiên làm việc"""
    global current_session
    
    if current_session is None:
        return jsonify({'success': False, 'error': 'No active work session'})
    
    camera.stop_monitoring()
    print("🔚 Dừng giám sát camera")
    
    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    start_dt = datetime.strptime(current_session['start_time'], '%Y-%m-%d %H:%M:%S')
    end_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
    duration_seconds = (end_dt - start_dt).total_seconds()
    
    hours = int(duration_seconds // 3600)
    minutes = int((duration_seconds % 3600) // 60)
    duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
    
    avg_distance = 0
    if current_session['distances']:
        avg_distance = sum(current_session['distances']) / len(current_session['distances'])
    
    avg_distance_str = f"{avg_distance:.1f}cm"
    
    distance_warning = any(d < SAFE_DISTANCE_CM for d in current_session['distances'])
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO sessions (start_time, end_time, duration, avg_distance, break_warnings, distance_warning)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (current_session['start_time'], end_time, duration_str, avg_distance_str,
          current_session['break_warnings'], distance_warning))
    
    conn.commit()
    conn.close()
    
    result = {
        'success': True,
        'duration': duration_str,
        'avg_distance': avg_distance_str,
        'break_warnings': current_session['break_warnings'],
        'distance_warning': distance_warning
    }
    
    current_session = None
    
    return jsonify(result)

@app.route('/dismiss_break_warning', methods=['POST'])
def dismiss_break_warning():
    """
    Tắt thông báo nghỉ ngơi hiện tại và reset bộ đếm thời gian.
    - Cập nhật last_break_taken_time để reset bộ đếm thời gian làm việc.
    """
    global current_session
    
    if current_session is None:
        return jsonify({'success': False, 'error': 'No active session'})
    
    current_session['break_warnings'] += 1
    current_session['last_break_taken_time'] = datetime.now()

    print("✅ Người dùng đã xác nhận thông báo nghỉ ngơi, bộ đếm thời gian đã được reset.")
    return jsonify({'success': True})

@app.route('/snooze_break_warning', methods=['POST'])
def snooze_break_warning():
    """
    Snooze break, không cần thay đổi gì trên backend, logic xử lý ở frontend.
    """
    return jsonify({'success': True})

@app.route('/add_distance', methods=['POST'])
def add_distance():
    """Thêm dữ liệu khoảng cách từ camera"""
    global current_session
    
    if current_session is None:
        return jsonify({'success': False, 'error': 'No active session'})
    
    data = request.get_json()
    distance = data.get('distance')
    
    if distance is not None and distance > 0:
        current_session['distances'].append(float(distance))
        print(f"📊 Nhận dữ liệu khoảng cách: {distance:.1f}cm")
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Invalid distance data'})

@app.route('/check_distance')
def check_distance():
    """Kiểm tra khoảng cách hiện tại"""
    global current_session
    
    try:
        too_close, distance = camera.is_too_close()
        
        if current_session and distance > 0:
            current_session['distances'].append(distance)
        
        return jsonify({
            'distance': distance,
            'warning': too_close,
            'safe_distance': SAFE_DISTANCE_CM
        })
    
    except Exception as e:
        print(f"❌ Lỗi kiểm tra khoảng cách: {e}")
        return jsonify({
            'distance': 0,
            'warning': False,
            'error': str(e)
        })

@app.route('/api/current_session')
def current_session_info():
    """Lấy thông tin session hiện tại"""
    global current_session
    
    if current_session is None:
        return jsonify({'active': False})
    
    last_reset_time = current_session.get('last_break_taken_time', 
                                          datetime.strptime(current_session['start_time'], '%Y-%m-%d %H:%M:%S'))
    current_time = datetime.now()
    work_duration = (current_time - last_reset_time).total_seconds() / 60  # phút
    
    return jsonify({
        'active': True,
        'start_time': current_session['start_time'],
        'work_duration': round(work_duration, 1),
        'distance_count': len(current_session['distances']),
        'break_warnings': current_session['break_warnings'],
        'avg_distance': sum(current_session['distances']) / len(current_session['distances']) if current_session['distances'] else 0,
        'next_break_in': max(0, BREAK_REMINDER_MINUTES - work_duration)
    })

def cleanup():
    """Dọn dẹp khi tắt server"""
    print("🔚 Đang dọn dẹp...")
    camera.stop_monitoring()
    camera.stop_camera()

atexit.register(cleanup)

if __name__ == '__main__':
    print("🚀 Khởi động Work Session Monitor...")
    
    init_db()
    
    print("✅ Hệ thống sẵn sàng!")
    print(f"⏰ Nhắc nghỉ ngơi mỗi {BREAK_REMINDER_MINUTES} phút")
    print("📱 Truy cập: http://localhost:5000")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    except KeyboardInterrupt:
        print("⏹️ Dừng server...")
        cleanup()