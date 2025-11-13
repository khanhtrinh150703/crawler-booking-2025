# core/reporter.py
import os
from config import LOG_DIR_INVALID, LOG_DIR_SUMMARY, FILE_SUMMARY, MODE, PROCESS_BY
from core.file_handler import write_invalid_log, write_summary_log
from utils.helpers import get_timestamp

def write_unit_log(unit_name, error_count, review_count, log_lines, is_range=True):
    mode_str = MODE.upper() if MODE else "LOG ONLY"
    now = get_timestamp().replace("_", " ", 1).replace("_", ":")

    header = [
        f"{'RANGE' if is_range else 'TỈNH'}: {unit_name}",
        f"TỔNG SỐ FILE LỖI: {error_count}",
        f"TỔNG SỐ REVIEWS: {review_count}",
        f"CHẾ ĐỘ: {mode_str}",
        f"THỜI GIAN: {now}"
    ]
    filename = f"invalid_hotels_{unit_name}.txt"
    return write_invalid_log(filename, header, log_lines)  # ← vào invalid/


def write_summary(total_files, total_errors, total_reviews, results):
    error_rate = (total_errors / total_files * 100) if total_files > 0 else 0
    now = get_timestamp().replace("_", " ", 1).replace("_", ":")

    lines = [
        f"TỔNG HỢP LỖI & REVIEWS THEO {PROCESS_BY.upper()}",
        f"THỜI GIAN: {now}",
        f"CHẾ ĐỘ: {MODE.upper() if MODE else 'LOG ONLY'}",
        f"TỔNG SỐ FILE ĐÃ DUYỆT: {total_files}",
        f"TỔNG SỐ FILE LỖI: {total_errors}",
        f"TỔNG SỐ REVIEWS: {total_reviews}",
        f"TỶ LỆ LỖI: {error_rate:.2f}%",
        "="*60,
        ""
    ]

    for key, info in sorted(results.items()):
        status = "CÓ LỖI" if info["count"] > 0 else "KHÔNG LỖI"
        lines.append(f"{key}: {info['count']} file, {info['reviews']} reviews → {os.path.basename(info['log_file'])} [{status}]")

    return write_summary_log(FILE_SUMMARY, lines)  # ← vào summary/


def write_province_review_stats(stats, total_reviews):
    now = get_timestamp().replace("_", " ", 1).replace("_", ":")
    lines = [
        "THỐNG KÊ SỐ REVIEWS THEO TỈNH",
        f"THỜI GIAN: {now}",
        f"TỔNG SỐ REVIEWS: {total_reviews}",
        "="*60,
        ""
    ]
    for prov, rev in sorted(stats.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"{prov}: {rev} reviews")

    return write_summary_log("reviews_by_province.txt", lines)  # ← vào summary/