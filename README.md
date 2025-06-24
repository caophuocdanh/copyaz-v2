# CopyAZ v2 - Ứng dụng Sao chép & Bảo mật Dữ liệu

CopyAZ v2 là ứng dụng Python giúp sao chép, mã hóa và ẩn dữ liệu với giao diện đơn giản, dễ dùng. Dữ liệu được bảo vệ bằng nhiều lớp: mã hóa tên file/folder, tạo thư mục giả, lưu trữ ở vị trí ẩn trên hệ thống.

## Tính năng chính
- Sao chép & mã hóa thư mục từ `source/` (tên file và thư mục được mã hóa bằng MD5)
- Tạo cấu trúc thư mục sâu, tăng độ khó phát hiện dữ liệu thật
- Tạo shortcut tự động trên Desktop (Windows), giúp truy cập nhanh file đã mã hóa
- Sinh nhiều thư mục giả (decoy) để làm nhiễu, tăng bảo mật
- Ẩn toàn bộ dữ liệu đã sao chép bằng thuộc tính hệ thống
- Giao diện Tkinter đơn giản, dễ dùng, có log hoạt động trực tiếp

## Yêu cầu
- Python 3.6 trở lên (khuyên dùng 3.8+)
- Windows 10/11 (Linux/macOS: chỉ hỗ trợ cơ bản, không có shortcut)
- Cài đặt: `pip install pywin32`

## Cài đặt & Sử dụng
1. **Chạy từ source:**
   - Clone project, cài pywin32, chạy `python CopyAZ.py`
2. **Build file .exe:**
   - Chạy file `build.cmd` (nội dung:)
     ```bat
     pyinstaller --onefile --windowed --icon="icon.ico" --name "CopyAZ" --hidden-import "win32timezone" CopyAZ.py
     ```
   - Hoặc tự chạy lệnh trên trong terminal
   - File .exe sẽ nằm trong thư mục `dist/`
3. **Portable:**
   - Tải file `.exe` đã build, chạy trực tiếp trên Windows, không cần cài Python

### Hướng dẫn nhanh
- Đặt thư mục cần bảo mật vào `source/` (mỗi thư mục nên có file .html để shortcut trỏ tới)
- Có thể chỉnh file `config.ini` để thay đổi số lượng thư mục giả, pattern tên, v.v.
- Mở app, chọn thư mục, nhấn **COPY** để bắt đầu mã hóa và sao chép
- Khi cần dọn dẹp, dùng chức năng xóa shortcut hoặc xóa toàn bộ dữ liệu đã tạo

## Cấu trúc thư mục mẫu
```
CopyAZ v2/
├── CopyAZ.py
├── build.cmd
├── config.ini
├── icon.ico
├── README.md
└── source/
    ├── Thumuc1/
    │   └── index.html
    └── Thumuc2/
```

## Bảo mật
- Tên file/thư mục được mã hóa bằng MD5, khó nhận diện
- Dữ liệu thật được ẩn trong nhiều lớp thư mục và hàng trăm thư mục giả (decoy)
- Dữ liệu được lưu ở %LOCALAPPDATA% với tên ngẫu nhiên, khó phát hiện
- Shortcut tạo qua COM interface, chỉ có trên Windows
- Có thể phục hồi hoặc dọn dẹp dễ dàng nếu giữ lại file `pattern.log`

## Lưu ý
- Chỉ dùng cho mục đích hợp pháp, không dùng để che giấu dữ liệu bất hợp pháp
- Xóa dữ liệu sẽ không thể khôi phục, hãy backup trước khi thao tác
- Giữ file `pattern.log` để phục hồi shortcut hoặc dữ liệu nếu cần

## Tác giả
- Cao Phước Danh  
- Email: danhcptube@gmail.com
- YouTube, Facebook: xem trong file gốc

## License
MIT License (xem chi tiết trong file)
