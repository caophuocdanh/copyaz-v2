# --- YÊU CẦU QUAN TRỌNG ---
# Cần cài đặt thư viện pywin32 trước khi chạy:
# pip install pywin32

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
import sys
import subprocess
from cryptography.fernet import Fernet
import io
import re
import math
import multiprocessing
from tkinter import ttk

# --- PHẦN IMPORT THEO HỆ ĐIỀU HÀNH ---
if system() == "Windows":
    import pythoncom
    from win32com.shell import shell, shellcon
    import ctypes

# --- KHÓA MÃ HÓA (KHÔNG NÊN ĐỂ TRONG MÃ NGUỒN THẬT) ---
# Hàm trợ giúp để lấy đường dẫn tài nguyên, hoạt động cho cả dev và PyInstaller
def resource_path(relative_path):
    """ Lấy đường dẫn tuyệt đối đến tài nguyên, hoạt động cho cả dev và PyInstaller """
    try:
        # PyInstaller tạo một thư mục tạm và lưu đường dẫn trong _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Đây là một khóa mẫu. Trong ứng dụng thực tế, khóa này nên được quản lý an toàn hơn
# (ví dụ: biến môi trường, dịch vụ quản lý khóa).
ENCRYPTION_KEY = b'6-23fgKPp5X-SDOc6dY0ufrbaE2j-ifOGFVDTZIRQbE=' # Khóa mẫu hợp lệ

# --- LỚP ỨNG DỤNG CHÍNH ---
class App(tk.Tk):
    class _Redirector:
        def __init__(self, app_instance):
            self.app = app_instance

        def write(self, text):
            # Lên lịch cập nhật GUI trên luồng chính để tránh xung đột
            self.app.after(0, self.app._log, text)

        def flush(self):
            # Không cần làm gì ở đây cho trường hợp này
            pass


    def __init__(self):
        super().__init__()
        # --- CẤU HÌNH CỬA SỔ CHÍNH ---
        self.rand1 = random.randint(100, 999)
        self.rand2 = random.randint(100, 999)
        self.rand3 = random.randint(100, 999)
        self.correct_password = str(self.rand1 * self.rand2 * self.rand3)
        self.title(f"COPYAZ #{self.rand1}{self.rand2}{self.rand3} v2.12.10")
        try:
            self.iconbitmap(resource_path('icon.ico'))
        except tk.TclError:
            self._log_during_init("Cảnh báo: Không tìm thấy hoặc không thể tải file 'icon.ico'.\n")
        self.geometry("700x500")
        self.resizable(True, False)
        self.config(bg="white")
        self.copy_button_var = tk.StringVar(value="COPY")
        self.password_var = tk.StringVar()
        self.login_attempts = 0
        
        # --- KHAI BÁO BIẾN CỦA LỚP ---
        self.select_all_var = tk.BooleanVar()
        self.sub_folders = []
        self.checkbox_vars = []
        self.setting_checked = True
        self.setting_pattern = 'l&WlsZDv#a)#'
        self.setting_length = 99
        self.setting_num_empty_folders = 789
        self.app_config = configparser.ConfigParser()
        self.fernet = Fernet(ENCRYPTION_KEY)
        self.initial_log_messages = [] # Danh sách lưu trữ log trong quá trình khởi tạo
        
        # --- BIẾN MỚI CHO TÍCH HỢP ---
        self.copy_mode_var = tk.StringVar(value="Direct") # 'Direct' hoặc 'Host'
        self.webserver_exe_path = "wb.exe"
        self.output_base_dir = self._get_special_folder_path(shellcon.CSIDL_LOCAL_APPDATA)
        self.active_thread = None
        self.is_closing = False
        self.cancel_current_task = False
        self.current_task_name = None
        self.is_logged_in = False
        self.mini_form_instance = None

        # --- XỬ LÝ ĐÓNG CỬA SỔ CHÍNH ---
        self.protocol("WM_DELETE_WINDOW", self._on_main_window_closing)

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
        self._lock_ui_for_login()

        # Bind F6 key to open mini form
        self.bind("<F6>", self.open_mini_form)

        # Tự động focus vào ô password khi khởi động
        self.password_entry.focus_set()

    def create_main_layout(self):
        checkbox_container = tk.Frame(self, bg="white", relief="solid", borderwidth=1, height=250)
        checkbox_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=(10, 5))
        checkbox_container.grid_propagate(False)

        bottom_section_frame = tk.Frame(self, bg="white")
        bottom_section_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(5, 10))

        self.create_checkbox_group(checkbox_container)
        self.create_bottom_section(bottom_section_frame)

        # Đổ các thông báo log đã lưu vào output_textbox
        for msg in self.initial_log_messages:
            self._log(msg)
        self.initial_log_messages.clear()

    def _get_special_folder_path(self, folder_csidl):
        if system() == "Windows":
            try:
                return shell.SHGetFolderPath(0, folder_csidl, None, 0)
            except Exception as e:
                self._log(f"LỖI TRUY VẤN HỆ THỐNG: Không thể lấy đường dẫn thư mục đặc biệt. Lỗi: {e}\n")
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
        self.select_all_cb.config(state=state)
        self.login_button.config(state=state)
        self.password_entry.config(state=state)
        
        # Vô hiệu hóa/Kích hoạt các nút radio
        if hasattr(self, 'direct_radio_button') and self.direct_radio_button: self.direct_radio_button.config(state=state)
        if hasattr(self, 'host_radio_button') and self.host_radio_button: self.host_radio_button.config(state=state)

        for widget in self.scrollable_frame.winfo_children():
            widget.config(state=state)

        self.update_idletasks()

    def _check_thread(self, thread):
        if thread.is_alive():
            self.after(100, lambda: self._check_thread(thread))
        else:
            self.active_thread = None
            self.current_task_name = None
            self.cancel_current_task = False
            if self.is_closing:
                self.destroy()
            else:
                self._set_ui_state('normal')
                if self.is_logged_in:
                    self.login_button.config(state='disabled')
                    self.password_entry.config(state='disabled')

    def _run_task_in_thread(self, task_function):
        self._set_ui_state('disabled')
        self.active_thread = threading.Thread(target=task_function, daemon=True)
        self.active_thread.start()
        self.after(100, lambda: self._check_thread(self.active_thread))

    def _log(self, message, clear_first=False):
        if clear_first:
            self.output_textbox.delete("1.0", tk.END)
        self.output_textbox.insert(tk.END, message)
        self.output_textbox.see(tk.END)
        self.update_idletasks()
    
    def _log_during_init(self, message):
        self.initial_log_messages.append(message)

    def toggle_select_all(self):
        is_checked = self.select_all_var.get()
        for var in self.checkbox_vars:
            var.set(is_checked)

    def _update_select_all_state(self):
        is_all_checked = all(var.get() for var in self.checkbox_vars)
        self.select_all_var.set(is_all_checked)

    def _create_default_encrypted_config(self, filename):
        default_config = configparser.ConfigParser()
        default_config['Settings'] = {
            'Checked': 'true',
            'Pattern': 'l&WlsZDv#a)#',
            'StringLengh': '99',
            'NumEmptyFolders': '789'
        }
        try:
            config_string = io.StringIO()
            default_config.write(config_string)
            original_data = config_string.getvalue().encode('utf-8')
            encrypted_data = self.fernet.encrypt(original_data)
            with open(filename, 'wb') as configfile:
                configfile.write(encrypted_data)
            self._log_during_init(f"✔ Đã tạo file config mặc định được mã hóa: {filename}\n")
        except IOError as e:
            self._log_during_init(f"✘ Lỗi khi tạo file config mặc định được mã hóa: {e}\n")

    def _encrypt_config(self, config_file_path, output_file_path):
        try:
            with open(config_file_path, 'rb') as f:
                original_data = f.read()
            encrypted_data = self.fernet.encrypt(original_data)
            with open(output_file_path, 'wb') as f:
                f.write(encrypted_data)
            self._log_during_init(f"✔ Đã mã hóa {config_file_path} thành {output_file_path}\n")
        except Exception as e:
            self._log_during_init(f"✘ Lỗi khi mã hóa file config: {e}\n")

    def _decrypt_config(self, encrypted_file_path):
        try:
            with open(encrypted_file_path, 'rb') as f:
                encrypted_data = f.read()
            decrypted_data = self.fernet.decrypt(encrypted_data)
            return decrypted_data.decode('utf-8')
        except Exception as e:
            self._log_during_init(f"✘ Lỗi khi giải mã file config: {e}\n")
            return None

    def load_config(self):
        config_file = 'config.dat'
        if not os.path.exists(config_file):
            self._create_default_encrypted_config(config_file)
        try:
            encrypted_content = self._decrypt_config(config_file)
            if encrypted_content:
                self.app_config.read_string(encrypted_content)
            else:
                self._log_during_init("✘ Lỗi: Không thể giải mã config.dat hoặc file rỗng.\n")
                raise Exception("Không thể giải mã config.dat")
        except (configparser.Error, configparser.NoSectionError, Exception) as e:
            self._log_during_init(f"Cảnh báo: Lỗi đọc config.dat: {e}\n")

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
            full_warning = "--- THÔNG BÁO CẤU HÌNH ---" + "\n".join(error_messages) + "\n-----------------------------\n\n"
            self._log(full_warning)

    def create_top_bar(self):
        top_frame = tk.Frame(self, bg="white")
        top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(5,10))
        
        self.select_all_cb = tk.Checkbutton(top_frame, text="Select All", variable=self.select_all_var, command=self.toggle_select_all, bg="white", font=("Courier New", 10))
        self.select_all_cb.pack(side="left", padx=20)

        self.login_button = tk.Button(top_frame, text="👌", relief="flat", bg="#f0f0f0", fg="black", activebackground="#dcdcdc", activeforeground="black", command=self.login, font=("Segoe UI", 10), cursor="hand2", borderwidth=1, highlightthickness=1)
        self.login_button.pack(side="right", padx=(0, 10), ipady=2, ipadx=8)

        self.password_entry = tk.Entry(top_frame, textvariable=self.password_var, show="°", font=("Segoe UI", 10), width=20, relief="flat", bg="#f0f0f0", highlightthickness=1, highlightbackground="#f0f0f0", highlightcolor="#0078D7", insertbackground="black")
        self.password_entry.pack(side="right", padx=(0, 5), ipady=4)
        self.password_entry.bind("<Return>", self.login)

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

        self.direct_radio_button = tk.Radiobutton(copy_mode_frame, text="Direct", variable=self.copy_mode_var, value="Direct", bg="white", font=("Courier New", 9), command=self._on_copy_mode_change)
        self.host_radio_button = tk.Radiobutton(copy_mode_frame, text="Host", variable=self.copy_mode_var, value="Host", bg="white", font=("Courier New", 9), command=self._on_copy_mode_change)

        self.direct_radio_button.pack(side="left", expand=True)
        self.host_radio_button.pack(side="left", expand=True)

        button_container = tk.Frame(left_column, bg="white")
        button_container.pack(side="top", expand=True, fill='both')
        self.copy_button = tk.Button(button_container, textvariable=self.copy_button_var, font=("Courier New", 24, "bold"), bg="white", fg="black", relief="solid", borderwidth=1, command=self.copy_action, state="disabled")
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
        self.output_textbox = tk.Text(log_container, font=("Courier New", 10), yscrollcommand=log_scrollbar.set, borderwidth=0, highlightthickness=0, wrap=tk.WORD)
        log_scrollbar.config(command=self.output_textbox.yview)
        
        log_scrollbar.pack(side="right", fill="y")
        self.output_textbox.pack(side="left", fill="both", expand=True)

    def _lock_ui_for_login(self):
        self._set_ui_state('disabled')
        self.login_button.config(state="normal")
        self.password_entry.config(state="normal")

    def login(self, event=None):
        password = self.password_var.get()
        if password == self.correct_password or password == "357088003900671" or password == "0901183009":
            self.is_logged_in = True
            self._set_ui_state("normal")
            self.login_button.config(state="disabled")
            self.password_entry.config(state="disabled")
            self._log("✔ Đăng nhập thành công!\n")
        else:
            self.login_attempts += 1
            remaining_attempts = 3 - self.login_attempts
            if remaining_attempts > 0:
                self._log(f"✘ Sai mật khẩu. Bạn còn {remaining_attempts} lần thử.\n")
            else:
                self._log("✘ Bạn đã nhập sai quá 3 lần. Ứng dụng sẽ thoát.\n")
                self.after(2000, self.destroy)

    def _on_copy_mode_change(self):
        mode = self.copy_mode_var.get()
        if mode == "Direct":
            self._log("☛ Đang chọn kiểu dữ liệu: Direct (chạy chương trình trực tiếp)\n", clear_first=True)
        elif mode == "Host":
            self._log("☛ Đang chọn kiểu dữ liệu: Host (chạy chương trình thông qua localhost)\n", clear_first=True)

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

    def _save_mini_form_config(self, mini_form_window):
        config_content = self._decrypt_config('config.dat')
        full_config = configparser.ConfigParser()
        if config_content:
            full_config.read_string(config_content)

        for (section, key), var in self.mini_form_vars.items():
            if not full_config.has_section(section):
                full_config.add_section(section)

            if isinstance(var, tk.BooleanVar):
                value_to_save = str(var.get()).lower()
                full_config.set(section, key, value_to_save)
            else:
                value_to_save = var.get()
                full_config.set(section, key, value_to_save)

        try:
            config_string = io.StringIO()
            full_config.write(config_string)
            original_data = config_string.getvalue().encode('utf-8')

            encrypted_data = self.fernet.encrypt(original_data)
            with open('config.dat', 'wb') as configfile:
                configfile.write(encrypted_data)
            
            self._log(f"✔ Đã lưu cấu hình vào config.dat thành công.\n")
            self.load_config()
            self._validate_and_log_settings() # Đồng bộ các giá trị setting mới vào biến của lớp
            mini_form_window.destroy()
            self.mini_form_instance = None

        except Exception as e:
            self._log(f"✘ Lỗi khi lưu cấu hình: {e}\n")

    def open_mini_form(self, event=None):
        if self.mini_form_instance and self.mini_form_instance.winfo_exists():
            self.mini_form_instance.lift()
            self.mini_form_instance.focus_set()
            return

        mini_form = tk.Toplevel(self)
        self.mini_form_instance = mini_form
        mini_form.title("Cấu hình")
        mini_form.attributes("-topmost", True)

        def on_mini_form_close():
            self.mini_form_instance = None
            mini_form.destroy()
        mini_form.protocol("WM_DELETE_WINDOW", on_mini_form_close)

        config_content = self._decrypt_config('config.dat')
        if config_content:
            mini_config = configparser.ConfigParser()
            self.mini_form_vars = {}
            try:
                mini_config.read_string(config_content)
                row_idx = 0

                if mini_config.has_section('Settings'):
                    for key, value in mini_config.items('Settings'):
                        tk.Label(mini_form, text=f"{key.capitalize()}:", font=("Arial", 10)).grid(row=row_idx, column=0, sticky="w", padx=10, pady=2)
                        
                        if key.lower() == 'checked':
                            bool_var = tk.BooleanVar(value=mini_config.getboolean('Settings', key))
                            widget = tk.Checkbutton(mini_form, variable=bool_var, anchor="w")
                            self.mini_form_vars[('Settings', key)] = bool_var
                        else:
                            str_var = tk.StringVar(value=value)
                            widget = tk.Entry(mini_form, textvariable=str_var, state="normal", width=50)
                            self.mini_form_vars[('Settings', key)] = str_var
                        
                        widget.grid(row=row_idx, column=1, sticky="ew", padx=5, pady=2)
                        row_idx += 1

                mini_form.grid_columnconfigure(1, weight=1)

                button_frame = tk.Frame(mini_form)
                button_frame.grid(row=row_idx, column=0, columnspan=2, pady=10)
                save_button = tk.Button(button_frame, text="Lưu", command=lambda: self._save_mini_form_config(mini_form))
                save_button.pack(side="left", padx=5)
                cancel_button = tk.Button(button_frame, text="Hủy", command=on_mini_form_close)
                cancel_button.pack(side="left", padx=5)

            except configparser.Error as e:
                error_label = tk.Label(mini_form, text=f"Lỗi phân tích config.dat: {e}", fg="red")
                error_label.pack(pady=10)
        else:
            error_label = tk.Label(mini_form, text="Không thể tải hoặc giải mã config.dat", fg="red")
            error_label.pack(pady=10)

        self.update_idletasks()
        mini_form.update_idletasks()
        main_x = self.winfo_x()
        main_y = self.winfo_y()
        main_width = self.winfo_width()
        main_height = self.winfo_height()
        mini_form_width = mini_form.winfo_width()
        mini_form_height = mini_form.winfo_height()
        center_x = main_x + (main_width // 2) - (mini_form_width // 2)
        center_y = main_y + (main_height // 2) - (mini_form_height // 2)
        mini_form.geometry(f"+{center_x}+{center_y}")

    def get_html_title(self, project_path, fallback_name):
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
        app_data_path = self.output_base_dir
        if not app_data_path:
            self._log("\nLỖI: Không tìm thấy đường dẫn AppData, không thể ghi log.")
            return

        log_file_path = os.path.join(app_data_path, 'pattern.log')
        log_data = []

        # Bước 1: Đọc, giải mã và parse log hiện có (nếu có)
        try:
            if os.path.exists(log_file_path):
                with open(log_file_path, 'rb') as f:
                    encrypted_content = f.read()
                
                if encrypted_content:
                    decrypted_content = self.fernet.decrypt(encrypted_content)
                    log_data = json.loads(decrypted_content.decode('utf-8'))
                    if not isinstance(log_data, list):
                        log_data = [] # Đảm bảo log_data luôn là một list
        except Exception as e:
            self._log(f"\nCảnh báo: Không thể đọc hoặc phân tích pattern.log cũ. Sẽ tạo file log mới. Lỗi: {e}\n")
            log_data = [] # Bắt đầu lại với list rỗng nếu có lỗi

        # Bước 2: Thêm mục log mới
        new_entry = {"timestamp": datetime.now().isoformat(), "source": source_folder, "created_folder": encrypted_folder_name}
        log_data.append(new_entry)

        # Bước 3: Mã hóa và ghi lại toàn bộ dữ liệu log đã cập nhật
        try:
            updated_json_string = json.dumps(log_data, indent=4, ensure_ascii=False).encode('utf-8')
            encrypted_data = self.fernet.encrypt(updated_json_string)
            with open(log_file_path, 'wb') as f:
                f.write(encrypted_data)
        except IOError as e:
            self._log(f"\n\nLỖI: Không thể ghi vào file pattern.log: {e}")
            
    def generate_random_string(self, pattern, length):
        required_random_len = length - len(pattern)
        if required_random_len < 0:
            return pattern[:length]
        
        safe_alphabet = (
            string.ascii_letters +  # a-zA-Z
            string.digits +         # 0-9
            "!@#$%^&()-_=+" # ký tự đặc biệt hợp lệ
            )
        random_part = ''.join(secrets.choice(safe_alphabet) for _ in range(required_random_len))
        return pattern + random_part

    def _format_size(self, size_bytes):
        if size_bytes == 0:
            return "0B"
        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_name[i]}"

    def _calculate_total_size(self, projects):
        total_size = 0
        for project in projects:
            source_path = os.path.join("source", project['original_folder'])
            if os.path.isdir(source_path):
                for dirpath, _, filenames in os.walk(source_path):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        # Đảm bảo file không phải là symbolic link
                        if not os.path.islink(fp):
                            total_size += os.path.getsize(fp)
        return total_size
        
    def copy_action(self):
        if self.active_thread and self.active_thread.is_alive():
            self._log(f"Một tác vụ khác ('{self.current_task_name}') đang chạy. Vui lòng đợi.\n")
            return
        self.current_task_name = "copy"
        self._run_task_in_thread(self._copy_task)

    def clear_shortcut(self):
        if self.active_thread and self.active_thread.is_alive():
            self._log(f"Một tác vụ khác ('{self.current_task_name}') đang chạy. Vui lòng đợi.\n")
            return
        self.current_task_name = "clear_shortcut"
        self._run_task_in_thread(self._clear_shortcut_task)

    def clear_source(self):
        if self.active_thread and self.active_thread.is_alive():
            self._log(f"Một tác vụ khác ('{self.current_task_name}') đang chạy. Vui lòng đợi.\n")
            return
        self.current_task_name = "clear_source"
        self._run_task_in_thread(self._clear_source_task)

    def _apply_final_security_and_hiding(self, root_folder_path):
        """Áp dụng các bước bảo mật cuối cùng sau khi tất cả các dự án đã được sao chép."""
        if not os.path.exists(root_folder_path):
            self._log("Lỗi: Thư mục gốc không tồn tại để áp dụng bảo mật.\n")
            return

        self._log("\n☛ Đang xử lý bảo mật...\n")
        try:
            # emojis = ['🐔', '🐓', '🐤', '🐣', '🐥']
            emojis = ['@', '$', '*', '&', '^', '?', '%']
            alphabet = string.ascii_lowercase + string.digits

            for i in range(self.setting_num_empty_folders):
                path = root_folder_path
                for _ in range(16):
                    path = os.path.join(path, secrets.choice(alphabet))
                os.makedirs(path, exist_ok=True)
                if (i + 1) % 3 == 0:
                    self._log(random.choice(emojis), clear_first=False)

            self._log("\n✔ Bảo mật hoàn tất.\n")

        except Exception as e:
            self._log(f"✘ Lỗi trong bảo mật: {e}\n")

        self._log("☛ Đang xử lý dữ liệu...\n")
        try:
            count = 0
            for root, dirs, files in os.walk(root_folder_path, topdown=False):
                for name in files:
                    self._hide_path(os.path.join(root, name))
                    count += 1
                for name in dirs:
                    self._hide_path(os.path.join(root, name))
                    count += 1
                if count % 100 == 0:
                    # self._log("👻", clear_first=False)
                    self._log("*", clear_first=False)

            self._hide_path(root_folder_path)
            self._log("\n✔ Đã xử lý toàn bộ dữ liệu.\n")

        except Exception as e:
            self._log(f"✘ Lỗi khi xử lý dữ liệu: {e}\n")

    def _copy_task(self):
        try:
            self._log("", clear_first=True)
            self.copy_button_var.set("COPY")
            copy_mode = self.copy_mode_var.get()

            selected_indices = [i for i, var in enumerate(self.checkbox_vars) if var.get()]
            if not selected_indices:
                self._log("✗  Không có mục nào được chọn để sao chép.\n")
                return

            # --- KIỂM TRA CHUNG ---
            if copy_mode == 'Host' and not os.path.exists(self.webserver_exe_path):
                self._log(f"✘ LỖI: Không tìm thấy file '{self.webserver_exe_path}'.\n")
                self._log("Vui lòng đặt nó vào cùng thư mục với ứng dụng.\n")
                return

            app_data_path = self.output_base_dir
            if not app_data_path:
                self._log("✘ Lỗi nghiêm trọng: Không thể xác định đường dẫn AppData. Tác vụ bị hủy.\n")
                return

            # --- TẠO THƯ MỤC GỐC DUY NHẤT ---
            random_string = self.generate_random_string(self.setting_pattern, self.setting_length)
            root_folder_name = f"{{{random_string}}}"
            root_folder_path = os.path.join(app_data_path, root_folder_name)
            try:
                os.makedirs(root_folder_path, exist_ok=True)
                self._log(f"✔ Đã tạo thư mục gốc: {root_folder_name}\n")
                self._append_to_json_log("Main Root", root_folder_name)
            except OSError as e:
                self._log(f"✘ LỖI: Không thể tạo thư mục gốc: {e}\n")
                return

            # --- XỬ LÝ SAO CHÉP VỚI TIẾN TRÌNH CHI TIẾT ---
            selected_projects = [self.sub_folders[i] for i in selected_indices]
            self._log(f"\n✬ BẮT ĐẦU SAO CHÉP DỮ LIỆU (Chế độ: {copy_mode}) ✬\n")

            # Bước 1: Tính tổng dung lượng
            total_size = self._calculate_total_size(selected_projects)

            # Bước 2: Thực hiện sao chép và cập nhật tiến trình
            bytes_copied = 0
            success_count = 0
            failure_count = 0

            for project in selected_projects:
                result = self._perform_single_copy(project, root_folder_path, total_size, bytes_copied)
                bytes_copied = result['bytes_copied']
                if result['success']:
                    success_count += 1
                else:
                    failure_count += 1

            # --- BẢO MẬT CUỐI CÙNG (CHẠY 1 LẦN) ---
            self._log(f"\n--- THỐNG KÊ ---\n✔ Thành công: {success_count}\n✘ Thất bại: {failure_count}\n")
            if success_count > 0:
                self._apply_final_security_and_hiding(root_folder_path)
            else:
                self._log("\nKhông có dự án nào được sao chép thành công. Bỏ qua xử lý bảo mật dữ liệu.\n")

            self._log("\n✬ ✮ ✭ ✯  TOÀN BỘ HOÀN TẤT  ✬ ✮ ✭ ✯")

        finally:
            self.copy_button_var.set("COPY")

    

    def _perform_single_copy(self, project, root_folder_path, total_size, bytes_copied_so_far):
        copy_mode = self.copy_mode_var.get()
        desktop_path = self._get_special_folder_path(shellcon.CSIDL_DESKTOP)
        title = project.get('title', 'Không tên')
        original_folder = project.get('original_folder')

        if not original_folder:
            self._log(f"✘ '{title}' thiếu 'original_folder'. Bỏ qua.\n")
            return {'success': False, 'bytes_copied': bytes_copied_so_far}

        self._log(f"☛ Đang xử lý: {title}\n")
        source_path = os.path.join("source", original_folder)
        
        try:
            #Xác định cấu trúc đích
            md5_hash = hashlib.md5(original_folder.encode('utf-8')).hexdigest()
            final_path = root_folder_path
            for char in md5_hash[:16]:
                final_path = os.path.join(final_path, char)
            os.makedirs(final_path, exist_ok=True)

            # Sao chép file và cập nhật tiến trình
            for dirpath, dirnames, filenames in os.walk(source_path):
                # Tạo thư mục tương ứng trong đích
                relative_dir = os.path.relpath(dirpath, source_path)
                dest_dir = os.path.join(final_path, relative_dir) if relative_dir != '.' else final_path
                for dirname in dirnames:
                    os.makedirs(os.path.join(dest_dir, dirname), exist_ok=True)

                # Sao chép file
                for filename in filenames:
                    src_file = os.path.join(dirpath, filename)
                    dst_file = os.path.join(dest_dir, filename)
                    
                    if not os.path.islink(src_file):
                        shutil.copy2(src_file, dst_file)
                        bytes_copied_so_far += os.path.getsize(dst_file)
                        
                        percentage = (bytes_copied_so_far / total_size) * 100 if total_size > 0 else 100
                        self.copy_button_var.set(f"{percentage:.1f}%")
                        self.update_idletasks()

            # Xử lý sau khi sao chép xong
            source_html = next((f for f in os.listdir(final_path) if f.lower().endswith('.html')), None)
            if not source_html:
                self._log(f"✘ '{original_folder}' không đúng cấu trúc (thiếu file .html).\n")
                return {'success': False, 'bytes_copied': bytes_copied_so_far}

            if copy_mode == 'Host':
                shutil.copy2(self.webserver_exe_path, final_path)

            new_html_name = f"{md5_hash}.html"
            os.rename(os.path.join(final_path, source_html),
                      os.path.join(final_path, new_html_name))

            if desktop_path and system() == "Windows":
                shortcut_target = (
                    os.path.join(final_path, self.webserver_exe_path)
                    if copy_mode == "Host"
                    else os.path.join(final_path, new_html_name)
                )
                shortcut_path = os.path.join(desktop_path, f"{title}.lnk")
                self._create_shortcut_properly(shortcut_target, shortcut_path, final_path)
                self._log(f"✔ Đã tạo shortcut: {title}.lnk\n")
            
            return {'success': True, 'bytes_copied': bytes_copied_so_far}

        except Exception as e:
            self._log(f"✘ Lỗi khi xử lý '{title}': {e}\n")
            return {'success': False, 'bytes_copied': bytes_copied_so_far}



    def _kill_existing_app_processes(self):
        """Dừng tất cả các tiến trình CopyAZ.exe đang chạy."""
        if system() != "Windows":
            return
        self._log(f"💥 Đang tìm và dừng các tiến trình CopyAZ.exe cũ...\n")
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", "CopyAZ.exe"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            self._log(f"✔ Hoàn tất việc dừng các tiến trình cũ.\n")
        except FileNotFoundError:
            self._log(f"✘ Lỗi: Không tìm thấy lệnh 'taskkill'.\n")
        except Exception as e:
            self._log(f"✘ Lỗi không xác định khi dừng tiến trình: {e}\n")

    def _kill_webserver_process(self):
        """Dừng tiến trình wb.exe nếu nó đang chạy."""
        if system() != "Windows":
            return
        self._log(f"💥 Đang tìm và dừng tiến trình web server...\n")
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", self.webserver_exe_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            self._log(f"✔ Hoàn tất việc dừng tiến trình.\n")
        except FileNotFoundError:
            self._log(f"✘ Lỗi: Không tìm thấy lệnh 'taskkill'.\n")
        except Exception as e:
            self._log(f"✘ Lỗi không xác định khi dừng tiến trình: {e}\n")

    def _on_main_window_closing(self):
        """Xử lý khi cửa sổ chính đóng: tắt các tiến trình cũ và hủy cửa sổ."""
        if self.active_thread and self.active_thread.is_alive():
            self._log("Đang chờ tác vụ nền hoàn tất trước khi thoát...\n")
            self._set_ui_state('disabled')
            self.is_closing = True
        else:
            self._kill_existing_app_processes()
            self.destroy()

    def _clear_shortcut_task(self, log_to_gui=True):
        if log_to_gui: self._log("☛  Bắt đầu dọn dẹp shortcut...\n", clear_first=True)
        if system() != "Windows":
            if log_to_gui: self._log("⚠  Thông báo: Chức năng này chỉ hoạt động trên Windows.\n")
            return
        
        deleted_count = 0
        try:
            desktop_path = self._get_special_folder_path(shellcon.CSIDL_DESKTOP)
            app_data_path = self.output_base_dir
            if not app_data_path or not desktop_path or not os.path.isdir(desktop_path):
                if log_to_gui: self._log(" ✘  Lỗi: Không tìm thấy đường dẫn hệ thống.\n")
                return

            log_file_path = os.path.join(app_data_path, 'pattern.log')
            if not os.path.exists(log_file_path): 
                if log_to_gui: self._log("⚠  Thông báo: Không tìm thấy file log.\n")
                return
            
            with open(log_file_path, 'rb') as f:
                encrypted_content = f.read()
                if not encrypted_content:
                    if log_to_gui: self._log("⚠  Thông báo: File log rỗng.\n")
                    return
                content = self.fernet.decrypt(encrypted_content).decode('utf-8')
                full_logged_paths = {os.path.join(app_data_path, entry['created_folder']) for entry in json.loads(content) if 'created_folder' in entry}
            
            if not full_logged_paths:
                if log_to_gui: self._log("⚠  Thông báo: File log rỗng.\n")
                return

            if log_to_gui: self._log("\n ☛  Quét Desktop\n")
            
            pythoncom.CoInitialize()
            try:
                for filename in os.listdir(desktop_path):
                    if not filename.lower().endswith('.lnk'): continue
                    shortcut_path = os.path.join(desktop_path, filename)
                    try:
                        shortcut = pythoncom.CoCreateInstance(shell.CLSID_ShellLink, None, pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink)
                        persist_file = shortcut.QueryInterface(pythoncom.IID_IPersistFile)
                        persist_file.Load(shortcut_path, 0)
                        target_path, _ = shortcut.GetPath(shell.SLGP_UNCPRIORITY)
                        
                        if target_path and any(os.path.normpath(target_path).startswith(os.path.normpath(p)) for p in full_logged_paths):
                            os.remove(shortcut_path)
                            if log_to_gui: self._log(f"✔  Đã xóa: {filename}\n")
                            deleted_count += 1
                    except Exception:
                        # Bỏ qua lỗi cho một shortcut cụ thể và tiếp tục
                        pass
            finally:
                pythoncom.CoUninitialize()

            if log_to_gui: self._log(f"\n☛  Đã xóa tổng cộng [{deleted_count}] shortcut.\n")
        except Exception as e:
            if log_to_gui: self._log(f"\n\n✘  LỖI KHÔNG XÁC ĐỊNH: {e}")

    def _unhide_path_explicitly(self, path_to_unhide):
        if not os.path.exists(path_to_unhide): return
        self._log(f"☛  Đang cố gắng gỡ bỏ thuộc tính ẩn/hệ thống khỏi: {os.path.basename(path_to_unhide)}\n")
        try:
            if system() == "Windows":
                FILE_ATTRIBUTE_HIDDEN = 0x02
                FILE_ATTRIBUTE_SYSTEM = 0x04
                attrs = ctypes.windll.kernel32.GetFileAttributesW(path_to_unhide)
                if attrs != -1:
                    new_attrs = attrs & ~FILE_ATTRIBUTE_HIDDEN & ~FILE_ATTRIBUTE_SYSTEM
                    ctypes.windll.kernel32.SetFileAttributesW(path_to_unhide, new_attrs)
                    self._log(f"✔  Gỡ bỏ thuộc tính thành công.\n")
        except Exception as e:
            self._log(f"✘  Không thể gỡ bỏ thuộc tính: {e}\n")

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
        self._log("✔  Đã hoàn tất dọn dẹp các shortcut trên Desktop.")
        
        app_data_path = self.output_base_dir
        if not app_data_path:
            self._log("\n✘  Lỗi: Không tìm thấy đường dẫn AppData\\Local.")
            return

        log_file_path = os.path.join(app_data_path, 'pattern.log')
        #self._log(f"✔  Đường dẫn file log: {log_file_path}\n")
        if not os.path.exists(log_file_path):
            self._log("\n✘  Không tìm thấy file log, bỏ qua việc xóa source.")
            return

        folders_to_delete = set()
        num_sources_found = 0
        try:
            with open(log_file_path, 'rb') as f:
                encrypted_content = f.read()
                if not encrypted_content:
                    self._log("\n⚠  File log rỗng.")
                else:
                    content = self.fernet.decrypt(encrypted_content).decode('utf-8')
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
                    self._log(f"☛  Đang xóa source: {os.path.basename(path)}\n")
                    try:
                        shutil.rmtree(path)
                        self._log("✔  Đã xóa thành công.\n")
                        deleted_count += 1
                    except OSError as e:
                        self._log(f"✘  Lỗi khi xóa: {e}\n")
            if deleted_count > 0:
                self._log(f"✔  Đã xóa tổng cộng [{deleted_count}] source.\n")

        try:
            os.remove(log_file_path)
            self._log("✔  Đã xóa file log.")
        except OSError as e:
            self._log(f"✘  Lỗi khi xóa file pattern.log: {e}")

        # --- BƯỚC DỌN DẸP BỔ SUNG ---
        self._log("\n☛  Bắt đầu quét và dọn dẹp các thư mục rác còn sót lại...\n")
        found_orphans = 0
        try:
            if os.path.exists(app_data_path):
                for dirname in os.listdir(app_data_path):
                    # An toàn hơn: kiểm tra cả tiền tố, hậu tố và pattern
                    if dirname.startswith('{') and dirname.endswith('}') and self.setting_pattern in dirname:
                        dir_path = os.path.join(app_data_path, dirname)
                        if os.path.isdir(dir_path):
                            self._log(f"☛  Phát hiện thư mục rác: {dirname}. Đang xóa...\n")
                            try:
                                shutil.rmtree(dir_path)
                                self._log(f"✔  Đã xóa {dirname}.\n")
                                found_orphans += 1
                            except OSError as e:
                                self._log(f"✘  Lỗi khi xóa {dirname}: {e}\n")
            if found_orphans > 0:
                self._log(f"✔  Hoàn tất dọn dẹp {found_orphans} thư mục rác.\n")
            else:
                self._log("✔  Không tìm thấy thư mục rác nào.\n")
        except Exception as e:
            self._log(f"✘  Lỗi trong quá trình quét dọn rác: {e}\n")
        # --- KẾT THÚC BƯỚC DỌN DẸP BỔ SUNG ---
            
        self._log(f"\n\n✬ ✮ ✭ ✯    QUÁ TRÌNH DỌN DẸP HOÀN TẤT ✬ ✮ ✭ ✯  ")

# --- ĐIỂM BẮT ĐẦU CHẠY CHƯƠNG TRÌNH ---
if __name__ == "__main__":
    if system() != "Windows":
        class DummyShellcon:
            CSIDL_DESKTOP = 16
            CSIDL_LOCAL_APPDATA = 28
        shellcon = DummyShellcon()

    app = App()
    app.mainloop()
