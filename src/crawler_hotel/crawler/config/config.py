# config.py
import os

# ====================== ĐƯỜNG DẪN ======================
ROOT_DIR = r"D:\private\crawler-booking-2025\src\crawler_hotel\data_final"
# ROOT_DIR = r"D:\private\data"

# ROOT_DIR = r"D:\private\crawler-booking\data"

# Thư mục GỐC lưu trữ (logs, errors, excel)
BASE_OUTPUT_DIR = r"D:\private\crawler-booking-2025\src\crawler_hotel\crawler\output_2025"
# BASE_OUTPUT_DIR = r"D:\private\crawler-booking-2025\src\crawler_hotel\crawler\output_2023"


# === CHỈ CẦN SỬA 1 DÒNG NÀY LÀ ĐỦ ===
ERROR_LINK_DIR = r"D:\private\crawler-booking-2025\src\crawler_hotel\crawler\output_error_link"

CRAWLER_AGAIN_ROOT_DIR = r"D:\private\crawler-booking-2025\src\crawler_hotel\crawler\province_crawler_again"
TIMEOUT_ERROR_DIR_ROOT = r"D:\private\crawler-booking-2025\src\crawler_hotel\crawler\output_error_link"
HOTEL_LINKS_DIR = r"D:\private\crawler-booking-2025\src\crawler_province\hotel_links_final"
SUCCESS_JSON_DIR = ROOT_DIR  # data_final chính là nơi chứa success JSON theo tỉnh

os.makedirs(ERROR_LINK_DIR, exist_ok=True)

# --- LOGS ---
LOG_ROOT_DIR = os.path.join(BASE_OUTPUT_DIR, "logs")
LOG_DIR_INVALID = os.path.join(LOG_ROOT_DIR, "invalid")     # File lỗi chi tiết
LOG_DIR_SUMMARY = os.path.join(LOG_ROOT_DIR, "summary")     # Tổng hợp

# --- LỖI (copy file) ---
ERROR_ROOT_DIR = os.path.join(BASE_OUTPUT_DIR, "errors_detected")  # Thư mục gốc copy file lỗi

# --- EXCEL ---
EXCEL_DIR = os.path.join(BASE_OUTPUT_DIR, "excel")

# ====================== TÊN FILE ======================
FILE_SUMMARY = "ALL_invalid_hotels.txt"
EXCEL_NAME = "REPORT_HOTELS_FULL_2025.xlsx"
# EXCEL_NAME = "REPORT_HOTELS_FULL_2023.xlsx"

# === GIỚI HẠN SAI SỐ REVIEW ===
MAX_REVIEW_DIFF = 20              # Sai số tối đa cho phép giữa total_rating và số review thực tế
                                 # Ví dụ: 1 → cho phép chênh lệch ±1 (total_rating = 5, thực tế 4 hoặc 6 → vẫn hợp lệ)
                                 # 0 → yêu cầu chính xác tuyệt đối (phải bằng nhau mới hợp lệ)
                                 # None → không kiểm tra sai số (chỉ kiểm tra kiểu dữ liệu)

# ====================== CÀI ĐẶT ======================
MODE = "copy"           # "copy" hoặc None
PROCESS_BY = "province" # "range" hoặc "province"

# TÙY CHỌN: Bật/tắt đếm review Việt Nam có comment_positive
COUNT_VN_POSITIVE_REVIEWS = True  # Đặt False để tắt hoàn toàn

SELECT_LANGUAGE = "0"   # Tiếng Việt -> vi