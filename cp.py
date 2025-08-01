# File: webserver.py (Phiên bản FLASK - đáng tin cậy)
# Mã nguồn này sử dụng Flask để phục vụ các file HTML, CSS, JS và hình ảnh từ thư mục gốc.
# Nó tự động tìm file HTML đầu tiên trong thư mục gốc và phục vụ nó tại
import sys
import os
import webbrowser
import threading
import socket
from flask import Flask, send_from_directory, redirect, url_for

# --- Xác định thư mục gốc (nơi chứa file exe) ---
try:
    # Dùng khi chạy từ file .exe đã được biên dịch
    BASE_DIR = os.path.dirname(sys.executable)
except NameError:
    # Dùng khi chạy từ file .py để debug
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Tạo ứng dụng Flask ---
# template_folder và static_folder được đặt là thư mục gốc
# Điều này cho phép Flask tìm các file css, js, images...
app = Flask(__name__, template_folder=BASE_DIR, static_folder=BASE_DIR)

TARGET_HTML_FILE = None

# Tìm file HTML đầu tiên trong thư mục gốc
for file in os.listdir(BASE_DIR):
    if file.lower().endswith('.html'):
        TARGET_HTML_FILE = file
        break

if not TARGET_HTML_FILE:
    print(f"Error: No .html file found in '{BASE_DIR}'.")
    input("Press Enter to exit.")
    sys.exit(1)

# --- Định nghĩa các route (đường dẫn URL) ---

# Route cho trang gốc: http://localhost:PORT/
@app.route('/')
def index():
    # Chuyển hướng đến route phục vụ file HTML chính
    return redirect(url_for('serve_main_html'))

# Route để phục vụ file HTML chính
@app.route('/app')
def serve_main_html():
    # Gửi file HTML từ thư mục gốc
    return send_from_directory(BASE_DIR, TARGET_HTML_FILE)

# Route để phục vụ các file tĩnh khác (CSS, JS, ảnh...)
# Flask sẽ tự động xử lý các file này nếu chúng được tham chiếu đúng trong HTML
# Ví dụ: <link rel="stylesheet" href="style.css">
# Flask sẽ tìm 'style.css' trong thư mục gốc (BASE_DIR)
@app.route('/<path:filename>')
def serve_static_files(filename):
    return send_from_directory(BASE_DIR, filename)


def find_free_port(start_port=5000):
    """Tìm một cổng trống, bắt đầu từ 5000."""
    port = start_port
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
        port += 1

def open_browser(port):
    """Mở trình duyệt sau một khoảng trễ ngắn."""
    def _open():
        webbrowser.open(f'http://127.0.0.1:{port}/')
    
    # Đợi 1 giây để server có thời gian khởi động hoàn toàn
    t = threading.Timer(1.0, _open)
    t.start()

if __name__ == '__main__':
    PORT = find_free_port()
    
    # Mở trình duyệt trong một luồng riêng
    open_browser(PORT)
    
    print(f"Flask server is running on http://127.0.0.1:{PORT}")
    print(f"Serving content from: {BASE_DIR}")
    print(f"Main HTML file: {TARGET_HTML_FILE}")
    
    # Chạy server
    # host='127.0.0.1' để đảm bảo chỉ có thể truy cập từ máy cục bộ
    app.run(host='127.0.0.1', port=PORT, debug=False)