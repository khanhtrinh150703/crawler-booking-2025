# main.py
import os
from config import *
from utils.helpers import ensure_dir, get_timestamp, get_main_error_dir  # <<< ĐÃ SỬA
from core.processor import get_folders_to_process, process_range_folder, process_province_folder
from core.reporter import write_unit_log, write_summary, write_province_review_stats
from core.excel_exporter import export_to_excel
from datetime import datetime

def main():
    if not os.path.exists(ROOT_DIR):
        print(f"Thư mục không tồn tại: {ROOT_DIR}")
        return

    # Tạo timestamp MỚI cho lần chạy này
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    main_error_dir = f"{ERROR_ROOT_DIR}_{timestamp}"

    # Tạo các thư mục cần thiết
    for dir_path in [LOG_ROOT_DIR, LOG_DIR_INVALID, LOG_DIR_SUMMARY, EXCEL_DIR]:
        ensure_dir(dir_path)

    # Tạo thư mục lỗi nếu MODE == "copy"
    if MODE == "copy":
        ensure_dir(main_error_dir)
        print(f"Thư mục lỗi sẽ được tạo tại: {main_error_dir}")
        
    timestamp = get_timestamp()
    main_error_dir = f"{ERROR_ROOT_DIR}_{timestamp}"
    error_dir_created = False

    total_processed = total_errors = total_reviews = 0
    results = {}
    province_stats = {}

    print(f"Bắt đầu quét theo: {PROCESS_BY.upper()}...")

    folders = get_folders_to_process()

    for name, path in folders:
        print(f"\n--- Đang xử lý {'range' if PROCESS_BY == 'range' else 'tỉnh'}: {name} ---")

        if PROCESS_BY == "range":
            err, rev, lines, error_dir_created = process_range_folder(name, path, main_error_dir, error_dir_created)
            log_file = write_unit_log(name, err, rev, lines, is_range=True)
        else:
            err, rev, lines, error_dir_created = process_province_folder(name, path, main_error_dir, error_dir_created)
            log_file = write_unit_log(name, err, rev, lines, is_range=False)
            province_stats[name] = rev

        total_errors += err
        total_reviews += rev
        total_processed += sum(1 for f in os.listdir(path) if f.endswith(".json"))
        results[name] = {"count": err, "reviews": rev, "log_file": log_file}

        print(f"{'Range' if PROCESS_BY == 'range' else 'Tỉnh'} {name}: {err} lỗi, {rev} reviews")

    # Báo cáo tổng
    write_summary(total_processed, total_errors, total_reviews, results)
    if PROCESS_BY == "province":
        write_province_review_stats(province_stats, total_reviews)

    # Xuất Excel
    export_to_excel()

    # Kết quả cuối
    error_rate = (total_errors / total_processed * 100) if total_processed > 0 else 0
    print("\n" + "="*60)
    print("HOÀN TẤT!")
    print(f" - Tổng file: {total_processed} | Lỗi: {total_errors} | Reviews: {total_reviews}")
    print(f" - Tỷ lệ lỗi: {error_rate:.2f}%")
    print(f" - Log: {LOG_ROOT_DIR}/")
    if MODE == "copy" and total_errors:
        print(f" - File lỗi: {main_error_dir}/")
    print("="*60)


if __name__ == "__main__":
    main()