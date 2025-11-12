
# Crawler-Booking

## Mô tả
Dự án **Crawler-Booking** là một công cụ thu thập dữ liệu (web crawler) từ trang Booking.com sử dụng Python. Nó hỗ trợ trích xuất thông tin khách sạn, giá cả, đánh giá, v.v., bằng cách kết hợp BeautifulSoup cho parsing HTML tĩnh và Selenium cho nội dung động (JavaScript-rendered).

**Lưu ý đạo đức**: Chỉ sử dụng cho mục đích học tập hoặc nghiên cứu cá nhân. Tuân thủ Terms of Service của Booking.com và luật pháp địa phương. Tránh spam hoặc overload server.

## Yêu cầu
- Python 3.8+ (khuyến nghị 3.10+)
- Git (để clone repo)
- Trình duyệt Chrome/Firefox (cho Selenium driver)

## Cài đặt
### Bước 1: Clone repository
```bash
git clone https://github.com/yourusername/crawler-booking.git
cd crawler-booking
```

### Bước 2: Tạo và kích hoạt môi trường ảo (venv)
Sử dụng PowerShell trên Windows (hoặc tương đương trên macOS/Linux). Nếu dùng VS Code, mở terminal tích hợp.

1. Tạo venv:
   ```powershell
   python -m venv myenv
   ```

2. Set Execution Policy (chỉ cần 1 lần trên PowerShell):
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
   ```

3. Kích hoạt venv:
   ```powershell
   myenv\Scripts\Activate.ps1
   ```
   - Nếu prompt không thay đổi (do custom theme như Oh My Posh), kiểm tra bằng:
     ```powershell
     $env:VIRTUAL_ENV
     ```
     Output nên là đường dẫn đến `myenv` (ví dụ: `C:\path\to\crawler-booking\myenv`).

   - Để thoát venv: `deactivate`.

### Bước 3: Cài đặt dependencies
```powershell
pip install -r requirements.txt
```

### Bước 4: Cấu hình VS Code (tùy chọn nhưng khuyến nghị)
- Cài extension **Python** (Microsoft).
- Chọn interpreter: `Ctrl+Shift+P` > "Python: Select Interpreter" > Chọn `./myenv/Scripts/python.exe`.
- Reload window: `Ctrl+Shift+P` > "Developer: Reload Window".

## Sử dụng
### Chạy crawler cơ bản
```python
# Trong file crawler.py
python crawler.py  
```

- **Arguments phổ biến**:
  - `--url`: URL tìm kiếm trên Booking.com.
  - `--output`: File CSV/JSON để lưu dữ liệu.
  - `--headless`: Chạy Selenium không mở browser (mặc định: False).

### Ví dụ extract dữ liệu
Sử dụng `data/extractor.py` để xử lý dữ liệu thô:
```python
from data.extractor import extract_hotels

hotels = extract_hotels('path/to/raw_data.html')
hotels.to_csv('hotels.csv', index=False)
```

### Cấu trúc dự án
```
crawler-booking/
├── myenv/                  # Môi trường ảo (không commit)
├── data/                   # Dữ liệu đầu ra
│   ├── extractor.py        # Xử lý dữ liệu
│   └── utils.py            # Helper functions
├── src/                    # Source code
│   ├── crawler.py          # Main crawler script
│   └── selenium_utils.py   # Selenium helpers
├── tests/                  # Unit tests
│   └── test_extractor.py
├── requirements.txt        # Dependencies
├── README.md               # Tài liệu này
└── .gitignore              # Ignore venv, data, etc.
```

## Troubleshooting
- **Lỗi import (e.g., bs4)**: Đảm bảo venv kích hoạt và `pip install -r requirements.txt`.
- **Selenium driver**: Cài `webdriver-manager` để tự động tải ChromeDriver.
- **Proxy/Rate limiting**: Thêm delay trong code hoặc dùng proxy nếu bị block.
- **Venv không kích hoạt**: Thử Command Prompt: `myenv\Scripts\activate.bat`.

## Dependencies (requirements.txt)
```
beautifulsoup4>=4.12.0
requests>=2.31.0
selenium>=4.15.0
webdriver-manager>=4.0.0
pandas>=2.1.0
lxml>=4.9.0
openpyxl>=3.1.0
```


