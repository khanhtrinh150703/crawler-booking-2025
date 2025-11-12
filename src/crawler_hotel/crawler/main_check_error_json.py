import os
import shutil
from datetime import datetime

from error.check_json import check_invalid_evaluation_categories, process_json_file

# ================== CẤU HÌNH ==================
ROOT_DIR = r"D:\private\crawler-booking-2025\src\crawler_hotel\data"
ERROR_ROOT_DIR = "errors_detected"
LOG_DIR = "output_logs"  # <<<< THÊM DÒNG NÀY

MODE = "copy"

def main():
    if not os.path.exists(ROOT_DIR):
        print(f"Thư mục không tồn tại: {ROOT_DIR}")
        return

    # Tạo thư mục log chính
    os.makedirs(LOG_DIR, exist_ok=True)
    print(f"Tất cả log sẽ được lưu vào: {LOG_DIR}/")

    # Tạo thư mục lỗi chính (nếu copy)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    main_error_dir = f"{ERROR_ROOT_DIR}_{timestamp}"
    if MODE == "copy":
        os.makedirs(main_error_dir, exist_ok=True)
        print(f"Tạo thư mục lỗi chính: {main_error_dir}")

    total_error_count = 0
    range_results = {}

    print("Bắt đầu quét các range...")

    for range_folder in sorted(os.listdir(ROOT_DIR)):
        range_path = os.path.join(ROOT_DIR, range_folder)
        if not os.path.isdir(range_path):
            continue

        if not ('-' in range_folder and range_folder.replace('-', '').isdigit()):
            print(f"Bỏ qua thư mục không phải range: {range_folder}")
            continue

        print(f"\n--- Đang xử lý range: {range_folder} ---")
        range_error_count = 0
        range_log_lines = []

        range_error_dir = None
        if MODE == "copy":
            range_error_dir = os.path.join(main_error_dir, range_folder)
            os.makedirs(range_error_dir, exist_ok=True)

        for province_folder in os.listdir(range_path):
            province_path = os.path.join(range_path, province_folder)
            if not os.path.isdir(province_path):
                continue

            province_error_dir = None
            if MODE == "copy":
                province_error_dir = os.path.join(range_error_dir, province_folder)
                os.makedirs(province_error_dir, exist_ok=True)

            for json_file in os.listdir(province_path):
                if not json_file.endswith(".json"):
                    continue

                file_path = os.path.join(province_path, json_file)
                has_error, reason = process_json_file(file_path)

                if has_error:
                    range_error_count += 1
                    total_error_count += 1
                    rel_path = f"{range_folder}/{province_folder}/{json_file}"
                    log_line = f"{rel_path}  [{reason}]"
                    range_log_lines.append(log_line)

                    if MODE == "copy":
                        dest_file = os.path.join(province_error_dir, json_file)
                        shutil.copy2(file_path, dest_file)

        # GHI LOG VÀO THƯ MỤC output_logs/
        range_log_file = os.path.join(LOG_DIR, f"invalid_hotels_{range_folder}.txt")
        with open(range_log_file, 'w', encoding='utf-8') as f:
            if range_error_count > 0:
                f.write(f"RANGE: {range_folder}\n")
                f.write(f"TỔNG SỐ FILE LỖI: {range_error_count}\n")
                f.write(f"CHẾ ĐỘ: {MODE.upper()}\n")
                f.write(f"THỜI GIAN: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("="*60 + "\n\n")
                for line in range_log_lines:
                    f.write(line + "\n")
            else:
                f.write(f"RANGE: {range_folder}\n")
                f.write("KHÔNG TÌM THẤY FILE NÀO CÓ LỖI.\n")

        range_results[range_folder] = {
            "count": range_error_count,
            "log_file": range_log_file
        }

        print(f"Range {range_folder}: {range_error_count} file lỗi → {range_log_file}")

    # GHI TỔNG HỢP VÀO output_logs/
    summary_file = os.path.join(LOG_DIR, "invalid_hotels_summary.txt")
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"TỔNG HỢP LỖI THEO RANGE\n")
        f.write(f"THỜI GIAN: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"CHẾ ĐỘ: {MODE.upper()}\n")
        f.write(f"TỔNG SỐ FILE LỖI: {total_error_count}\n")
        f.write("="*60 + "\n\n")
        for range_folder, info in sorted(range_results.items()):
            status = "CÓ LỖI" if info["count"] > 0 else "KHÔNG LỖI"
            log_name = os.path.basename(info["log_file"])
            f.write(f"{range_folder}: {info['count']} file → {log_name} [{status}]\n")

    print("\n" + "="*60)
    print("HOÀN TẤT!")
    print(f" - Tổng file lỗi: {total_error_count}")
    print(f" - Tất cả log đã lưu vào: {LOG_DIR}/")
    if MODE == "copy" and total_error_count > 0:
        print(f" - File lỗi đã được sao chép vào: {main_error_dir}/")
    print("="*60)

if __name__ == "__main__":
    main()