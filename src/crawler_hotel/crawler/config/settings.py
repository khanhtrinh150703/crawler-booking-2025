# config/settings.py
import os

# Đường dẫn
BASE_INPUT_DIR_MODE1 = r"D:\private\crawler-booking-2025\src\crawler_province\hotel_group_by_range"
BASE_INPUT_DIR_MODE2 = r"D:\private\crawler-booking-2025\src\crawler_province\hotel_one_province"

OUTPUT_DIR_MODE1 = "data_range_province"
OUTPUT_DIR_MODE2 = "data_one_provnce"

LOGS_DIR = "logs"

# Cấu hình chạy
MAX_WORKERS = 1
MAX_RUNTIME_MINUTES = None  # None = không giới hạn

# Tạo thư mục logs
os.makedirs(LOGS_DIR, exist_ok=True)