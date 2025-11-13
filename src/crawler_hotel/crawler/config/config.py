# config.py
import os

# ====================== ĐƯỜNG DẪN ======================
ROOT_DIR = r"D:\private\crawler-booking-2025\src\crawler_hotel\data_final"

# ROOT_DIR = r"D:\private\crawler-booking\data"

# Thư mục GỐC lưu trữ (logs, errors, excel)
BASE_OUTPUT_DIR = r"D:\private\crawler-booking-2025\src\crawler_hotel\crawler\output_2025"

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
EXCEL_NAME = "REPORT_HOTELS_FULL.xlsx"

# ====================== CÀI ĐẶT ======================
MODE = "copy"           # "copy" hoặc None
PROCESS_BY = "province" # "range" hoặc "province"