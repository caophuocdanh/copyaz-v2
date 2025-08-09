import os
import json
import configparser
from flask import Flask, jsonify, send_from_directory
import logging
import time
import sys
import re

# --- CẤU HÌNH CACHE ---
_cache = None
_cache_timestamp = 0
CACHE_DURATION = 300  # 300 giây = 5 phút

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the application's root directory (where the .exe is located)
APP_ROOT_DIR = os.path.dirname(sys.executable)

# --- Helper function to get HTML title ---
def get_html_title(project_path, fallback_name):
    """Tries to find an HTML file and parse its <title> tag."""
    html_file = os.path.join(project_path, 'index.html')
    if not os.path.exists(html_file):
        # If index.html doesn't exist, try to find any other .html file
        try:
            html_file = next(f for f in os.listdir(project_path) if f.lower().endswith('.html'))
            html_file = os.path.join(project_path, html_file)
        except StopIteration:
            return fallback_name # No HTML file found

    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
            title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
            if title_match:
                return title_match.group(1).strip()
    except (IOError, UnicodeDecodeError):
        pass # Fallthrough to return fallback_name
    return fallback_name

# --- Hàm tạo list.json ---
def create_list_json():
    script_dir = APP_ROOT_DIR
    source_dir = os.path.join(script_dir, 'source')
    
    # Ensure source directory exists
    if not os.path.exists(source_dir):
        try:
            os.makedirs(source_dir)
            logging.info(f"Thư mục 'source' đã được tạo tại: {source_dir}")
        except OSError as e:
            logging.error(f"Lỗi khi tạo thư mục 'source' tại {source_dir}: {e}")
            return False

    projects = []
    for project_name in sorted(os.listdir(source_dir)):
        project_path = os.path.join(source_dir, project_name)
        if os.path.isdir(project_path):
            
            display_title = get_html_title(project_path, project_name)
            
            files_data = []
            total_project_size = 0
            for dirpath, _, filenames in sorted(os.walk(project_path)):
                for filename in sorted(filenames):
                    full_path = os.path.join(dirpath, filename)
                    relative_path = os.path.relpath(full_path, project_path).replace('\\', '/')
                    try:
                        file_size = os.path.getsize(full_path)
                        files_data.append({"path": relative_path, "size": file_size})
                        total_project_size += file_size
                    except OSError:
                        # Ignore files that can't be accessed
                        pass

            project_data = {
                "title": display_title,
                "original_folder": project_name,
                "total_size": total_project_size,
                "files": files_data
            }
            projects.append(project_data)

    list_json_path = os.path.join(script_dir, 'list.json')
    try:
        with open(list_json_path, 'w', encoding='utf-8') as f:
            json.dump(projects, f, ensure_ascii=False, indent=4)
        logging.info(f"Tệp list.json đã được tạo/cập nhật thành công: {list_json_path}")
        return True
    except IOError as e:
        logging.error(f"Lỗi khi tạo/ghi tệp list.json tại {list_json_path}: {e}")
        return False

# --- Khởi tạo Flask ---
app = Flask(__name__)

# --- Định nghĩa API ---
@app.route('/api/online', methods=['GET'])
def api_online():
    return jsonify(1)

@app.route('/api/list', methods=['GET'])
def api_list():
    global _cache, _cache_timestamp
    current_time = time.time()

    # Kiểm tra xem cache có cần làm mới không
    if _cache is None or (current_time - _cache_timestamp > CACHE_DURATION):
        logging.info("Cache miss or expired. Regenerating list.json...")
        if create_list_json():
            try:
                with open(os.path.join(APP_ROOT_DIR, 'list.json'), 'r', encoding='utf-8') as f:
                    _cache = json.load(f)
                _cache_timestamp = current_time
                logging.info("Cache updated successfully.")
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logging.error(f"Error reading list.json after creation: {e}")
                return jsonify({"error": "Could not read list file after creation."}), 500
        else:
            return jsonify({"error": "Could not create list file."}), 500
    else:
        logging.info("Serving request from cache.")

    return jsonify(_cache)

# API mới để buộc làm mới cache
@app.route('/api/refresh', methods=['POST'])
def api_refresh_cache():
    global _cache
    # Đặt cache thành None để lần gọi /api/list tiếp theo sẽ tái tạo nó
    _cache = None 
    logging.info("Cache refresh requested. Cache will be regenerated on the next /api/list call.")
    return jsonify({"status": "cache cleared"}), 200

# API mới để phục vụ các tệp trong thư mục source
@app.route('/source/<project_title>/<path:file_path>')
def serve_source_file(project_title, file_path):
    # Tạo đường dẫn an toàn đến thư mục của dự án cụ thể
    project_directory = os.path.join(APP_ROOT_DIR, 'source', project_title)
    # Gửi tệp từ thư mục đó
    return send_from_directory(project_directory, file_path)

# --- Khối thực thi chính ---
if __name__ == '__main__':
    create_list_json()
    
    config = configparser.ConfigParser()
    config.read(os.path.join(APP_ROOT_DIR, 'config.ini'))
    host = '0.0.0.0' #config.get('server', 'host', fallback='127.0.0.1')
    port = config.getint('server', 'port', fallback=12345)

    print(f"Khởi động server (Waitress) tại http://{host}:{port}")
    
    from waitress import serve
    serve(app, host=host, port=port, threads=24)