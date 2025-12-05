# main.py
import os
from config.config import *
from utils.helpers import ensure_dir, get_timestamp, get_main_error_dir  
from core.processor import get_folders_to_process, process_range_folder, process_province_folder
from core.reporter import write_unit_log, write_summary, write_province_review_stats
from core.excel_exporter import export_to_excel
from datetime import datetime
from utils.crawl_again_generator import run_crawl_again_generator

# main.py

def main():
    if not os.path.exists(ROOT_DIR):
        print(f"Thư mục không tồn tại: {ROOT_DIR}")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    main_error_dir = f"{ERROR_ROOT_DIR}_{timestamp}"

    for dir_path in [LOG_ROOT_DIR, LOG_DIR_INVALID, LOG_DIR_SUMMARY, EXCEL_DIR]:
        ensure_dir(dir_path)

    if MODE == "copy":
        ensure_dir(main_error_dir)
        print(f"Thư mục lỗi sẽ được tạo tại: {main_error_dir}")
        
    timestamp = get_timestamp()
    main_error_dir = f"{ERROR_ROOT_DIR}_{timestamp}"
    error_dir_created = False

    total_processed = total_errors = total_reviews = total_viet_positive = total_province = 0
    results = {}
    province_stats = {}

    print(f"Bắt đầu quét theo: {PROCESS_BY.upper()}...")

    folders = get_folders_to_process()

    for name, path in folders:
        print(f"\n--- Đang xử lý {'range' if PROCESS_BY == 'range' else 'tỉnh'}: {name} ---")

        if PROCESS_BY == "range":
            err, rev, viet_pos, lines, error_dir_created = process_range_folder(name, path, main_error_dir, error_dir_created)
            log_file = write_unit_log(name, err, rev, lines, is_range=True)
        else:
            err, rev, viet_pos, lines, error_dir_created = process_province_folder(name, path, main_error_dir, error_dir_created)
            log_file = write_unit_log(name, err, rev, lines, is_range=False)
            province_stats[name] = (rev, viet_pos)  # Lưu cả 2

        total_province += 1
        total_errors += err
        total_reviews += rev
        total_viet_positive += viet_pos  # ← CỘNG DỒN TỔNG
        total_processed += sum(1 for f in os.listdir(path) if f.endswith(".json"))
        results[name] = {"count": err, "reviews": rev, "viet_pos": viet_pos, "log_file": log_file}

        # IN RA MÀN HÌNH CHO TỪNG TỈNH/RANGE
        print(f"→ {name}: {err} lỗi | {rev} reviews | {viet_pos} VN có comment+")

    # Báo cáo tổng
    write_summary(total_processed, total_errors, total_reviews, results)
    if PROCESS_BY == "province":
        write_province_review_stats(province_stats, total_reviews)  # Cần sửa hàm này nếu muốn in thêm viet_pos

    # Xuất Excel
    export_to_excel()

    # Kết quả cuối
    error_rate = (total_errors / total_processed * 100) if total_processed > 0 else 0
    print("\n" + "="*70)
    print("HOÀN TẤT!")
    print(f" - Tổng file: {total_processed:,} | Lỗi: {total_errors:,} | Reviews: {total_reviews:,} | Province : {total_province}")
    print(f" - Tỷ lệ lỗi: {error_rate:.2f}%")
    print(f" - Tổng review từ Việt Nam có comment_positive: {total_viet_positive:,}")
    print(f" - Log: {LOG_ROOT_DIR}/")
    if MODE == "copy" and total_errors:
        print(f" - File lỗi: {main_error_dir}/")
        print("BẮT ĐẦU TẠO DANH SÁCH CRAWL LẠI...")
        run_crawl_again_generator(main_error_dir)  
        print("="*50)
    print("="*70)


if __name__ == "__main__":
    main()