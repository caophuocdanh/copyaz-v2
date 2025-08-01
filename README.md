# CopyAZ v2 - Ứng dụng Sao chép & Bảo mật Dữ liệu Đa Năng

CopyAZ v2 là ứng dụng Python mạnh mẽ giúp sao chép, mã hóa và ẩn dữ liệu với giao diện trực quan, dễ sử dụng. Ứng dụng nay hỗ trợ nhiều tùy chọn nguồn dữ liệu và phương thức thực thi, đảm bảo dữ liệu của bạn được bảo vệ và truy cập linh hoạt.

## Tính năng chính

-   **Hỗ trợ đa nguồn dữ liệu:**
    -   **Local:** Sao chép và mã hóa thư mục từ thư mục `source/` cục bộ.
    -   **Online:** Tải và xử lý dữ liệu từ một server từ xa (yêu cầu server đang hoạt động và kết nối mạng).
-   **Hỗ trợ đa phương thức thực thi:**
    -   **Direct:** Tạo shortcut trỏ trực tiếp đến file HTML đã mã hóa (mở bằng trình duyệt mặc định).
    -   **Host:** Tạo shortcut trỏ đến một web server cục bộ (`cp.exe`) được sao chép cùng với dữ liệu, giúp phục vụ file HTML một cách độc lập và an toàn hơn.
-   **Mã hóa & Ẩn dữ liệu:**
    -   Tên file và thư mục được mã hóa bằng MD5, làm cho chúng khó nhận diện.
    -   Tạo cấu trúc thư mục sâu và hàng trăm thư mục giả (decoy) để làm nhiễu, tăng độ khó phát hiện dữ liệu thật.
    -   Ẩn toàn bộ dữ liệu đã sao chép bằng thuộc tính hệ thống (hidden attribute).
    -   Dữ liệu được lưu trữ ở vị trí ẩn trên hệ thống (%LOCALAPPDATA%) với tên ngẫu nhiên.
-   **Tạo shortcut tự động trên Desktop (Windows):** Giúp truy cập nhanh file đã mã hóa.
-   **Dọn dẹp toàn diện:** Chức năng xóa shortcut và xóa toàn bộ dữ liệu đã tạo, bao gồm cả việc dừng các tiến trình `cp.exe` đang chạy.
-   **Giao diện Tkinter:** Đơn giản, dễ dùng, có log hoạt động trực tiếp.

## Yêu cầu

-   **Python:** 3.6 trở lên (khuyên dùng 3.8+).
-   **Hệ điều hành:** Windows 10/11 (Linux/macOS: chỉ hỗ trợ cơ bản, không có shortcut và tính năng `cp.exe`).
-   **Thư viện Python:**
    -   `pywin32` (cho các tính năng Windows-specific như shortcut và ẩn file).
    -   `requests` (cho chế độ nguồn dữ liệu Online).
-   **File thực thi `cp.exe`:** (Chỉ cần cho chế độ thực thi **Host**) File này phải được đặt cùng thư mục với `CopyAZ.py` hoặc file `.exe` đã build.

## Cài đặt & Sử dụng

1.  **Chạy từ mã nguồn:**
    -   Clone project: `git clone <địa chỉ repo>`
    -   Cài đặt các thư viện cần thiết: `pip install pywin32 requests`
    -   Chạy ứng dụng: `python CopyAZ.py`
2.  **Build file .exe:**
    -   Chạy file `build.cmd` (nội dung: `pyinstaller --onefile --windowed --icon="icon.ico" --name "CopyAZ" --hidden-import "win32timezone" CopyAZ.py`)
    -   Hoặc tự chạy lệnh trên trong terminal.
    -   File `.exe` sẽ nằm trong thư mục `dist/`.
3.  **Portable:**
    -   Tải file `.exe` đã build, chạy trực tiếp trên Windows, không cần cài Python.
    -   **Lưu ý:** Nếu sử dụng chế độ **Host**, bạn cần đảm bảo file `cp.exe` cũng nằm cùng thư mục với file `CopyAZ.exe`.

### Hướng dẫn nhanh

-   **Chuẩn bị dữ liệu:** Đặt thư mục cần bảo mật vào `source/` (mỗi thư mục nên có file .html để shortcut trỏ tới).
-   **Cấu hình:** Chỉnh sửa file `config.ini` để thay đổi số lượng thư mục giả, pattern tên, v.v.
-   **Khởi động ứng dụng:** Mở `CopyAZ.py` hoặc `CopyAZ.exe`.
-   **Chọn chế độ nguồn:** Chọn "Local" hoặc "Online" (nếu có server).
-   **Chọn phương thức thực thi:** Chọn "Direct" hoặc "Host".
-   **Thực hiện:** Chọn các thư mục mong muốn từ danh sách và nhấn nút **COPY** để bắt đầu quá trình mã hóa và sao chép.
-   **Dọn dẹp:** Khi cần dọn dẹp, sử dụng các nút "Clear Shortcut" (xóa shortcut trên Desktop) hoặc "Clear source" (xóa toàn bộ dữ liệu đã tạo và dừng các tiến trình liên quan).

## Cấu trúc thư mục mẫu

```
CopyAZ v2/
├── CopyAZ.py
├── build.cmd
├── config.ini
├── icon.ico
├── README.md
├── cp.exe (chỉ cần nếu sử dụng chế độ Host)
└── source/
    ├── Thumuc1/
    │   └── index.html
    └── Thumuc2/
```

## Bảo mật

-   **Mã hóa mạnh mẽ:** Tên file/thư mục được mã hóa bằng MD5, gây khó khăn cho việc nhận diện thủ công.
-   **Hệ thống ma trận:** Dữ liệu thật được ẩn sâu trong nhiều lớp thư mục và hàng trăm thư mục giả (decoy), tạo ra một "mê cung" ảo.
-   **Vị trí ẩn:** Dữ liệu được lưu trữ ở `%LOCALAPPDATA%` với tên ngẫu nhiên, một khu vực ít được người dùng thông thường kiểm tra.
-   **Shortcut thông minh:**
    -   Chế độ **Direct:** Shortcut trỏ trực tiếp đến file HTML.
    -   Chế độ **Host:** Shortcut trỏ đến `cp.exe`, một web server cục bộ, giúp tách biệt việc truy cập nội dung khỏi file HTML gốc, tăng cường khả năng che giấu.
-   **Quản lý log:** Giữ file `pattern.log` để phục hồi shortcut hoặc dữ liệu nếu cần.

## Lưu ý

-   Chỉ dùng cho mục đích hợp pháp, không dùng để che giấu dữ liệu bất hợp pháp.
-   Xóa dữ liệu sẽ không thể khôi phục, hãy backup trước khi thao tác.
-   Giữ file `pattern.log` để phục hồi shortcut hoặc dữ liệu nếu cần.
-   Chế độ **Host** yêu cầu file `cp.exe` phải có sẵn và được đặt đúng chỗ.

## Tác giả

-   Cao Phước Danh

## License

MIT License (xem chi tiết trong file)