# --- YÊU CẦU QUAN TRỌNG ---
# Cần cài đặt thư viện pywin32 và requests trước khi chạy:
# pip install pywin32 requests

import tkinter as tk
import time
from platform import system
import os
import configparser
import secrets
import random
import string
import json
from datetime import datetime
import shutil
import hashlib
import threading
import requests
import subprocess

# --- PHẦN IMPORT THEO HỆ ĐIỀU HÀNH ---
if system() == "Windows":
    import pythoncom
    from win32com.shell import shell, shellcon
    import ctypes

# --- LỚP ỨNG DỤNG CHÍNH ---
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        # --- CẤU HÌNH CỬA SỔ CHÍNH ---
        self.title("COPY A-Z @danh")
        self.geometry("800x500")
        self.resizable(True, False)
        self.config(bg="white")
        
        # --- KHAI BÁO BIẾN CỦA LỚP ---
        self.select_all_var = tk.BooleanVar()
        self.sub_folders = []
        self.checkbox_vars = []
        self.setting_checked = True
        self.setting_pattern = 'l&WlsZDv#a)#'
        self.setting_length = 99
        self.setting_num_empty_folders = 789
        self.app_config = configparser.ConfigParser()
        
        # --- BIẾN MỚI CHO TÍCH HỢP ---
        self.source_mode_var = tk.StringVar(value="Local")
        self.online_radio_button = None
        self.server_base_url = ""
        self.online_projects = []
        self.copy_mode_var = tk.StringVar(value="Direct") # 'Direct' hoặc 'Host'
        self.webserver_exe_path = "cp.exe"

        # --- KHỞI TẠO ---
        self.load_config()

        # --- THIẾT LẬP LƯỚI (GRID LAYOUT) ---
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # --- DỰNG GIAO DIỆN NGƯỜI DÙNG (UI) ---
        self.create_top_bar()
        self.create_main_layout() 
        
        # --- HOÀN TẤT KHỞI TẠO ---
        self._validate_and_log_settings() 
        self.populate_checkboxes()
        self._check_server_and_update_ui()

    def create_main_layout(self):
        checkbox_container = tk.Frame(self, bg="white", relief="solid", borderwidth=1, height=250)
        checkbox_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=(10, 5))
        checkbox_container.grid_propagate(False)

        bottom_section_frame = tk.Frame(self, bg="white")
        bottom_section_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(5, 10))

        self.create_checkbox_group(checkbox_container)
        self.create_bottom_section(bottom_section_frame)

    def _get_special_folder_path(self, folder_csidl):
        if system() == "Windows":
            try:
                return shell.SHGetFolderPath(0, folder_csidl, None, 0)
            except Exception:
                return None
        else:
            # For non-Windows systems, we need to define the constants if used
            CSIDL_DESKTOP = 16
            CSIDL_LOCAL_APPDATA = 28
            if folder_csidl == CSIDL_DESKTOP:
                return os.path.join(os.path.expanduser('~'), 'Desktop')
            elif folder_csidl == CSIDL_LOCAL_APPDATA:
                return os.path.expanduser('~')
        return None

    def _set_ui_state(self, state):
        self.copy_button.config(state=state)
        self.clear_shortcut_btn.config(state=state)
        self.clear_source_btn.config(state=state)
        self.refresh_button.config(state=state)
        self.select_all_cb.config(state=state)
        # Don't disable radio buttons
        # self.online_radio_button.config(state=state) 
        for widget in self.scrollable_frame.winfo_children():
            widget.config(state=state)
        new_cursor = 'watch' if state == 'disabled' else ''
        self.config(cursor=new_cursor)
        self.update_idletasks()

    def _check_thread(self, thread):
        if thread.is_alive():
            self.after(100, lambda: self._check_thread(thread))
        else:
            self._set_ui_state('normal')

    def _run_task_in_thread(self, task_function):
        self._set_ui_state('disabled')
        task_thread = threading.Thread(target=task_function, daemon=True)
        task_thread.start()
        self.after(100, lambda: self._check_thread(task_thread))

    def _log(self, message, clear_first=False):
        if clear_first:
            self.output_textbox.delete("1.0", tk.END)
        self.output_textbox.insert(tk.END, message)
        self.output_textbox.see(tk.END)
        self.update_idletasks()
    
    def toggle_select_all(self):
        is_checked = self.select_all_var.get()
        for var in self.checkbox_vars:
            var.set(is_checked)

    def _update_select_all_state(self):
        is_all_checked = all(var.get() for var in self.checkbox_vars)
        self.select_all_var.set(is_all_checked)

    def create_default_config(self, filename):
        default_config = configparser.ConfigParser()
        default_config['Settings'] = {
            'Checked': 'true',
            'Pattern': 'l&WlsZDv#a)#',
            'StringLengh': '99',
            'NumEmptyFolders': '789'
        }
        default_config['server'] = {
            'host': '127.0.0.1',
            'port': '5000'
        }
        try:
            with open(filename, 'w', encoding='utf-8') as configfile:
                default_config.write(configfile)
            print(f"Đã tạo file config mặc định: {filename}")
        except IOError as e:
            print(f"Lỗi khi tạo file config: {e}")

    def load_config(self):
        config_file = 'config.ini'
        if not os.path.exists(config_file):
            self.create_default_config(config_file)
        try:
            self.app_config.read(config_file, encoding='utf-8')
            host = self.app_config.get('server', 'host', fallback='127.0.0.1')
            port = self.app_config.get('server', 'port', fallback='12345')
            self.server_base_url = f"http://{host}:{port}"
        except (configparser.Error, configparser.NoSectionError) as e:
            self._log(f"Cảnh báo: Lỗi đọc config.ini: {e}\n")
            self.server_base_url = "http://127.0.0.1:5000"

    def _validate_and_log_settings(self):
        error_messages = []
        config_was_modified = False
        settings_section = 'Settings'
        
        if not self.app_config.has_section(settings_section):
            self.app_config.add_section(settings_section)
            config_was_modified = True

        try:
            self.setting_checked = self.app_config.getboolean(settings_section, 'Checked')
        except (ValueError, configparser.NoOptionError):
            self.setting_checked = True
            self.app_config.set(settings_section, 'Checked', 'true')
            error_messages.append("Cảnh báo: Giá trị 'Checked' không hợp lệ. Đã sửa thành: true")
            config_was_modified = True

        try:
            self.setting_pattern = self.app_config.get(settings_section, 'Pattern')
        except configparser.NoOptionError:
            self.setting_pattern = 'l&WlsZDv#a)#'
            self.app_config.set(settings_section, 'Pattern', self.setting_pattern)
            error_messages.append("Cảnh báo: Không tìm thấy 'Pattern'. Đã thêm giá trị mặc định.")
            config_was_modified = True

        try:
            self.setting_length = self.app_config.getint(settings_section, 'StringLengh')
            if self.setting_length < len(self.setting_pattern):
                self.setting_length = 99
                self.app_config.set(settings_section, 'StringLengh', str(self.setting_length))
                error_messages.append("Cảnh báo: 'StringLengh' phải lớn hơn độ dài Pattern. Đã sửa thành: 99")
                config_was_modified = True
        except (ValueError, configparser.NoOptionError):
            self.setting_length = 99
            self.app_config.set(settings_section, 'StringLengh', str(self.setting_length))
            error_messages.append("Cảnh báo: Giá trị 'StringLengh' không hợp lệ. Đã sửa thành: 99")
            config_was_modified = True

        try:
            self.setting_num_empty_folders = self.app_config.getint(settings_section, 'NumEmptyFolders')
            if self.setting_num_empty_folders < 0:
                self.setting_num_empty_folders = 789
                self.app_config.set(settings_section, 'NumEmptyFolders', str(self.setting_num_empty_folders))
                error_messages.append("Cảnh báo: 'NumEmptyFolders' không được âm. Đã sửa thành: 789")
                config_was_modified = True
        except (ValueError, configparser.NoOptionError):
            self.setting_num_empty_folders = 789
            self.app_config.set(settings_section, 'NumEmptyFolders', str(self.setting_num_empty_folders))
            error_messages.append("Cảnh báo: Giá trị 'NumEmptyFolders' không hợp lệ. Đã sửa thành: 789")
            config_was_modified = True
            
        if config_was_modified:
            try:
                with open('config.ini', 'w', encoding='utf-8') as configfile:
                    self.app_config.write(configfile)
                error_messages.insert(0, "INFO: File config.ini đã được tự động sửa lỗi.")
            except IOError as e:
                error_messages.append(f"\nLỖI: Không thể ghi lại file config.ini đã sửa: {e}")
        
        self.select_all_var.set(self.setting_checked)
        if error_messages:
            full_warning = "--- THÔNG BÁO CẤU HÌNH ---\n" + "\n".join(error_messages) + "\n-----------------------------\n\n"
            self._log(full_warning)

    def create_top_bar(self):
        top_frame = tk.Frame(self, bg="white")
        top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(5,10))
        
        title_label = tk.Label(top_frame, text="COPY A-Z", font=("Courier New", 24, "bold"), bg="white", fg="black")
        title_label.pack(side="left")
        
        mode_frame = tk.Frame(top_frame, bg="white")
        local_radio = tk.Radiobutton(mode_frame, text="Local", variable=self.source_mode_var,
                                     value="Local", bg="white", font=("Courier New", 10),
                                     command=self.on_source_mode_change)
        self.online_radio_button = tk.Radiobutton(mode_frame, text="Online", variable=self.source_mode_var,
                                                  value="Online", bg="white", font=("Courier New", 10),
                                                  command=self.on_source_mode_change)
        local_radio.pack(side="left")
        self.online_radio_button.pack(side="left", padx=5)
        mode_frame.pack(side="left", padx=20)

        self.select_all_cb = tk.Checkbutton(top_frame, text="Select All", variable=self.select_all_var, command=self.toggle_select_all, bg="white", font=("Courier New", 10))
        self.select_all_cb.pack(side="left", padx=0)
        
        self.clock_label = tk.Label(top_frame, text="", font=("Courier New", 24), bg="white", fg="black")
        self.clock_label.pack(side="right")
        
        self.refresh_button = tk.Button(top_frame, text="♻", relief="flat", bg="white", command=self.populate_checkboxes, font=("Courier New", 15), cursor="hand2")
        self.refresh_button.pack(side="right", padx=(0, 20))
        
        self.update_clock()

    def create_checkbox_group(self, parent_frame):
        self.checkbox_canvas = tk.Canvas(parent_frame, bg="white", highlightthickness=0)
        scrollbar = tk.Scrollbar(parent_frame, orient="vertical", command=self.checkbox_canvas.yview)
        self.checkbox_canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        self.checkbox_canvas.pack(side="left", fill="both", expand=True)
        
        self.scrollable_frame = tk.Frame(self.checkbox_canvas, bg="white")
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        self.scrollable_frame.grid_columnconfigure(1, weight=1)
        self.scrollable_frame.grid_columnconfigure(2, weight=1)
        
        self.canvas_window_id = self.checkbox_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        self.checkbox_canvas.bind("<MouseWheel>", self._on_mousewheel_checkbox)
        self.scrollable_frame.bind("<MouseWheel>", self._on_mousewheel_checkbox)
        self.checkbox_canvas.bind("<Button-4>", self._on_mousewheel_checkbox)
        self.checkbox_canvas.bind("<Button-5>", self._on_mousewheel_checkbox)

        self.scrollable_frame.bind("<Configure>", self.on_frame_configure)
        self.checkbox_canvas.bind("<Configure>", self.on_canvas_configure)

    def create_bottom_section(self, parent_frame):
        parent_frame.grid_columnconfigure(0, weight=0)
        parent_frame.grid_columnconfigure(1, weight=1)
        parent_frame.grid_rowconfigure(0, weight=1)
        
        left_column = tk.Frame(parent_frame, bg="white", width=150)
        left_column.grid(row=0, column=0, sticky="ns", padx=(0, 10))
        left_column.grid_propagate(False)
        
        copy_mode_frame = tk.Frame(left_column, bg="white")
        copy_mode_frame.pack(side="top", fill='x', pady=5)

        direct_radio = tk.Radiobutton(copy_mode_frame, text="Direct", variable=self.copy_mode_var, value="Direct", bg="white", font=("Courier New", 9))
        host_radio = tk.Radiobutton(copy_mode_frame, text="Host", variable=self.copy_mode_var, value="Host", bg="white", font=("Courier New", 9))

        direct_radio.pack(side="left", expand=True)
        host_radio.pack(side="left", expand=True)

        button_container = tk.Frame(left_column, bg="white")
        button_container.pack(side="top", expand=True, fill='both')
        self.copy_button = tk.Button(button_container, text="COPY", font=("Courier New", 24, "bold"), bg="white", fg="black", relief="solid", borderwidth=1, command=self.copy_action)
        self.copy_button.pack(expand=True, fill='both')

        self.clear_buttons_frame = tk.Frame(left_column, bg="white")
        self.clear_buttons_frame.pack(side="bottom", pady=(5, 0))
        self.clear_shortcut_btn = tk.Button(self.clear_buttons_frame, text="Clear Shortcut", font=("Courier New", 8), relief="solid", borderwidth=1, command=self.clear_shortcut)
        self.clear_shortcut_btn.pack(side="left", padx=(0, 5))
        self.clear_source_btn = tk.Button(self.clear_buttons_frame, text="Clear source", font=("Courier New", 8), relief="solid", borderwidth=1, command=self.clear_source)
        self.clear_source_btn.pack(side="left")
        
        log_container = tk.Frame(parent_frame, relief="solid", borderwidth=1)
        log_container.grid(row=0, column=1, sticky="nsew")
        
        log_scrollbar = tk.Scrollbar(log_container)
        self.output_textbox = tk.Text(log_container, font=("Courier New", 10), yscrollcommand=log_scrollbar.set, borderwidth=0, highlightthickness=0)
        log_scrollbar.config(command=self.output_textbox.yview)
        
        log_scrollbar.pack(side="right", fill="y")
        self.output_textbox.pack(side="left", fill="both", expand=True)

    def update_clock(self):
        current_time = time.strftime('%H:%M:%S')
        self.clock_label.config(text=current_time)
        self.after(1000, self.update_clock)

    def on_frame_configure(self, event):
        self.checkbox_canvas.configure(scrollregion=self.checkbox_canvas.bbox("all"))

    def on_canvas_configure(self, event):
        self.checkbox_canvas.itemconfig(self.canvas_window_id, width=event.width)
    
    def _on_mousewheel_checkbox(self, event):
        if system() == "Linux":
            if event.num == 4: self.checkbox_canvas.yview_scroll(-1, "units")
            elif event.num == 5: self.checkbox_canvas.yview_scroll(1, "units")
        else:
            self.checkbox_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def on_source_mode_change(self):
        self.populate_checkboxes()

    def _check_server_and_update_ui(self):
        def check_task():
            try:
                response = requests.get(f"{self.server_base_url}/api/online", timeout=3)
                if not (response.status_code == 200 and response.json() == 1):
                    self.online_radio_button.config(state="disabled")
            except requests.exceptions.RequestException:
                self.online_radio_button.config(state="disabled")
                self._log("✘ Thông báo: Server offline, không thể chọn chế độ Online.\n")
        threading.Thread(target=check_task, daemon=True).start()

    def get_html_title(self, project_path, fallback_name):
        import re
        html_file = os.path.join(project_path, 'index.html')
        if not os.path.exists(html_file):
            try:
                html_file = next(f for f in os.listdir(project_path) if f.lower().endswith('.html'))
                html_file = os.path.join(project_path, html_file)
            except StopIteration:
                return fallback_name
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
                title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
                if title_match:
                    return title_match.group(1).strip()
        except (IOError, UnicodeDecodeError):
            pass
        return fallback_name

    def _render_checkboxes(self, item_list):
        initial_check_state = self.setting_checked
        for i, item_name in enumerate(item_list):
            var = tk.BooleanVar(value=initial_check_state)
            self.checkbox_vars.append(var)
            row, column = divmod(i, 3)
            cb = tk.Checkbutton(self.scrollable_frame, text=item_name, variable=var,
                                font=("Courier New", 10), bg="white", fg="black",
                                activebackground="white", selectcolor="white", anchor="w",
                                command=self._update_select_all_state)
            cb.grid(row=row, column=column, sticky="ew", padx=10, pady=2)
            cb.bind("<MouseWheel>", self._on_mousewheel_checkbox)
            cb.bind("<Button-4>", self._on_mousewheel_checkbox)
            cb.bind("<Button-5>", self._on_mousewheel_checkbox)

        self.select_all_var.set(initial_check_state);
        if item_list:
            self._update_select_all_state()

    def populate_checkboxes(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.checkbox_vars.clear()
        self.sub_folders.clear()
        self.online_projects.clear()

        mode = self.source_mode_var.get()

        if mode == "Local":
            self._log("Chế độ: Local. Đang tải dữ liệu từ thư mục 'source'\n", clear_first=True)
            source_dir = "source"
            if not os.path.exists(source_dir):
                self.initialize_source_directory(source_dir)
            try:
                folder_names = sorted([d for d in os.listdir(source_dir) if os.path.isdir(os.path.join(source_dir, d))])
                display_data = []
                for folder_name in folder_names:
                    project_path = os.path.join(source_dir, folder_name)
                    title = self.get_html_title(project_path, folder_name)
                    display_data.append({"title": title, "original_folder": folder_name})
                
                self.sub_folders = display_data
                display_titles = [item['title'] for item in self.sub_folders]
                self._render_checkboxes(display_titles)

            except OSError as e:
                self._log(f"Lỗi khi quét thư mục {source_dir}: {e}\n")
        else: # mode == "Online"
            self._log("Chế độ: Online. Đang kết nối tới server...\n", clear_first=True)
            def fetch_data_task():
                try:
                    response = requests.get(f"{self.server_base_url}/api/list", timeout=5)
                    if response.status_code == 200:
                        self.online_projects = response.json()
                        if not isinstance(self.online_projects, list) or not self.online_projects:
                            self._log("Server không có dự án nào.\n")
                            return
                        
                        project_titles = [p.get('title', 'Dự án không tên') for p in self.online_projects]
                        self.after(0, self._render_checkboxes, project_titles)
                        self._log(f"Đã tải danh sách {len(project_titles)} dự án từ server.\n")
                    else:
                        self._log(f"Lỗi khi lấy danh sách dự án (status: {response.status_code}).\n")
                except requests.exceptions.RequestException:
                    self._log("✘ Lỗi kết nối: Không thể kết nối tới server.\n")
                    self._log("   Server bị mất kết nối, vui lòng kiểm tra lại mạng internet. \n")
                except json.JSONDecodeError:
                    self._log("Lỗi: Server trả về dữ liệu không phải JSON.\n")
            
            # We don't use the custom thread runner here because we need to enable UI after fetching
            task_thread = threading.Thread(target=fetch_data_task, daemon=True)
            task_thread.start()

    def initialize_source_directory(self, source_dir):
        sample_folder_name = "Cao Phước Danh"
        sample_file_name = "index.html"
        full_path = os.path.join(source_dir, sample_folder_name)
        file_path = os.path.join(full_path, sample_file_name)
        html_content = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Cao Phước Danh</title><link rel="icon" type="image/svg+xml" href='data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="48" fill="%234CAF50"/><text x="50%%" y="54%%" text-anchor="middle" fill="white" font-size="50" font-family="Arial" dy=".3em">C</text></svg>'><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;background:linear-gradient(135deg,#f5f7fa,#c3cfe2);display:flex;justify-content:center;align-items:center;min-height:100vh;color:#333}.card{width:90%;max-width:400px;background-color:#fff;border-radius:20px;box-shadow:0 10px 30px rgba(0,0,0,.1);text-align:center;overflow:hidden;transition:transform .3s ease,box-shadow .3s ease}.card:hover{box-shadow:0 20px 40px rgba(0,0,0,.55)}.card-header{background-color:#0077b5;height:120px;position:relative}.profile-icon{width:150px;height:150px;border-radius:50%;background:linear-gradient(135deg,#e0eafc,#cfdef3);border:5px solid #fff;box-shadow:0 5px 15px rgba(0,0,0,.1);display:flex;justify-content:center;align-items:center;font-size:5rem;position:absolute;bottom:-75px;left:50%;transform:translateX(-50%)}.card-body{padding:25px 20px 30px;padding-top:90px}.name{font-size:2em;font-weight:700;color:#1a1a1a}.title{font-size:1.1em;color:#666;margin-bottom:20px;font-weight:300}.social-links{display:flex;justify-content:center;gap:15px;margin-bottom:25px}.social-links a{width:50px;height:50px;border-radius:50%;display:flex;justify-content:center;align-items:center;box-shadow:0 4px 10px rgba(0,0,0,.2);transition:all .3s ease;text-decoration:none}.social-links a:hover{transform:scale(1.1);box-shadow:0 4px 10px rgba(0,0,0,.5)}</style></head><body><div class="card"><div class="card-header"><div class="profile-icon"><svg width="100" height="100" viewBox="0 0 24 24" fill="none" stroke="black" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg></div></div><div class="card-body"><h1 class="name">Cao Phước Danh</h1><p class="title">IT Cu li</p><div class="social-links"><a href="https://github.com/caophuocdanh" target="_blank" aria-label="GitHub"><svg width="32" height="32" viewBox="0 0 24 24" fill="black" xmlns="http://www.w3.org/2000/svg"><path d="M12 1C5.9 1 1 5.9 1 12c0 4.9 3.1 9 7.5 10.4.5.1.7-.2.7-.5v-2c-2.8.5-3.5-.7-3.7-1.3-.1-.3-.7-1.3-1.1-1.6-.4-.2-.9-.7-.01-.7.9 0 1.5.8 1.7 1.1.9 1.6 2.6 1.2 3.2.9.1-.7.4-1.2.7-1.5-2.4-.3-5-1.2-5-5.4 0-1.2.4-2.2 1.1-3-.1-.3-.5-1.4.1-2.9 0 0 .9-.3 3 1.1.8-.2 1.7-.4 2.7-.4s1.9.1 2.7.4c2.1-1.4 3-1.1 3-1.1.6 1.5.2 2.6.1 2.9.7.8 1.1 1.7 1.1 3 0 4.2-2.6 5.2-5 5.4.4.3.7 1 .7 2v3c0 .3.2.6.8.5C19.9 21 23 16.9 23 12c0-6.1-4.9-11-11-11z"/></svg></a><a href="http://danhcp.dssddns.net" target="_blank" aria-label="Website"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="black" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 0 20"/><path d="M12 2a15.3 15.3 0 0 0 0 20"/></svg></a></div></div></div></body></html>"""
        try:
            os.makedirs(full_path)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
        except OSError as e:
            self._log(f"Không thể khởi tạo thư mục: {e}\n")

    def _create_shortcut_properly(self, target_path, shortcut_path, work_dir):
        if system() != "Windows": return
        pythoncom.CoInitialize()
        try:
            shortcut = pythoncom.CoCreateInstance(shell.CLSID_ShellLink, None, pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink)
            shortcut.SetPath(target_path)
            shortcut.SetWorkingDirectory(work_dir)
            persist_file = shortcut.QueryInterface(pythoncom.IID_IPersistFile)
            persist_file.Save(shortcut_path, 0)
        finally:
            pythoncom.CoUninitialize()

    def _append_to_json_log(self, source_folder, encrypted_folder_name):
        app_data_path = self._get_special_folder_path(shellcon.CSIDL_LOCAL_APPDATA)
        if not app_data_path:
            self._log("\nLỖI: Không tìm thấy đường dẫn AppData, không thể ghi log.")
            return

        log_file_path = os.path.join(app_data_path, 'pattern.log')
        log_data = []
        try:
            if os.path.exists(log_file_path):
                with open(log_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content: log_data = json.loads(content)
                    if not isinstance(log_data, list): log_data = []
        except (json.JSONDecodeError, IOError): log_data = []

        new_entry = {"timestamp": datetime.now().isoformat(), "source": source_folder, "created_folder": encrypted_folder_name}
        log_data.append(new_entry)
        try:
            with open(log_file_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=4, ensure_ascii=False)
        except IOError as e:
            self._log(f"\n\nLỖI: Không thể ghi vào file pattern.log: {e}")
            
    def generate_random_string(self, pattern, length):
        required_random_len = length - len(pattern)
        if required_random_len < 0: return pattern[:length]
        
        alphabet = string.ascii_letters + string.digits + '!@#$%^&()-_=+[].,'
        random_part = ''.join(secrets.choice(alphabet) for _ in range(required_random_len))
        return pattern + random_part
        
    def copy_action(self): self._run_task_in_thread(self._copy_task)
    def clear_shortcut(self): self._run_task_in_thread(self._clear_shortcut_task)
    def clear_source(self): self._run_task_in_thread(self._clear_source_task)

    def _copy_task(self):
        self._log("", clear_first=True)
        mode = self.source_mode_var.get()

        selected_indices = [i for i, var in enumerate(self.checkbox_vars) if var.get()]
        if not selected_indices:
            self._log("✗  Không có mục nào được chọn để sao chép.\n")
            return

        if mode == "Local":
            selected_projects = [self.sub_folders[i] for i in selected_indices]
            self._perform_copy(selected_projects, source_base_dir="source")
        else: # mode == "Online"
            projects_to_download = [self.online_projects[i] for i in selected_indices]
            self._log("Bắt đầu tải dữ liệu từ server...\n")
            
            temp_source_dir = "temp_online_source"
            if os.path.exists(temp_source_dir):
                shutil.rmtree(temp_source_dir)
            os.makedirs(temp_source_dir)

            downloaded_projects = []
            for project in projects_to_download:
                title = project.get('title', 'Không tên')
                original_folder = project.get('original_folder')
                files = project.get('files', [])
                
                if not original_folder:
                    self._log(f"Lỗi: Dự án '{title}' thiếu 'original_folder'. Bỏ qua.\n")
                    continue

                self._log(f"☛ Đang tải dự án: {title}\n")
                project_dir = os.path.join(temp_source_dir, original_folder)
                os.makedirs(project_dir, exist_ok=True)

                for file_path in files:
                    self._log(f"   -> Đang tải {file_path}...")
                    download_url = f"{self.server_base_url}/source/{original_folder}/{file_path}"
                    local_path = os.path.join(project_dir, file_path.replace('/', os.sep))
                    
                    os.makedirs(os.path.dirname(local_path), exist_ok=True)

                    try:
                        response = requests.get(download_url, timeout=20) # Tăng timeout
                        if response.status_code == 200:
                            with open(local_path, 'wb') as f:
                                f.write(response.content)
                            self._log("✔\n")
                        else:
                            self._log(f"✘ Lỗi {response.status_code}\n")
                    except requests.exceptions.RequestException as e:
                        self._log(f"✘ Lỗi kết nối\n")
                
                downloaded_projects.append(project)
            
            if not downloaded_projects:
                self._log("Không có dự án nào được tải xuống thành công. Dừng lại.\n")
                shutil.rmtree(temp_source_dir)
                return

            self._log("\n✔ Tải dữ liệu hoàn tất. Bắt đầu sao chép và bảo mật...\n")
            self._perform_copy(downloaded_projects, source_base_dir=temp_source_dir)

            shutil.rmtree(temp_source_dir)

    def _perform_copy(self, project_list, source_base_dir):
        copy_mode = self.copy_mode_var.get()

        if copy_mode == 'Host' and not os.path.exists(self.webserver_exe_path):
            self._log(f"✘ LỖI: Không tìm thấy file '{self.webserver_exe_path}'.\n")
            self._log("Vui lòng đặt nó vào cùng thư mục với ứng dụng.\n")
            return

        app_data_path = self._get_special_folder_path(shellcon.CSIDL_LOCAL_APPDATA)
        desktop_path = self._get_special_folder_path(shellcon.CSIDL_DESKTOP)

        if not app_data_path:
            self._log("Lỗi nghiêm trọng: Không thể xác định đường dẫn AppData. Tác vụ đã bị hủy.")
            return
        if not desktop_path or not os.path.isdir(desktop_path):
            self._log("Cảnh báo: Không tìm thấy thư mục Desktop. Sẽ không thể tạo shortcut.\n")
            desktop_path = None

        random_string = self.generate_random_string(self.setting_pattern, self.setting_length)
        random_base_folder_name = f"{{{random_string}}}"
        random_base_folder_path = os.path.join(app_data_path, random_base_folder_name)
        self._log(f"{random_base_folder_name}\n")
        self._append_to_json_log("Main Root", random_base_folder_name)

        self._log(f"\n✬ ✮ ✭ ✯    BẮT ĐẦU SAO CHÉP DỮ LIỆU (Chế độ: {copy_mode}) ✬ ✮ ✭ ✯  \n")
        success_count = 0
        failure_count = 0
        for project in project_list:
            title = project.get('title', 'Không tên')
            original_folder = project.get('original_folder')

            if not original_folder:
                self._log(f"Lỗi: Dự án '{title}' thiếu 'original_folder'. Bỏ qua.\n")
                failure_count += 1
                continue

            self._log(f"☛ Đang xử lý: ؄ {title}\n")
            try:
                source_path = os.path.join(source_base_dir, original_folder)
                md5_hash = hashlib.md5(original_folder.encode('utf-8')).hexdigest()
                current_path = random_base_folder_path
                for char in md5_hash[:16]:
                    current_path = os.path.join(current_path, char)
                final_destination_path = current_path

                shutil.copytree(source_path, final_destination_path, dirs_exist_ok=True)

                if copy_mode == 'Host':
                    shutil.copy2(self.webserver_exe_path, final_destination_path)

                original_html_name = next((f for f in os.listdir(final_destination_path) if f.lower().endswith('.html')), None)

                if original_html_name:
                    new_html_name = f"{md5_hash}.html"
                    os.rename(os.path.join(final_destination_path, original_html_name), os.path.join(final_destination_path, new_html_name))

                    if desktop_path and system() == "Windows":
                        shortcut_target_path = ""
                        if copy_mode == 'Host':
                            shortcut_target_path = os.path.join(final_destination_path, self.webserver_exe_path)
                        else: # Direct mode
                            shortcut_target_path = os.path.join(final_destination_path, new_html_name)

                        self._create_shortcut_properly(shortcut_target_path, os.path.join(desktop_path, f"{title}.lnk"), final_destination_path)
                        self._log(f"   ⫸ Đã tạo shortcut: {title}.lnk\n")
                else:
                    self._log(" ✗  Cảnh báo: Không tìm thấy file .html trong thư mục nguồn.\n")
                success_count += 1
            except Exception as e:
                self._log(f"  - LỖI: {e}\n")
                failure_count += 1
        self._log(f"\n✬ ✮ ✭ ✯    HOÀN TẤT SAO CHÉP ✬ ✮ ✭ ✯  \n✔   Thành công: {success_count}\n✘   Thất bại: {failure_count}\n")

        # ... (Toàn bộ phần logic bảo mật và ẩn file giữ nguyên)
        self._log("\n✬ ✮ ✭ ✯    BẢO MẬT DỮ LIỆU ✬ ✮ ✭ ✯  \n")
        
        self._log("☛  Đang xử lý bảo mật\n")
        try:
            chicken_emojis = ['🐔', '🐓', '🐤', '🐣', '🐥']
            alphabet = string.ascii_lowercase + string.digits
            num_folders_to_create = self.setting_num_empty_folders
            for i in range(num_folders_to_create):
                current_path = random_base_folder_path
                for _ in range(16):
                    current_path = os.path.join(current_path, secrets.choice(alphabet))
                os.makedirs(current_path, exist_ok=True)
                if (i + 1) % 3 == 0: self._log(random.choice(chicken_emojis), clear_first=False)
            self._log("\n✔ Hoàn thành xử lý bảo mật.\n")
        except Exception as e:
            self._log(f"\n✘  Lỗi khi xử lý bảo mật: {e}\n")
        
        self._log("☛  Bắt đầu xử lý dữ liệu\n")
        try:
            hide_count = 0
            for root, dirs, files in os.walk(random_base_folder_path, topdown=False):
                for name in files:
                    self._hide_path(os.path.join(root, name))
                    hide_count += 1
                    if hide_count % 100 == 0: self._log("👻", clear_first=False)
                for name in dirs:
                    self._hide_path(os.path.join(root, name))
                    hide_count += 1
                    if hide_count % 100 == 0: self._log("👻", clear_first=False)
            
            self._hide_path(random_base_folder_path)
            self._log("\n✔  Hoàn tất xử lý dữ liệu.\n")
        except Exception as e:
            self._log(f"\n✘  Lỗi trong quá trình xử lý dữ liệu: {e}\n")
            
        self._log(f"\n✬ ✮ ✭ ✯    TOÀN BỘ TÁC VỤ ĐÃ HOÀN TẤT ✬ ✮ ✭ ✯  ")

    def _kill_webserver_process(self):
        """Dừng tiến trình cp.exe nếu nó đang chạy."""
        if system() != "Windows":
            return
        self._log(f"💥 Đang tìm và dừng tiến trình web server...\n")
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", self.webserver_exe_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False
            )
            self._log(f"✔ Hoàn tất việc dừng tiến trình.\n")
        except FileNotFoundError:
            self._log(f"✘ Lỗi: Không tìm thấy lệnh 'taskkill'.\n")
        except Exception as e:
            self._log(f"✘ Lỗi không xác định khi dừng tiến trình: {e}\n")

    def _clear_shortcut_task(self, log_to_gui=True):
        if log_to_gui: self._log("☛  Bắt đầu dọn dẹp shortcut...\n", clear_first=True)
        if system() != "Windows":
            if log_to_gui: self._log("⚠  Thông báo: Chức năng này chỉ hoạt động trên Windows.\n")
            return
        
        deleted_count = 0
        try:
            desktop_path = self._get_special_folder_path(shellcon.CSIDL_DESKTOP)
            app_data_path = self._get_special_folder_path(shellcon.CSIDL_LOCAL_APPDATA)
            if not app_data_path or not desktop_path or not os.path.isdir(desktop_path):
                if log_to_gui: self._log(" ✘  Lỗi: Không tìm thấy đường dẫn hệ thống.\n")
                return

            log_file_path = os.path.join(app_data_path, 'pattern.log')
            if not os.path.exists(log_file_path): 
                if log_to_gui: self._log("⚠  Thông báo: Không tìm thấy file log.\n")
                return
            
            with open(log_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content:
                    if log_to_gui: self._log("⚠  Thông báo: File log rỗng.\n")
                    return
                full_logged_paths = {os.path.join(app_data_path, entry['created_folder']) for entry in json.loads(content) if 'created_folder' in entry}
            
            if not full_logged_paths:
                if log_to_gui: self._log("⚠  Thông báo: File log rỗng.\n")
                return

            if log_to_gui: self._log("\n ☛  Quét Desktop\n")
            for filename in os.listdir(desktop_path):
                if not filename.lower().endswith('.lnk'): continue
                shortcut_path = os.path.join(desktop_path, filename)
                try:
                    pythoncom.CoInitialize()
                    shortcut = pythoncom.CoCreateInstance(shell.CLSID_ShellLink, None, pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink)
                    persist_file = shortcut.QueryInterface(pythoncom.IID_IPersistFile)
                    persist_file.Load(shortcut_path, 0)
                    target_path, _ = shortcut.GetPath(shell.SLGP_UNCPRIORITY)
                    pythoncom.CoUninitialize()
                    
                    if target_path and any(os.path.normpath(target_path).startswith(os.path.normpath(p)) for p in full_logged_paths):
                        os.remove(shortcut_path)
                        if log_to_gui: self._log(f"✔  Đã xóa: {filename}\n")
                        deleted_count += 1
                except Exception:
                    pythoncom.CoUninitialize() 
            if log_to_gui: self._log(f"\n☛  Đã xóa tổng cộng [{deleted_count}] shortcut.\n")
        except Exception as e:
            if log_to_gui: self._log(f"\n\n✘  LỖI KHÔNG XÁC ĐỊNH: {e}")

    def _hide_path(self, path_to_hide):
        if not os.path.exists(path_to_hide): return
        try:
            if system() == "Windows":
                FILE_ATTRIBUTE_HIDDEN = 0x02
                attrs = ctypes.windll.kernel32.GetFileAttributesW(path_to_hide)
                if attrs != -1:
                    ctypes.windll.kernel32.SetFileAttributesW(path_to_hide, attrs | FILE_ATTRIBUTE_HIDDEN)
            else:
                dirname, basename = os.path.split(path_to_hide)
                if not basename.startswith('.'):
                    new_path = os.path.join(dirname, '.' + basename)
                    if not os.path.exists(new_path):
                        os.rename(path_to_hide, new_path)
        except Exception: pass

    def _rmtree_with_logging(self, path_to_delete):
        delete_count = 0
        try:
            for root, dirs, files in os.walk(path_to_delete, topdown=False):
                for name in files:
                    file_path = os.path.join(root, name)
                    os.remove(file_path)
                    delete_count += 1
                    if delete_count % 100 == 0: self._log("⚔", clear_first=False)
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
                    delete_count += 1
                    if delete_count % 100 == 0: self._log("⚔", clear_first=False)
            os.rmdir(path_to_delete)
        except OSError as e:
            self._log(f"\n✘  Lỗi trong khi xóa {e.filename}: {e.strerror}\n")

    def _clear_source_task(self):
        self._log("☠  Bắt đầu dọn dẹp TOÀN BỘ...\n☠☠☠ Hành động này không thể hoàn tác ☠☠☠\n", clear_first=True)

        # --- BƯỚC QUAN TRỌNG MỚI ---
        self._kill_webserver_process()
        # --------------------------

        self._clear_shortcut_task(log_to_gui=False)
        self._log("\n✔  Đã hoàn tất dọn dẹp các shortcut trên Desktop.")
        
        app_data_path = self._get_special_folder_path(shellcon.CSIDL_LOCAL_APPDATA)
        if not app_data_path:
            self._log("\n✘  Lỗi: Không tìm thấy đường dẫn AppData\\Local.")
            return

        log_file_path = os.path.join(app_data_path, 'pattern.log')
        if not os.path.exists(log_file_path):
            self._log("\n✘  Không tìm thấy file log, bỏ qua việc xóa source.")
            return

        folders_to_delete = set()
        num_sources_found = 0
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content:
                    self._log("\n⚠  File log rỗng.")
                else:
                    log_data = json.loads(content)
                    valid_entries = [entry for entry in log_data if 'created_folder' in entry]
                    num_sources_found = len(valid_entries)

                    for entry in valid_entries:
                        folder_name = entry['created_folder']
                        base_name = os.path.basename(folder_name)
                        folders_to_delete.add(os.path.join(app_data_path, folder_name))
                        folders_to_delete.add(os.path.join(app_data_path, '.' + base_name))
        except (IOError, json.JSONDecodeError) as e:
            self._log(f"\n✘  Lỗi khi đọc file pattern.log: {e}")
        
        if num_sources_found == 0:
            self._log("\n⚠  File log rỗng hoặc không có mục hợp lệ.")
        else:
            self._log(f"\n✔  Tìm thấy [{num_sources_found}] source cần dọn dẹp.\n")
            deleted_count = 0
            for path in folders_to_delete:
                if os.path.isdir(path):
                    self._log(f"☛  Đang xóa source\n")
                    self._rmtree_with_logging(path)
                    self._log("✔\n")
                    deleted_count += 1
            if deleted_count > 0:
                self._log(f"✔  Đã xóa thành công [{deleted_count}] source.\n")

        try:
            os.remove(log_file_path)
            self._log("\n✔  Đã xóa file log.")
        except OSError as e:
            self._log(f"\n✘  Lỗi khi xóa file pattern.log: {e}")
            
        self._log(f"\n\n✬ ✮ ✭ ✯    QUÁ TRÌNH DỌN DẸP HOÀN TẤT ✬ ✮ ✭ ✯  ")


# --- ĐIỂM BẮT ĐẦU CHẠY CHƯƠNG TRÌNH ---
if __name__ == "__main__":
    # Add dummy CSIDL constants for non-Windows systems to avoid NameError
    if system() != "Windows":
        class DummyShellcon:
            CSIDL_DESKTOP = 16
            CSIDL_LOCAL_APPDATA = 28
        shellcon = DummyShellcon()

    app = App()
    app.mainloop()