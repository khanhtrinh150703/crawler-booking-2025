# core/file_handler.py
import os
import shutil
from config import MODE, LOG_DIR_INVALID, LOG_DIR_SUMMARY
from utils.helpers import ensure_dir

def copy_error_file(file_path, main_error_dir, *path_parts):
    error_dir_created = False
    current_dir = main_error_dir

    if not os.path.exists(main_error_dir):
        ensure_dir(main_error_dir)
        print(f"Tạo thư mục lỗi chính: {main_error_dir}")
        error_dir_created = True

    for part in path_parts:
        current_dir = os.path.join(current_dir, part)
        ensure_dir(current_dir)

    dest = os.path.join(current_dir, os.path.basename(file_path))
    shutil.copy2(file_path, dest)
    return error_dir_created


def write_invalid_log(filename, header_lines, detail_lines):
    """Ghi log lỗi vào thư mục invalid/"""
    ensure_dir(LOG_DIR_INVALID)
    log_path = os.path.join(LOG_DIR_INVALID, filename)
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(header_lines) + "\n")
        f.write("="*60 + "\n\n")
        if detail_lines:
            f.write("\n".join(detail_lines) + "\n")
        else:
            f.write("KHÔNG TÌM THẤY FILE NÀO CÓ LỖI.\n")
    return log_path


def write_summary_log(filename, lines):
    """Ghi summary vào thư mục summary/ (hoặc invalid nếu không cần tách)"""
    ensure_dir(LOG_DIR_SUMMARY)
    log_path = os.path.join(LOG_DIR_SUMMARY, filename)
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines) + "\n")
    return log_path